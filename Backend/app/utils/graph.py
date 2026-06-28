import json
import re
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
    route: Literal["greeting", "rag", "chat", "student", "auth_required", "clarify", "mental_support"] | None
    is_authenticated: bool
    user_reg_id: str | None
    top_k: int | None
    conversation_history: List[dict] | None

GREETING_RESPONSES = {
    "hello": "Hello! How can I help you today?",
    "hi": "Hi! What would you like to know?",
    "hey": "Hey! How can I help?",
    "good morning": "Good morning! How can I assist you?",
    "good afternoon": "Good afternoon! How can I assist you?",
    "good evening": "Good evening! What brings you here today?",
    "how are you": "I'm doing well, buddy. How are you doing?",
    "how are you doing": "I'm doing well, buddy. How are you doing?",
    "how are you feeling": "I'm feeling good and ready to help. How are you feeling?",
    "what's up": "Not much, buddy. How can I help?",
    "whats up": "Not much, buddy. How can I help?",
}

CASUAL_ADDRESS_PATTERN = re.compile(r"\b(buddy|bro|friend|dear)\b", re.IGNORECASE)

# -----------------------------
# Detection Logic
# -----------------------------
def detect_greeting(q: str) -> bool:
    q = q.lower().strip()
    return any(re.search(rf"\b{re.escape(key)}\b", q) for key in GREETING_RESPONSES.keys())

def get_greeting_response(q: str) -> str:
    q = q.lower().strip()
    for key, resp in GREETING_RESPONSES.items():
        if re.search(rf"\b{re.escape(key)}\b", q):
            return resp
    if CASUAL_ADDRESS_PATTERN.search(q):
        return "Hey buddy! How can I help you today?"
    return "Hey there! How can I help you today?"


FIRST_PERSON_PATTERN = re.compile(
    r"\b(my|me|mine|i|ami|amar|amake|apnar)\b|আমার|আমি|আমাকে|আপনার",
    re.IGNORECASE,
)

STUDENT_RECORD_PATTERN = re.compile(
    r"\b("
    r"name|marks?|grades?|cgpa|cggpa|gpa|fees?|dues?|payment|semester|registration|"
    r"student\s*id|result|transcript|profile|record|attendance|department|email|courses?"
    r")\b|"
    r"নাম|মার্ক|গ্রেড|সিজিপিএ|জিপিএ|ফি|সেমিস্টার|রেজিস্ট্রেশন|আইডি|রেজাল্ট|"
    r"ট্রান্সক্রিপ্ট|প্রোফাইল|রেকর্ড|উপস্থিতি|বিভাগ|ডিপার্টমেন্ট|ইমেইল",
    re.IGNORECASE,
)

PRIVATE_STUDENT_TERMS = [
    "cgpa",
    "cggpa",
    "gpa",
    "marks",
    "mark",
    "grade",
    "grades",
    "fees",
    "fee",
    "dues",
    "payment",
    "semester",
    "course",
    "courses",
    "attendance",
    "result",
    "transcript",
    "registration",
    "profile",
    "record",
    "email",
]

IDENTITY_INTENT_PATTERN = re.compile(
    r"\b("
    r"do you know me|do you know who i am|do you know my name|do you know my details|"
    r"who am i|what is my name|what's my name|tell me my name|show my name|"
    r"my name|my profile|my details|about me|know me|know who i am"
    r")\b",
    re.IGNORECASE,
)

ADMISSION_TERMS = [
    "admission",
    "admissions",
    "apply",
    "application",
    "eligibility",
    "eligible",
    "requirement",
    "requirements",
]

PROGRAM_LEVEL_TERMS = [
    "undergraduate",
    "bachelor",
    "bba",
    "bss",
    "honours",
    "honors",
    "masters",
    "master",
    "msc",
    "mphil",
    "phd",
    "doctoral",
    "doctorate",
]

CRISIS_TERMS = [
    "i want to die",
    "don't want to live",
    "dont want to live",
    "do not want to live",
    "kill myself",
    "end my life",
    "no reason to live",
    "not worth living",
    "self harm",
    "suicidal",
    "can't continue",
    "cannot continue",
]

SUPPORT_TERMS = [
    "not feeling good",
    "don't feel good",
    "dont feel good",
    "feeling bad",
    "feel bad",
    "feeling low",
    "feel low",
    "stressed",
    "stress",
    "can't stay positive",
    "cant stay positive",
    "depressed",
    "anxious",
    "anxiety",
    "should quit",
    "want to quit",
    "sekhane jete chai na",
]

