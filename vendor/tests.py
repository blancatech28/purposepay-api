# vendor/tests.py
from accounts.models import CustomUser
from rest_framework.test import APITestCase
from rest_framework import status
from .models import VendorProfile, VendorFinance, VendorVerification
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from io import BytesIO

User = CustomUser

# This helper function generates a simple 1x1 PNG image for testing
def get_test_image_file(filename="location.png"):
    image_io = BytesIO()
    image = Image.new("RGB", (1, 1), color=(255, 0, 0))  # red pixel
    image.save(image_io, format='PNG')
    image_io.seek(0)
    return SimpleUploadedFile(filename, image_io.read(), content_type="image/png")


class VendorCreationTests(APITestCase):
    def setUp(self):
        # Create a user who is a vendor
        self.user = User.objects.create_user(username="ppgyim",email="vendor@example.com",
            password="password123",is_vendor=True)
        self.client.force_authenticate(user=self.user)

    def get_vendor_data(self):
        """ This return a  fresh vendor data with new files each time"""
        return {
            "business_name": "Test Vendor",
            "category": "PHARMACY",
            "phone_number": "0241234567",
            "city": "Accra",
            "business_address": "Amasaman",
            "gps_code": "GW-0000-0000",
            "finance.payout_account_number": "1234567890",
            "finance.payout_bank_name": "Purpose Bank",
            "verification.owner_id_type": "GHANA_CARD",
            "verification.owner_id_document": SimpleUploadedFile(
                "owner_id.pdf", b"file_content", content_type="application/pdf"
            ),
            "verification.business_registration_document": SimpleUploadedFile(
                "business_cert.pdf", b"file_content", content_type="application/pdf"
            ),
            "verification.business_location_image": get_test_image_file()
        }

    def test_vendor_creation_success(self):
        """A vendor can be created with the nested finance and verification serializers"""
        vendor_data = self.get_vendor_data()
        response = self.client.post("/vendor/create/", vendor_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(VendorProfile.objects.filter(user=self.user).exists())
        self.assertTrue(VendorFinance.objects.filter(vendor__user=self.user).exists())
        self.assertTrue(VendorVerification.objects.filter(vendor__user=self.user).exists())

    def test_duplicate_vendor_creation_fail(self):
        """This test shows a vendor cannot create multiple vendor profiles"""
        vendor_data = self.get_vendor_data()
        self.client.post("/vendor/create/", vendor_data, format='multipart')
        response = self.client.post("/vendor/create/", self.get_vendor_data(), format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



# ----------------------------
# Vendor Self View & Update
# ----------------------------
class VendorSelfTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ppgyim2",
            email="vendor2@example.com", password="password123", is_vendor=True)
        
        self.client.force_authenticate(user=self.user)
        self.vendor = VendorProfile.objects.create(
            user=self.user,business_name="Vendor Self",
            phone_number="0249876543",
            city="Kumasi",business_address="TestGhana",
            gps_code="GW-0001-0001"
        )

    def test_get_vendor_self(self):
        """A vendor can retrieve their own profile"""
        response = self.client.get("/vendor/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['business_name'], self.vendor.business_name)

    def test_update_vendor_self(self):
        """The vendor can update allowed fields"""
        data = {"phone_number": "0241112322", "city": "Accra", "business_address": "New Address"}
        response = self.client.patch("/vendor/me/", data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vendor.refresh_from_db()
        self.assertEqual(self.vendor.phone_number, "0241112322")
        self.assertEqual(self.vendor.city, "Accra")
        self.assertEqual(self.vendor.business_address, "New Address")


# ----------------------------
# Admin Approve/Reject Tests
# ----------------------------
class VendorAdminTests(APITestCase):
    def setUp(self):
        # Superuser for the admin actions
        self.admin = User.objects.create_superuser(username="admin", 
            email="admin@example.com", password="adminpass")
        
        self.vendor_user = User.objects.create_user(
            username="ppgyimadmin",
            email="vendor4@example.com", 
            password="password123", 
            is_vendor=True
        )
        self.vendor = VendorProfile.objects.create(
            user=self.vendor_user,
            business_name="Vendor Admin",phone_number="0241112222",
            city="Tamale",business_address="Address",
            gps_code="GW-0003-0003"
        )
        # Ensures a verification record exists for the vendor
        if not hasattr(self.vendor, 'verification'):
            VendorVerification.objects.create(
                vendor=self.vendor,
                owner_id_type="GHANA_CARD",
                owner_id_document=None,
                business_registration_document=None,
                business_location_image=None
            )
        self.client.force_authenticate(user=self.admin)

    def test_admin_approve_vendor(self):
        """Test for approving a vendor"""
        response = self.client.post(f"/vendor/admin/{self.vendor.id}/approve/")
        self.assertEqual(response.status_code, 200)
        self.vendor.verification.refresh_from_db()
        self.assertEqual(self.vendor.verification.status, "APPROVED")

    def test_admin_reject_vendor(self):
        """Admin can reject a vendor"""
        response = self.client.post(f"/vendor/admin/{self.vendor.id}/reject/")
        self.assertEqual(response.status_code, 200)
        self.vendor.verification.refresh_from_db()
        self.assertEqual(self.vendor.verification.status, "REJECTED")


# Vendor Payout Tests
class VendorPayoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ppgyimpayout",
            email="vendor2@example.com", password="password123", 
            is_vendor=True)
        
        self.client.force_authenticate(user=self.user)
        self.vendor = VendorProfile.objects.create(user=self.user,
            business_name="Vendor Payout",phone_number="0249876543",
            city="Kumasi",business_address="Test Address",gps_code="GW-0001-0001")
        
        # Create a finance record
        self.finance = VendorFinance.objects.create(vendor=self.vendor, balance=1000, 
            payout_account_number="1234567890", 
            payout_bank_name="Test Bank")
        
        # Check if the vendor is approved for payout
        if not hasattr(self.vendor, 'verification'):
            VendorVerification.objects.create(vendor=self.vendor,owner_id_type="GHANA_CARD",
                owner_id_document=None,business_registration_document=None,
                business_location_image=None)
        self.vendor.verification.status = "APPROVED"
        self.vendor.verification.save()

    def test_payout_too_low(self):
        "Withdrawal below minimum shoudl fail"
        response = self.client.post("/vendor/payout/", {"amount": 20})
        self.assertEqual(response.status_code, 400)

    def test_payout_success(self):
        "Withdrawal should fail if it's above minimum"
        response = self.client.post("/vendor/payout/", {"amount": 200})
        self.assertEqual(response.status_code, 200)
        self.finance.refresh_from_db()
        self.assertEqual(float(self.finance.balance), 800)
