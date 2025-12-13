# accounts/admin.py
from django.contrib import admin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Admin view for users."""

    list_display = (
        'email','username','is_vendor',
        'is_customer','is_staff','is_active',
    )

    list_filter = (
        'is_vendor','is_customer',
        'is_staff','is_active',
    )

    search_fields = ('email','username',)
