import hashlib
import json
import math
from typing import Any

from app.core.config import settings


class RedisSemanticCacheService:
    """Semantic Q&A cache backed by Redis.

    This cache is intentionally used only for public, non-personal answers.
    It stores the question embedding beside the answer and returns a cached
    answer only when cosine similarity passes the configured threshold.
    """

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        ttl: int | None = None,
        threshold: float | None = None,
        max_candidates: int | None = None,
    ):
        self.enabled = settings.REDIS_CACHE_ENABLED
        self.ttl = ttl or settings.REDIS_CACHE_TTL_SECONDS
        self.threshold = threshold or settings.REDIS_CACHE_SIMILARITY_THRESHOLD
        self.max_candidates = max_candidates or settings.REDIS_CACHE_MAX_CANDIDATES
        self.index_key = "qa_cache:index"
        self.key_prefix = "qa_cache:item:"
        self.redis_client = None

        if not self.enabled:
            return

        try:
            import redis

            self.redis_client = redis.Redis(
                host=host or settings.REDIS_HOST,
                port=port or settings.REDIS_PORT,
                db=db if db is not None else settings.REDIS_DB,
                decode_responses=True,
                socket_connect_timeout=0.5,
                socket_timeout=0.5,
            )
            self.redis_client.ping()
        except Exception as exc:
            print(f"[RedisSemanticCache] Disabled: {exc}")
            self.enabled = False
            self.redis_client = None

    def is_available(self) -> bool:
        return bool(self.enabled and self.redis_client)

    def _embedding(self, text: str) -> list[float]:
        from app.services.embedding import get_model

        model = get_model()
        vector = model.encode([text], convert_to_numpy=True, show_progress_bar=False)[0]
        return vector.astype(float).tolist()

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0

        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return dot / (left_norm * right_norm)

    @staticmethod
    def _cache_id(question: str) -> str:
        normalized = " ".join(question.lower().strip().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get_similar_answer(self, question: str) -> dict[str, Any] | None:
        if not self.is_available():
            return None

        try:
            query_embedding = self._embedding(question)
            item_ids = list(self.redis_client.smembers(self.index_key))[: self.max_candidates]
            best_match = None
            best_score = 0.0

            for item_id in item_ids:
                cached = self.redis_client.get(f"{self.key_prefix}{item_id}")
                if not cached:
                    self.redis_client.srem(self.index_key, item_id)
                    continue

                item = json.loads(cached)
                score = self._cosine_similarity(query_embedding, item.get("embedding", []))
                if score > best_score:
                    best_score = score
                    best_match = item

            if best_match and best_score >= self.threshold:
                return {
                    "answer": best_match["answer"],
                    "matched_question": best_match["question"],
                    "similarity": round(best_score, 4),
                    "sources": best_match.get("sources", []),
                }
        except Exception as exc:
            print(f"[RedisSemanticCache] Read failed: {exc}")

        return None

    def set_answer(
        self,
        question: str,
        answer: str,
        sources: list[dict[str, Any]] | None = None,
        route: str = "rag",
    ) -> None:
        if not self.is_available() or not answer:
            return

        try:
            item_id = self._cache_id(question)
            key = f"{self.key_prefix}{item_id}"
            payload = {
                "question": question,
                "answer": answer,
                "embedding": self._embedding(question),
                "sources": sources or [],
                "route": route,
            }
            self.redis_client.set(key, json.dumps(payload), ex=self.ttl)
            self.redis_client.sadd(self.index_key, item_id)
            self.redis_client.expire(self.index_key, self.ttl)
        except Exception as exc:
            print(f"[RedisSemanticCache] Write failed: {exc}")

    def clear_cache(self) -> None:
        if self.is_available():
            self.redis_client.delete(self.index_key)
