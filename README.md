# BUP Student Assistant

A FastAPI and React assistant for public BUP information, authenticated student records, and supportive wellbeing conversations. Public university answers use Pinecone retrieval and a local Ollama model; private record access is bound to the authenticated JWT session.

## Architecture

```text
React/Vite
   |
FastAPI routes -- authentication/admin -- SQLite or DATABASE_URL
   |
LangGraph router
   |-- greeting / general chat
   |-- public RAG -- Pinecone -- multilingual embeddings -- Ollama
   |-- authenticated student records
   `-- wellbeing support -- rules + calibrated ML signal -- admin alert

Optional Redis semantic cache (public RAG answers only)
```

The wellbeing component is a risk-signal and response-routing aid, not a diagnosis system. Explicit safety language takes priority over ML output. Ambiguous statements such as “I am not feeling well” receive a gentle clarification instead of an automatic crisis response or diagnosis.

## Local setup

Requirements: Python 3.11+, Node.js 22+, Ollama, and optionally Redis. Pinecone is required for document ingestion and public RAG queries.

```bash
cp Backend/.env.example Backend/.env
cd Backend
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
ollama pull llama3.2:3b
./venv/bin/uvicorn app.main:app --reload
```

In another terminal:

```bash
cd Frontend
npm ci
npm run dev
```

Copy `Backend/app/db/students.example.json` to `students.json` and `private.example.json` to `private.json` only for local seed data. Those runtime files, the SQLite database, chat memory, credentials, and bytecode are intentionally excluded from Git.

## Configuration

Use `Backend/.env.example` as the complete configuration template. Important production requirements:

- Set `APP_ENV=production`, a strong `JWT_SECRET_KEY`, admin credentials, and exact `CORS_ORIGINS`.
- Set `REQUIRE_EMAIL_DELIVERY=true` and configure SMTP. Development is the only environment that logs OTP values.
- Set `SEED_LOCAL_DATA=false`, `CHAT_MEMORY_BACKEND=database`, and a durable `DATABASE_URL` for deployed environments.
- Keep `PINECONE_DIMENSION` aligned with the configured embedding model.
- Keep Redis optional; the app disables its cache if Redis is unavailable.

## Verification

```bash
cd Backend
./venv/bin/python -B -m unittest discover -s tests -p 'test*.py'
./venv/bin/python -B -m unittest app.services.test_mental_health_service
./venv/bin/python -m pip check

cd ../Frontend
npm run build
npm audit
```

The backend unit tests cover routing regressions, input validation, secure OTP utilities, ingestion utilities, memory persistence, admin tokens, cache behavior, and wellbeing risk rules. End-to-end RAG tests additionally require live Ollama, Pinecone, and optionally Redis services.

## Deployment notes

- Build from `Backend/Dockerfile`; its non-root runtime includes Poppler and Tesseract for PDF OCR.
- Use a managed relational database and migrations before horizontal scaling. The JSON memory store is deliberately limited to single-process local use; replace it with a database or Redis conversation repository for multiple workers.
- Terminate TLS at the platform/reverse proxy and apply request rate limits to login, signup, OTP, query, and upload endpoints.
- Rotate any secret ever committed to Git. Removing a secret from the current source does not remove it from repository history.
- Validate the wellbeing model on representative BUP data, with human review and documented consent/retention policy, before using alerts operationally.
