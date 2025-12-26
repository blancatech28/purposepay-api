# voucher/serializers.py

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
import voucher
from .models import Voucher, VoucherRedemption
from vendor.models import VendorProfile, VendorVerification, VendorFinance
from .models import CustomerVoucherWallet


#--------------------
# Customer Wallet serializers
#---------------------
class CustomerVoucherWalletSerializer(serializers.ModelSerializer):
    """"" This serializer display the customer's voucher wallet details (read-only)."""""
    customer_username = serializers.ReadOnlyField(source="customer.username")
    class Meta:
        model = CustomerVoucherWallet
        fields = ["id", "customer_username", "balance"]
        read_only_fields = fields


class WalletDepositSerializer(serializers.Serializer):
    """"" Handles deposits into the customer's voucher wallet. """""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= Decimal("0.00"):
            raise serializers.ValidationError("Deposit amount must be greater than 0.")
        return value

    def deposit(self):
        wallet = self.context["wallet"]
        amount = self.validated_data["amount"]

        # Perform atomic and row-level locked update to prevent race conditions
        with transaction.atomic():
            wallet = CustomerVoucherWallet.objects.select_for_update().get(pk=wallet.pk)
            wallet.balance += amount
            wallet.save(update_fields=["balance"])
        return wallet




# ---------------------------
# Customer Voucher serializers
# -----------------------------

class VoucherCreateSerializer(serializers.ModelSerializer):
    """""
    Serializer for creating vouchers by customers. 
    The customer's wallet balance is checked before voucher creation.
    Amount is deducted from the wallet to create the voucher only if enough balance exists.
    """""

    customer_username = serializers.ReadOnlyField(source="customer.username")

    class Meta:
        model = Voucher
        fields = [
            "id", "customer_username", "category", "initial_amount",
                  "expiry_date", "status", "created_at", "code"
        ]
        read_only_fields = ["customer_username", "expiry_date", "status", "created_at", "code"]


    # Validation to check minimum initial amount
    def validate_initial_amount(self, value):
        if value < Decimal("100.00"):
            raise serializers.ValidationError("Minimum voucher amount is 100 GHS.")
        return value

    def create(self, validated_data):
        customer = self.context["request"].user
        amount = validated_data["initial_amount"]

        # Atomic operation to deduct wallet balance and create voucher
        with transaction.atomic():
            wallet, _ = CustomerVoucherWallet.objects.select_for_update().get_or_create(
                customer=customer,defaults={"balance": Decimal("0.00")})


            if wallet.balance < amount:
                raise serializers.ValidationError("Insufficient wallet balance to create this voucher.")

            # Subtract the amount from the wallet
            wallet.balance -= amount
            wallet.save(update_fields=["balance"])

            # The voucher is created with status=PENDING
            voucher = Voucher.objects.create(customer=customer, status=Voucher.PENDING, **validated_data)

        return voucher


class CustomerVoucherSerializer(serializers.ModelSerializer):
    """""This shows the list of a customer's vouchers (read-only)."""""

    customer_username = serializers.ReadOnlyField(source="customer.username")

    class Meta:
        model = Voucher
        fields = [
            "id", "customer_username", "code", "category", "initial_amount", "remaining_balance",
                  "status", "expiry_date", "created_at"
        ]
        read_only_fields = fields 



class CustomerVoucherDetailSerializer(serializers.ModelSerializer):
    """"" Shows the detailed information of a single customer's voucher, read-only."""""

    customer_username = serializers.ReadOnlyField(source="customer.username")
    redemptions = serializers.SerializerMethodField()

    class Meta:
        model = Voucher
        fields = [
            "id", "customer_username", "code", "category", "initial_amount", "remaining_balance",
                  "status", "expiry_date", "created_at", "redemptions"
        ]
        read_only_fields = fields

    def get_redemptions(self, obj):
        return VoucherRedemptionSerializer(obj.redemptions.all().order_by("-redeemed_at"), many=True).data




# ------------------------------
# Voucher Redemption serializers
# ------------------------------

