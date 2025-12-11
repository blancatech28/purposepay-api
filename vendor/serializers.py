# vendor/serializers.py
from rest_framework import serializers
from .models import VendorProfile


# Serializer for reading vendor profile (GET)
class VendorProfileReadSerializer(serializers.ModelSerializer):
    """
    Serializer for viewing vendor profiles.
    All fields are read-only.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id',
            'user_email',
            'business_name',
            'category',
            'status',
            'admin_approved_date',
            'balance',
            'payout_account_number',
            'payout_bank_name',
        ]
        read_only_fields = fields  # Everything is read-only


# Serializer for vendor create/update (POST/PUT)
class VendorProfileWriteSerializer(serializers.ModelSerializer):
    """
    Serializer for vendor updating their own profile.
    Allows editing business info and payout details.
    """
    class Meta:
        model = VendorProfile
        fields = [
            'business_name',
            'category',
            'payout_account_number',
            'payout_bank_name',
        ]


# Admin Serializer
class VendorAdminSerializer(serializers.ModelSerializer):
    """
    Admin operations on vendor profiles.
    Admin can only change 'status'.
    Other fields are read-only.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = VendorProfile
        fields = [
            'id',
            'user_email',
            'business_name',
            'category',
            'status',
            'admin_approved_date',
            'last_modified_by',
            'balance',
            'payout_account_number',
            'payout_bank_name',
        ]
        read_only_fields = [
            'user_email',
            'business_name',
            'category',
            'admin_approved_date',
            'last_modified_by',
            'balance',
            'payout_account_number',
            'payout_bank_name',
        ]

    def update(self, instance, validated_data):
        """
        Only allow admin to update status.
        Automatically set admin_approved_date and last_modified_by if approved/rejected.
        """
        new_status = validated_data.get('status', instance.status)
        if new_status != instance.status:
            instance.status = new_status
            instance.admin_approved_date = serializers.datetime.datetime.now()
            instance.last_modified_by = self.context['request'].user
            instance.save()
        return instance


# Payout Serializer
class VendorPayoutSerializer(serializers.Serializer):
    """
    Handles simulated vendor payout requests.
    """
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount vendor wants to withdraw from balance."
    )

    def validate_amount(self, value):
        """
        Ensure amount is positive and does not exceed current balance.
        """
        vendor_profile = self.context.get('vendor_profile')
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        if vendor_profile and value > vendor_profile.balance:
            raise serializers.ValidationError("Amount exceeds current balance.")
        return value
