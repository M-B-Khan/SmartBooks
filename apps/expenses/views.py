from rest_framework import generics, status, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Sum, Count
from django.db.models.functions import TruncMonth

from .models import Expense, ExpenseCategory
from .serializers import (
    ExpenseSerializer,
    ExpenseListSerializer,
    ExpenseCategorySerializer,
    AICategorizeSerializer,
)
from apps.ai_engine.categorizer import categorize_expense


class ExpenseCategoryListView(generics.ListCreateAPIView):
    """
    GET  /api/expenses/categories/  → List all categories
    POST /api/expenses/categories/  → Create custom category
    """

    serializer_class = ExpenseCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        business = self.request.user.business_profile
        # Return default categories + business custom categories
        from django.db.models import Q
        return ExpenseCategory.objects.filter(
            Q(is_default=True) | Q(business=business)
        )

    def perform_create(self, serializer):
        serializer.save(business=self.request.user.business_profile)


class ExpenseListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/expenses/  → List all expenses
    POST /api/expenses/  → Create expense (AI auto-categorizes if no category given)
    """

    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'vendor']
    ordering_fields = ['date', 'amount', 'created_at']
    ordering = ['-date']

    def get_queryset(self):
        business = self.request.user.business_profile
        queryset = Expense.objects.filter(
            business=business
        ).select_related('category')

        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        # Filter by date range
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        return queryset

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ExpenseListSerializer
        return ExpenseSerializer

    def perform_create(self, serializer):
        business = self.request.user.business_profile

        # If no category provided — use AI to categorize
        category = serializer.validated_data.get('category')
        ai_categorized = False
        ai_confidence = None

        if not category:
            title = serializer.validated_data.get('title', '')
            description = serializer.validated_data.get('description', '')

            result = categorize_expense(title, description)

            try:
                category = ExpenseCategory.objects.get(name=result['category'])
                ai_categorized = True
                ai_confidence = result['confidence']
            except ExpenseCategory.DoesNotExist:
                pass

        serializer.save(
            business=business,
            category=category,
            ai_categorized=ai_categorized,
            ai_confidence=ai_confidence,
        )


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/expenses/<id>/  → Get expense detail
    PUT    /api/expenses/<id>/  → Update expense
    DELETE /api/expenses/<id>/  → Delete expense
    """

    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(
            business=self.request.user.business_profile
        )


class AICategorizeView(APIView):
    """
    POST /api/expenses/ai-categorize/
    Predict category for an expense without saving it.
    Useful for showing suggestions in the frontend form.
    """
    serializer_class = AICategorizeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = AICategorizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = categorize_expense(
            serializer.validated_data['title'],
            serializer.validated_data.get('description', '')
        )

        return Response({
            'suggested_category': result['category'],
            'confidence': result['confidence'],
            'confidence_percent': f"{result['confidence'] * 100:.0f}%",
            'method': result['method'],
        })


class ExpenseStatsView(APIView):
    """
    GET /api/expenses/stats/
    Spending summary — total, by category, by month.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        business = request.user.business_profile
        expenses = Expense.objects.filter(business=business)

        # Date range filter
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        if date_from:
            expenses = expenses.filter(date__gte=date_from)
        if date_to:
            expenses = expenses.filter(date__lte=date_to)

        # Total spending
        total = expenses.aggregate(total=Sum('amount'))['total'] or 0

        # By category
        by_category = expenses.values(
            'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')

        # By month (last 6 months)
        by_month = expenses.annotate(
            month=TruncMonth('date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')

        # AI categorization rate
        ai_count = expenses.filter(ai_categorized=True).count()
        total_count = expenses.count()
        ai_rate = (ai_count / total_count * 100) if total_count > 0 else 0

        return Response({
            'total_spending': total,
            'total_expenses': total_count,
            'by_category': list(by_category),
            'by_month': list(by_month),
            'ai_categorization_rate': f'{ai_rate:.1f}%',
        })