class VoucherRedemptionCreateSerializer(serializers.ModelSerializer):
    """""
    Serializer for vendors to request voucher redemption.
    The vendor redeems by entering code and amount, redemption is created as unconfirmed.
    This is a simulation of a vendor requesting redemption.
    """""

    voucher_code = serializers.CharField(write_only=True)
    vendor_name = serializers.ReadOnlyField(source="vendor.business_name")
    voucher_category = serializers.ReadOnlyField(source="voucher.category")

    class Meta:
        model = VoucherRedemption
        fields = [
            "id", "voucher_code", "vendor_name",
            "redeemed_amount", "redemption_status", "redeemed_at", "voucher_category"
        ]
        read_only_fields = ["id", "vendor_name", "redeemed_at", "voucher_category", "redemption_status"]


    # Validation of voucher code and redemption amount
    def validate(self, data):
        vendor = self.context["vendor_profile"]
        code = data["voucher_code"]
        amount = data["redeemed_amount"]

        #--------------------
        # Voucher validation
        #--------------------
        try:
            voucher = Voucher.objects.get(code=code)
        except Voucher.DoesNotExist:
            raise serializers.ValidationError("Invalid voucher code.")

        
        if voucher.status != Voucher.ACTIVE:
            raise serializers.ValidationError("Voucher is not active.")
        
        if voucher.expiry_date and voucher.expiry_date < timezone.now():
            raise serializers.ValidationError(
                "Voucher has expired."
            )

        if amount < Decimal("50.00"):
            raise serializers.ValidationError("Minimum redemption amount is 50 GHS.")

        if amount > voucher.remaining_balance:
            raise serializers.ValidationError("Amount exceeds remaining balance.")


        # Ensures voucher category matches the vendor category
        if voucher.category != vendor.category:
              raise serializers.ValidationError(
                f"This voucher is for the '{voucher.category}' category. "
                f"Your vendor category is '{vendor.category}'."
            )
        
        # Attach the actual object to the validated data
        data["voucher"] = voucher
        data["vendor"] = vendor
        
        return data

    # Create redemption for vendor with is_confirmed=False
    def create(self, validated_data):
        validated_data.pop("voucher_code")

        # status of redemption is PENDING by default
        return VoucherRedemption.objects.create(**validated_data)


class CustomerPendingRedemptionSerializer(serializers.ModelSerializer):
    """
    Customer views the pending simulated redemption requests (read-only).
    """

    vendor_name = serializers.ReadOnlyField(source="vendor.business_name")
    voucher_category = serializers.ReadOnlyField(source="voucher.category")
    voucher_code = serializers.ReadOnlyField(source="voucher.code")
    
    class Meta:
        model = VoucherRedemption
        fields = ["id", "vendor_name","voucher_code","voucher_category", "redeemed_amount",
            "redemption_status", "redeemed_at"]
        read_only_fields = fields


