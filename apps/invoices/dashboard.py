from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta

from .models import Invoice
from apps.expenses.models import Expense


def get_dashboard_data(business):
    """
    Returns complete financial summary for a business.
    Called by the dashboard API endpoint.
    """

    today = timezone.localdate()
    first_day_this_month = today.replace(day=1)
    first_day_last_month = (first_day_this_month - timedelta(days=1)).replace(day=1)

    invoices = Invoice.objects.filter(business=business)
    expenses = Expense.objects.filter(business=business)

    # ── Auto-update overdue invoices ──────────────────────────────
    overdue_candidates = invoices.filter(
        status=Invoice.STATUS_SENT,
        due_date__lt=today
    )
    overdue_candidates.update(status=Invoice.STATUS_OVERDUE)

    # ── Revenue ───────────────────────────────────────────────────
    total_revenue = invoices.filter(
        status=Invoice.STATUS_PAID
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    revenue_this_month = invoices.filter(
        status=Invoice.STATUS_PAID,
        paid_at__date__gte=first_day_this_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    revenue_last_month = invoices.filter(
        status=Invoice.STATUS_PAID,
        paid_at__date__gte=first_day_last_month,
        paid_at__date__lt=first_day_this_month
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # ── Revenue growth ────────────────────────────────────────────
    if revenue_last_month > 0:
        revenue_growth = (
            (revenue_this_month - revenue_last_month) / revenue_last_month * 100
        )
    else:
        revenue_growth = 100.0 if revenue_this_month > 0 else 0.0

    # ── Outstanding & Overdue ─────────────────────────────────────
    outstanding = invoices.filter(
        status__in=[Invoice.STATUS_SENT, Invoice.STATUS_OVERDUE]
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    overdue_amount = invoices.filter(
        status=Invoice.STATUS_OVERDUE
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    overdue_invoices = invoices.filter(
        status=Invoice.STATUS_OVERDUE
    ).select_related('client').values(
        'id', 'invoice_number',
        'client__name', 'total_amount',
        'due_date'
    )[:5]  # Top 5 most urgent

    # ── Expenses ──────────────────────────────────────────────────
    total_expenses = expenses.aggregate(
        total=Sum('amount')
    )['total'] or 0

    expenses_this_month = expenses.filter(
        date__gte=first_day_this_month
    ).aggregate(total=Sum('amount'))['total'] or 0

    # ── Net Profit ────────────────────────────────────────────────
    net_profit = total_revenue - total_expenses
    net_profit_this_month = revenue_this_month - expenses_this_month

    # ── Invoice breakdown ─────────────────────────────────────────
    invoice_breakdown = invoices.values('status').annotate(
        count=Count('id'),
        total=Sum('total_amount')
    )

    # ── Revenue by month (last 6 months) ─────────────────────────
    six_months_ago = today - timedelta(days=180)

    revenue_by_month = invoices.filter(
        status=Invoice.STATUS_PAID,
        paid_at__date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('paid_at')
    ).values('month').annotate(
        revenue=Sum('total_amount'),
        count=Count('id')
    ).order_by('month')

    expenses_by_month = expenses.filter(
        date__gte=six_months_ago
    ).annotate(
        month=TruncMonth('date')
    ).values('month').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('month')

    # ── Top expense categories ────────────────────────────────────
    top_categories = expenses.values(
        'category__name'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')[:5]

    # ── Recent activity ───────────────────────────────────────────
    recent_invoices = invoices.select_related(
        'client'
    ).values(
        'id', 'invoice_number', 'client__name',
        'total_amount', 'status', 'created_at'
    ).order_by('-created_at')[:5]

    recent_expenses = expenses.select_related(
        'category'
    ).values(
        'id', 'title', 'amount',
        'category__name', 'date'
    ).order_by('-created_at')[:5]

    return {
        # Summary cards
        'summary': {
            'total_revenue': total_revenue,
            'revenue_this_month': revenue_this_month,
            'revenue_last_month': revenue_last_month,
            'revenue_growth_percent': round(revenue_growth, 1),
            'outstanding_amount': outstanding,
            'overdue_amount': overdue_amount,
            'total_expenses': total_expenses,
            'expenses_this_month': expenses_this_month,
            'net_profit': net_profit,
            'net_profit_this_month': net_profit_this_month,
        },

        # Invoice stats
        'invoices': {
            'breakdown': list(invoice_breakdown),
            'overdue_list': list(overdue_invoices),
        },

        # Charts data
        'charts': {
            'revenue_by_month': list(revenue_by_month),
            'expenses_by_month': list(expenses_by_month),
            'top_expense_categories': list(top_categories),
        },

        # Recent activity feed
        'recent_activity': {
            'invoices': list(recent_invoices),
            'expenses': list(recent_expenses),
        },
    }