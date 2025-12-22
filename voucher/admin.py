from django.contrib import admin
from .models import Voucher, VoucherRedemption

# Voucher model Admin registration
@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = (
        "code","customer","category","status","initial_amount",
        "remaining_balance","expiry_date","created_at",
    )

    list_filter = ("status", "category")
    search_fields = ("code", "customer__email", "customer__username")
    ordering = ("-created_at",)

    readonly_fields = ("code","remaining_balance","created_at",)


# Register VoucherRedemption model in admin
@admin.register(VoucherRedemption)
class VoucherRedemptionAdmin(admin.ModelAdmin):
    list_display = ("voucher","vendor","redeemed_amount","redemption_status","redeemed_at",)

    list_filter = ("redemption_status",)
    search_fields = ("voucher__code", "vendor__business_name")
    ordering = ("-redeemed_at",)

    readonly_fields = ("voucher","vendor","redeemed_amount","redemption_status","redeemed_at",)
