"""
Project-level URL configuration for tasknest.

Includes each vertical slice's own urls.py per Section 7.3 of the spec.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('tasks/', include('tasks.urls')),
    # Root of the site sends visitors straight to the dashboard
    # (redirects to Login automatically if not authenticated).
    path('', RedirectView.as_view(pattern_name='tasks:dashboard', permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)