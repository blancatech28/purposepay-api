# vendor/serializers.py
import re
from rest_framework import serializers
from .models import VendorProfile, VendorVerification, VendorFinance, VendorPayoutHistory
from datetime import datetime
from accounts.utils import validate_ghanaian_phone_format
from .utils import (
validate_vendor_city, validate_vendor_business_address, 
validate_vendor_payout_bank_name, validate_vendor_payout_account_number
)


# Payout histrory serializer
class VendorPayoutHistorySerializer(serializers.ModelSerializer):
       """Money transactions made to approved vendors are captured here"""
       processed_by = serializers.CharField(source='processed_by.username', read_only=True)
       
       class Meta:
        model = VendorPayoutHistory
        fields = ['id', 'amount', 'processed_by', 'created_at']


# Vendor Read Serializer (vendor auth view)
class VendorReadSerializer(serializers.ModelSerializer):
    """Vendors can view all their profile info here with this serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    # Nested fields from related tables (verification and finance)
    status = serializers.CharField(source='verification.status', read_only=True)

    admin_approved_date = serializers.DateTimeField(source='verification.admin_approved_date', read_only=True)

    owner_id_type = serializers.CharField(source='verification.owner_id_type', read_only=True)

    owner_id_document = serializers.FileField(source='verification.owner_id_document', read_only=True)

    business_registration_document = serializers.FileField(
        source='verification.business_registration_document', read_only=True
    )
    business_location_image = serializers.ImageField(
        source='verification.business_location_image', read_only=True
    )
    balance = serializers.DecimalField(
        source='finance.balance', max_digits=12, decimal_places=2, read_only=True
    )
    payout_account_number = serializers.CharField(source='finance.payout_account_number', read_only=True
    )
    payout_bank_name = serializers.CharField(source='finance.payout_bank_name', read_only=True)

    payout_history = VendorPayoutHistorySerializer(many=True, read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id','business_name','user_email','category','status','admin_approved_date', 'phone_number', 
            'country', 'city','business_address', 'gps_code', 'balance', 'payout_account_number','payout_bank_name',
            'owner_id_type', 'owner_id_document','business_registration_document', 'business_location_image', 'payout_history'
        ]
        read_only_fields = fields



# Public Read Serializer (customer view)
class VendorPublicReadSerializer(serializers.ModelSerializer):
    """
    All authenticated users can view vendor information with limited access.
    Sensitive data like balance, payout info, and documents are all excluded.
    """
    business_location_image = serializers.ImageField(source='verification.business_location_image', read_only=True)
    
    class Meta:
        model = VendorProfile
        fields = [
            'id', 'business_name', 'category', 'phone_number', 
            'country','city', 'business_address', 'gps_code', 'business_location_image',
        ]
        read_only_fields = fields


# Vendor Finance Serializer (nested in vendorprofile create)
class VendorFinanceSerializer(serializers.ModelSerializer):
    """""Serializer for vendor finance details during vendor profile creation."""

    class Meta:
        model = VendorFinance
        fields = ['payout_account_number', 'payout_bank_name']

    def validate_payout_account_number(self, value):
        return validate_vendor_payout_account_number(value)

    def validate_payout_bank_name(self, value):
        return validate_vendor_payout_bank_name(value)
        
        

# Nested serializer for verification in vendor creation
class VendorVerificationSerializer(serializers.ModelSerializer):
    """""Serializer for vendor verification documents during creation."""""

    class Meta:
        model = VendorVerification
        fields = ['owner_id_type', 'owner_id_document', 
                  'business_registration_document', 'business_location_image']

    # File size limits
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 megabytes
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 megabytes

    def validate_owner_id_document(self, value):
        allowed = ('.pdf', '.doc', '.docx', '.jpg', '.png')
        if not value.name.lower().endswith(allowed):
            raise serializers.ValidationError("Owner ID must be PDF, DOC/DOCX, or image file.")
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError("File too large (max 10MB).")
        return value

    def validate_business_registration_document(self, value):
        allowed = ('.pdf', '.doc', '.docx')
        if not value.name.lower().endswith(allowed):
            raise serializers.ValidationError("Business registration must be PDF or DOC/DOCX file.")
        if value.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError("File too large (max 10MB).")
        return value

    def validate_business_location_image(self, value):
        allowed = ('.jpg', '.jpeg', '.png')
        if not value.name.lower().endswith(allowed):
            raise serializers.ValidationError("Business location image must be JPG or PNG.")
        if value.size > self.MAX_IMAGE_SIZE:
            raise serializers.ValidationError("Image too large (max 5MB).")
        return value


# Vendor Creation Serializer
class VendorProfileCreateSerializer(serializers.ModelSerializer):
    """""This serializer is for creating a new vendor profile with nested finance and verification data."""""
    
    finance = VendorFinanceSerializer()
    verification = VendorVerificationSerializer()

    class Meta:
        model = VendorProfile
        fields = ['business_name', 'category', 'phone_number', 
            'city', 'business_address', 'gps_code',
            'finance', 'verification']
       
        
    def validate(self, attrs):       
        user = self.context['request'].user

        # Check if user already has a vendor profile
        if VendorProfile.objects.filter(user=user).exists():
            raise serializers.ValidationError("You already have a vendor profile.")
        
        # Check if business name is already taken to prevent duplicates
        business_name = attrs.get('business_name')
        if VendorProfile.objects.filter(business_name__iexact=business_name).exists():
            raise serializers.ValidationError("This business name is already in use by another vendor.")
        
        return attrs

    # Override create to handle the nested financial and verification data
    def create(self, validated_data):
        finance_data = validated_data.pop('finance', {})
        verification_data = validated_data.pop('verification', {})
        vendor = VendorProfile.objects.create(**validated_data)
        VendorFinance.objects.create(vendor=vendor, **finance_data)
        VendorVerification.objects.create(vendor=vendor, **verification_data)
        return vendor

    # file size limits
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 megabytes
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 megabytes

    # Field level validations
    def validate_gps_code(self, value):
        pattern = r"^[A-Z]{2}-\d{4}-\d{4}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "GPS code must be in format XX-0000-0000 (e.g., GW-0065-1601)."
            )
        return value
    
    def validate_business_address(self, value):
        return validate_vendor_business_address(value)

    def validate_phone_number(self, value):
        validate_ghanaian_phone_format(value)

        # Check if phone number is used by another vendor
        if VendorProfile.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("This phone number is already in use by another vendor.")
        return value

    def validate_city(self, value):
        return validate_vendor_city(value)
    

# Vendor Update Serializer (vendors can update certain fields)
class VendorProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for vendors to update allowed fields and payout info."""

    phone_number = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    business_address = serializers.CharField(required=False)
    payout_account_number = serializers.CharField(write_only=True, required=False)
    payout_bank_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = VendorProfile
        fields = ['phone_number', 'city', 'business_address', 'payout_account_number', 'payout_bank_name']

    def validate_phone_number(self, value):
        validate_ghanaian_phone_format(value)
        
        # Check if phone number is used by another vendor
        user = self.context['request'].user
        if VendorProfile.objects.filter(phone_number=value).exclude(user=user).exists():
            raise serializers.ValidationError("This phone number is already in use by another vendor.")
        return value

    def validate_city(self, value):
        return validate_vendor_city(value)

    def validate_business_address(self, value):
        return validate_vendor_business_address(value)

    def validate_payout_account_number(self, value):
        return validate_vendor_payout_account_number(value)


    def validate_payout_bank_name(self, value):
        return validate_vendor_payout_bank_name(value)

    def update(self, instance, validated_data):
        # Update the VendorProfile fields
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.city = validated_data.get('city', instance.city)
        instance.business_address = validated_data.get('business_address', instance.business_address)
        instance.save()

        # Update the finance fields if its provided (optional)
        finance = getattr(instance, 'finance', None)
        if finance:
            if 'payout_account_number' in validated_data:
                finance.payout_account_number = validated_data['payout_account_number']
            if 'payout_bank_name' in validated_data:
                finance.payout_bank_name = validated_data['payout_bank_name']
            finance.save()

        return instance

    
