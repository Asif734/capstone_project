import os
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_FILE)
load_dotenv()

class Settings:
    APP_ENV = os.getenv("APP_ENV", "development").lower()

    INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "multilingual-text")
    EMBEDDING_MODEL = os.getenv(
        "EMBEDDING_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_CACHE_ENABLED = os.getenv("REDIS_CACHE_ENABLED", "true").lower() == "true"
    REDIS_CACHE_TTL_SECONDS = int(os.getenv("REDIS_CACHE_TTL_SECONDS", "86400"))
    REDIS_CACHE_SIMILARITY_THRESHOLD = float(
        os.getenv("REDIS_CACHE_SIMILARITY_THRESHOLD", "0.80")
    )
    REDIS_CACHE_MAX_CANDIDATES = int(os.getenv("REDIS_CACHE_MAX_CANDIDATES", "500"))

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@bup.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    ADMIN_DASHBOARD_TOKEN = os.getenv("ADMIN_DASHBOARD_TOKEN")

    REQUIRE_EMAIL_DELIVERY = os.getenv("REQUIRE_EMAIL_DELIVERY", "false").lower() == "true"

    @property
    def pinecone_client(self):
        if not self.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is not configured")
        try:
            from pinecone import Pinecone
        except ImportError as exc:
            raise ImportError("pinecone package is required for Pinecone client") from exc
        return Pinecone(api_key=self.PINECONE_API_KEY)

    def validate_startup(self) -> None:
        missing = []
        if not self.JWT_SECRET_KEY:
            missing.append("JWT_SECRET_KEY")
        if not self.ADMIN_PASSWORD:
            missing.append("ADMIN_PASSWORD")
        if not self.ADMIN_DASHBOARD_TOKEN:
            missing.append("ADMIN_DASHBOARD_TOKEN")
        if self.LLM_PROVIDER != "ollama":
            missing.append("LLM_PROVIDER=ollama")

        if missing and self.APP_ENV == "production":
            raise RuntimeError(
                "Missing required production configuration: " + ", ".join(missing)
            )

settings = Settings()
