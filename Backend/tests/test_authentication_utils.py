import unittest

from app.utils import authentication
from app.utils.authentication import generate_otp, hash_otp, verify_otp_value


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


if __name__ == "__main__":
    unittest.main()
