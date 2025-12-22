# voucher/models.py

import string
import secrets
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
from vendor.models import VendorProfile


def generate_voucher_code():
    """Generate a unique voucher code with a purposepay prefix as PP."""
    characters = string.ascii_uppercase + string.digits
    code_length = 11
    unique_part = ''.join(secrets.choice(characters) for _ in range(code_length))
    return f"PP-{unique_part}"


def default_expiry():
    """Voucher expiry is set to 30 days from creation."""
    return timezone.now() + timedelta(days=30)


class Voucher(models.Model):
    """Table to store details of voucher issued to customers."""

    PENDING_PAYMENT = "PENDING_PAYMENT"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    EXPIRED = "EXPIRED"

    STATUS_CHOICES = [
        (PENDING_PAYMENT, "Pending Payment"),
        (ACTIVE, "Active"),
        (LOCKED, "Locked"),
        (EXPIRED, "Expired"),
    ]

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vouchers"
    )
    code = models.CharField(max_length=14, unique=True, default=generate_voucher_code, db_index=True)

    category = models.CharField(
        max_length=50, choices=VendorProfile.CATEGORY_CHOICES, help_text="Redeemable by vendors in this category"
    )
    initial_amount = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=PENDING_PAYMENT
    )
    expiry_date = models.DateTimeField(
        default=default_expiry,null=True,blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # The remaining balance is set to the initial amount on creation
        if not self.pk:
            self.remaining_balance = self.initial_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} ({self.status})"


class VoucherRedemption(models.Model):
    """This table tracks all the voucher redemptions made by a vendor."""
    
    PENDING = "PENDING"
    REDEEMED = "REDEEMED"
    CANCELLED = "CANCELLED"

    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (REDEEMED, "Redeemed"),
        (CANCELLED, "Cancelled"),
    ]
    voucher = models.ForeignKey(
        Voucher,
        on_delete=models.CASCADE,
        related_name="redemptions"
    )
    vendor = models.ForeignKey(
        VendorProfile,
        on_delete=models.CASCADE,
        related_name="voucher_redemptions"
    )
    redeemed_amount = models.DecimalField(max_digits=12, decimal_places=2)
    redeemed_at = models.DateTimeField(auto_now_add=True)

    redemption_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)

    class Meta:
        verbose_name = "Voucher Redemption"
        verbose_name_plural = "Voucher Redemptions"

    def __str__(self):
        return f"{self.voucher.code} redeemed by {self.vendor.business_name}"
