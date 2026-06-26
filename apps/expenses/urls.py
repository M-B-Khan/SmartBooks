from django.urls import path
from . import views

urlpatterns = [
    path('', views.ExpenseListCreateView.as_view(), name='expense_list_create'),
    path('stats/', views.ExpenseStatsView.as_view(), name='expense_stats'),
    path('categories/', views.ExpenseCategoryListView.as_view(), name='category_list'),
    path('ai-categorize/', views.AICategorizeView.as_view(), name='ai_categorize'),
    path('<int:pk>/', views.ExpenseDetailView.as_view(), name='expense_detail'),
]