from django.contrib import admin
from .models import Expense, ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_default', 'business']
    list_filter = ['is_default']
    search_fields = ['name']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'amount', 'date', 'category',
        'payment_method', 'ai_categorized', 'business'
    ]
    list_filter = ['category', 'payment_method', 'ai_categorized']
    search_fields = ['title', 'vendor', 'description']
    readonly_fields = ['ai_categorized', 'ai_confidence', 'created_at', 'updated_at']