import unittest

from fastapi import HTTPException

from app.core.config import settings
from app.routes.admin import admin_login, require_admin
from app.schemas.admin import AdminLoginRequest


class AdminAuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.original_email = settings.ADMIN_EMAIL
        self.original_password = settings.ADMIN_PASSWORD
        self.original_secret = settings.JWT_SECRET_KEY
        settings.ADMIN_EMAIL = "admin@example.edu"
        settings.ADMIN_PASSWORD = "a-strong-admin-password"
        settings.JWT_SECRET_KEY = "test-secret-that-is-long-enough-for-tests"

    def tearDown(self):
        settings.ADMIN_EMAIL = self.original_email
        settings.ADMIN_PASSWORD = self.original_password
        settings.JWT_SECRET_KEY = self.original_secret

    def test_login_returns_a_valid_expiring_admin_token(self):
        response = admin_login(AdminLoginRequest(
            email="admin@example.edu",
            password="a-strong-admin-password",
        ))
        self.assertIsNone(require_admin(response.access_token))

    def test_static_or_invalid_token_is_rejected(self):
        with self.assertRaises(HTTPException) as context:
            require_admin("not-a-jwt")
        self.assertEqual(context.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
