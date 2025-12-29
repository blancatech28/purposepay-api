# vendor/utils.py
import re
from rest_framework import serializers
from vendor.models import VendorFinance


def validate_vendor_city(value):
    """A reusable validator for the vendor city fields."""
    if not value.strip():
        raise serializers.ValidationError("City cannot be empty.")
    
    if not re.match(r'^[A-Za-z\s]+$', value):
        raise serializers.ValidationError("City name can only contain letters and spaces.")
    return value


def validate_vendor_business_address(value):
    """validation for vendor business address."""
    if not value.strip():
        raise serializers.ValidationError("Business address cannot be empty.")
    
    # Allow alphanumeric, spaces, commas, periods, hyphens
    if not re.match(r'^[A-Za-z0-9\s,.\-]+$', value):
        raise serializers.ValidationError("Business address contains invalid characters.")
    return value


def validate_vendor_payout_bank_name(value):
    """validator for vendor payout bank name."""
    if not value.strip():
        raise serializers.ValidationError("Bank name cannot be empty.")
    
    if not re.match(r'^[A-Za-z\s]+$', value):
        raise serializers.ValidationError("Bank name can only contain letters and spaces.")
    
    return value


def validate_vendor_payout_account_number(value, instance=None):
    """Checks for the right bank account number for withdrawals and also its uniqueness"""
    if not value.isdigit():
        raise serializers.ValidationError("Account number must contain only digits.")
    if len(value) < 10 or len(value) > 18:
        raise serializers.ValidationError("Account number length seems invalid.")
    
    # Bank account number uniqueness check
    existing_finance = VendorFinance.objects.filter(payout_account_number=value).first()
    if existing_finance:
        if instance is None or existing_finance.id != instance.id:
            raise serializers.ValidationError("This payout account number is already in use.")

    return value
    

