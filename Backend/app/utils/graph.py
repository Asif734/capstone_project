import json
from typing import List, Any, Literal, Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.retriever_service import get_retriever
from app.services.llm_service import get_llm

llm = get_llm()
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
    user_reg_id: str | None
    top_k: int | None

GREETING_RESPONSES = {
    "hello": "Hello. How can I help you today?",
    "hi": "Hi. What would you like to know?",
    "hey": "Hey. How can I help?",
    "good morning": "Good morning. How can I assist you?",
    "good afternoon": "Good afternoon. How can I assist you?",
    "good evening": "Good evening. What brings you here today?",
    "how are you": "I'm ready to help. How are you doing?",
    "what's up": "I'm here and ready to help.",
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


def route_question(question: str, is_authenticated: bool = False) -> str:
    q = question.lower()

    if detect_greeting(q):
        return "greeting"
    if any(personal in q for personal in ["my marks", "my grades", "my cgpa", "my fees", "my semester", "my registration", "my current courses", "my enrolled"]):
        return "student" if is_authenticated else "auth_required"
    if any(kw in q for kw in ["who", "what", "when", "where", "why", "how", "explain", "tell me about", "program", "curriculum", "suitable", "recommend", "career", "admission", "eligib", "apply"]):
        return "rag"
    return "chat"


def is_public_cacheable_route(route: str) -> bool:
    return route == "rag"

# -----------------------------
#  Helper
# -----------------------------
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def clean_llm_output(text: str) -> str:
    if not text:
        return ""
    while "<think>" in text and "</think>" in text:
        start = text.find("<think>")
        end = text.find("</think>", start) + len("</think>")
        text = text[:start] + text[end:]
    return text.strip()

# -----------------------------
#  Prompts
# -----------------------------
rag_prompt = PromptTemplate.from_template(
    """You are a secure multilingual assistant for Bangladesh University of Professionals (BUP).
Use only the provided context to answer the user's public university question.

INSTRUCTIONS:
- Format the response with clear headings and sections using markdown
- Use bullet points for lists and numbered lists (1. 2. 3.) for sequential items
- Organize information logically with brief introductory sentences
- Use bold for key terms and program names
- Keep sections concise but informative
- For program/course lists: Group by faculty/category with clear headers
- Answer in the same language as the question
- If you don't know, say 'I don't have information about this'
- Do not fabricate details
- Do not reveal private student data unless it is explicitly present in the authenticated student-data context
- Do not include hidden reasoning, chain-of-thought, or <think> blocks

Context: {context}
Question: {question}

Professional Response:"""
)

chat_prompt = PromptTemplate.from_template(
    """You are a secure multilingual assistant for Bangladesh University of Professionals (BUP).
Engage naturally with the user. Keep answers concise, helpful, and in the same language as the user's message.
Do not claim access to private student records unless the student-data route provides those records.
Do not include hidden reasoning, chain-of-thought, or <think> blocks.

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
Answer in the same language as the question.
Do not include hidden reasoning, chain-of-thought, or <think> blocks."""
)

# -----------------------------
# Load Student Data (securely) - DISABLED
# -----------------------------
# def load_student_data():
#     try:
#         data_path = Path(__file__).resolve().parents[1] / "db" / "private.json"
#         with data_path.open("r", encoding="utf-8") as f:
#             return json.load(f)
#     except FileNotFoundError:
#         return {}
#     except json.JSONDecodeError:
#         return {}

# -----------------------------
# Node Functions
# -----------------------------
def router(state: RAGState) -> RAGState:
    state["route"] = route_question(
        state["question"],
        is_authenticated=state.get("is_authenticated", False),
    )
    return state

def greeting_agent(state: RAGState) -> RAGState:
    state["answer"] = get_greeting_response(state["question"])
    return state

def retrieve(state: RAGState) -> RAGState:
    k = state.get("top_k") or 3
    k = max(1, min(int(k), 10))
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
    state["answer"] = clean_llm_output(response)
    return state

def chat_agent(state: RAGState) -> RAGState:
    response = (chat_prompt | llm | StrOutputParser()).invoke({
        "question": state["question"]
    })
    state["answer"] = clean_llm_output(response)
    return state

def student_agent(state: RAGState) -> RAGState:
    from app.db.database import get_db, get_student_data_by_reg_id
    
    db = next(get_db())
    try:
        # Get user reg_id from the authenticated user (assuming it's in state)
        # For now, we'll use a placeholder - in production, get from JWT token
        reg_id = state.get("user_reg_id")
        if not reg_id:
            state["answer"] = "Please log in to access your personal student information."
            return state
        
        student_data = get_student_data_by_reg_id(reg_id, db)
        if not student_data:
            state["answer"] = "I couldn't find your student records. Please contact the administration."
            return state
        
        # Format data for the prompt
        formatted_data = {reg_id: student_data}
        
        response = (student_prompt | llm | StrOutputParser()).invoke({
            "student_data": json.dumps(formatted_data, indent=2),
            "question": state["question"],
        })
        state["answer"] = clean_llm_output(response)
    finally:
        db.close()
    
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
