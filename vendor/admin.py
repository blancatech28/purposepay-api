# vendor/admin.py


from django.contrib import admin
from .models import VendorProfile


@admin.register(VendorProfile)
class VendorProfileAdmin(admin.ModelAdmin):
    """Vendor profile admin view."""
  

    list_display = (
        'business_name',
        'category',
        'status',
        'city',
        'balance',
    )

    list_filter = ('status', 'category')

    search_fields = ('business_name', 'user__username', 'user__email')

    readonly_fields = (
        'admin_approved_date',
        'last_modified_by',
    )

