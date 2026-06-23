# Project Features

## 1. Secure Multilingual University Chatbot

The project provides an AI-powered chatbot for Bangladesh University of Professionals (BUP). It is designed to answer student and university-related questions in a conversational way while supporting multilingual interaction.

Key capabilities:

- Answers general university questions
- Supports multilingual semantic retrieval
- Uses a local LLM through Ollama
- Keeps sensitive conversations inside the local system
- Responds through a React-based chat interface

The chatbot is not only a generic assistant. It is connected to university documents, student records, authentication, admin monitoring, and mental-health risk detection.

## 2. Local LLM Integration

The backend uses a locally hosted Ollama model:

```text
qwen3:4b
```

This improves privacy because user messages do not need to be sent to a third-party cloud LLM provider.

Benefits:

- Better control over sensitive student data
- Local inference
- Reduced dependency on external AI APIs
- More suitable for secure institutional use

## 3. Retrieval-Augmented Generation

The chatbot uses RAG to answer public university questions from uploaded documents.

RAG features:

- Upload PDF, DOCX, or TXT files
- Extract text from documents
- Use OCR for scanned PDF pages when text is not directly extractable
- Clean and split documents into chunks
- Generate multilingual embeddings
- Store vectors in Pinecone
- Retrieve relevant chunks during question answering
- Generate grounded answers from retrieved context

This helps the chatbot answer from university-specific knowledge instead of relying only on the LLM's general knowledge.

## 4. Document Upload and Knowledge Base Creation

Admins or operators can upload documents to build the chatbot's knowledge base.

Supported file types:

- PDF
- DOCX
- TXT

Processing pipeline:

1. Extract text from the uploaded file.
2. Clean unnecessary whitespace.
3. Split the text into chunks.
4. Generate embeddings for each chunk.
5. Store the chunks and metadata in Pinecone.

This makes the system expandable because new university documents can be added without retraining the LLM.

## 5. Public and Private Query Separation

The system separates public university questions from private student-data questions.

Public questions include:

- Admission information
- Program details
- Curriculum questions
- Career guidance
- General university information

Private questions include:

- My marks
- My CGPA
- My semester
- My courses
- My pending fees
- My registration details

Private data is only accessible after login. If an unauthenticated user asks for personal information, the system asks them to sign in instead of exposing data.

## 6. Student Authentication

The backend includes a student authentication system.

Authentication features:

- Registration ID and email verification
- OTP-based signup
- Password creation
- Password strength validation
- Secure password hashing
- Login with registration ID and password
- JWT access token generation
- Session tracking
- Login history
- Failed login attempt tracking
- Temporary account lockout after repeated failed attempts

This ensures that private student records are only available to verified students.

## 7. Private Student Record Access

Authenticated students can ask questions about their own records.

Supported private data:

- Name
- Department
- Year
- Semester
- Courses
- Marks
- CGPA history
- Pending fees
- Academic status

The system uses the registration ID from the authenticated JWT token. This prevents a user from accessing another student's information by simply typing another registration ID.

## 8. Agent-Based Query Routing

The backend uses a LangGraph-based agent workflow to route each question.

Main agents:

- **Greeting Agent:** Handles greetings without calling the LLM.
- **Chat Agent:** Handles normal conversation using the local LLM.
- **RAG Agent:** Handles public university questions using retrieved context.
- **Student Agent:** Handles authenticated private student-record questions.
- **Auth Required Agent:** Blocks private-data access when the user is not logged in.
- **Router Agent:** Decides which agent should handle each question.

This makes the chatbot more structured and secure than a single prompt-based chatbot.

## 9. Redis Semantic Cache for Frequent Questions

The project includes a Redis-based semantic cache for frequently asked public questions.

How it works:

1. The system checks whether a question is public and cacheable.
2. It creates an embedding for the question.
3. It compares the question with cached questions.
4. If similarity is at least `80%`, it returns the cached answer.
5. If similarity is below `80%`, the system uses RAG or the local LLM.
6. The new public answer is saved to Redis for future reuse.

Security rule:

```text
Private student-data answers are not cached.
```

Benefits:

