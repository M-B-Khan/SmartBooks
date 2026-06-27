from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

logger = get_task_logger(__name__)


@shared_task
def send_invoice_email(invoice_id):
    """
    Background task: sends invoice to client via email.
    Triggered when invoice status changes to 'sent'.
    """
    from .models import Invoice

    try:
        invoice = Invoice.objects.select_related(
            'client', 'business'
        ).get(id=invoice_id)

        send_mail(
            subject=f'Invoice {invoice.invoice_number} from {invoice.business.business_name}',
            message=f"""
Dear {invoice.client.name},

Please find your invoice details below:

Invoice Number : {invoice.invoice_number}
Issue Date     : {invoice.issue_date}
Due Date       : {invoice.due_date}
Amount Due     : {invoice.business.currency} {invoice.total_amount}

Please ensure payment is made before the due date.

{invoice.notes}

Regards,
{invoice.business.business_name}
{invoice.business.business_email}
{invoice.business.phone}
            """,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[invoice.client.email],
            fail_silently=False,
        )

        logger.info(f'Invoice email sent for {invoice.invoice_number}')

    except Invoice.DoesNotExist:
        logger.error(f'Invoice {invoice_id} not found')
    except Exception as e:
        logger.error(f'Failed to send invoice email: {e}')
        raise  # Re-raise so Celery marks task as failed


@shared_task
def send_overdue_reminders():
    """
    Periodic task: runs daily and sends reminders for all overdue invoices.
    Configured in Celery Beat schedule below.
    """
    from .models import Invoice

    today = timezone.localdate()

    overdue_invoices = Invoice.objects.filter(
        status=Invoice.STATUS_OVERDUE
    ).select_related('client', 'business')

    sent_count = 0

    for invoice in overdue_invoices:
        try:
            days_overdue = (today - invoice.due_date).days

            send_mail(
                subject=f'Payment Reminder: Invoice {invoice.invoice_number} is Overdue',
                message=f"""
Dear {invoice.client.name},

This is a reminder that the following invoice is overdue:

Invoice Number : {invoice.invoice_number}
Due Date       : {invoice.due_date}
Days Overdue   : {days_overdue} days
Amount Due     : {invoice.business.currency} {invoice.total_amount}

Please arrange payment at your earliest convenience.
If you have already made payment, please disregard this reminder.

Regards,
{invoice.business.business_name}
{invoice.business.business_email}
                """,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[invoice.client.email],
                fail_silently=True,  # Don't crash if one email fails
            )
            sent_count += 1

        except Exception as e:
            logger.error(
                f'Failed to send reminder for invoice {invoice.invoice_number}: {e}'
            )

    logger.info(f'Overdue reminders sent: {sent_count}')
    return f'{sent_count} reminders sent'


@shared_task
def update_overdue_statuses():
    """
    Periodic task: runs daily and marks sent invoices as overdue
    if their due date has passed.
    """
    from .models import Invoice

    today = timezone.localdate()

    updated = Invoice.objects.filter(
        status=Invoice.STATUS_SENT,
        due_date__lt=today
    ).update(status=Invoice.STATUS_OVERDUE)

    logger.info(f'Marked {updated} invoices as overdue')
    return f'{updated} invoices marked overdue'