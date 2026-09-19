import unittest

from pydantic import ValidationError

from app.schemas.models import QueryRequest


class QueryRequestTests(unittest.TestCase):
    def test_strips_text_and_accepts_valid_limits(self):
        request = QueryRequest(user_id="  conversation-123  ", question="  hello  ", top_k=10)
        self.assertEqual(request.user_id, "conversation-123")
        self.assertEqual(request.question, "hello")

    def test_rejects_blank_question(self):
        with self.assertRaises(ValidationError):
            QueryRequest(user_id="conversation-123", question="   ")

    def test_rejects_excessive_top_k(self):
        with self.assertRaises(ValidationError):
            QueryRequest(user_id="conversation-123", question="hello", top_k=11)


if __name__ == "__main__":
    unittest.main()
