import unittest

from app.utils import authentication
from app.utils.authentication import (
    create_access_token,
    extract_bearer_token,
    generate_otp,
    has_scope,
    hash_otp,
    verify_otp_value,
    verify_token,
)


class AuthenticationUtilityTests(unittest.TestCase):
    def setUp(self):
        self.original_secret = authentication.SECRET_KEY
        authentication.SECRET_KEY = "test-secret-that-is-long-enough-for-tests"

    def tearDown(self):
        authentication.SECRET_KEY = self.original_secret

    def test_generated_otp_has_six_digits(self):
        otp = generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    def test_otp_is_hashed_and_verifiable(self):
        otp = "123456"
        stored = hash_otp(otp)
        self.assertNotEqual(stored, otp)
        self.assertTrue(verify_otp_value(otp, stored))
        self.assertFalse(verify_otp_value("654321", stored))

    def test_bearer_token_parser_rejects_malformed_headers(self):
        self.assertEqual(extract_bearer_token("Bearer abc123"), "abc123")
        self.assertEqual(extract_bearer_token("bearer abc123"), "abc123")
        self.assertIsNone(extract_bearer_token("Basic abc123"))
        self.assertIsNone(extract_bearer_token("Bearer"))

    def test_scope_check_requires_exact_scope(self):
        payload = {"scope": "student.academic.read student.profile.read"}
        self.assertTrue(has_scope(payload, "student.academic.read"))
        self.assertFalse(has_scope(payload, "student.financial.read"))

    def test_local_access_token_can_include_academic_scope(self):
        token = create_access_token(
            user_id=7,
            reg_id="TEST001",
            scopes=["student.profile.read", "student.academic.read"],
        )
        payload = verify_token(token)
        self.assertIsNotNone(payload)
        self.assertTrue(has_scope(payload, "student.academic.read"))


if __name__ == "__main__":
    unittest.main()
