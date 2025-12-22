# voucher/permissions.py

from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    """
    Only allows access to users with the 'is_customer' attribute set to True.
    """

    def has_permission(self, request, view):
        return bool(request.user.is_customer)
