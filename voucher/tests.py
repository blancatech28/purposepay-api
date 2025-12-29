# voucher/tests.py

from decimal import Decimal
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from voucher.models import Voucher, VoucherRedemption, CustomerVoucherWallet
from vendor.models import VendorProfile, VendorVerification, VendorFinance

User = get_user_model()



class VoucherAppTests(APITestCase):
    def setUp(self):
       
        # Create a customer user
        self.customer = User.objects.create_user(username="customer1", email="customer@example.com", password="password123")
        self.client.force_authenticate(user=self.customer)

        # Customer voucher wallet
        self.wallet = CustomerVoucherWallet.objects.create(customer=self.customer, balance=Decimal("1000.00"))

        # Create an approved vendor
        self.vendor_user = User.objects.create_user(
            username="vendor1", email="vendor@example.com", password="password123", is_vendor=True)
        
        self.vendor = VendorProfile.objects.create(
            user=self.vendor_user,business_name="Vendor One",
            phone_number="0241234567",city="Accra",
            business_address="Vendor Address",
            gps_code="GW-0001-0001",category="PHARMACY"
        )
        self.vendor_verification = VendorVerification.objects.create(vendor=self.vendor, status=VendorVerification.APPROVED)
        self.vendor_finance = VendorFinance.objects.create(vendor=self.vendor, balance=Decimal("0.00"),
                            payout_account_number="1234567890", payout_bank_name="Purpose Bank")


    # The Wallet Deposit Test
    def test_wallet_deposit(self):
        response = self.client.post("/voucher/wallet/deposit/", {"amount": "500.00"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("1500.00"))


    # Voucher Creation Test
    def test_voucher_creation_success(self):
        voucher_data = {"category": "PHARMACY","initial_amount": "200.00"}
        response = self.client.post("/voucher/create/", voucher_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Voucher created in database
        voucher = Voucher.objects.get(customer=self.customer)
        self.assertEqual(voucher.remaining_balance, Decimal("200.00"))
        self.assertEqual(voucher.escrow_balance, Decimal("200.00"))
        self.assertEqual(voucher.status, Voucher.PENDING)

        # Wallet balance deducted
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal("800.00"))

   
    # Voucher Activation Test
    def test_voucher_activation(self):
        voucher = Voucher.objects.create(customer=self.customer, category="PHARMACY", 
                initial_amount=Decimal("100.00"), status=Voucher.PENDING)
        
        response = self.client.post(f"/voucher/{voucher.id}/activate/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        voucher.refresh_from_db()
        self.assertEqual(voucher.status, Voucher.ACTIVE)

  
    # Redemption request of voucher by Vendor
    def test_voucher_redemption_request(self):
        # Create an active voucher
        voucher = Voucher.objects.create(customer=self.customer, category="PHARMACY",
                                         initial_amount=Decimal("200.00"), status=Voucher.ACTIVE)
        self.client.force_authenticate(user=self.vendor_user)
        redemption_data = {"voucher_code": voucher.code, "redeemed_amount": "100.00"}
        response = self.client.post("/voucher/vendor/redemptions/create/", redemption_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        redemption = VoucherRedemption.objects.get(voucher=voucher, vendor=self.vendor)
        self.assertEqual(redemption.redeemed_amount, Decimal("100.00"))
        self.assertEqual(redemption.redemption_status, VoucherRedemption.PENDING)


    # Redemption Confirmation by Customer who owns the voucher
    def test_voucher_redemption_confirm(self):
        voucher = Voucher.objects.create(customer=self.customer, category="PHARMACY",
                                         initial_amount=Decimal("200.00"), status=Voucher.ACTIVE)
        redemption = VoucherRedemption.objects.create(voucher=voucher, vendor=self.vendor,
                                                      redeemed_amount=Decimal("100.00"))

        # The customer confirms redemption
        self.client.force_authenticate(user=self.customer)
        response = self.client.patch(f"/voucher/redemptions/{redemption.id}/confirm/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        redemption.refresh_from_db()
        voucher.refresh_from_db()
        self.vendor_finance.refresh_from_db()

        self.assertEqual(redemption.redemption_status, VoucherRedemption.REDEEMED)
        self.assertEqual(voucher.remaining_balance, Decimal("100.00"))
        self.assertEqual(voucher.escrow_balance, Decimal("100.00"))
        self.assertEqual(self.vendor_finance.balance, Decimal("100.00"))


    # Cancel Redemption Test
    def test_redemption_cancel(self):
        voucher = Voucher.objects.create(customer=self.customer, category="PHARMACY",
                                         initial_amount=Decimal("200.00"), status=Voucher.ACTIVE)
        redemption = VoucherRedemption.objects.create(voucher=voucher, vendor=self.vendor,
                                                      redeemed_amount=Decimal("100.00"))
        self.client.force_authenticate(user=self.customer)
        response = self.client.patch(f"/voucher/redemptions/{redemption.id}/cancel/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        redemption.refresh_from_db()
        self.assertEqual(redemption.redemption_status, VoucherRedemption.CANCELLED)


    # Admin Voucher List Test
    def test_admin_voucher_list(self):
        Voucher.objects.create(customer=self.customer, category="PHARMACY", initial_amount=Decimal("100.00"))
        admin_user = User.objects.create_superuser(username="admin", email="admin@example.com", password="adminpass")
        self.client.force_authenticate(user=admin_user)
        response = self.client.get("/voucher/admin/vouchers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

