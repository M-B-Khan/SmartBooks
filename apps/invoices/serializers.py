from rest_framework import serializers
from .models import Invoice, InvoiceItem
from apps.clients.serializers import ClientListSerializer


class InvoiceItemSerializer(serializers.ModelSerializer):

    class Meta:
        model = InvoiceItem
        fields = ['id', 'description', 'quantity', 'unit_price', 'total_price']
        read_only_fields = ['id', 'total_price']


class InvoiceSerializer(serializers.ModelSerializer):
    """Full invoice serializer — used for create and detail view."""

    items = InvoiceItemSerializer(many=True)
    client_detail = ClientListSerializer(source='client', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    days_overdue = serializers.ReadOnlyField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'status',
            'client', 'client_detail',
            'issue_date', 'due_date',
            'subtotal', 'tax_rate', 'tax_amount',
            'discount_amount', 'total_amount',
            'notes', 'terms',
            'is_overdue', 'days_overdue',
            'items',
            'created_at', 'updated_at', 'paid_at',
        ]
        read_only_fields = [
            'id', 'invoice_number', 'subtotal',
            'tax_amount', 'total_amount',
            'created_at', 'updated_at', 'paid_at',
        ]

    def validate_client(self, client):
        """Ensure client belongs to the same business."""
        request = self.context['request']
        if client.business != request.user.business_profile:
            raise serializers.ValidationError('Client does not belong to your business.')
        return client

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError('Invoice must have at least one item.')
        return items

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        business = self.context['request'].user.business_profile

        # Generate invoice number
        from .utils import generate_invoice_number
        invoice_number = generate_invoice_number(business)

        # Create invoice
        invoice = Invoice.objects.create(
            business=business,
            invoice_number=invoice_number,
            **validated_data
        )

        # Create line items
        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)

        # Calculate totals
        invoice.calculate_totals()

        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)

        # Update invoice fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Replace line items if provided
        if items_data is not None:
            instance.items.all().delete()
            for item_data in items_data:
                InvoiceItem.objects.create(invoice=instance, **item_data)

        instance.calculate_totals()
        return instance


class InvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for invoice list view."""

    client_name = serializers.CharField(source='client.name', read_only=True)
    is_overdue = serializers.ReadOnlyField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'client_name',
            'status', 'issue_date', 'due_date',
            'total_amount', 'is_overdue'
        ]