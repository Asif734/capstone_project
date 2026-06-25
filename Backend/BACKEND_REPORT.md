# Backend Technical Report

## 1. Project Overview

This backend is a FastAPI-based service for a secure, multilingual university assistant for Bangladesh University of Professionals (BUP). It is not only a simple chatbot backend. It combines a local LLM chatbot, retrieval-augmented generation (RAG), authenticated student record access, document ingestion, admin controls, and mental-health risk monitoring.

The backend is organized around these major responsibilities:

- Accepting chat questions from the frontend through `/query`
- Routing each question to the correct agent or workflow
- Answering public university questions with RAG
- Protecting private student information behind authentication
- Allowing admins to manage authorized students and mental-health alerts
- Uploading and indexing documents into Pinecone
- Detecting mental-health risk signals from authenticated student conversations
- Running the LLM locally through Ollama using `qwen3:4b`

Main backend entry point:

```text
app/main.py
```

Important modules:

```text
app/routes/query.py
app/routes/authentication.py
app/routes/admin.py
app/routes/upload_file.py
app/utils/graph.py
app/services/llm_service.py
app/services/retriever_service.py
app/services/mental_health_service.py
app/services/memory_service.py
app/db/database.py
app/db/student_tables.py
```

## 2. Backend Startup Flow

The FastAPI application is created in `app/main.py`. During startup, the lifespan function runs several initialization tasks:

1. Validates important runtime configuration through `settings.validate_startup()`.
2. Opens a database session.
3. Applies lightweight schema migrations for existing SQLite databases.
4. Initializes authorized users from local JSON data if needed.
5. Populates private student records from `private.json`.
6. Creates SQLAlchemy tables through `sqldb.Base.metadata.create_all`.
7. Registers the API routers:
   - Authentication routes
   - Admin routes
   - Upload route
   - Query route

The app also enables CORS for local frontend development and deployed frontend origins.

## 3. Configuration and Local LLM Setup

Configuration is defined in:

```text
app/core/config.py
```

The backend is now configured as a local-LLM-first system:

```text
LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen3:4b
OLLAMA_BASE_URL=http://localhost:11434
LLM_TEMPERATURE=0.3
```

The LLM is created in:

```text
app/services/llm_service.py
```

This file exposes `get_llm()`, which returns a `ChatOllama` instance using the configured local Ollama model. The current model is:

```text
qwen3:4b
```

This design makes the LLM layer clean and isolated. The graph does not need to know the full model setup details; it simply calls `get_llm()`.

## 4. Main Query Flow

The main chatbot endpoint is:

```text
POST /query
```

Defined in:

```text
app/routes/query.py
```

The request schema is:

```python
class QueryRequest(BaseModel):
    user_id: str
    question: str
    top_k: Optional[int] = 3
```

The high-level flow is:

1. Frontend sends a question to `/query`.
2. Backend checks for `X-User-Token`.
3. If a valid JWT token exists, the request is treated as authenticated.
4. The query state is passed into the LangGraph RAG graph.
5. The graph decides which agent should handle the question.
6. The selected agent generates an answer.
7. Retrieved source documents are returned if the RAG path was used.
8. The interaction is saved in chat memory.
9. If the user is authenticated, the mental-health service evaluates recent messages.
10. The final response is sent back to the frontend.

The response schema is:

```python
class QueryResponse(BaseModel):
    answer: str
    sources: List[SourceDocument]
```

## 5. Agent Architecture

The agent workflow is implemented in:

```text
app/utils/graph.py
```

The backend uses LangGraph to route a query into different specialized nodes. The graph state contains:

```python
class RAGState(TypedDict):
    question: str
    context: str | None
    docs: List[Any] | None
    answer: str | None
    route: Literal["greeting", "rag", "chat", "student", "auth_required"] | None
    is_authenticated: bool
    user_reg_id: str | None
    top_k: int | None
```

### Router Agent

The router agent is the decision-maker. It inspects the user question and assigns one route:

```text
greeting
rag
chat
student
auth_required
```

It uses simple intent rules:

- Greeting-like messages go to the greeting agent.
- Personal student-data questions such as "my marks", "my CGPA", "my fees", or "my current courses" require authentication.
- General university questions such as admissions, programs, career guidance, curriculum, and eligibility go to RAG.
- Other conversational questions go to the chat agent.

### Greeting Agent

