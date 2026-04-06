# import os
# from pinecone import Pinecone

# class Settings:
#     PINECONE_API_KEY = os.getenv(
#         "PINECONE_API_KEY",
#         "pcsk_5MgxE2_SvtRBE7ARYHwcVd5S5ucZEucguxrL86BCdEovgadhSFoHqDE3CmKVP5nVNRW4cm"
#     )
#     INDEX_NAME = "multilingual-text"
#     LLM_MODEL = "gemma3:4b"
#     EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

#     # Gemini model (optional)
#     GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBw_vv1SHpPSjd_14RDbNyLolPNl5kkrIs")
#     GEMINI_MODEL = "gemini-2.5-flash"

# # ✅ Environment setup
# os.environ["PINECONE_API_KEY"] = Settings.PINECONE_API_KEY
# os.environ["GOOGLE_API_KEY"] = Settings.GEMINI_API_KEY

# settings = Settings()
# pc = Pinecone(api_key=settings.PINECONE_API_KEY)





import os
from dotenv import load_dotenv
from pinecone import Pinecone

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Pinecone setup
    INDEX_NAME = "multilingual-text"
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

    # 🔥 Choose your LLM provider
    # Options: "ollama" or "gemini"
    #LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

    # Default LLM Models
    #OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:4b")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # API Keys (read from .env)
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    #JWT token
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    # Initialize Pinecone client
    @property
    def pinecone_client(self):
        return Pinecone(api_key=self.PINECONE_API_KEY)


# Create a global instance
settings = Settings()

