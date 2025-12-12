from rest_framework import permissions

class IsVendorOwner(permissions.BasePermission):
    """
    Allow access only to the vendor who owns the profile.
    """

    def has_object_permission(self, request, view, obj):
        # obj is the VendorProfile instance
        return obj.user == request.user
