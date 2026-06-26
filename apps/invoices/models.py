from django.db import models
from django.utils import timezone
from apps.accounts.models import BusinessProfile
from apps.clients.models import Client


class Invoice(models.Model):
    """
    Core invoice model.
    Each invoice belongs to a business and is sent to a client.
    """

    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_PAID = 'paid'
    STATUS_OVERDUE = 'overdue'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SENT, 'Sent'),
        (STATUS_PAID, 'Paid'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    # Tenant isolation
    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,  # Protect — don't delete client if invoice exists
        related_name='invoices'
    )

    # Invoice identity
    invoice_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_DRAFT)

    # Dates
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField()

    # Amounts (calculated from line items)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # e.g. 17.00 for 17%
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Extra
    notes = models.TextField(blank=True)
    terms = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.invoice_number} - {self.client.name}'

    def calculate_totals(self):
        """Recalculate totals from line items."""
        self.subtotal = sum(item.total_price for item in self.items.all())
        self.tax_amount = (self.subtotal * self.tax_rate) / 100
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        self.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])

    def mark_as_paid(self):
        self.status = self.STATUS_PAID
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at'])

    def check_overdue(self):
        """Mark invoice as overdue if past due date and not paid."""
        if (
            self.status == self.STATUS_SENT and
            self.due_date < timezone.now().date()
        ):
            self.status = self.STATUS_OVERDUE
            self.save(update_fields=['status'])
            return True
        return False

    @property
    def is_overdue(self):
        return (
            self.status in [self.STATUS_SENT, self.STATUS_OVERDUE] and
            self.due_date < timezone.now().date()
        )

    @property
    def days_overdue(self):
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0


class InvoiceItem(models.Model):
    """
    A single line item on an invoice.
    e.g. 'Web Development - 10 hours @ Rs.5000/hr = Rs.50,000'
    """

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'invoice_items'

    def save(self, *args, **kwargs):
        """Auto-calculate total price before saving."""
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.description} x {self.quantity}'