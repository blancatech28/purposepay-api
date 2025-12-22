# voucher/serializers.py

from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from .models import Voucher, VoucherRedemption
from vendor.models import VendorProfile, VendorVerification, VendorFinance


# ---------------------------
# Customer Voucher serializers
# -----------------------------

class VoucherCreateSerializer(serializers.ModelSerializer):
    """""
    Serializer for creating vouchers by customers.
    Only 'category' and 'initial_amount' are required from the user. The rest are read-only.
    """""

    customer_username = serializers.ReadOnlyField(source="customer.username")

    class Meta:
        model = Voucher
        fields = [
            "id", "customer", "customer_username", "category", "initial_amount",
                  "expiry_date", "status", "created_at", "code"
        ]
        read_only_fields = ["customer","customer_username", "expiry_date", "status", "created_at", "code"]


    # Validation to check minimum initial amount
    def validate_initial_amount(self, value):
        if value < Decimal("100.00"):
            raise serializers.ValidationError("Minimum voucher amount is 100 GHS.")
        return value

    def create(self, validated_data):
        # The customer is set from the request user
        return Voucher.objects.create(**validated_data)


class CustomerVoucherSerializer(serializers.ModelSerializer):
    """""This shows the list of a customer's vouchers (read-only)."""""

    customer_username = serializers.ReadOnlyField(source="customer.username")

    class Meta:
        model = Voucher
        fields = [
            "id", "code", "category", "initial_amount", "remaining_balance",
                  "status", "expiry_date", "created_at", "customer_username"
        ]
        read_only_fields = fields 



class CustomerVoucherDetailSerializer(serializers.ModelSerializer):
    """"" Shows the detailed information of a single customer's voucher, read-only."""""

    customer_username = serializers.ReadOnlyField(source="customer.username")
    redemptions = serializers.SerializerMethodField()

    class Meta:
        model = Voucher
        fields = [
            "id", "code", "category", "initial_amount", "remaining_balance",
                  "status", "expiry_date", "created_at", "customer_username", "redemptions"
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
    This is simulation of a vendor requesting redemption.
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
    
    class Meta:
        model = VoucherRedemption
        fields = [
            "id", "vendor_name", "redeemed_amount",
            "redemption_status", "redeemed_at", "voucher_category"
        ]
        read_only_fields = fields


class VoucherRedemptionConfirmSerializer(serializers.ModelSerializer):
    """
    Customer confirms a redemption request.
    Vendor balance is credited and voucher balance is deducted upon confirmation.
    All these requests are simulated.
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
            raise serializers.ValidationError(
                "This redemption has already been redeemed."
            )
    

        # Voucher state may have changed after redemption request
        if voucher.status != Voucher.ACTIVE:
            raise serializers.ValidationError(
                "Voucher is no longer active."
            )

        if voucher.expiry_date and voucher.expiry_date < timezone.now():
            raise serializers.ValidationError(
                "Voucher has expired."
            )

        return data
        

    # Upon confirmation, update voucher and vendor balances atomically (simulation)
    def update(self, instance, validated_data):
        voucher = instance.voucher
        vendor = instance.vendor
        amount = instance.redeemed_amount

        # Vendor finance record must exist before crediting
        if not hasattr(vendor, "finance"):
            raise serializers.ValidationError(
                "Vendor finance record not found."
            )

        
        with transaction.atomic():
            # Re-fetch from the database to avoid against concurrent confirmations
            instance.refresh_from_db()
            voucher.refresh_from_db()

            if instance.redemption_status == VoucherRedemption.REDEEMED:
                raise serializers.ValidationError("This redemption is already redeemed.")
           

           # Voucher balance check before finalizing
            if amount > voucher.remaining_balance:
                raise serializers.ValidationError(
                    "Insufficient voucher balance to confirm this redemption."
                )
            

            # Only finalize voucher redemption after customer confirms
            instance.redemption_status = VoucherRedemption.REDEEMED
            instance.save(update_fields=["redemption_status"])

            # Deduct voucher balance
            voucher.remaining_balance -= amount
            if voucher.remaining_balance <= 0:
                voucher.remaining_balance = 0
                voucher.status = Voucher.LOCKED
                voucher.save(update_fields=["remaining_balance", "status"])

                # Other pending redemptions will be cancelled,
                # if voucher is locked or balance is zero
                VoucherRedemption.objects.filter(
                    voucher=voucher,
                    redemption_status=VoucherRedemption.PENDING
                ).exclude(id=instance.id).update(
                    redemption_status=VoucherRedemption.CANCELLED
                )
            else:
                voucher.save(update_fields=["remaining_balance"])

            # Credit the vendor
            vendor_finance = vendor.finance
            vendor_finance.balance += amount
            vendor_finance.save(update_fields=["balance"])

        return instance


class VoucherRedemptionSerializer(serializers.ModelSerializer):
    """"" Serializer to display voucher redemption records (read-only)."""""

    vendor_name = serializers.ReadOnlyField(source="vendor.business_name")
    voucher_code = serializers.ReadOnlyField(source="voucher.code")

    class Meta:
        model = VoucherRedemption
        fields = ["id", "voucher_code", "vendor_name", "redeemed_amount", "redeemed_at","redemption_status"]
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
        fields = ["id", "code", "category", "initial_amount", "remaining_balance",
                  "status", "expiry_date", "created_at", "customer_username", "redemptions_count"]
        read_only_fields = fields

    def get_redemptions_count(self, obj):
        return obj.redemptions.count()


class AdminVoucherDetailSerializer(serializers.ModelSerializer):
    """"" Admin detailed view of a voucher including all redemptions."""""
    customer_username = serializers.ReadOnlyField(source="customer.username")
    redemptions = serializers.SerializerMethodField()

    class Meta:
        model = Voucher
        fields = ["id", "code", "category", "initial_amount", "remaining_balance",
                  "status", "expiry_date", "created_at", "customer_username", "redemptions"]
        read_only_fields = fields

    def get_redemptions(self, obj):
        return VoucherRedemptionSerializer(obj.redemptions.all().order_by("-redeemed_at"), many=True).data