- Faster answers for repeated public questions
- Lower local LLM workload
- Lower RAG retrieval cost
- Better user experience for common queries

## 10. Mental-Health Risk Detection

The backend includes a mental-health risk detection feature for authenticated students.

The system analyzes recent student messages and checks for possible risk signals.

Detection features:

- Uses recent chat history
- Loads a trained LightGBM model
- Uses TF-IDF text features
- Predicts mental-health categories
- Maps predicted classes into risk levels
- Creates alerts when risk is high enough
- Includes a rule-based fallback if the ML model is unavailable

Possible model classes:

- Normal
- Anxiety
- Stress
- Depression
- Suicidal
- Bipolar
- Personality disorder

The feature is intended as an early warning support mechanism, not as a clinical diagnosis.

## 11. Admin Mental-Health Alerts

When the mental-health detector identifies risk, the backend creates an admin alert.

Alert information includes:

- Student registration ID
- Severity
- Risk score
- Predicted class
- Confidence
- Latest concerning message sample
- Alert status
- Admin notes
- Created and reviewed timestamps

Alert severity levels:

- Critical
- High
- Moderate
- Low

The system also uses a cooldown period to reduce duplicate alerts for the same student.

## 12. Admin Dashboard

The frontend includes an admin dashboard connected to protected backend admin APIs.

Admin features:

- Admin login
- View mental-health summary
- View all mental-health alerts
- Review critical and high-risk alerts
- Update alert status
- Add admin notes
- View student-specific mental-health alert history
- Add authorized students
- Edit authorized student information
- Delete authorized students

Admin endpoints are protected using an admin token.

## 13. Authorized Student Management

Admins can manage which students are allowed to register and use private student services.

Authorized student data includes:

- Registration ID
- Name
- Email
- Department
- Year
- Semester
- Status

This prevents random users from creating accounts unless their registration ID and email exist in the authorized student list.

## 14. Database-Backed Records

The backend uses SQLAlchemy with SQLite for local development.

Database tables include:

- Authorized users
- Registered users
- OTP records
- Sessions
- Login history
- Academic records
- Financial records
- Student courses
- CGPA records
- Mental-health alerts

This gives the project a proper data layer instead of depending only on static files.

## 15. Security Features

Security-focused features include:

- JWT authentication
- Password hashing
- Password strength checks
- OTP verification
- OTP expiration
- OTP attempt limits
- Login attempt tracking
- Temporary account lockout
- Admin-token-protected routes
- Public/private route separation
- Private-data access through authenticated token identity
- Production environment secret validation
- Local LLM inference for sensitive conversations
- No Redis caching for private student answers

These features make the project stronger than a normal chatbot demo.

## 16. Frontend Features

The frontend is built with React, Vite, and Tailwind CSS.

Frontend features:

- Chat interface
- Message input
- Welcome screen
- Authentication modal
- Sign in flow
- Signup with OTP flow
- Header navigation
- Admin dashboard view
- Student management UI
- Alert review UI
- API service layer for backend communication

The frontend communicates with the backend through centralized API functions.

## 17. Multilingual Support

The project supports multilingual behavior in two ways:

- The embedding model is multilingual.
- The prompts instruct the LLM to answer in the same language as the question.

This allows the assistant to support English, Bangla, and mixed-language queries more naturally, depending on the indexed content and model capability.

## 18. Production-Oriented Design

The project includes several production-oriented design choices:

- Modular backend routes
- Separate services for LLM, Redis, retrieval, memory, and mental-health detection
- Environment-based configuration
- Local LLM support
- Redis cache support
- Admin workflows
- Database-backed user and student data
- ML model artifacts for runtime inference
- CORS configuration
- Dockerfile for backend deployment

## 19. Overall Feature Summary

This project includes:

- Local LLM chatbot
- Multilingual RAG
- Document upload and indexing
- Pinecone vector search
- Redis semantic cache
- Student authentication
- Private student-data access
- Admin dashboard
- Authorized student management
- Mental-health risk detection
- Admin alert system
- Secure public/private data separation
- Full-stack React + FastAPI architecture

Together, these features make the system a secure, AI-powered university assistant rather than a simple chatbot.
