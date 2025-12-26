# voucher/views.py

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .models import Voucher, VoucherRedemption, CustomerVoucherWallet
from .serializers import (
    VoucherCreateSerializer,CustomerVoucherSerializer,CustomerVoucherDetailSerializer,
    VoucherRedemptionCreateSerializer,CustomerPendingRedemptionSerializer,VoucherRedemptionConfirmSerializer,
    VendorRedemptionHistorySerializer,AdminVoucherListSerializer,
    AdminVoucherDetailSerializer, WalletDepositSerializer, CustomerVoucherWalletSerializer
)
from .permissions import IsCustomer
from vendor.models import VendorProfile, VendorVerification
from vendor.permissions import IsApprovedVendor
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter



# ---------------------
# Customer Wallet Views
# ---------------------
class CustomerVoucherWalletView(generics.RetrieveAPIView):
    """Customer views their voucher wallet balance."""
    serializer_class = CustomerVoucherWalletSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def get_object(self):
        # Get or create the wallet of the logged-in customer
        wallet, _ = CustomerVoucherWallet.objects.get_or_create(customer=self.request.user)
        return wallet

class WalletDepositView(generics.GenericAPIView):
    """Customer deposits funds into their voucher wallet."""
    serializer_class = WalletDepositSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    def post(self, request, *args, **kwargs):
        # Same thing here: Get or create the voucher wallet for the customer
        wallet, _ = CustomerVoucherWallet.objects.get_or_create(customer=request.user)

        serializer = self.get_serializer(data=request.data, context={"wallet": wallet})
        serializer.is_valid(raise_exception=True)
        wallet = serializer.deposit()
        return Response({"detail": "Deposit is successful", " Your wallet balance is": str(wallet.balance) + " GHS"})



# -----------------------------
# Customer Views for Vouchers
# -----------------------------
class VoucherCreateView(generics.CreateAPIView):
    """Customer creates a voucher (status=PENDING) is initially set in the serializer.
    """
    serializer_class = VoucherCreateSerializer
    permission_classes = [IsAuthenticated, IsCustomer]



class CustomerVoucherListView(generics.ListAPIView):
    """This view displays a list of all the vouchers belonging to the logged-in customer."""
    
    serializer_class = CustomerVoucherSerializer
    permission_classes = [IsAuthenticated, IsCustomer]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "category"]
    search_fields = ["code"]
    ordering_fields = ["created_at", "initial_amount"]
    ordering = ["-created_at"]

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
    """Vendor requests a redemption of voucher, redemption not unconfirmed yet, status is PENDING."""

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

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["redemption_status"]
    search_fields = ["voucher__code"]
    ordering_fields = ["redeemed_at", "redeemed_amount"]
    ordering = ["-redeemed_at"]

    def get_queryset(self):
        # Get the vendor profile of the logged-in user
        user = self.request.user
        vendor = user.vendor_profile
        return VoucherRedemption.objects.filter(vendor=vendor)



# -----------------------------
# Customer Views for Redemptions
# -----------------------------

class CustomerPendingRedemptionListView(generics.ListAPIView):
    """The Customer sees pending redemptions for their vouchers."""
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
    The redeemed amount is deducted from the escrow balance and the vendor balance is credited atomically.
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

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "category"]
    search_fields = ["code", "customer__username"]
    ordering_fields = ["created_at","initial_amount","remaining_balance"]
    ordering = ["-created_at"]
    
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
    Customer only endpoint to simulate voucher activation after voucher creation.
    
    How it functions:
    1. Voucher must belong to the authenticated customer.
    2. The Status of the voucher must be at PENDING.
    3. If the voucher is valid, its status is set to ACTIVE.
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

        # Only vouchers pending can be activated
        if voucher.status != Voucher.PENDING:
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

