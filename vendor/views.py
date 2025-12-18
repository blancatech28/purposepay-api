# vendor/views.py

from rest_framework import generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import VendorProfile, VendorVerification
from .serializers import (
    VendorReadSerializer, VendorPublicReadSerializer,
    VendorProfileCreateSerializer, VendorProfileUpdateSerializer,
    VendorAdminSerializer, VendorPayoutSerializer
)
from .permissions import IsVendorOwner
from rest_framework.views import APIView
from django.utils import timezone
from rest_framework.exceptions import NotFound


# Vendor view (authenticated vendor)
class VendorSelfView(generics.RetrieveUpdateAPIView):
    """
    A vendor can see their profile or update fields that are allowed.
    GET - view full profile
    PUT/PATCH - update editable fields
    """
    permission_classes = [permissions.IsAuthenticated, IsVendorOwner]

    def get_object(self):
        # get the logged in vendor's profile
        user = self.request.user
        try:
            return user.vendor_profile
        except VendorProfile.DoesNotExist:
            raise NotFound("No vendor profile found for this user.")

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return VendorProfileUpdateSerializer
        return VendorReadSerializer


# Vendor profile creation view (user must be flagged as vendor)
class VendorCreateView(generics.CreateAPIView):
    queryset = VendorProfile.objects.all()
    serializer_class = VendorProfileCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        # check if user is flagged as vendor
        if not getattr(user, 'is_vendor', False):
            raise PermissionDenied("You need to be a vendor to create a vendor profile.")
        serializer.save(user=user)


# Public vendor list and retrieve views for customers (NO anonymous access)
class VendorPublicListView(generics.ListAPIView):
    queryset = VendorProfile.objects.filter(verification__status=VendorVerification.APPROVED)
    serializer_class = VendorPublicReadSerializer
    permission_classes = [permissions.IsAuthenticated]


class VendorPublicDetailView(generics.RetrieveAPIView):
    """Show details of a single approved vendor."""
    queryset = VendorProfile.objects.filter(verification__status=VendorVerification.APPROVED)
    serializer_class = VendorPublicReadSerializer
    permission_classes = [permissions.IsAuthenticated]


# Admin vendor views
class VendorAdminListView(generics.ListAPIView):
    serializer_class = VendorAdminSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        qs = VendorProfile.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(verification__status=status_filter.upper())
        return qs


class VendorAdminDetailView(generics.RetrieveUpdateAPIView):
    """Admin can see a vendor profile and update only the status field."""
    queryset = VendorProfile.objects.all()
    serializer_class = VendorAdminSerializer
    permission_classes = [permissions.IsAdminUser]


# Vendor payout view
class VendorPayoutView(generics.GenericAPIView):
    serializer_class = VendorPayoutSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendorOwner]
    
    def post(self, request, *args, **kwargs):
        # Get the vendor profile safely
        vendor = getattr(request.user, 'vendor_profile', None)
        if not vendor:
            return Response(
                {"error": "You must be a vendor to access this endpoint."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(
            data=request.data,
            context={'vendor_profile': vendor}
        )
        serializer.is_valid(raise_exception=True)

         # Subtract the requested amount from the available balance
        amount = serializer.validated_data['amount']

        vendor.finance.balance -= amount
        vendor.finance.save()

        return Response(
            {"message": f"Successfully processed payment of GH₵{amount}."},
            status=status.HTTP_200_OK
        )


#---------------------------
# Admin approve/reject views
#---------------------------

class VendorApproveView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk, *args, **kwargs):
        try:
            vendor = VendorProfile.objects.get(pk=pk)
        except VendorProfile.DoesNotExist:
            return Response({"error": "Vendor not found."}, status=404)

        vendor.verification.status = VendorVerification.APPROVED
        vendor.verification.admin_approved_date = timezone.now()
        vendor.verification.last_modified_by = request.user
        vendor.verification.save()

        return Response(
            {"message": f"Vendor {vendor.business_name} approved."},
            status=200
        )


class VendorRejectView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk, *args, **kwargs):
        try:
            vendor = VendorProfile.objects.get(pk=pk)
        except VendorProfile.DoesNotExist:
            return Response({"error": "Vendor not found."}, status=404)

        vendor.verification.status = VendorVerification.REJECTED
        vendor.verification.admin_approved_date = timezone.now()
        vendor.verification.last_modified_by = request.user
        vendor.verification.save()

        return Response(
            {"message": f"Vendor {vendor.business_name} rejected."},
            status=200
        )
    


# Temporary view for topping up vendor balance (for testing purposes)
# vendor/views.py
from decimal import Decimal, InvalidOperation
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

class VendorTopUpView(APIView):
    """
    Temporary endpoint for testing: top up vendor balance.
    Only for testing purposes.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        amount = request.data.get("amount")
        if amount is None:
            return Response({"error": "Amount is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Convert to Decimal safely
        try:
            amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            return Response({"error": "Amount must be a valid number."}, status=status.HTTP_400_BAD_REQUEST)

        if amount <= 0:
            return Response({"error": "Amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)

        # Get the vendor profile
        try:
            vendor_profile = request.user.vendor_profile
        except AttributeError:
            return Response({"error": "Vendor profile not found."}, status=status.HTTP_404_NOT_FOUND)

        # Add the top-up amount
        vendor_profile.finance.balance += amount
        vendor_profile.finance.save()

        return Response({
            "message": "Balance topped up successfully.",
            "new_balance": str(vendor_profile.finance.balance)  # Return as string to avoid JSON Decimal issues
        }, status=status.HTTP_200_OK)

