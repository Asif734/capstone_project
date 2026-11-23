import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from app.services import faiss_service


class TestFaissService(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)
        # Reset cached globals
        faiss_service._vectorstore = None

    def tearDown(self):
        faiss_service._vectorstore = None

    def test_empty_vectorstore_returns_empty_retrieval(self):
        with patch.object(faiss_service.settings, "FAISS_INDEX_PATH", self.tmp_dir.name):
            retriever = faiss_service.get_retriever(k=3)
            # Empty index should return empty docs without error
            docs = retriever.invoke("any query")
            self.assertEqual(docs, [])

    def test_store_and_retrieve_embeddings(self):
        with patch.object(faiss_service.settings, "FAISS_INDEX_PATH", self.tmp_dir.name):
            chunks = [
                "Bangladesh University of Professionals (BUP) offers CSE and ICE programs.",
                "Dhaka is the capital and largest city of Bangladesh.",
            ]
            # Use deterministic mock embeddings
            dim = 384
            emb1 = np.zeros(dim, dtype=np.float32)
            emb1[0] = 1.0  # Vector pointing along dim 0
            emb2 = np.zeros(dim, dtype=np.float32)
            emb2[1] = 1.0  # Vector pointing along dim 1
            embeddings = [emb1, emb2]

            stored_count = faiss_service.store_embeddings(
                chunks=chunks,
                embeddings=embeddings,
                doc_id="test-doc-1",
                source_name="test.txt",
                titles=["Academic Info", "General Info"],
            )
            self.assertEqual(stored_count, 2)

            # Check that files were saved to disk
            saved_dir = Path(self.tmp_dir.name)
            self.assertTrue((saved_dir / "index.faiss").exists())
            self.assertTrue((saved_dir / "index.pkl").exists())

            # Now test loading from disk in a fresh vectorstore instance
            faiss_service._vectorstore = None
            vs = faiss_service.get_vectorstore()
            self.assertEqual(vs.index.ntotal, 2)

            # Similarity search with mock query vector
            query_emb = np.zeros(dim, dtype=np.float32)
            query_emb[0] = 1.0  # should match doc 1 perfectly
            results = vs.similarity_search_by_vector(query_emb.tolist(), k=1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].metadata["doc_id"], "test-doc-1")
            self.assertEqual(results[0].metadata["chunk_index"], 0)
            self.assertEqual(results[0].metadata["source_name"], "test.txt")
            self.assertEqual(results[0].metadata["title"], "Academic Info")
            self.assertIn("offers CSE", results[0].page_content)

    def test_store_embeddings_validation(self):
        with patch.object(faiss_service.settings, "FAISS_INDEX_PATH", self.tmp_dir.name):
            # Mismatched chunk and embedding lengths
            with self.assertRaises(ValueError):
                faiss_service.store_embeddings(chunks=["c1"], embeddings=[])

            # Empty chunks
            with self.assertRaises(ValueError):
                faiss_service.store_embeddings(chunks=[], embeddings=[])

            # Wrong dimension
            with self.assertRaises(ValueError):
                faiss_service.store_embeddings(
                    chunks=["c1"], embeddings=[np.zeros(10, dtype=np.float32)]
                )


if __name__ == "__main__":
    unittest.main()