ACADEMIC_WORRY_PATTERN = re.compile(
    r"\b("
    r"not going well|worried|worry|afraid|scared|tense|panic|upset|sad|bad|worse|fail|failed|"
    r"can't stay positive|cant stay positive"
    r")\b.*\b("
    r"academic|academics|study|studies|result|results|marks?|grades?|cgpa|gpa|exam|exams|semester"
    r")\b|"
    r"\b("
    r"academic|academics|study|studies|result|results|marks?|grades?|cgpa|gpa|exam|exams|semester"
    r")\b.*\b("
    r"not going well|worried|worry|afraid|scared|tense|panic|upset|sad|bad|worse|fail|failed|"
    r"can't stay positive|cant stay positive"
    r")\b",
    re.IGNORECASE,
)


def has_identity_intent(q: str) -> bool:
    return bool(IDENTITY_INTENT_PATTERN.search(q))


def has_private_data_intent(q: str) -> bool:
    asks_about_self = bool(FIRST_PERSON_PATTERN.search(q))
    asks_about_record = bool(STUDENT_RECORD_PATTERN.search(q))
    mentions_student_id = bool(re.search(r"\b\d{6,}\b", q))
    has_private_term = any(term in q.lower() for term in PRIVATE_STUDENT_TERMS)
    return asks_about_record and (asks_about_self or mentions_student_id or has_private_term)


def is_bangla(text: str) -> bool:
    return any("\u0980" <= char <= "\u09ff" for char in text)


def is_banglish(text: str) -> bool:
    q = text.lower()
    banglish_terms = [
        "ami", "amr", "amar", "tmi", "tumi", "apni", "apnar", "kemon",
        "acho", "achi", "valo", "bhalo", "kharap", "keno", "ki", "kisu",
        "kichu", "koto", "kon", "konta", "naam", "nam", "bolen", "bolo",
        "hobe", "hocche", "lagche",
    ]
    return any(re.search(rf"\b{re.escape(term)}\b", q) for term in banglish_terms)


def response_language_instruction(text: str) -> str:
    if is_bangla(text):
        return "Reply in Bangla using Bengali script only."
    if is_banglish(text):
        return "Reply in Banglish, using romanized Bangla words and English letters only. Do not use Bengali script."
    return "Reply in English only. Do not use Bengali script."


def has_crisis_intent(q: str) -> bool:
    return any(term in q for term in CRISIS_TERMS)


def has_support_intent(q: str) -> bool:
    return any(term in q for term in SUPPORT_TERMS)


def has_academic_worry_intent(q: str) -> bool:
    return bool(ACADEMIC_WORRY_PATTERN.search(q))


def is_support_follow_up(q: str, conversation_history: List[dict] | None = None) -> bool:
    if len(q.split()) > 4 or not conversation_history:
        return False

    if q.strip(" ?.!").lower() not in {"why", "why not", "what should i do", "what now"}:
        return False

    recent_text = " ".join(
        f"{item.get('question', '')} {item.get('answer', '')}".lower()
        for item in conversation_history[-3:]
    )
    return any(
        term in recent_text
        for term in [
            "feeling this way",
            "academic pressure",
            "can't stay positive",
            "cant stay positive",
            "result is going to be worse",
        ]
    )


def is_broad_admission_question(q: str, conversation_history: List[dict] | None = None) -> bool:
    has_admission_intent = any(term in q for term in ADMISSION_TERMS)
    has_specific_level = any(term in q for term in PROGRAM_LEVEL_TERMS)
    words = set(q.replace("/", " ").replace("-", " ").replace("?", " ").split())
    has_specific_program = bool(words.intersection({"mice", "mict", "miss", "fbs", "fss", "fsst"}))

    if not has_admission_intent:
        return False
    if has_specific_level or has_specific_program:
        return False

    recent_assistant_text = " ".join(
        item.get("answer", "").lower()
        for item in (conversation_history or [])[-3:]
    )
    if "which level" in recent_assistant_text or "undergraduate" in recent_assistant_text:
        return False

    return True


def is_contextual_follow_up(q: str) -> bool:
    words = q.split()
    if len(words) > 6:
        return False
    return any(term in q for term in PROGRAM_LEVEL_TERMS + ["yes", "that one", "the first", "the second", "the third"])


def format_conversation_history(history: List[dict] | None, limit: int = 4) -> str:
    if not history:
        return "No previous conversation."

    lines = []
    for item in history[-limit:]:
        question = item.get("question", "").strip()
        answer = item.get("answer", "").strip()
        if question:
            lines.append(f"User: {question}")
        if answer:
            lines.append(f"Assistant: {answer[:500]}")

    return "\n".join(lines) if lines else "No previous conversation."


