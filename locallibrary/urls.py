"""
URL configuration for locallibrary project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView


urlpatterns = [
    path('admin/', admin.site.urls),
]

from django.urls import include
urlpatterns += [
    path('catalog/', include('catalog.urls')),
    path('chat/', include('chat.urls')),
]

# Add URL maps to redirect the base URL to our application
from django.views.generic import RedirectView
urlpatterns += [
    path('', RedirectView.as_view(url='catalog/', permanent=True)),
]

# Use static() to add URL mapping to serve static files during development (only)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Add Django site authentication urls (for login, logout, password management)

# Provide a safe logout entry that redirects anonymous users to the login
# page instead of allowing a GET to the logout view (which may expect POST).
from django.contrib.auth.views import LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy

def _safe_logout_view(request, *args, **kwargs):
    """If the visitor isn't authenticated, send them to login instead of
    attempting logout (which could be a POST-only endpoint and return 405).
    Otherwise delegate to Django's LogoutView.
    """
    if not request.user.is_authenticated:
        return redirect(reverse_lazy('login'))
    return LogoutView.as_view()(request, *args, **kwargs)

urlpatterns += [
    # override the logout URL so GETs by anonymous users don't end up at POST-only logout
    path('accounts/logout/', _safe_logout_view, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]

urlpatterns += [
    # Add URL maps to enable language switching
    path('i18n/', include('django.conf.urls.i18n')),
]

