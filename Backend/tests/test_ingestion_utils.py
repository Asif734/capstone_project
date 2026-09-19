import unittest

from fastapi import HTTPException

from app.routes.upload_file import normalize_doc_id
from app.utils.preprocess_text import chunk_text, extract_text


class IngestionUtilityTests(unittest.TestCase):
    def test_document_id_is_sanitized(self):
        self.assertEqual(normalize_doc_id(" Admissions / 2026 "), "Admissions-2026")

    def test_invalid_document_id_is_rejected(self):
        with self.assertRaises(HTTPException):
            normalize_doc_id("////")

    def test_chunks_have_overlap_without_duplicate_tail(self):
        text = " ".join(str(number) for number in range(10))
        chunks = chunk_text(text, chunk_size=5, overlap=2)
        self.assertEqual(chunks, ["0 1 2 3 4", "3 4 5 6 7", "6 7 8 9"])

    def test_txt_must_be_utf8(self):
        with self.assertRaisesRegex(ValueError, "UTF-8"):
            extract_text(b"\xff\xfe", "document.txt")


if __name__ == "__main__":
    unittest.main()
