# vendor/urls.py

from django.urls import path
from .views import (
    VendorSelfView,VendorCreateView,
    VendorPublicListView,VendorPublicDetailView,
    VendorAdminListView,VendorAdminDetailView,
    VendorPayoutView,VendorApproveView,VendorRejectView,VendorTopUpView
)


urlpatterns = [
    # Vendor self profile endpoint
    path('me/', VendorSelfView.as_view(), name='vendor-self'),

    # Endpoint to create vendor profile
    path('create/', VendorCreateView.as_view(), name='vendor-create'),

    # vendor list & detail for public (authenticated users only)
    path('public/', VendorPublicListView.as_view(), name='vendor-public-list'),
    path('public/<int:pk>/', VendorPublicDetailView.as_view(), name='vendor-public-detail'),

    # Endpoint for admin to view vendor list & detail
    path('admin/', VendorAdminListView.as_view(), name='vendor-admin-list'),
    path('admin/<int:pk>/', VendorAdminDetailView.as_view(), name='vendor-admin-detail'),

    # Admin approve/reject vendor profile endpoints
    path('admin/<int:pk>/approve/', VendorApproveView.as_view(), name='vendor-approve'),
    path('admin/<int:pk>/reject/', VendorRejectView.as_view(), name='vendor-reject'),

    # Vendor payout endpoint
    path('payout/', VendorPayoutView.as_view(), name='vendor-payout'),

    # Temporary vendor top-up endpoint (for testing purposes)
    path('top-up/', VendorTopUpView.as_view(), name='vendor-top-up'),
    
]



