from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """""Admin interface for the CustomUser model."""""
    model = CustomUser

    list_display = (
        "email","username","is_vendor","is_customer",
        "is_staff","is_active",
    )

    list_filter = ("is_vendor", "is_customer", "is_staff", "is_active")
    search_fields = ("email", "username")
    ordering = ("email",)

    # Editing an existing user
    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("PurposePay Roles", {"fields": ("is_vendor", "is_customer")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active","is_staff","is_superuser",
                    "groups","user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Creating a new user
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email","username","password1",
                    "password2","is_vendor","is_customer",
                    "is_active","is_staff",
                ),
            },
        ),
    )
