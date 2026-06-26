from django.db import models
from apps.accounts.models import BusinessProfile


class ExpenseCategory(models.Model):
    """
    Categories for expenses.
    Some are default (system-wide), some are custom per business.
    """

    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name='expense_categories',
        null=True,
        blank=True  # null = system default category
    )
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=50, blank=True)  # e.g. 'laptop', 'car'
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'expense_categories'
        verbose_name_plural = 'Expense Categories'

    def __str__(self):
        return self.name


class Expense(models.Model):
    """
    A single business expense.
    e.g. 'Bought a laptop for Rs. 120,000'
    """

    PAYMENT_CASH = 'cash'
    PAYMENT_CARD = 'card'
    PAYMENT_BANK = 'bank_transfer'
    PAYMENT_CHEQUE = 'cheque'
    PAYMENT_CHOICES = [
        (PAYMENT_CASH, 'Cash'),
        (PAYMENT_CARD, 'Card'),
        (PAYMENT_BANK, 'Bank Transfer'),
        (PAYMENT_CHEQUE, 'Cheque'),
    ]

    # Tenant isolation
    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name='expenses'
    )

    # Core fields
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_CHOICES,
        default=PAYMENT_CASH
    )

    # Category (set manually or by AI)
    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses'
    )
    ai_categorized = models.BooleanField(default=False)  # Was it AI-categorized?
    ai_confidence = models.FloatField(null=True, blank=True)  # AI confidence score

    # Receipt
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)

    # Vendor
    vendor = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'expenses'
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f'{self.title} - {self.amount}'