The greeting agent returns a fixed friendly response for common greetings. It avoids unnecessary LLM calls, which improves latency.

### RAG Agent

The RAG workflow has two nodes:

```text
retrieve -> generate
```

The retrieve node gets relevant chunks from Pinecone. The generate node sends the retrieved context and the user question to the local Qwen model.

### Chat Agent

The chat agent handles general conversation. It uses the local Ollama model with a prompt that instructs the assistant to be concise, multilingual, and secure.

### Student Agent

The student agent handles private student-data questions. It only runs when the user is authenticated. It retrieves the student's own record from the database using the registration ID stored in the JWT token.

If no authenticated `user_reg_id` is available, it refuses access and asks the user to log in.

### Auth Required Agent

This agent protects private data. If a user asks about personal records without being logged in, the graph returns a login-required message instead of retrieving or generating private data.

## 6. Public vs Private Data Separation

The backend separates public and private data at several levels.

### Public Data

Public information includes:

- Admissions information
- Program descriptions
- Curriculum details
- General BUP information
- Uploaded university documents stored in Pinecone

Public questions are handled by the RAG route. These questions do not require authentication.

### Private Student Data

Private data includes:

- Marks
- CGPA
- Course enrollment
- Semester
- Pending fees
- Registration-related information

This data is stored in SQL tables and loaded from `private.json` into database tables such as:

```text
authorized_users
academic_records
financial_records
student_courses
cgpa_records
```

Private-data access is protected by:

- JWT token validation
- `X-User-Token` request header
- Route-level intent separation in the graph
- Registration ID from token payload, not from user text
- Student agent refusing access when no authenticated registration ID exists

This prevents a user from asking for another student's data by simply typing a registration ID in the prompt.

## 7. Authentication and Security

Authentication is implemented in:

```text
app/routes/authentication.py
app/utils/authentication.py
app/db/database.py
```

The signup flow:

1. Student provides registration ID and email.
2. Backend checks whether the student exists in the authorized user list.
3. Backend generates and stores an OTP.
4. OTP is sent or printed depending on environment configuration.
5. Student verifies OTP and sets a password.
6. Password is hashed with bcrypt after SHA-256 prehashing.
7. A verified user account is created.

The login flow:

1. Student submits registration ID and password.
2. Backend checks account existence and active status.
3. Backend blocks login if the account is locked.
4. Password is verified.
5. Failed login attempts are tracked.
6. After repeated failures, the account is locked temporarily.
7. Successful login creates a JWT access token.
8. A session record is stored with a token hash.
9. Login history is recorded.

Security features:

- Password hashing with bcrypt
- Password strength validation
- JWT access tokens
- Token hashing for sessions
- Failed login attempt tracking
- Temporary account lockout
- OTP expiration and attempt limits
- Admin routes protected by `X-Admin-Token`
- Production startup validation for critical secrets
- Removed hardcoded OTP bypass
- Removed fake JWT fallback secret

## 8. RAG System

The RAG system is responsible for answering public university questions using indexed documents.

### Document Upload

The upload endpoint is:

```text
POST /Upload
```

Defined in:

```text
app/routes/upload_file.py
```

The upload pipeline:

1. Receives a PDF, DOCX, or TXT file.
2. Extracts text using `extract_text`.
3. For PDFs without extractable text, OCR is attempted with `pytesseract`.
4. Cleans the text by normalizing whitespace.
5. Splits text into chunks of around 300 words.
6. Generates embeddings for each chunk.
7. Stores vectors and metadata in Pinecone.

### Embeddings

Embeddings are generated in:

```text
app/services/embedding.py
```

The embedding model is:

```text
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
```

This model supports multilingual semantic search, which is important because the assistant is intended to work with multilingual queries.

### Vector Store

Vector storage is handled in:

```text
app/services/pinecone.py
app/services/retriever_service.py
```

Each stored vector includes:

```python
{
    "text": safe_text,
    "doc_id": doc_id,
    "chunk_index": i
}
```

The retriever uses Pinecone similarity search:

```python
search_type="similarity"
search_kwargs={"k": k}
```

The backend clamps `top_k` between 1 and 10 to prevent excessive retrieval.

### RAG Answer Generation

For public university questions:

