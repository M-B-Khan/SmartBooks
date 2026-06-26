from django.urls import path
from . import views

urlpatterns = [
    path('', views.ClientListCreateView.as_view(), name='client_list_create'),
    path('stats/', views.ClientStatsView.as_view(), name='client_stats'),
    path('<int:pk>/', views.ClientDetailView.as_view(), name='client_detail'),
]