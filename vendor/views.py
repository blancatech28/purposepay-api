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
from .permissions import IsApprovedVendor, IsVendorOwner
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

        # def get_object(self):
        #  Directly return the user's vendor profile
        #     return self.request.user.vendor_profile

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
    permission_classes = [permissions.IsAuthenticated, IsApprovedVendor]
    
    def post(self, request, *args, **kwargs):
        vendor = self.request.user.vendor_profile
        
        serializer = self.get_serializer(
            data=request.data,
            context={'vendor_profile': vendor}
        )
        serializer.is_valid(raise_exception=True)
        
        # Get the requested withdrawal amount from the validated data
        amount = serializer.validated_data['amount']

        # Subtract the requested amount from the available balance
        vendor.finance.balance -= amount
        vendor.finance.save()

        return Response(
            {"message": f"Successfully processed payment of GH₵{amount}."},
            status=status.HTTP_200_OK
        )


#---------------------------
# Approve/reject views for admin
#---------------------------


def get_vendor_and_verification(pk):
    """Helper function to get vendor and verification objects."""
    try:
        vendor = VendorProfile.objects.get(pk=pk)
    except VendorProfile.DoesNotExist:
        raise NotFound("Vendor profile not found.")
    
    verification = getattr(vendor, 'verification', None)
    if verification is None:
        raise NotFound("The vendor verification record does not exist."
                       "Vendor may not have completed verification setup.")
    return vendor, verification



class VendorApproveView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, pk, *args, **kwargs):
        vendor, verification = get_vendor_and_verification(pk)

        # Check for already approved vendor
        if verification.status == VendorVerification.APPROVED:
            return Response(
                {"message": f"Vendor {vendor.business_name} is already approved."},
                status=status.HTTP_200_OK
            )

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
        vendor, verification = get_vendor_and_verification(pk)

        # Check for already rejected vendor
        if verification.status == VendorVerification.REJECTED:
            return Response(
                {"message": f"Vendor {vendor.business_name} is already rejected."},
                status=status.HTTP_200_OK
            )

        vendor.verification.status = VendorVerification.REJECTED
        vendor.verification.admin_approved_date = timezone.now()
        vendor.verification.last_modified_by = request.user
        vendor.verification.save()

        return Response(
            {"message": f"Vendor {vendor.business_name} rejected."},
            status=200
        )
    


