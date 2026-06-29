from django.test import TestCase
from django.core import signing
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import pyotp

from .models import PortalUser, PortalRoles


def create_user(username="testuser", password="testpass123", totp_enabled=False, totp_secret=None):
    role, _ = PortalRoles.objects.get_or_create(name="viewer")
    user = PortalUser.objects.create_user(
        username=username, password=password, email=f"{username}@test.com",
        role=role, status=True,
    )
    if totp_secret:
        user.totp_secret = totp_secret
    if totp_enabled:
        user.totp_enabled = True
    if totp_secret or totp_enabled:
        user.save()
    return user


def auth_client(user):
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return client


class LoginWithoutTOTPTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.url = reverse("user-login")

    def test_login_success_no_totp(self):
        res = self.client.post(self.url, {"username": "testuser", "password": "testpass123"})
        self.assertEqual(res.status_code, 200)
        self.assertIn("access_token", res.data)
        self.assertNotIn("requires_totp", res.data)

    def test_login_wrong_password(self):
        res = self.client.post(self.url, {"username": "testuser", "password": "wrong"})
        self.assertEqual(res.status_code, 401)

    def test_login_missing_fields(self):
        res = self.client.post(self.url, {"username": "testuser"})
        self.assertEqual(res.status_code, 400)

    def test_login_inactive_user(self):
        self.user.status = False
        self.user.save()
        res = self.client.post(self.url, {"username": "testuser", "password": "testpass123"})
        self.assertEqual(res.status_code, 400)


class LoginWithTOTPTests(TestCase):
    def setUp(self):
        self.secret = pyotp.random_base32()
        self.user = create_user(totp_enabled=True, totp_secret=self.secret)
        self.client = APIClient()
        self.login_url = reverse("user-login")
        self.verify_url = reverse("totp-login-verify")

    def test_login_returns_totp_challenge(self):
        res = self.client.post(self.login_url, {"username": "testuser", "password": "testpass123"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data.get("requires_totp"))
        self.assertIn("totp_token", res.data)
        self.assertNotIn("access_token", res.data)

    def test_totp_login_verify_success(self):
        res = self.client.post(self.login_url, {"username": "testuser", "password": "testpass123"})
        totp_token = res.data["totp_token"]
        valid_code = pyotp.TOTP(self.secret).now()
        res2 = self.client.post(self.verify_url, {"totp_token": totp_token, "totp_code": valid_code})
        self.assertEqual(res2.status_code, 200)
        self.assertIn("access_token", res2.data)

    def test_totp_login_verify_wrong_code(self):
        res = self.client.post(self.login_url, {"username": "testuser", "password": "testpass123"})
        totp_token = res.data["totp_token"]
        res2 = self.client.post(self.verify_url, {"totp_token": totp_token, "totp_code": "000000"})
        self.assertEqual(res2.status_code, 401)

    def test_totp_login_verify_expired_token(self):
        expired = signing.dumps({"user_id": self.user.id}, salt="totp-login")
        # Tamper max_age by using a fake bad signature instead
        res = self.client.post(self.verify_url, {"totp_token": "bad.token.value", "totp_code": "123456"})
        self.assertEqual(res.status_code, 400)

    def test_totp_login_verify_missing_fields(self):
        res = self.client.post(self.verify_url, {"totp_token": "abc"})
        self.assertEqual(res.status_code, 400)


class TOTPSetupTests(TestCase):
    def setUp(self):
        self.user = create_user()
        self.client = auth_client(self.user)
        self.url = reverse("totp-setup")

    def test_setup_generates_secret_and_qr(self):
        res = self.client.get(self.url)
        self.assertEqual(res.status_code, 200)
        self.assertIn("secret", res.data)
        self.assertIn("qr_uri", res.data)
        self.assertIn("otpauth://totp/", res.data["qr_uri"])

    def test_setup_reuses_existing_secret(self):
        res1 = self.client.get(self.url)
        res2 = self.client.get(self.url)
        self.assertEqual(res1.data["secret"], res2.data["secret"])

    def test_setup_requires_auth(self):
        res = APIClient().get(self.url)
        self.assertEqual(res.status_code, 401)


class TOTPEnableTests(TestCase):
    def setUp(self):
        self.secret = pyotp.random_base32()
        self.user = create_user(totp_secret=self.secret)
        self.client = auth_client(self.user)
        self.url = reverse("totp-enable")

    def test_enable_with_valid_code(self):
        code = pyotp.TOTP(self.secret).now()
        res = self.client.post(self.url, {"totp_code": code})
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.totp_enabled)

    def test_enable_with_invalid_code(self):
        res = self.client.post(self.url, {"totp_code": "000000"})
        self.assertEqual(res.status_code, 400)
        self.user.refresh_from_db()
        self.assertFalse(self.user.totp_enabled)

    def test_enable_without_setup(self):
        self.user.totp_secret = None
        self.user.save()
        res = self.client.post(self.url, {"totp_code": "123456"})
        self.assertEqual(res.status_code, 400)

    def test_enable_missing_code(self):
        res = self.client.post(self.url, {})
        self.assertEqual(res.status_code, 400)


class TOTPDisableTests(TestCase):
    def setUp(self):
        self.secret = pyotp.random_base32()
        self.user = create_user(totp_enabled=True, totp_secret=self.secret)
        self.client = auth_client(self.user)
        self.url = reverse("totp-disable")

    def test_disable_with_valid_code(self):
        code = pyotp.TOTP(self.secret).now()
        res = self.client.post(self.url, {"totp_code": code})
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.totp_enabled)
        self.assertIsNone(self.user.totp_secret)

    def test_disable_with_invalid_code(self):
        res = self.client.post(self.url, {"totp_code": "000000"})
        self.assertEqual(res.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.totp_enabled)

    def test_disable_when_not_enabled(self):
        self.user.totp_enabled = False
        self.user.save()
        res = self.client.post(self.url, {"totp_code": "123456"})
        self.assertEqual(res.status_code, 400)

    def test_disable_missing_code(self):
        res = self.client.post(self.url, {})
        self.assertEqual(res.status_code, 400)

