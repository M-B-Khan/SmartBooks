from django.db import models
from apps.accounts.models import BusinessProfile


class Client(models.Model):
    """
    A client belongs to a BusinessProfile (multi-tenant).
    One business can have many clients.
    """

    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    # Tenant isolation — every client belongs to one business
    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name='clients'
    )

    # Client info
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, default='Pakistan')
    company_name = models.CharField(max_length=100, blank=True)
    tax_number = models.CharField(max_length=50, blank=True)  # NTN

    # Status
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE
    )
    notes = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients'
        ordering = ['-created_at']
        # Same email can exist across different businesses (multi-tenant)
        unique_together = ['business', 'email']

    def __str__(self):
        return f'{self.name} ({self.business.business_name})'

    @property
    def total_invoiced(self):
        """Total amount invoiced to this client."""
        return self.invoices.aggregate(
            total=models.Sum('total_amount')
        )['total'] or 0

    @property
    def outstanding_amount(self):
        """Total unpaid amount from this client."""
        from django.db.models import Sum
        return self.invoices.filter(
            status__in=['sent', 'overdue']
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or 0