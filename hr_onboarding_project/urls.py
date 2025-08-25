"""
HR Onboarding System URL Configuration

Main URL routing for the application.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

def redirect_to_onboarding(request):
    """Redirect root URL to onboarding dashboard."""
    return redirect('onboarding:dashboard')

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Main application
    path('onboarding/', include('onboarding.urls')),
    
    # Root redirect
    path('', redirect_to_onboarding, name='home'),
    
    # API endpoints (handled by onboarding app)
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Customize admin site
admin.site.site_header = "NXZEN Ticketing System Administration"
admin.site.site_title = "NXZEN Ticketing Admin"
admin.site.index_title = "Welcome to NXZEN Ticketing System Administration"
