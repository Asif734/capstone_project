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
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
    OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))
    OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "1024"))
    OLLAMA_TIMEOUT_SECONDS = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "60"))

    DATABASE_URL = os.getenv("DATABASE_URL")
    DATABASE_ECHO = os.getenv("DATABASE_ECHO", "false").lower() == "true"
    CHAT_MEMORY_BACKEND = os.getenv(
        "CHAT_MEMORY_BACKEND", "database" if APP_ENV == "production" else "json"
    ).lower()
    CHAT_MEMORY_MAX_INTERACTIONS = int(os.getenv("CHAT_MEMORY_MAX_INTERACTIONS", "100"))
    CORS_ORIGINS = tuple(
        origin.strip().rstrip("/")
        for origin in os.getenv(
            "CORS_ORIGINS",
            "https://bup-chat.vercel.app,http://localhost:3000,http://localhost:5173,http://localhost:3001",
        ).split(",")
        if origin.strip()
    )
    MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))
    MAX_DOCUMENT_PAGES = int(os.getenv("MAX_DOCUMENT_PAGES", "200"))
    PINECONE_DIMENSION = int(os.getenv("PINECONE_DIMENSION", "384"))
    PINECONE_CLOUD = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION = os.getenv("PINECONE_REGION", "us-east-1")
    PINECONE_UPSERT_BATCH_SIZE = int(os.getenv("PINECONE_UPSERT_BATCH_SIZE", "100"))
    RAG_SCORE_THRESHOLD = float(os.getenv("RAG_SCORE_THRESHOLD", "0.35"))
    MENTAL_HEALTH_ML_THRESHOLD = float(os.getenv("MENTAL_HEALTH_ML_THRESHOLD", "0.45"))
    SEED_LOCAL_DATA = os.getenv(
        "SEED_LOCAL_DATA", "true" if APP_ENV == "development" else "false"
    ).lower() == "true"

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    REDIS_CACHE_ENABLED = os.getenv("REDIS_CACHE_ENABLED", "true").lower() == "true"
    REDIS_CACHE_TTL_SECONDS = int(os.getenv("REDIS_CACHE_TTL_SECONDS", "86400"))
    REDIS_CACHE_SIMILARITY_THRESHOLD = float(
        os.getenv("REDIS_CACHE_SIMILARITY_THRESHOLD", "0.92")
    )
    REDIS_CACHE_MAX_CANDIDATES = int(os.getenv("REDIS_CACHE_MAX_CANDIDATES", "500"))

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    OAUTH_ISSUER = os.getenv("OAUTH_ISSUER")
    OAUTH_AUDIENCE = os.getenv("OAUTH_AUDIENCE")
    OAUTH_JWKS_URL = os.getenv("OAUTH_JWKS_URL")
    OAUTH_USER_ID_CLAIM = os.getenv("OAUTH_USER_ID_CLAIM", "user_id")
    OAUTH_REG_ID_CLAIM = os.getenv("OAUTH_REG_ID_CLAIM", "reg_id")
    ALLOW_LOCAL_OAUTH = os.getenv(
        "ALLOW_LOCAL_OAUTH", "true" if APP_ENV == "development" else "false"
    ).lower() == "true"
    ALLOW_LEGACY_USER_TOKEN = os.getenv(
        "ALLOW_LEGACY_USER_TOKEN", "true" if APP_ENV == "development" else "false"
    ).lower() == "true"
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@bup.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    ADMIN_TOKEN_EXPIRE_MINUTES = int(os.getenv("ADMIN_TOKEN_EXPIRE_MINUTES", "480"))

    REQUIRE_EMAIL_DELIVERY = os.getenv("REQUIRE_EMAIL_DELIVERY", "false").lower() == "true"
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

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
        if not self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32:
            missing.append("JWT_SECRET_KEY (at least 32 characters)")
        if self.APP_ENV == "production":
            if not self.OAUTH_ISSUER:
                missing.append("OAUTH_ISSUER")
            if not self.OAUTH_AUDIENCE:
                missing.append("OAUTH_AUDIENCE")
            if not self.OAUTH_JWKS_URL:
                missing.append("OAUTH_JWKS_URL")
            if not self.OAUTH_USER_ID_CLAIM or not self.OAUTH_REG_ID_CLAIM:
                missing.append("OAUTH_USER_ID_CLAIM and OAUTH_REG_ID_CLAIM")
            if self.ALLOW_LOCAL_OAUTH:
                missing.append("ALLOW_LOCAL_OAUTH=false")
            if self.ALLOW_LEGACY_USER_TOKEN:
                missing.append("ALLOW_LEGACY_USER_TOKEN=false")
        if not self.ADMIN_PASSWORD or len(self.ADMIN_PASSWORD) < 12:
            missing.append("ADMIN_PASSWORD (at least 12 characters)")
        if self.LLM_PROVIDER != "ollama":
            missing.append("LLM_PROVIDER=ollama")
        if not self.REQUIRE_EMAIL_DELIVERY:
            missing.append("REQUIRE_EMAIL_DELIVERY=true")
        elif not self.SMTP_HOST or not self.SMTP_FROM_EMAIL:
            missing.append("SMTP_HOST and SMTP_FROM_EMAIL")
        if not self.PINECONE_API_KEY:
            missing.append("PINECONE_API_KEY")
        if not self.DATABASE_URL:
            missing.append("DATABASE_URL")
        if not self.CORS_ORIGINS or "*" in self.CORS_ORIGINS:
            missing.append("explicit CORS_ORIGINS")

        if not 0 <= self.LLM_TEMPERATURE <= 2:
            raise RuntimeError("LLM_TEMPERATURE must be between 0 and 2")
        if self.OLLAMA_NUM_CTX <= 0 or self.OLLAMA_NUM_PREDICT <= 0:
            raise RuntimeError("Ollama token limits must be positive")
        if self.OLLAMA_TIMEOUT_SECONDS <= 0:
            raise RuntimeError("OLLAMA_TIMEOUT_SECONDS must be positive")
        if self.MAX_UPLOAD_BYTES <= 0 or self.MAX_DOCUMENT_PAGES <= 0:
            raise RuntimeError("Upload limits must be positive")
        if self.CHAT_MEMORY_BACKEND not in {"json", "database"}:
            raise RuntimeError("CHAT_MEMORY_BACKEND must be 'json' or 'database'")
        if self.CHAT_MEMORY_MAX_INTERACTIONS <= 0:
            raise RuntimeError("CHAT_MEMORY_MAX_INTERACTIONS must be positive")
        if self.PINECONE_DIMENSION <= 0 or self.PINECONE_UPSERT_BATCH_SIZE <= 0:
            raise RuntimeError("Pinecone dimension and batch size must be positive")
        if not 0 <= self.RAG_SCORE_THRESHOLD <= 1:
            raise RuntimeError("RAG_SCORE_THRESHOLD must be between 0 and 1")
        if not 0 <= self.MENTAL_HEALTH_ML_THRESHOLD <= 1:
            raise RuntimeError("MENTAL_HEALTH_ML_THRESHOLD must be between 0 and 1")
        if self.ADMIN_TOKEN_EXPIRE_MINUTES <= 0:
            raise RuntimeError("ADMIN_TOKEN_EXPIRE_MINUTES must be positive")

        if missing and self.APP_ENV == "production":
            raise RuntimeError(
                "Missing required production configuration: " + ", ".join(missing)
            )

settings = Settings()
