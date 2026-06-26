from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import Client
from .serializers import ClientSerializer, ClientListSerializer


class ClientListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/clients/       → List all clients for current business
    POST /api/clients/       → Create a new client
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'email', 'company_name', 'phone']
    ordering_fields = ['name', 'created_at', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        CRITICAL: Always filter by business.
        This ensures tenant isolation — users only see their own clients.
        """
        business = self.request.user.business_profile
        queryset = Client.objects.filter(business=business)

        # Optional status filter: /api/clients/?status=active
        status_filter = self.request.query_params.get('status')
        if status_filter in ['active', 'inactive']:
            queryset = queryset.filter(status=status_filter)

        return queryset

    def get_serializer_class(self):
        """Use lightweight serializer for listing, full for creating."""
        if self.request.method == 'GET':
            return ClientListSerializer
        return ClientSerializer

    def perform_create(self, serializer):
        """Auto-attach the business profile on creation."""
        serializer.save(business=self.request.user.business_profile)


class ClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/clients/<id>/  → Get client detail
    PUT    /api/clients/<id>/  → Update client
    DELETE /api/clients/<id>/  → Delete client
    """

    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Tenant isolation — can only access own clients."""
        return Client.objects.filter(
            business=self.request.user.business_profile
        )

    def destroy(self, request, *args, **kwargs):
        client = self.get_object()

        # Prevent deletion if client has invoices
        if client.invoices.exists():
            return Response(
                {'error': 'Cannot delete client with existing invoices. Deactivate them instead.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        client.delete()
        return Response(
            {'message': 'Client deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


class ClientStatsView(APIView):
    """
    GET /api/clients/stats/
    Returns summary statistics for the business's clients.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        business = request.user.business_profile
        clients = Client.objects.filter(business=business)

        stats = {
            'total_clients': clients.count(),
            'active_clients': clients.filter(status='active').count(),
            'inactive_clients': clients.filter(status='inactive').count(),
        }

        return Response(stats)