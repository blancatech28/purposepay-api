# vendor/models.py
from django.db import models
from django.conf import settings





class VendorProfile(models.Model):
    """
    Stores supplementary profile information for users identified as Vendors.
    Handles approval status, simulated balance, and payout info for the vendor.
    """

    # Status Choices
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (PENDING, "Pending Review"),       # Default state after registration
        (APPROVED, "Approved - Active"),   # Vendor can redeem vouchers
        (REJECTED, "Rejected - Inactive"), # Vendor cannot use system
    ]

    # Relationship to User (1:1)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_profile',
        help_text='The corresponding user account for login and authentication.'
    )




    # -------------------------------------------------------------------------
    # Business Details
    # -------------------------------------------------------------------------
    business_name = models.CharField(
        max_length=255,
        unique=True,
        help_text='Official name of the vendor business.'
    )

    # Use choices for category instead of free text for consistency
    PHARMACY = "PHARMACY"
    SCHOOL = "SCHOOL"
    HARDWARE = "HARDWARE"
    OTHER = "OTHER"

    CATEGORY_CHOICES = [
        (PHARMACY, "Pharmacy"),
        (SCHOOL, "School"),
        (HARDWARE, "Hardware Store"),
        (OTHER, "Other"),
    ]

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default=OTHER,
        help_text='Select the vendor business category.'
    )

    
    
    # Status & Audit Fields
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
        help_text='Current approval state of the vendor.'
    )

    admin_approved_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Date/time when admin approved the vendor.'
    )

    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="vendor_profiles_modified",
        on_delete=models.SET_NULL,
        help_text='Admin who last modified this vendor profile.'
    )

    
    
    
    # Payment Simulation Fields
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        help_text='Simulated balance for the vendor (updated after voucher redemption).'
    )

    payout_account_number = models.CharField(
        max_length=50,
        blank=True,
        help_text='Simulated payout account number for vendor withdrawals.'
    )

    payout_bank_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Simulated bank name where vendor withdraws money.'
    )

    
    
    
    # String Representation
    def __str__(self):
        return f"{self.business_name} ({self.status}) - Balance: ${self.balance}"

    class Meta:
        verbose_name = 'Vendor Profile'
        verbose_name_plural = 'Vendor Profiles'
