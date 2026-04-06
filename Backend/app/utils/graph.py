import json
from pathlib import Path
from typing import List, Any, Literal, Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_ollama import ChatOllama
from app.services.retriever_service import get_retriever
from app.core.config import settings

# -----------------------------
# Initialize LLM
# -----------------------------
from langchain_google_genai import ChatGoogleGenerativeAI

def initialize_llm(settings):
    # if settings.LLM_PROVIDER.lower() == "gemini":
    llm = ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.7,
    )
    return llm
    # # else:
    # llm = ChatOllama(model=settings.OLLAMA_MODEL, temperature=0.7)
    # return llm

# Use this everywhere instead of direct OllamaLLM
llm = initialize_llm(settings)
print(llm)
# -----------------------------
#  Define RAG State Schema
# -----------------------------
class RAGState(TypedDict):
    question: Annotated[str, "Input"]
    context: str | None
    docs: List[Any] | None
    answer: str | None
    route: Literal["greeting", "rag", "chat", "student", "auth_required"] | None
    is_authenticated: bool
    top_k: int | None

# -----------------------------
# 💬 Greeting Responses
# -----------------------------
GREETING_RESPONSES = {
    "hello": "Hello there! 👋 How can I help you today?",
    "hi": "Hi! 😊 What would you like to know?",
    "hey": "Hey! 👋 How are you doing?",
    "good morning": "Good morning! ☀️ Hope your day is going well!",
    "good afternoon": "Good afternoon! 🌞 How can I assist you?",
    "good evening": "Good evening! 🌙 What brings you here today?",
    "how are you": "I'm just a bunch of algorithms, but I'm feeling great! 😄 How about you?",
    "what's up": "Not much, just waiting to chat with you! 🤖",
}

# -----------------------------
# Detection Logic
# -----------------------------
def detect_greeting(q: str) -> bool:
    q = q.lower().strip()
    return any(key in q for key in GREETING_RESPONSES.keys())

def get_greeting_response(q: str) -> str:
    q = q.lower()
    for key, resp in GREETING_RESPONSES.items():
        if key in q:
            return resp
    return "Hey there! 😊 How can I help you today?"

# -----------------------------
#  Helper
# -----------------------------
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# -----------------------------
#  Prompts
# -----------------------------
rag_prompt = PromptTemplate.from_template(
    """Use the following context to answer the question.
If it's small talk, respond naturally and friendly.
Answer in the same language as the question.
If you don't know, say 'I don’t know' — do not fabricate.

Context: {context}
Question: {question}
Answer:"""
)

chat_prompt = PromptTemplate.from_template(
    """You are a friendly and helpful AI assistant for Bangladesh University of Professionals(BUP). 
Engage in a natural conversation with the user, providing thoughtful, contextual, 
and empathetic responses. Keep answers concise but engaging.

User: {question}
Assistant:"""
)

student_prompt = PromptTemplate.from_template(
    """You are a student assistant AI with access to verified student records.
Answer questions based strictly on the provided JSON data.

Data:
{student_data}

User Question: {question}

If information is unavailable or unclear, say: "I couldn’t find that information in the records."
Answer in the same language as the question."""
)

# -----------------------------
# Load Student Data (securely)
# -----------------------------
def load_student_data():
    try:
        data_path = Path(__file__).resolve().parents[1] / "db" / "private.json"
        with data_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

# -----------------------------
# Node Functions
# -----------------------------
def router(state: RAGState) -> RAGState:
    q = state["question"].lower()

    if detect_greeting(q):
        state["route"] = "greeting"
    elif any(kw in q for kw in ["cgpa", "fees", "course", "mark", "semester", "registration", "subject", "student"]):
        state["route"] = "student" if state.get("is_authenticated") else "auth_required"
    elif any(kw in q for kw in ["who", "what", "when", "where", "why", "how", "explain", "tell me about"]):
        state["route"] = "rag"
    else:
        state["route"] = "chat"
    return state

def greeting_agent(state: RAGState) -> RAGState:
    state["answer"] = get_greeting_response(state["question"])
    return state

def retrieve(state: RAGState) -> RAGState:
    k = state.get("top_k") or 3
    retriever = get_retriever(k)
    docs = retriever.invoke(state["question"])
    state["docs"] = docs
    state["context"] = format_docs(docs)
    return state

def generate(state: RAGState) -> RAGState:
    response = (rag_prompt | llm | StrOutputParser()).invoke({
        "context": state["context"],
        "question": state["question"],
    })
    state["answer"] = response
    return state

def chat_agent(state: RAGState) -> RAGState:
    response = (chat_prompt | llm | StrOutputParser()).invoke({
        "question": state["question"]
    })
    state["answer"] = response
    return state

def student_agent(state: RAGState) -> RAGState:
    student_data = load_student_data()
    response = (student_prompt | llm | StrOutputParser()).invoke({
        "student_data": json.dumps(student_data, indent=2),
        "question": state["question"],
    })
    state["answer"] = response
    return state

def auth_required_agent(state: RAGState) -> RAGState:
    state["answer"] = (
        "Please log in to access your personal student information. "
        "You can still ask about admissions or general university info."
    )
    return state

# -----------------------------
#  Build Graph
# -----------------------------
graph = StateGraph(RAGState)
graph.add_node("router", router)
graph.add_node("greeting_agent", greeting_agent)
graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)
graph.add_node("chat_agent", chat_agent)
graph.add_node("student_agent", student_agent)
graph.add_node("auth_required_agent", auth_required_agent)

def route_decision(state: RAGState):
    match state["route"]:
        case "greeting":
            return "greeting_agent"
        case "rag":
            return "retrieve"
        case "chat":
            return "chat_agent"
        case "student":
            return "student_agent"
        case "auth_required":
            return "auth_required_agent"
        case _:
            return "chat_agent"

graph.set_entry_point("router")
graph.add_conditional_edges("router", route_decision)
graph.add_edge("greeting_agent", END)
graph.add_edge("chat_agent", END)
graph.add_edge("student_agent", END)
graph.add_edge("auth_required_agent", END)
graph.add_edge("retrieve", "generate")
graph.add_edge("generate", END)

# -----------------------------
# ✅ Compile
# -----------------------------
rag_graph = graph.compile()


# graph_image_path = "rag_graph.png"

# # get raw PNG bytes
# png_bytes = rag_graph.get_graph().draw_mermaid_png()

# # write to file
# with open(graph_image_path, "wb") as f:
#     f.write(png_bytes)

# print(f"✅ Graph image saved at: {graph_image_path}")