def build_contextual_question(question: str, history: List[dict] | None) -> str:
    q = question.lower().strip()
    if not history or not is_contextual_follow_up(q):
        return question

    recent_text = " ".join(
        f"{item.get('question', '')} {item.get('answer', '')}".lower()
        for item in history[-4:]
    )
    if any(term in recent_text for term in ADMISSION_TERMS + ["which level", "mphil", "phd"]):
        return f"BUP admission details for {question}"

    return question


def route_question(
    question: str,
    is_authenticated: bool = False,
    conversation_history: List[dict] | None = None,
) -> str:
    q = question.lower()

    if has_identity_intent(q):
        return "student" if is_authenticated else "auth_required"
    if has_crisis_intent(q):
        return "mental_support"
    if is_support_follow_up(q, conversation_history):
        return "mental_support"
    if has_support_intent(q) or has_academic_worry_intent(q):
        return "mental_support"
    if has_private_data_intent(q):
        return "student" if is_authenticated else "auth_required"
    if is_broad_admission_question(q, conversation_history):
        return "clarify"
    if detect_greeting(q):
        return "greeting"
    if any(kw in q for kw in ["who", "what", "when", "where", "why", "how", "explain", "tell me about", "program", "curriculum", "suitable", "recommend", "career", "admission", "eligib", "apply"]):
        return "rag"
    if is_contextual_follow_up(q):
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
- Be conversational, specific, and easy to scan
- Prefer a short answer with 3-5 bullets unless the user asks for details
- Ask one helpful follow-up question when the answer depends on program level, faculty, or degree type
- Do not include large tables unless the user asks for comparison
- Use bold for key terms and program names
- Follow the required response language exactly
- If you don't know, say 'I don't have information about this'
- Do not fabricate details
- Do not reveal private student data unless it is explicitly present in the authenticated student-data context
- Do not include hidden reasoning, chain-of-thought, or <think> blocks

Required response language:
{response_language}

Recent conversation:
{conversation_history}

Context: {context}
Question: {question}

Helpful response:"""
)

chat_prompt = PromptTemplate.from_template(
    """You are a secure multilingual assistant for Bangladesh University of Professionals (BUP).
Engage naturally with the user. Keep answers concise and helpful.
Do not claim access to private student records unless the student-data route provides those records.
Follow the required response language exactly.
Do not include hidden reasoning, chain-of-thought, or <think> blocks.

Required response language:
{response_language}

Recent conversation:
{conversation_history}

User: {question}
Assistant:"""
)

mental_support_prompt = PromptTemplate.from_template(
    """You are a calm, supportive assistant for Bangladesh University of Professionals (BUP).
The user is sharing stress, low mood, or academic worry.

INSTRUCTIONS:
- Do not jump directly to "contact BUP well-being cell" for normal stress.
- First try to understand the exact problem by asking one gentle follow-up question.
- Keep the response to 2 short sentences.
- Validate the feeling briefly, then ask what specific part is hardest.
- If academics are mentioned, ask whether the main issue is exams, CGPA/results, attendance, family pressure, finances, or time management.
- Do not claim access to private student records.
- Follow the required response language exactly.
- Do not include hidden reasoning, chain-of-thought, or <think> blocks.

Required response language:
{response_language}

Recent conversation:
{conversation_history}

User: {question}
Assistant:"""
)

student_prompt = PromptTemplate.from_template(
    """You are a secure student-record assistant for Bangladesh University of Professionals (BUP).
You are answering for the authenticated student only.

Authenticated registration ID:
{reg_id}

Authenticated student record:
{student_data}

Recent conversation:
{conversation_history}

User Question: {question}

INSTRUCTIONS:
- Answer only from the authenticated student record above.
- Never reveal, infer, compare, or fetch another student's private data.
- If the user asks whether the assistant knows them, or asks for their name, answer using the authenticated student's name from the record.
- If the user asks about another registration ID, refuse briefly.
- If a field is missing or empty, say that specific information is not available in the record.
- For direct factual questions, answer in one short sentence.
- For broader record questions, give a concise bullet list of relevant fields.
- Follow the required response language exactly.
- Do not include hidden reasoning, chain-of-thought, or <think> blocks.

Required response language:
{response_language}