class VendorAdminSerializer(serializers.ModelSerializer):
    """Admin operations on vendor profiles, can only change 'status'."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    status = serializers.CharField(source='verification.status')
    admin_approved_date = serializers.DateTimeField(source='verification.admin_approved_date', read_only=True)
    owner_id_type = serializers.CharField(source='verification.owner_id_type', read_only=True)
    owner_id_document = serializers.FileField(source='verification.owner_id_document', read_only=True)
    business_registration_document = serializers.FileField(
        source='verification.business_registration_document', read_only=True
    )
    business_location_image = serializers.ImageField(
        source='verification.business_location_image', read_only=True
    )
    payout_account_number = serializers.CharField(source='finance.payout_account_number', read_only=True)
    payout_bank_name = serializers.CharField(source='finance.payout_bank_name', read_only=True)
    last_modified_by = serializers.CharField(source='verification.last_modified_by.username', read_only=True)
    balance = serializers.DecimalField(source='finance.balance', max_digits=12, decimal_places=2, read_only=True)
    payout_history = VendorPayoutHistorySerializer(many=True, read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id','business_name','user_email','business_address','city','phone_number','gps_code','category', 'status',
            'admin_approved_date','owner_id_type', 'owner_id_document','business_registration_document', 
            'business_location_image','last_modified_by', 'balance',
            'payout_account_number', 'payout_bank_name', 'payout_history',
            'owner_id_type', 'owner_id_document','business_registration_document', 'business_location_image'
        ]
        read_only_fields = [
            'business_name','user_email','business_address','city','phone_number','gps_code','category', 'admin_approved_date',
            'owner_id_type', 'owner_id_document','business_registration_document', 'business_location_image'
            'last_modified_by', 'balance', 'payout_account_number',
            'payout_bank_name', 'payout_history'
        ]

    def update(self, instance, validated_data):
        verification_data = validated_data.get('verification', {})
        new_status = verification_data.get('status', instance.verification.status)
        if new_status != instance.verification.status:
            instance.verification.status = new_status
            instance.verification.admin_approved_date = datetime.now()
            instance.verification.last_modified_by = self.context['request'].user
            instance.verification.save()
        return instance



# Payout Serializer (Handles the simulated vendor payment requests.)
class VendorPayoutSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Amount vendor wants to withdraw.")

    def validate_amount(self, value):
        vendor_profile = self.context.get('vendor_profile')
        
        # Check the minimum amount
        if value < 50:
            raise serializers.ValidationError("Minimum withdrawal amount must be 50.00 GHS or above.")
        
        # Check if a finance record exists
        if not getattr(vendor_profile, 'finance', None):
            raise serializers.ValidationError("This vendor has no finance record. Please set up payout details for payment.")
        
        if value > vendor_profile.finance.balance:
            raise serializers.ValidationError("The withdrawal amount exceeds current balance.")
        return value
