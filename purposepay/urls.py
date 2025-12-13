"""
URL configuration for purposepay project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
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
from django.conf import settings
from django.urls import re_path
from django.views.static import serve

urlpatterns = [
    # Admin panel
    path("admin/", admin.site.urls),

    # Auth routes: only login/logout
    # Using namespace 'auth' for reverse lookups: auth:login, auth:logout
    path('auth/', include(('accounts.urls', 'accounts'), namespace='auth')),

    # Account routes: registration, profile, etc.
    # Namespace 'accounts' for reverse lookups: accounts:register, accounts:profile
    path('account/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # Vendor routes
    path('vendor/', include(('vendor.urls', 'vendor'), namespace='vendor')),

] 

# Serving static files for vendor-related documents
urlpatterns += [
    re_path(r'^vendor_ids/(?P<path>.*)$', serve, {'document_root': settings.VENDOR_ID_DIR}),
    re_path(r'^vendor_certificates/(?P<path>.*)$', serve, {'document_root': settings.VENDOR_CERT_DIR}),
    re_path(r'^vendor_locations/(?P<path>.*)$', serve, {'document_root': settings.VENDOR_LOCATION_DIR}),
]