Secure answer:"""
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
        conversation_history=state.get("conversation_history"),
    )
    return state

def greeting_agent(state: RAGState) -> RAGState:
    state["answer"] = get_greeting_response(state["question"])
    return state

def clarify_agent(state: RAGState) -> RAGState:
    state["answer"] = (
        "Sure. BUP admission depends on the program level.\n\n"
        "Which one are you interested in?\n\n"
        "1. Undergraduate\n"
        "2. Master's\n"
        "3. MPhil / PhD\n\n"
        "If you already have a specific program in mind, tell me the program name."
    )
    return state

def mental_support_agent(state: RAGState) -> RAGState:
    if not has_crisis_intent(state["question"].lower()):
        response = (mental_support_prompt | llm | StrOutputParser()).invoke({
            "question": state["question"],
            "conversation_history": format_conversation_history(state.get("conversation_history")),
            "response_language": response_language_instruction(state["question"]),
        })
        state["answer"] = clean_llm_output(response)
        return state

    state["answer"] = (
        "I'm really sorry you're feeling this way. You do not have to handle it alone.\n\n"
        "- If you might hurt yourself or feel unsafe right now, please call local emergency support immediately or ask someone nearby to stay with you.\n"
        "- If this is about academic pressure, tell me one thing that feels heaviest right now: exams, CGPA, family pressure, finances, or something else.\n"
        "- I can stay with you here and help you break the next step into something smaller."
    )
    return state

def retrieve(state: RAGState) -> RAGState:
    k = state.get("top_k") or 3
    k = max(1, min(int(k), 10))
    retriever = get_retriever(k)
    retrieval_question = build_contextual_question(
        state["question"],
        state.get("conversation_history"),
    )
    docs = retriever.invoke(retrieval_question)
    state["docs"] = docs
    state["context"] = format_docs(docs)
    return state

def generate(state: RAGState) -> RAGState:
    response = (rag_prompt | llm | StrOutputParser()).invoke({
        "context": state["context"],
        "question": state["question"],
        "conversation_history": format_conversation_history(state.get("conversation_history")),
        "response_language": response_language_instruction(state["question"]),
    })
    state["answer"] = clean_llm_output(response)
    return state

def chat_agent(state: RAGState) -> RAGState:
    response = (chat_prompt | llm | StrOutputParser()).invoke({
        "question": state["question"],
        "conversation_history": format_conversation_history(state.get("conversation_history")),
        "response_language": response_language_instruction(state["question"]),
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

        mentioned_reg_ids = set(re.findall(r"\b\d{6,}\b", state["question"]))
        if mentioned_reg_ids and any(mentioned_reg_id != str(reg_id) for mentioned_reg_id in mentioned_reg_ids):
            if is_bangla(state["question"]):
                state["answer"] = "দুঃখিত, আমি শুধুমাত্র আপনার নিজের ব্যক্তিগত ছাত্র তথ্য দেখাতে পারি।"
            elif is_banglish(state["question"]):
                state["answer"] = "Dukhito, ami shudhu apnar nijer private student data dekhate pari."
            else:
                state["answer"] = "Sorry, I can only show your own private student information."
            return state
        
        student_data = get_student_data_by_reg_id(reg_id, db)
        if not student_data:
            state["answer"] = "I couldn't find your student records. Please contact the administration."
            return state
        
        # Format data for the prompt
        formatted_data = {reg_id: student_data}
        
        response = (student_prompt | llm | StrOutputParser()).invoke({
            "reg_id": reg_id,
            "student_data": json.dumps(formatted_data, indent=2),
            "question": state["question"],
            "conversation_history": format_conversation_history(state.get("conversation_history")),
            "response_language": response_language_instruction(state["question"]),
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
graph.add_node("clarify_agent", clarify_agent)
graph.add_node("mental_support_agent", mental_support_agent)
graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)
graph.add_node("chat_agent", chat_agent)
graph.add_node("student_agent", student_agent)
graph.add_node("auth_required_agent", auth_required_agent)

def route_decision(state: RAGState):
    route = state["route"]
    if route == "greeting":
        return "greeting_agent"
    if route == "clarify":
        return "clarify_agent"
    if route == "mental_support":
        return "mental_support_agent"
    if route == "rag":
        return "retrieve"
    if route == "chat":
        return "chat_agent"
    if route == "student":
        return "student_agent"
    if route == "auth_required":
        return "auth_required_agent"
    return "chat_agent"

graph.set_entry_point("router")
graph.add_conditional_edges("router", route_decision)
graph.add_edge("greeting_agent", END)
graph.add_edge("clarify_agent", END)
graph.add_edge("mental_support_agent", END)
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
