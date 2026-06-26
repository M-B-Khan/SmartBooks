from rest_framework import serializers
from .models import Expense, ExpenseCategory


class ExpenseCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'description', 'icon', 'is_default']


class ExpenseSerializer(serializers.ModelSerializer):
    """Full serializer for creating and updating expenses."""

    category_detail = ExpenseCategorySerializer(source='category', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'title', 'description', 'amount', 'date',
            'payment_method', 'category', 'category_detail',
            'ai_categorized', 'ai_confidence',
            'vendor', 'receipt',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'ai_categorized', 'ai_confidence',
            'created_at', 'updated_at'
        ]

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than zero.')
        return value


class ExpenseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing expenses."""

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Expense
        fields = [
            'id', 'title', 'amount', 'date',
            'payment_method', 'category_name',
            'ai_categorized', 'vendor'
        ]


class AICategorizeSerializer(serializers.Serializer):
    """Input serializer for AI categorization endpoint."""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, default='')