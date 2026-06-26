from rest_framework import serializers
from .models import Client


class ClientSerializer(serializers.ModelSerializer):
    """Full serializer for creating and updating clients."""

    total_invoiced = serializers.ReadOnlyField()
    outstanding_amount = serializers.ReadOnlyField()

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'email', 'phone', 'address',
            'city', 'country', 'company_name', 'tax_number',
            'status', 'notes', 'total_invoiced', 'outstanding_amount',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_email(self, value):
        """
        Ensure email is unique per business.
        We get the business from the request context.
        """
        request = self.context.get('request')
        business = request.user.business_profile

        queryset = Client.objects.filter(business=business, email=value)

        # On update, exclude the current instance
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                'A client with this email already exists in your business.'
            )
        return value


class ClientListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing clients (less data = faster response)."""

    class Meta:
        model = Client
        fields = [
            'id', 'name', 'email', 'phone',
            'company_name', 'status', 'total_invoiced'
        ]