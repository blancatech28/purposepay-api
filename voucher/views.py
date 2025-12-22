# voucher/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.db import transaction
from django.utils import timezone

from .models import Voucher, VoucherRedemption
from .serializers import (
    VoucherCreateSerializer,CustomerVoucherSerializer,CustomerVoucherDetailSerializer,
    VoucherRedemptionCreateSerializer,CustomerPendingRedemptionSerializer,VoucherRedemptionConfirmSerializer,
    VendorRedemptionHistorySerializer,AdminVoucherListSerializer,
    AdminVoucherDetailSerializer,
)
from .permissions import IsCustomer
from vendor.models import VendorProfile, VendorVerification
from vendor.permissions import IsApprovedVendor
from rest_framework.exceptions import PermissionDenied


# -----------------------------
# Customer Views for Vouchers
# -----------------------------

class VoucherCreateView(generics.CreateAPIView):
    """Customer creates a voucher (status=PENDING_PAYMENT initially)."""
    
    serializer_class = VoucherCreateSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def perform_create(self, serializer):
        serializer.save(customer=self.request.user, status=Voucher.PENDING_PAYMENT)


class CustomerVoucherListView(generics.ListAPIView):
    """Show a list of all the vouchers belonging to the logged-in customer."""
    
    serializer_class = CustomerVoucherSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self):
        return Voucher.objects.filter(customer=self.request.user)


class CustomerVoucherDetailView(generics.RetrieveAPIView):
    """Display a single voucher details for the customer, including all the redemptions tied to the voucher."""
    
    serializer_class = CustomerVoucherDetailSerializer
    permission_classes = [IsAuthenticated, IsCustomer]
    lookup_field = 'id'

    def get_queryset(self):
        return Voucher.objects.filter(customer=self.request.user)


# ------------------------------------
# Views for Voucher Redemptions by Vendor
# -------------------------------------

class VoucherRedemptionCreateView(generics.CreateAPIView):
    """Vendor requests a redemption of voucher, redemption not unconfirmed yet."""

    serializer_class = VoucherRedemptionCreateSerializer
    permission_classes = [IsAuthenticated, IsApprovedVendor]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['vendor_profile'] = self.request.user.vendor_profile
        return context

class VendorRedemptionHistoryView(generics.ListAPIView):
    """Vendor sees all confirmed redemption history."""
    serializer_class = VendorRedemptionHistorySerializer
    permission_classes = [IsAuthenticated, IsApprovedVendor]

    def get_queryset(self):
        # Get the vendor profile of the logged-in user
        user = self.request.user
        vendor = user.vendor_profile
        return VoucherRedemption.objects.filter(vendor=vendor).order_by("-redeemed_at")


# -----------------------------
# Customer Views for Redemptions
# -----------------------------

class CustomerPendingRedemptionListView(generics.ListAPIView):
    """Customer sees pending redemptions for their vouchers."""
    serializer_class = CustomerPendingRedemptionSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_queryset(self):
        return VoucherRedemption.objects.filter(
        voucher__customer=self.request.user,
        redemption_status=VoucherRedemption.PENDING).order_by("-redeemed_at")




class VoucherRedemptionCancelView(generics.UpdateAPIView):
    """Customer cancels a pending voucher redemption."""
    permission_classes = [IsAuthenticated, IsCustomer]
    lookup_field = 'id'

    def get_queryset(self):
        return VoucherRedemption.objects.filter(voucher__customer=self.request.user, redemption_status=VoucherRedemption.PENDING)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.redemption_status = VoucherRedemption.CANCELLED
        instance.save(update_fields=["redemption_status"])
        return Response({"detail": "The voucher redemption is cancelled.", "redemption_status": instance.redemption_status})


class VoucherRedemptionConfirmView(generics.UpdateAPIView):
    """
    Voucher redemption is confirmed as redeemed by the customer.
    Deducts voucher balance and credits the vendor atomically.
    """
    serializer_class = VoucherRedemptionConfirmSerializer
    permission_classes = [IsAuthenticated, IsCustomer]
    lookup_field = "id"

    def get_queryset(self):
        return VoucherRedemption.objects.filter(voucher__customer=self.request.user,
            redemption_status=VoucherRedemption.PENDING)

    
# -----------------------------
# Admin Views
# -----------------------------

class AdminVoucherListView(generics.ListAPIView):
    """Admin sees a list of all vouchers."""
    serializer_class = AdminVoucherListSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Voucher.objects.all()


class AdminVoucherDetailView(generics.RetrieveAPIView):
    """Admin views details of a voucher including all the redemptions tied to it."""
    serializer_class = AdminVoucherDetailSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]
    queryset = Voucher.objects.all()
    lookup_field = 'id'



# Customer only: Voucher simulation view
class VoucherActivateSimulationView(APIView):
    """
    Payment is simulated for voucher activation
    
    The Flow:
    1. Voucher must belong to the authenticated customer.
    2. The Status of the voucher must be at PENDING_PAYMENT.
    3. The system "approves" the payment and sets status to ACTIVE after customer access the endpoint.
    """
    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, request, voucher_id):
        # Fetch the voucher for the authenticated customer
        try:
            voucher = Voucher.objects.get(id=voucher_id, customer=request.user)
        except Voucher.DoesNotExist:
            return Response(
                {"detail": "Voucher not found or does not belong to you."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Only vouchers pending payment can be activated
        if voucher.status != Voucher.PENDING_PAYMENT:
            return Response(
                {"detail": "Voucher cannot be activated. Current status: {}".format(voucher.status)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # payment simulation is successful and the voucher is activated
        voucher.status = Voucher.ACTIVE
        voucher.save(update_fields=['status'])

        return Response(
            {
                "detail": f"Voucher {voucher.code} is now ACTIVE.",
                "voucher_status": voucher.status
            },
            status=status.HTTP_200_OK
        )



# Show approved vendors list
class ApprovedVendorsListView(generics.ListAPIView):
    """
    Authenticated users can view approved vendors for a given category and filter optionally by city.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = None 

    # get the optional city and also filter by approved vendors
    def get(self, request, category):
        city = request.query_params.get('city', None)

        vendors = VendorProfile.objects.filter(
            category=category,
            verification__status=VendorVerification.APPROVED
        )

        # If city is provided, filter by city as well
        if city:
            vendors = vendors.filter(city__iexact=city)

        data = []
        for vendor in vendors:
            vendor_info = {
                "business_name": vendor.business_name,
                "city": vendor.city,
                "gps_code": vendor.gps_code,
                "category": vendor.category,
                "phone_number": vendor.phone_number,
            }
            data.append(vendor_info)

        return Response(data, status=status.HTTP_200_OK)

