# vendor/models.py
from django.db import models
from django.conf import settings


class VendorProfile(models.Model):
    """
    Stores detailed profile information for users identified as Vendors.
    Includes verification documents, business info, simulated balance, and payout info.
    """

    # Relationship to User (1:1)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendor_profile'
    )



#-------------------------
    # Business Details
#--------------------------
    business_name = models.CharField(max_length=255, unique=True)

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

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default=OTHER)

    # Contact information
    phone_number = models.CharField(
        max_length=20,
        help_text="Official business phone number."
    )

    # Country (hardcoded to Ghana for now)
    country = models.CharField(
        max_length=50,
        default="Ghana",
        editable=False,
        help_text="Country where the vendor operates."
    )

    city = models.CharField(
        max_length=100,
        help_text="City or town in Ghana where the business is located."
    )

    business_address = models.CharField(
        max_length=255, default="Unknown Address",
        help_text="Physical business address (e.g., Ghana Post address)."
    )

    gps_code = models.CharField(
        max_length=20,
        help_text="GPS code (e.g., GW-0062-1604). Must be provided."
    )




    # Verification Documents
    GHANA_CARD = "GHANA_CARD"
    PASSPORT = "PASSPORT"
    DRIVERS_LICENSE = "DRIVERS_LICENSE"
    OTHER_ID = "OTHER_ID"

    OWNER_ID_CHOICES = [
        (GHANA_CARD, "Ghana Card"),
        (PASSPORT, "Passport"),
        (DRIVERS_LICENSE, "Driver’s License"),
        (OTHER_ID, "Other ID"),
    ]

    owner_id_type = models.CharField(
        max_length=30,
        choices=OWNER_ID_CHOICES,
        help_text="Type of ID submitted by business owner."
    )

    owner_id_document = models.FileField(
        upload_to="vendor_ids/",
        help_text="Upload of Ghana Card, Passport, etc."
    )

    business_registration_document = models.FileField(
        upload_to="vendor_certificates/",
        help_text="Business registration / certificate document."
    )

    business_location_image = models.ImageField(
        upload_to="vendor_locations/",
        help_text="Photo of the business physical location."
    )




    # Status & Audit Fields
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    STATUS_CHOICES = [
        (PENDING, "Pending Review"),
        (APPROVED, "Approved - Active"),
        (REJECTED, "Rejected - Inactive"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING)
    admin_approved_date = models.DateTimeField(null=True, blank=True)
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="vendor_profiles_modified",
        on_delete=models.SET_NULL,
    )



    # Payment Simulation Fields
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    payout_account_number = models.CharField(max_length=50)
    payout_bank_name = models.CharField(max_length=100)

    
    # String Representation
    def __str__(self):
        return f"{self.business_name} ({self.status}) - Balance: ${self.balance}"

    class Meta:
        verbose_name = 'Vendor Profile'
        verbose_name_plural = 'Vendor Profiles'

