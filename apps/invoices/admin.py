from django.contrib import admin
from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    readonly_fields = ['total_price']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'client', 'status', 'total_amount', 'due_date', 'is_overdue']
    list_filter = ['status', 'issue_date', 'due_date']
    search_fields = ['invoice_number', 'client__name']
    readonly_fields = ['invoice_number', 'subtotal', 'tax_amount', 'total_amount', 'created_at', 'updated_at']
    inlines = [InvoiceItemInline]