1. Router sends the query to the RAG route.
2. Retriever fetches the most relevant document chunks.
3. Chunks are formatted as context.
4. Local Qwen model receives the context and question.
5. The prompt instructs the model to answer only from the provided context.
6. If the information is not present, it should say it does not have the information.

This reduces hallucination because the model is not asked to invent university facts from memory.

## 9. Mental-Health Detection System

Mental-health monitoring is implemented in:

```text
app/services/mental_health_service.py
```

This service runs only after an authenticated user's query has been answered and saved to memory. It does not run for anonymous users.

### Chat Memory

Chat memory is managed by:

```text
app/services/memory_service.py
```

Each interaction is stored as:

```python
{
    "timestamp": "...",
    "question": "...",
    "answer": "..."
}
```

The mental-health service analyzes the most recent messages for the authenticated user.

### ML-Based Detection

The primary detector is a saved ML model:

```text
app/services/best_mental_health_model.pkl
app/services/tfidf_vectorizer.pkl
app/services/label_encoder.pkl
```

The service loads:

- A LightGBM classifier
- A TF-IDF vectorizer
- A label encoder

The recent user messages are combined into one text string, preprocessed, vectorized with TF-IDF, and classified.

The model predicts classes such as:

```text
Normal
Anxiety
Stress
Depression
Suicidal
Bipolar
Personality disorder
```

The predicted class is mapped into an application risk level:

```python
{
    "Normal": "normal",
    "Anxiety": "moderate",
    "Stress": "moderate",
    "Depression": "high",
    "Suicidal": "high",
    "Bipolar": "high",
    "Personality disorder": "high"
}
```

The service also calculates:

- Prediction confidence
- Risk score from confidence
- Severity level
- Latest risky message sample

### Rule-Based Fallback

If the model artifacts are missing, the service falls back to rule-based detection.

The fallback checks for high-risk and medium-risk phrases such as:

- suicidal phrases
- self-harm phrases
- depression and anxiety terms
- hopelessness terms
- support-seeking terms

This gives the system a backup safety mechanism if the ML model cannot load.

## 10. Mental-Health Model Training and Accuracy

The training script is:

```text
notebooks/mental_health_model.py
```

A dedicated LightGBM save script is:

```text
save_lgbm_model.py
```

The model pipeline:

1. Loads the dataset from `app/db/Combined Data.csv`.
2. Drops rows with missing statements.
3. Lowercases text.
4. Removes non-letter characters.
5. Removes English stopwords.
6. Lemmatizes words.
7. Converts text into TF-IDF features.
8. Uses up to 1000 TF-IDF features with unigram and bigram support.
9. Encodes labels with `LabelEncoder`.
10. Splits data into train/test with stratification.
11. Trains multiple classifiers.
12. Saves the selected model and artifacts with Joblib.

Models compared in the training script:

- Logistic Regression
- Random Forest
- XGBoost
- LightGBM
- AdaBoost

The training script compares the following model results:

| Model | Accuracy | Macro ROC-AUC |
| --- | ---: | ---: |
| LightGBM | 0.7642 | 0.9533 |
| XGBoost | 0.7514 | 0.9493 |
| Logistic Regression | 0.7453 | 0.9454 |
| Random Forest | 0.7261 | 0.9331 |
| AdaBoost | 0.6154 | 0.8669 |

The deployed runtime service expects the primary detector to be LightGBM, and the test file confirms this expectation:

```text
app/services/test_mental_health_service.py
```

The deployment script and runtime artifacts use LightGBM as the primary production model for the backend.

## 11. Alert Creation and Admin Notification

Mental-health alerts are stored in the database table:

```text
mental_health_alerts
```

Defined in:

```text
app/db/student_tables.py
```

An alert contains:

- User ID
- Registration ID
- Severity
- Score
- Predicted class
- Confidence
- Matched phrases or ML prediction summary
- Latest message sample
- Status
- Admin notes
- Review timestamps

Alert creation happens in:

```text
MentalHealthService.evaluate_user_risk()
```

The alert flow:

1. Authenticated student sends a query.
2. Query and answer are saved to memory.
3. Mental-health service loads the student's recent messages.
4. ML model predicts mental-health class and confidence.
5. Risk level is mapped to severity.
6. If risk is high enough, the service checks whether a recent alert already exists.
7. A cooldown prevents duplicate alerts within 24 hours.
8. A new alert is saved in the database.
9. Admin notification is triggered.

Alert threshold for ML mode:

