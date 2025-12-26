from django.urls import path
from .views import (
    VoucherCreateView, CustomerVoucherListView, CustomerVoucherDetailView,
    VoucherRedemptionCreateView, VendorRedemptionHistoryView,
    CustomerPendingRedemptionListView, VoucherRedemptionConfirmView,VoucherRedemptionCancelView,
    AdminVoucherListView, AdminVoucherDetailView,
    VoucherActivateSimulationView, ApprovedVendorsListView, CustomerVoucherWalletView, WalletDepositView
)

urlpatterns = [

    # Customer Voucher Wallet
    path('wallet/', CustomerVoucherWalletView.as_view(), name='customer-voucher-wallet'),
    path('wallet/deposit/', WalletDepositView.as_view(), name='wallet-deposit'),
    
    # Customer Vouchers
    path('create/', VoucherCreateView.as_view(), name='voucher-create'),
    path('my/', CustomerVoucherListView.as_view(), name='customer-voucher-list'),
    path('<int:id>/', CustomerVoucherDetailView.as_view(), name='customer-voucher-detail'),

    # Voucher Activation / Payment Simulation
    path('<int:voucher_id>/activate/', VoucherActivateSimulationView.as_view(), name='voucher-activate'),

    # Approved Vendors by Category
    path('vendors/approved/<str:category>/', ApprovedVendorsListView.as_view(), name='approved-vendors'),

    # Vendor Redemptions
    path('vendor/redemptions/create/', VoucherRedemptionCreateView.as_view(), name='voucher-redemption-create'),
    path('vendor/redemptions/history/', VendorRedemptionHistoryView.as_view(), name='vendor-redemption-history'),

    # Customer Pending Redemptions
    path('redemptions/pending/', CustomerPendingRedemptionListView.as_view(), name='customer-pending-redemptions'),
    path('redemptions/<int:id>/confirm/', VoucherRedemptionConfirmView.as_view(), name='voucher-redemption-confirm'),
    path('redemptions/<int:id>/cancel/', VoucherRedemptionCancelView.as_view(), name='voucher-redemption-cancel'),

    # Admin Voucher Views
    path('admin/vouchers/', AdminVoucherListView.as_view(), name='admin-voucher-list'),
    path('admin/vouchers/<int:id>/', AdminVoucherDetailView.as_view(), name='admin-voucher-detail'),
]
