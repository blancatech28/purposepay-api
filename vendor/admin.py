# vendor/admin.py

from django.contrib import admin
from .models import VendorProfile, VendorVerification, VendorFinance, VendorPayoutHistory


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    """Vendor profile admin view."""

    list_display = (
        'business_name','category',
        'phone_number','city',
    )

    list_filter = ('category',)

    search_fields = ('business_name', 'user__username', 'user__email')


@admin.register(VendorVerification)
class VendorVerificationAdmin(admin.ModelAdmin):
    """Verification documents for vendor and approval status admin view."""

    list_display = (
        'vendor','status','owner_id_type',
        'admin_approved_date','last_modified_by',
    )

    list_filter = ('status', 'owner_id_type')

    search_fields = ('vendor__business_name', 'vendor__user__username', 'vendor__user__email')

    readonly_fields = ('admin_approved_date','last_modified_by',)


@admin.register(VendorFinance)
class VendorFinanceAdmin(admin.ModelAdmin):
    """Vendor financial info admin view."""

    list_display = (
        'vendor','balance',
        'payout_account_number','payout_bank_name',
    )

    search_fields = ('vendor__business_name', 'vendor__user__username', 'vendor__user__email')
    readonly_fields = ('balance',)


@admin.register(VendorPayoutHistory)
class VendorPayoutHistoryAdmin(admin.ModelAdmin):
    """"Admin view for vendor payout history"""

    list_display = ('vendor', 'amount', 'created_at', 'processed_by')
    search_fields = ('vendor__business_name','vendor__user__username',)
    readonly_fields = list_display