```python
risk_level in ["high", "moderate"] and confidence > 0.7
```

Severity logic:

- Suicidal with confidence >= 0.7 becomes `critical`.
- High-risk class with confidence >= 0.9 becomes `critical`.
- Other high or moderate classes map to their risk level.
- Otherwise severity is `low`.

The notification method is:

```text
send_admin_notification()
```

Currently, this prints an admin alert message. The code is structured so a real email provider such as SendGrid or AWS SES can replace the print-based notification.

## 12. Admin Dashboard Backend

Admin APIs are defined in:

```text
app/routes/admin.py
```

Admin authentication:

```text
POST /admin/login
```

The admin enters configured admin email and password. If valid, the backend returns the admin dashboard token. Protected admin routes require:

```text
X-Admin-Token
```

Admin capabilities:

- View mental-health summary
- View all mental-health alerts
- Filter alerts by status
- Update alert status
- Add admin notes
- View a student's mental-health alert history
- Add authorized students
- Update authorized student records
- Delete authorized students

Important admin endpoints:

```text
GET    /admin/mental-health-summary
GET    /admin/mental-health-alerts
PATCH  /admin/mental-health-alerts/{alert_id}
GET    /admin/students/{reg_id}/mental-health
GET    /admin/authorized-students
POST   /admin/authorized-students
PATCH  /admin/authorized-students/{student_id}
DELETE /admin/authorized-students/{student_id}
```

Alerts are sorted so the most serious cases appear first:

1. Critical
2. High
3. Moderate
4. Low

Within severity groups, new or active alerts are prioritized.

## 13. How Everything Is Connected

The complete backend connection can be summarized as:

```text
Frontend
  |
  | POST /query
  v
FastAPI Query Route
  |
  | validates optional JWT token
  v
LangGraph Router
  |
  +--> Greeting Agent
  |
  +--> Chat Agent
  |      |
  |      v
  |   Local Ollama LLM: qwen3:4b
  |
  +--> RAG Agent
  |      |
  |      v
  |   Pinecone Retriever -> Context -> Local Ollama LLM
  |
  +--> Student Agent
  |      |
  |      v
  |   Authenticated DB lookup -> Local Ollama LLM
  |
  +--> Auth Required Agent
         |
         v
      Login-required response

After response:
  |
  v
MemoryService saves interaction
  |
  v
MentalHealthService analyzes authenticated user's recent messages
  |
  v
ML model or rule fallback detects risk
  |
  v
MentalHealthAlert saved to database
  |
  v
Admin dashboard can review alert
```

## 14. Production-Readiness Strengths

Current strengths:

- Clear route separation
- Local LLM support through Ollama
- RAG and student-record access separated by intent and authentication
- JWT-based student login
- Account lockout after failed login attempts
- OTP-based signup
- Admin-only endpoints protected by admin token
- ML-based mental-health monitoring
- Alert cooldown to reduce duplicate alerts
- Local model artifacts for mental-health detection
- Multilingual embedding model for retrieval
- Startup validation for required production secrets

## 15. Remaining Improvements

Recommended future improvements:

- Replace print-based OTP and admin notification with real email delivery.
- Move chat memory from JSON file to SQL database or Redis.
- Add refresh-token and logout endpoint behavior.
- Add request rate limiting.
- Add structured audit logs for private student-data access.
- Add row-level privacy tests for student records.
- Add streaming responses for local LLM output.
- Add health endpoints for Ollama, Pinecone, and database.
- Store ML model artifacts in a controlled artifact registry.
- Replace pickle-based model loading with a safer model persistence format if possible.
- Add evaluation data for Bangla and mixed Bangla-English mental-health inputs.

## 16. Conclusion

The backend is a full-stack AI service layer for a secure university assistant. It combines public RAG, private student-data access, authentication, local LLM generation, document indexing, admin workflows, and mental-health risk detection. The agent graph is the central controller: it decides whether a message should be answered as a greeting, general chat, public RAG question, authenticated student-record question, or rejected until login.

The most important engineering idea is separation of responsibility. Public university knowledge is answered through RAG. Private student records are only available after JWT authentication. Mental-health monitoring runs only for authenticated users and creates admin-reviewable alerts when the ML model detects risk. The local Ollama model keeps sensitive conversations inside the local system, which supports the project's goal of secure, multilingual, production-ready chatbot infrastructure.
