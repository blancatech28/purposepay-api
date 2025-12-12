# vendor/serializers.py
import re
from rest_framework import serializers
from .models import VendorProfile
from datetime import datetime



# Vendor Read Serializer (vendor auth view)
class VendorReadSerializer(serializers.ModelSerializer):

    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id', 'user_email', 'business_name', 'category', 'status','admin_approved_date', 'phone_number', 'country', 'city',
            'business_address', 'gps_code', 'balance', 'payout_account_number','payout_bank_name', 'owner_id_type', 
            'owner_id_document','business_registration_document', 'business_location_image',
        ]
        read_only_fields = fields



# Public Read Serializer (customer view)
class VendorPublicReadSerializer(serializers.ModelSerializer):
    """Customers or other users can view vendor information with limited access.
    Sensitive data like balance, payout info, and documents are all excluded.
    """
    
    class Meta:
        model = VendorProfile
        fields = [
            'id', 'business_name', 'category', 'phone_number', 
            'country','city', 'business_address', 'gps_code', 'business_location_image',
        ]
        read_only_fields = fields




# Serializer for creating vendor profiles
class VendorProfileCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = VendorProfile
        fields = [
            'business_name', 'category', 'phone_number', 'city','business_address', 'gps_code',
            'payout_account_number','payout_bank_name', 'owner_id_type', 'owner_id_document',
            'business_registration_document', 'business_location_image',
        ]


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

    def validate_phone_number(self, value):
        pattern = r"^(?:\+233|0)\d{9}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number must be in Ghanaian format."
            )
        return value

    def validate_city(self, value):
        if not value.strip():
            raise serializers.ValidationError("City cannot be empty.")
        return value

    def validate_payout_account_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Account number must contain only digits.")
        if len(value) < 10 or len(value) > 18:
            raise serializers.ValidationError("Account number length seems invalid.")
        return value

    def validate_payout_bank_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Bank name cannot be empty.")
        return value



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




# Vendor Update
class VendorProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for vendors to update only allowed fields after being approved."""
    
    class Meta:
        model = VendorProfile
        fields = [
            'phone_number', 'payout_account_number', 'payout_bank_name',
            'city', 'business_address',
        ]

    def validate_phone_number(self, value):
        pattern = r"^(?:\+233|0)\d{9}$"
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number must be in Ghanaian format."
            )
        return value

    def validate_payout_account_number(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Account number must contain only digits.")
        if len(value) < 10 or len(value) > 18:
            raise serializers.ValidationError("Account number length seems invalid.")
        return value

    def validate_payout_bank_name(self, value):
        if not value.strip():
            raise serializers.ValidationError("Bank name cannot be empty.")
        return value

    def validate_city(self, value):
        if not value.strip():
            raise serializers.ValidationError("City cannot be empty.")
        return value


class VendorAdminSerializer(serializers.ModelSerializer):
    """
    Admin operations on vendor profiles, can only change 'status'.
    All Other fields are read-only.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id', 'user_email', 'business_name', 'category', 'status',
            'admin_approved_date', 'last_modified_by', 'balance',
            'payout_account_number', 'payout_bank_name',
        ]
        read_only_fields = [
            'user_email', 'business_name', 'category', 'admin_approved_date',
            'last_modified_by', 'balance', 'payout_account_number',
            'payout_bank_name',
        ]

    def update(self, instance, validated_data):
        new_status = validated_data.get('status', instance.status)
        if new_status != instance.status:
            instance.status = new_status
            instance.admin_approved_date = datetime.now()
            instance.last_modified_by = self.context['request'].user
            instance.save()
        return instance





# Payout Serializer (Handles the  simulated vendor payment requests.)
class VendorPayoutSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Amount vendor wants to withdraw.")

    def validate_amount(self, value):
        vendor_profile = self.context.get('vendor_profile')
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        if vendor_profile and value > vendor_profile.balance:
            raise serializers.ValidationError("Amount exceeds current balance.")
        return value
