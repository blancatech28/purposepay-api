from rest_framework import permissions
from .models import VendorVerification
from rest_framework.exceptions import PermissionDenied

class IsVendorOwner(permissions.BasePermission):
    """Allow access only to the vendor who owns the profile."""

    def has_object_permission(self, request, view, obj):
        # obj is the VendorProfile instance
        return obj.user == request.user



class IsApprovedVendor(permissions.BasePermission):
    """
    This permission allows access only to vendors who:
    - checked is_vendor = True during registration
    - have a vendor profile
    - have a vendor verification record
    - and is approved
    """

    def has_permission(self, request, view):
        user = request.user

        # User must be marked as vendor
        if not getattr(user, "is_vendor", False):
            raise PermissionDenied("Only vendors can access this endpoint.")

        # The vendor must have a vendor profile
        vendor = getattr(user, "vendor_profile", None)
        if vendor is None:
            raise PermissionDenied(
                "Vendor profile not found. Please complete the vendor profile setup."
            )

        # Vendor must have a verification record
        verification = getattr(vendor, "verification", None)
        if verification is None:
            raise PermissionDenied(
                "Vendor verification not found. Please complete the vendor verification first."
            )

        # The vendor verification status must be approved
        if verification.status != VendorVerification.APPROVED:
            raise PermissionDenied(
                "The Vendor is not approved yet."
            )

        return True
