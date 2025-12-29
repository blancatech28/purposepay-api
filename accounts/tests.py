# accounts/tests_accounts.py

from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()


class AccountsAPITest(APITestCase):
    def setUp(self):
        # A test user is created
        self.user_password = "ebengyim967!"
        self.user = User.objects.create_user(username="eben",
            email="ebgyim@example.com",password=self.user_password)


    # ----------------
    # REGISTER TESTS
    # ------------------
    def test_register_success(self):
        url = reverse("accounts:register")
        payload = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "test645",
            "is_customer": True
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="alice@example.com").exists())

    def test_register_fail_duplicate_email(self):
        url = reverse("accounts:register")
        payload = {
            "username": "josonn",
            "email": "ebgyim@example.com",  # this is duplicate
            "password": "emmma385",
            "is_customer": True
        }
        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


    # ------------------
    # LOGIN TESTS
    # -----------------
    def test_login_success(self):
        url = reverse("accounts:login")
        payload = {"email": "ebgyim@example.com",
            "password": self.user_password}

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["user"]["email"],
            "ebgyim@example.com")

    def test_login_fail_wrong_password(self):
        url = reverse("accounts:login")
        payload = {"email": "john@example.com","password": "wrong967"}

        response = self.client.post(url, payload)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



    # ------------------
    # USER PROFILE TESTS
    # ------------------
    def test_get_profile_authenticated(self):
        url = reverse("accounts:user-profile")

        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["email"],
            "ebgyim@example.com"
        )

    def test_update_profile_authenticated(self):
        url = reverse("accounts:user-profile")

        self.client.force_authenticate(user=self.user)
        payload = {"username": "gyimeben_updated",
            "email": "gyimeb_new@example.com"}

        response = self.client.put(url, payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "gyimeben_updated")
        self.assertEqual(self.user.email, "gyimeb_new@example.com")



    # ------------------
    # LOGOUT TEST
    # ------------------
    def test_logout_success(self):
        url = reverse("accounts:logout")

        self.client.force_authenticate(user=self.user)
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