class VoucherRedemptionConfirmSerializer(serializers.ModelSerializer):
    """
    Customer confirms a vendor redemption request.
    Money moves from the voucher escrow_balance to vendor finance balance upon confirmation by the customer.
    At the same time, the voucher remaining_balance is reduced.
    All these money movements are simulated.
    """

    class Meta:
        model = VoucherRedemption
        fields = ["id", "redemption_status"]
        read_only_fields = ["id"]

    def validate(self, data):
        redemption = self.instance
        voucher = redemption.voucher

        # Prevent confirming already redeemed redemptions
        if redemption.redemption_status == VoucherRedemption.REDEEMED:
            raise serializers.ValidationError("This redemption has already been redeemed.")

        # Voucher state may have changed after redemption request
        if voucher.status != Voucher.ACTIVE:
            raise serializers.ValidationError("Voucher is no longer active.")

        if voucher.expiry_date and voucher.expiry_date < timezone.now():
            raise serializers.ValidationError("Voucher has expired.")

        return data

    # Upon confirmation, update voucher escrow balance and vendor balances atomically (simulation)
    def update(self, instance, validated_data):
        amount = instance.redeemed_amount

        with transaction.atomic():
            instance = (VoucherRedemption.objects.select_for_update().select_related("voucher", "vendor__finance")
                        .get(pk=instance.pk))

            voucher = instance.voucher
            vendor = instance.vendor

            # Vendor finance record must exist before crediting
            if not hasattr(vendor, "finance"):
                raise serializers.ValidationError("Vendor finance record not found.")

            # Perform final checks before confirming redemption
            if instance.redemption_status == VoucherRedemption.REDEEMED:
                raise serializers.ValidationError("This redemption is already redeemed.")

            # Escrow balance check before finalizing (the money source)
            if amount > voucher.escrow_balance:
                raise serializers.ValidationError("Insufficient escrow balance to confirm this redemption.")

            # Check remaining balance too
            if amount > voucher.remaining_balance:
                raise serializers.ValidationError("Insufficient voucher remaining balance.")

            # Only finalize voucher redemption after customer confirms
            instance.redemption_status = VoucherRedemption.REDEEMED
            instance.save(update_fields=["redemption_status"])

            # Deduct from voucher escrow balance and credit vendor finance balance
            voucher.escrow_balance -= amount
            vendor.finance.balance += amount

            # update voucher remaining balance
            voucher.remaining_balance -= amount

            # If voucher balance is zero or less, lock the voucher
            if voucher.remaining_balance <= 0:
                voucher.remaining_balance = 0
                voucher.status = Voucher.LOCKED

                # Other pending redemptions will be cancelled, as no more funds are available
                VoucherRedemption.objects.filter(
                    voucher=voucher,
                    redemption_status=VoucherRedemption.PENDING
                ).exclude(id=instance.id).update(redemption_status=VoucherRedemption.CANCELLED)

            # Save all the changes made
            voucher.save(update_fields=["escrow_balance", "remaining_balance", "status"])
            vendor.finance.save(update_fields=["balance"])

        return instance



class VoucherRedemptionSerializer(serializers.ModelSerializer):
    """"" Serializer to display voucher redemption records (read-only)."""""

    vendor_name = serializers.ReadOnlyField(source="vendor.business_name")
    voucher_code = serializers.ReadOnlyField(source="voucher.code")
    voucher_owner = serializers.ReadOnlyField(source="voucher.customer.username")

    class Meta:
        model = VoucherRedemption
        fields = ["id", "voucher_owner","voucher_code", "vendor_name", "redeemed_amount", "redeemed_at","redemption_status"]
        read_only_fields = fields


class VendorRedemptionHistorySerializer(serializers.ModelSerializer):
    """"" A read-only serializer for vendor redemption history."""""
    voucher_code = serializers.ReadOnlyField(source="voucher.code")

    class Meta:
        model = VoucherRedemption
        fields = ["id", "voucher_code", "redeemed_amount", "redeemed_at","redemption_status"]
        read_only_fields = fields
    
 

# ------------------------------
# Administrator serializers
# ------------------------------

class AdminVoucherListSerializer(serializers.ModelSerializer):
    """""A serializer to give an overview of all vouchers created by the customer."""

    customer_username = serializers.ReadOnlyField(source="customer.username")
    redemptions_count = serializers.SerializerMethodField()

    class Meta:
        model = Voucher
        fields = ["id", "customer_username", "code", "category", "initial_amount", "remaining_balance",
                  "status", "expiry_date", "created_at", "redemptions_count"]
        read_only_fields = fields

    def get_redemptions_count(self, obj):
        return obj.redemptions.count()


class AdminVoucherDetailSerializer(serializers.ModelSerializer):
    """"" Admin detailed view of a voucher including all redemptions."""""
    customer_username = serializers.ReadOnlyField(source="customer.username")
    redemptions = serializers.SerializerMethodField()

    class Meta:
        model = Voucher
        fields = ["id", "customer_username", "code", "category", "initial_amount", "remaining_balance", "escrow_balance",
                  "status", "expiry_date", "created_at", "redemptions"]
        read_only_fields = fields

    def get_redemptions(self, obj):
        return VoucherRedemptionSerializer(obj.redemptions.all().order_by("-redeemed_at"), many=True).data
