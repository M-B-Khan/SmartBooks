from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone

from .models import Invoice
from .serializers import InvoiceSerializer, InvoiceListSerializer
from .tasks import send_invoice_email
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import serializers as drf_serializers

class InvoiceListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/invoices/   → List all invoices
    POST /api/invoices/   → Create new invoice with line items
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'client__name']
    ordering_fields = ['issue_date', 'due_date', 'total_amount', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        business = self.request.user.business_profile
        queryset = Invoice.objects.filter(business=business).select_related('client')

        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter overdue
        overdue = self.request.query_params.get('overdue')
        if overdue == 'true':
            queryset = queryset.filter(
                status__in=['sent', 'overdue'],
                due_date__lt=timezone.now().date()
            )

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return InvoiceListSerializer
        return InvoiceSerializer


class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/invoices/<id>/  → Invoice detail with all line items
    PUT    /api/invoices/<id>/  → Update invoice
    DELETE /api/invoices/<id>/  → Delete invoice (only draft)
    """

    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Invoice.objects.filter(
            business=self.request.user.business_profile
        ).prefetch_related('items')

    def destroy(self, request, *args, **kwargs):
        invoice = self.get_object()
        if invoice.status != Invoice.STATUS_DRAFT:
            return Response(
                {'error': 'Only draft invoices can be deleted.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        invoice.delete()
        return Response(
            {'message': 'Invoice deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )

# Add this small inline serializer above the view
class StatusUpdateSerializer(drf_serializers.Serializer):
    status = drf_serializers.ChoiceField(
        choices=['sent', 'paid', 'cancelled'],
        help_text="New status for the invoice"
    )

class InvoiceStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=StatusUpdateSerializer,
        examples=[
            OpenApiExample(
                'Mark as Sent',
                value={'status': 'sent'}
            ),
            OpenApiExample(
                'Mark as Paid',
                value={'status': 'paid'}
            ),
        ]
    )
    def post(self, request, pk):
        invoice = get_object_or_404(
            Invoice,
            pk=pk,
            business=request.user.business_profile
        )

        new_status = request.data.get('status')

        if not new_status:
            return Response(
                {'error': 'Status is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_status = new_status.strip().lower()

        valid_transitions = {
            Invoice.STATUS_DRAFT: [Invoice.STATUS_SENT, Invoice.STATUS_CANCELLED],
            Invoice.STATUS_SENT: [Invoice.STATUS_PAID, Invoice.STATUS_CANCELLED],
            Invoice.STATUS_OVERDUE: [Invoice.STATUS_PAID, Invoice.STATUS_CANCELLED],
        }

        allowed = valid_transitions.get(invoice.status, [])
        if new_status not in allowed:
            return Response(
                {'error': f'Cannot transition from "{invoice.status}" to "{new_status}". Allowed: {allowed}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_status == Invoice.STATUS_PAID:
            invoice.mark_as_paid()
        else:
            invoice.status = new_status
            invoice.save(update_fields=['status'])

        if new_status == Invoice.STATUS_SENT:
            from .tasks import send_invoice_email
            send_invoice_email(invoice.id)

        return Response({
            'message': f'Invoice marked as {new_status}.',
            'status': invoice.status
        })


class InvoicePDFView(APIView):
    """
    GET /api/invoices/<id>/pdf/
    Generate and return invoice as PDF.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        invoice = get_object_or_404(
            Invoice,
            pk=pk,
            business=request.user.business_profile
        )

        try:
            from weasyprint import HTML
            business = request.user.business_profile

            html_string = render_to_string('invoices/invoice_pdf.html', {
                'invoice': invoice,
                'business': business,
            })

            pdf_file = HTML(string=html_string).write_pdf()

            response = HttpResponse(pdf_file, content_type='application/pdf')
            response['Content-Disposition'] = (
                f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
            )
            return response

        except Exception as e:
            return Response(
                {'error': f'PDF generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InvoiceStatsView(APIView):
    """
    GET /api/invoices/stats/
    Dashboard statistics for invoices.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Sum, Count
        business = request.user.business_profile
        invoices = Invoice.objects.filter(business=business)

        stats = {
            'total_invoices': invoices.count(),
            'total_revenue': invoices.filter(
                status='paid'
            ).aggregate(total=Sum('total_amount'))['total'] or 0,

            'outstanding': invoices.filter(
                status__in=['sent', 'overdue']
            ).aggregate(total=Sum('total_amount'))['total'] or 0,

            'overdue_count': invoices.filter(
                status='overdue'
            ).count(),

            'by_status': invoices.values('status').annotate(
                count=Count('id'),
                amount=Sum('total_amount')
            ),
        }

        return Response(stats)

from .dashboard import get_dashboard_data


class DashboardView(APIView):
    """
    GET /api/dashboard/
    Returns complete financial summary for the business.
    The frontend uses this single endpoint to populate the dashboard.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        business = request.user.business_profile
        data = get_dashboard_data(business)
        return Response(data)