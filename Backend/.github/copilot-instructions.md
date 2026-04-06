# Copilot / AI agent guidance for University_chatbot_using_langgraph

Purpose: Give an AI coding agent immediate, actionable context so it can be productive editing, extending, or fixing this project.

- Big picture
  - This is a small FastAPI service. The app entrypoint is `app/main.py` which creates the FastAPI `app` and includes routers from `app/routes/`.
  - Main responsibilities are: authentication (OTP + JSON-file user store), file upload, and a query/embedding pipeline powered by sentence-transformers and optional vector stores (Pinecone).
  - Persistent data is file-based JSON under `app/db/` (students.json, users.json, otp.json). Use `app/db/database.py` utilities (e.g. `load_students`, `save_user`, `get_otp`) — do not edit these JSON files directly unless adding test fixtures.

- Key files and what they contain
  - `app/main.py` — FastAPI app + router inclusion. Run target for `uvicorn` (use `uvicorn app.main:app --reload`).
  - `app/routes/authentication.py` — signup / verify-otp / login flows. OTPs are generated and stored in `otp.json`; verified users are saved in `users.json`. The file contains the project-specific password hashing (salt+sha256 encoded with base64) and calls into `app/utils/authentication.py` for token creation and mail sending.
  - `app/core/config.py` — loads environment variables (.env via python-dotenv) and exposes Settings (PINECONE keys, LLM provider selection, JWT secret). Prefer changing behavior through env variables rather than hard edits.
  - `app/services/embedding.py` — loads a SentenceTransformer model once at module import and exposes `get_embedding(chunks)`. Avoid re-instantiating the model per-request.
  - `app/db/database.py` — centralized JSON read/write helpers. Use these helpers to avoid concurrency/format mistakes.
  - `requirements.txt` — heavy ML/LLM dependencies are present (langchain, sentence-transformers, pinecone, google SDKs). Install with `pip install -r requirements.txt` before running.

- Conventions and important patterns
  - Data store is synchronous, file-based JSON. When modifying user/otp/student data, use `app/db/database.py` API to preserve file format and to keep single responsibility.
  - Authentication endpoints are mostly synchronous functions (non-async). Keep route signatures consistent with existing patterns.
  - Heavy resources (embedding models, clients) are loaded at module scope in `app/services/*` or via `app/core/config.py` (Pinecone client property). Reuse those singletons.
  - Environment configuration lives in `.env` and `app/core/config.py`. Keys to know: `PINECONE_API_KEY`, `GEMINI_API_KEY`, `LLM_PROVIDER` ("gemini" or "ollama"), `OLLAMA_MODEL` and `GEMINI_MODEL`.

- Developer workflows (how to run & debug)
  - Install deps: `pip install -r requirements.txt`.
  - Add `.env` with required keys (see `app/core/config.py`). Example keys: `PINECONE_API_KEY`, `GEMINI_API_KEY`, optional `LLM_PROVIDER`.
  - Run dev server (PowerShell):
    ```powershell
    pip install -r requirements.txt
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
  - Endpoints are under `/` and routers: Authentication tag contains `/signup`, `/verify-otp`, `/login` (see `app/routes/authentication.py`).

- Integration points and external deps
  - Vector DB / embeddings: Pinecone (configured by `app/core/config.py` and `app/services/pinecone.py`), sentence-transformers model in `app/services/embedding.py`.
  - LLM providers: Gemini (Google) and Ollama are supported — provider selection via `LLM_PROVIDER` env var. Many langchain/langgraph packages are installed.
  - Email/OTP: OTP sending is implemented via `app/utils/authentication.py` (used by signup flow); OTPs are stored in `app/db/otp.json`.

- When editing code
  - Prefer adding functionality under `app/routes/` (new routers) and registering them in `app/main.py`.
  - Use existing helpers in `app/db/database.py` for JSON I/O. Add unit-test-like example JSON fixture files if you need to change persistence shape.
  - Avoid changing the JWT secret or the default hashing algorithm without updating `app/utils/authentication.py` and all places that create/verify tokens.

- Quick pointers for common tasks
  - Add an API route: create file `app/routes/<name>.py`, define `router = APIRouter()` and endpoints, then `app.include_router(<module>.router, tags=["..."])` in `app/main.py`.
  - Add embeddings: use `get_embedding(chunks)` from `app/services/embedding.py` to keep behavior consistent.

If any section is unclear or you want more detail (examples of common edits, or to include additional files like `app/services/retriever_service.py`), tell me which area to expand and I will iterate.
