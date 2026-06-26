from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_invoice_email(invoice_id):
    """Send invoice notification email to client."""
    from .models import Invoice

    try:
        invoice = Invoice.objects.select_related(
            'client', 'business'
        ).get(id=invoice_id)

        send_mail(
            subject=f'Invoice {invoice.invoice_number} from {invoice.business.business_name}',
            message=f"""
Dear {invoice.client.name},

Please find attached invoice {invoice.invoice_number}.

Amount Due: {invoice.business.currency} {invoice.total_amount}
Due Date: {invoice.due_date}

Please ensure payment is made before the due date.

Thank you for your business.

— {invoice.business.business_name}
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[invoice.client.email],
            fail_silently=False,
        )
    except Invoice.DoesNotExist:
        pass


@shared_task
def check_overdue_invoices():
    """
    Periodic task — runs daily via Celery Beat.
    Marks all past-due invoices as overdue automatically.
    """
    from .models import Invoice
    from django.utils import timezone

    overdue_invoices = Invoice.objects.filter(
        status='sent',
        due_date__lt=timezone.now().date()
    )

    count = 0
    for invoice in overdue_invoices:
        invoice.status = 'overdue'
        invoice.save(update_fields=['status'])
        count += 1

    return f'{count} invoices marked as overdue.'