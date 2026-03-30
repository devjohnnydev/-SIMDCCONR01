"""
URL configuration for SaaS NR-01 project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', RedirectView.as_view(pattern_name='accounts:dashboard'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('companies/', include('companies.urls')),
    path('employees/', include('employees.urls')),
    path('forms/', include('forms_builder.urls')),
    path('reports/', include('reports.urls')),
    path('billing/', include('billing.urls')),
    path('api/', include('accounts.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
