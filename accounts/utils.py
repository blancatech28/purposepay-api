# accounts/utils.py
from django.contrib.auth import get_user_model
from rest_framework import serializers
import re

User = get_user_model()

def validate_email(email, instance=None):

    # Checks for email format correctness, raises an error if the email is invalid
    pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}$"
    if not re.match(pattern, email):
        raise serializers.ValidationError("Enter a valid email address.")
    
    # This validates the email for domain realism
    domain = email.split("@")[1].split(".")[0]
    if not re.match(r"^[A-Za-z][A-Za-z0-9-]*$", domain):
        raise serializers.ValidationError("Enter a valid email address.")

    # Ensure that the uniqueness of email across users.
    qs = User.objects.filter(email__iexact=email)
    if instance:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise serializers.ValidationError("A user with this email already exists.")
    return email


def validate_unique_username(username, instance=None):
    """
    Checks for the uniqueness of username across users.
    """
    qs = User.objects.filter(username__iexact=username)
    if instance:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise serializers.ValidationError("A user with this username already exists.")
    return username

def validate_user_roles(is_vendor, is_customer):
    """Validates that a user has at least one role and not both simultaneously."""
    
    if not is_vendor and not is_customer:
        raise serializers.ValidationError("At least one role (vendor or customer) must be selected.")
    if is_vendor and is_customer:
        raise serializers.ValidationError("You cannot be both a vendor and a customer.")
    return True


def validate_ghanaian_phone_format(value, instance=None):
    """Ensures the phone numbers provided are in Ghanaian format"""
    pattern = r"^(?:\+233|0)\d{9}$"

    if not re.match(pattern, value):
        raise serializers.ValidationError("Phone number must be in Ghanaian format.")
    return value


