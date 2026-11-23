import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.services import faiss_service

class DocumentEndpointsTestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_documents_endpoint(self):
        response = self.client.get("/documents")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("documents", data)
        self.assertIn("document_names", data)
        self.assertIn("total_documents", data)
        self.assertIsInstance(data["document_names"], list)

    def test_get_document_names_alias(self):
        response = self.client.get("/document-names")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("document_names", data)

    def test_get_single_document_not_found(self):
        response = self.client.get("/documents/non_existent_file_xyz_123.pdf")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"].lower())

    def test_delete_document_not_found(self):
        response = self.client.delete("/documents/non_existent_file_xyz_123.pdf")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"].lower())

    def test_delete_document_success_mocked(self):
        mock_result = {
            "document_name": "test_doc.docx",
            "document_id": "test-doc-id",
            "chunks_deleted": 5,
            "remaining_total_chunks": 10,
        }
        with patch("app.routes.upload_file.delete_document_by_name", return_value=mock_result):
            response = self.client.delete("/documents/test_doc.docx")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("deleted successfully", data["message"])
            self.assertEqual(data["document_name"], "test_doc.docx")
            self.assertEqual(data["chunks_deleted"], 5)

    def test_delete_document_by_query_param(self):
        mock_result = {
            "document_name": "test_doc.docx",
            "document_id": "test-doc-id",
            "chunks_deleted": 3,
            "remaining_total_chunks": 7,
        }
        with patch("app.routes.upload_file.delete_document_by_name", return_value=mock_result):
            response = self.client.delete("/documents?document_name=test_doc.docx")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["chunks_deleted"], 3)

    def test_faiss_service_delete_logic(self):
        # Test directly with faiss_service in-memory
        mock_meta = [
            {"document_id": "doc1", "document_name": "doc1.pdf", "source_name": "doc1.pdf", "chunks_count": 2, "ingested_at": "2026-01-01T00:00:00Z"}
        ]
        with patch("app.services.faiss_service.get_documents_metadata", return_value=mock_meta):
            names = faiss_service.get_document_names()
            self.assertEqual(names, ["doc1.pdf"])

    def test_real_faiss_ingest_and_delete_flow(self):
        import numpy as np
        # Ingest 2 dummy vectors for a temporary doc
        dim = getattr(faiss_service.settings, "VECTOR_DIMENSION", 384)
        dummy_embs = np.random.random((2, dim)).astype("float32")
        faiss_service.store_embeddings(
            chunks=["test chunk 1", "test chunk 2"],
            embeddings=dummy_embs,
            doc_id="temp-test-doc",
            source_name="temp_test_file.docx",
            titles=["Title 1", "Title 2"],
        )

        # 1. Verify it shows up in GET /documents
        get_res = self.client.get("/documents")
        self.assertEqual(get_res.status_code, 200)
        names = get_res.json()["document_names"]
        self.assertIn("temp_test_file.docx", names)

        # 2. Verify GET /documents/{name}
        single_res = self.client.get("/documents/temp_test_file.docx")
        self.assertEqual(single_res.status_code, 200)
        self.assertEqual(single_res.json()["document"]["document_id"], "temp-test-doc")

        # 3. Delete it via DELETE /documents/{name}
        del_res = self.client.delete("/documents/temp_test_file.docx")
        self.assertEqual(del_res.status_code, 200)
        self.assertEqual(del_res.json()["chunks_deleted"], 2)

        # 4. Verify it is gone
        get_res2 = self.client.get("/documents")
        self.assertNotIn("temp_test_file.docx", get_res2.json()["document_names"])

        # 5. Delete again -> 404
        del_res2 = self.client.delete("/documents/temp_test_file.docx")
        self.assertEqual(del_res2.status_code, 404)


if __name__ == "__main__":
    unittest.main()
