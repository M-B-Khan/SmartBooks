from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'company_name', 'business', 'status', 'created_at']
    list_filter = ['status', 'country', 'created_at']
    search_fields = ['name', 'email', 'company_name']
    ordering = ['-created_at']

    readonly_fields = ['created_at', 'updated_at']