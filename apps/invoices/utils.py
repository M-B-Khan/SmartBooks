from django.utils import timezone


def generate_invoice_number(business):
    """
    Generates a unique invoice number per business.
    Format: INV-2024-0001
    Resets count per year.
    """
    from .models import Invoice

    year = timezone.now().year
    prefix = f'INV-{year}'

    # Count invoices this year for this business
    count = Invoice.objects.filter(
        business=business,
        invoice_number__startswith=prefix
    ).count()

    # Zero-pad to 4 digits
    number = str(count + 1).zfill(4)
    return f'{prefix}-{number}'