import json
import unittest

from app.services.redis_service import RedisSemanticCacheService


class FakeRedis:
    def __init__(self, values=None, item_ids=None):
        self.values = values or {}
        self.item_ids = item_ids or set()

    def get(self, key):
        return self.values.get(key)

    def smembers(self, _key):
        return self.item_ids

    def srem(self, _key, item_id):
        self.item_ids.discard(item_id)


class RedisLanguageCacheTests(unittest.TestCase):
    def make_service(self, values=None, item_ids=None):
        service = RedisSemanticCacheService.__new__(RedisSemanticCacheService)
        service.enabled = True
        service.redis_client = FakeRedis(values, item_ids)
        service.key_prefix = "cache:item:"
        service.index_key = "cache:index"
        service.max_candidates = 10
        service.threshold = 0.8
        return service

    def test_exact_cached_answer_requires_matching_language(self):
        question = "What bachelor programs does BUP offer?"
        item = {
            "question": question,
            "answer": "A Bengali answer",
            "language": "bn",
            "sources": [],
        }
        service = self.make_service({
            f"cache:item:{RedisSemanticCacheService._cache_id(question)}": json.dumps(item)
        })

        self.assertIsNone(service.get_similar_answer(question, language="en"))
        self.assertEqual(
            service.get_similar_answer(question, language="bn")["answer"],
            "A Bengali answer",
        )

    def test_semantic_cached_answer_requires_matching_language(self):
        question = "Bachelor admission programs"
        item = {
            "question": "স্নাতক ভর্তি প্রোগ্রাম",
            "answer": "A Bengali answer",
            "language": "bn",
            "embedding": [1.0, 0.0],
            "sources": [],
        }
        service = self.make_service(
            {"cache:item:bangla-entry": json.dumps(item)},
            {"bangla-entry"},
        )
        service._embedding = lambda _text: [1.0, 0.0]

        self.assertIsNone(service.get_similar_answer(question, language="en"))


if __name__ == "__main__":
    unittest.main()