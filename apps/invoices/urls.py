from django.urls import path
from . import views

urlpatterns = [
    path('', views.InvoiceListCreateView.as_view(), name='invoice_list_create'),
    path('stats/', views.InvoiceStatsView.as_view(), name='invoice_stats'),
    path('<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('<int:pk>/status/', views.InvoiceStatusUpdateView.as_view(), name='invoice_status'),
    path('<int:pk>/pdf/', views.InvoicePDFView.as_view(), name='invoice_pdf'),
]