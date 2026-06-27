from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.invoices.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API routes
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/accounts/', include('apps.accounts.urls')),
    path('api/clients/', include('apps.clients.urls')),
    path('api/invoices/', include('apps.invoices.urls')),
    path('api/expenses/', include('apps.expenses.urls')), 

    # Swagger docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)