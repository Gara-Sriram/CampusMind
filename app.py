"""
app.py -- AskIIITA  🎓
Beautiful campus-themed RAG chatbot for IIIT Allahabad.
Run: streamlit run app.py
"""

import os
import base64
import warnings
from datetime import date
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)

import streamlit as st
from dotenv import load_dotenv

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AskIIITA – Campus AI Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_dotenv(override=True)
MONGO_URI             = os.getenv("MONGO_URI", "")
GEMINI_API_KEY        = os.getenv("GEMINI_API_KEY", "")
MONGO_DB_NAME         = os.getenv("MONGO_DB_NAME", "askiiita")
MONGO_COLLECTION_NAME = os.getenv("MONGO_COLLECTION_NAME", "documents")
ATLAS_INDEX           = os.getenv("ATLAS_VECTOR_SEARCH_INDEX", "vector_index")

import auth
from pymongo import MongoClient

# Initialize MongoDB client for authentication/audit logs
try:
    client = MongoClient(
        MONGO_URI, tls=True,
        tlsAllowInvalidCertificates=True,
        tlsAllowInvalidHostnames=True,
        serverSelectionTimeoutMS=2000,
    )
    # Ping to check if really connected
    client.admin.command('ping')
    db = client[MONGO_DB_NAME]
    is_mock_db = False
    print("[DB] Connected to MongoDB Atlas successfully.")
except Exception as db_err:
    import mongomock
    client = mongomock.MongoClient()
    db = client[MONGO_DB_NAME]
    is_mock_db = True
    print(f"[DB ERROR] MongoDB connection failed: {db_err}. Falling back to mongomock.")



# ── Load background images as base64 ─────────────────────────────────────────
def img_to_b64(path: str) -> str:
    p = Path(path)
    if p.exists():
        return base64.b64encode(p.read_bytes()).decode()
    return ""

b64_1 = img_to_b64("images/campus1.jpg")
b64_2 = img_to_b64("images/campus2.jpg")

# Use whichever image exists; fallback to gradient
if b64_1:
    bg_css = f"background-image: url('data:image/jpeg;base64,{b64_1}');"
elif b64_2:
    bg_css = f"background-image: url('data:image/jpeg;base64,{b64_2}');"
else:
    bg_css = "background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);"

# ── Category definitions ──────────────────────────────────────────────────────
CATEGORIES = {
    "📚 Academics & Courses": {
        "color": "#6366f1",
        "questions": [
            "What B.Tech & M.Tech programs are offered?",
            "When does the current semester end?",
            "What is the grading system at IIITA?",
            "What is the admission process for M.Tech?",
        ],
    },
    "💰 Fees": {
        "color": "#10b981",
        "questions": [
            "What are the one time fees for B.Tech 2026?",
            "What are the semester fees?",
            "What are the annual dues?",
            "What is the total fee for B.Tech?",
        ],
    },
    "📅 Calendar": {
        "color": "#f59e0b",
        "questions": [
            "When does the semester start?",
            "What are the holiday dates?",
            "When are the mid-semester exams?",
            "What is the summer semester schedule?",
        ],
    },
    "🏠 Hostel": {
        "color": "#ef4444",
        "questions": [
            "What are the hostel facilities?",
            "What is the hostel fee?",
            "What are the hostel rules?",
            "How is hostel allotment done?",
        ],
    },
    "📖 Library": {
        "color": "#8b5cf6",
        "questions": [
            "What are the library timings?",
            "How many books can I borrow?",
            "What is the library fine policy?",
            "How do I access online journals?",
        ],
    },
    "💼 Placements": {
        "color": "#06b6d4",
        "questions": [
            "What companies visit for placements?",
            "What is the placement process?",
            "What are the eligibility criteria for placements?",
            "What is the average package at IIITA?",
        ],
    },
    "📜 NEP": {
        "color": "#f97316",
        "questions": [
            "What is NEP 2020 at IIITA?",
            "How does NEP affect the B.Tech curriculum?",
            "What are the multidisciplinary courses under NEP?",
            "What are the exit options under NEP at IIITA?",
        ],
    },
    "🏥 Health Center": {
        "color": "#14b8a6",
        "questions": [
            "Where is the health center located?",
            "What are the health center timings?",
            "What medical facilities are available on campus?",
            "How do I get an appointment at the health center?",
        ],
    },
    "🏋️ Gymkhana": {
        "color": "#f43f5e",
        "questions": [
            "What are the gymkhana facilities?",
            "What are the gymkhana timings?",
            "What sports are available at IIITA?",
            "How do I join a sports team at IIITA?",
        ],
    },
    "👥 People": {
        "color": "#ec4899",
        "questions": [
            "Who is the Director of IIIT Allahabad?",
            "Who is the Dean of Academic Affairs?",
            "Who is the Dean of Student Affairs?",
            "Who is the Dean of Faculty Affairs?",
        ],
    },
}

# ── CSS ───────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* {{ font-family: 'Inter', sans-serif !important; box-sizing: border-box; }}

/* ── Lock overall page scroll ── */
html, body, [data-testid="stAppViewContainer"], .stApp {{
    overflow: hidden !important;
    height: 100vh !important;
    max-height: 100vh !important;
}}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding: 0.2rem 1rem 0 !important; max-width: 100% !important; height: 100vh !important; overflow: hidden !important; }}
section[data-testid="stSidebar"] {{ display: none; }}

/* ── Hero background ── */
.stApp {{
    {bg_css}
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    min-height: 100vh;
}}

/* Dark overlay */
.stApp::before {{
    content: '';
    position: fixed;
    inset: 0;
    background: linear-gradient(160deg, rgba(5,5,20,0.93) 0%, rgba(10,10,30,0.90) 50%, rgba(3,3,15,0.95) 100%);
    z-index: 0;
    pointer-events: none;
}}

/* All content above overlay */
.main .block-container > div {{ position: relative; z-index: 1; }}

/* ── Top title bar ── */
.top-title {{
    text-align: center;
    padding: 0.4rem 1rem 0.2rem;
}}
.top-title h1 {{
    font-size: 2.8rem;
    font-weight: 900;
    background: linear-gradient(90deg, #c084fc 0%, #818cf8 30%, #38bdf8 60%, #34d399 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.1;
    letter-spacing: -0.02em;
    text-shadow: none;
}}
.top-title p {{
    color: rgba(255,255,255,0.45);
    font-size: 0.85rem;
    font-weight: 300;
    margin: 0.1rem 0 0 0;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}
.title-bar {{
    width: 80px;
    height: 2.5px;
    background: linear-gradient(90deg, #c084fc, #38bdf8);
    margin: 0.4rem auto 0;
    border-radius: 2px;
}}

/* ── Side image columns ── */
.side-img-wrap {{
    border-radius: 20px;
    overflow: hidden;
    height: 74vh;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6);
    border: 1px solid rgba(255,255,255,0.07);
    position: sticky;
    top: 0.5rem;
}}
.side-img-wrap img {{
    width: 100%;
    height: 100%;
    object-fit: cover;
    opacity: 0.72;
    filter: brightness(0.85) saturate(1.15);
    transition: opacity 0.4s ease;
}}
.side-img-wrap:hover img {{ opacity: 0.88; }}

/* ── Center glass card (2nd column) ── */
[data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {{
    background: rgba(88, 28, 220, 0.10) !important;
    border: 1.5px solid rgba(167,139,250,0.38) !important;
    border-radius: 28px !important;
    backdrop-filter: blur(32px) !important;
    -webkit-backdrop-filter: blur(32px) !important;
    box-shadow:
        0 0 90px rgba(139,92,246,0.18),
        0 8px 40px rgba(0,0,0,0.45),
        inset 0 1px 0 rgba(255,255,255,0.08) !important;
    padding: 1.2rem 1.2rem 1.2rem !important;
    height: 74vh !important;
    overflow: hidden !important;
}}

/* ── Glass card inner title ── */
.glass-header {{
    text-align: center;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 1rem;
}}
.glass-logo {{ font-size: 2rem; line-height: 1; margin-bottom: 0.3rem; }}
.glass-title {{
    font-size: 1.8rem;
    font-weight: 800;
    background: linear-gradient(90deg, #c084fc 0%, #818cf8 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
}}
.glass-sub {{
    color: rgba(255,255,255,0.38);
    font-size: 0.78rem;
    font-weight: 400;
    margin-top: 0.3rem;
    letter-spacing: 0.05em;
}}

/* ── Category buttons inside glass card ── */
.cat-label {{
    text-align: center;
    color: rgba(255,255,255,0.38);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}}
/* ── Category tag buttons ── */
.stButton > button {{
    width: 100% !important;
    border-radius: 16px !important;
    padding: 0.65rem 0.5rem !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    background: rgba(255,255,255,0.07) !important;
    color: rgba(255,255,255,0.88) !important;
    backdrop-filter: blur(10px) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.01em;
}}
.stButton > button:hover {{
    background: rgba(167,139,250,0.22) !important;
    border-color: rgba(167,139,250,0.45) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(139,92,246,0.25) !important;
}}

/* ── Active tag badge (shown when a category is selected) ── */
.active-tag-badge {{
    display: inline-flex;
    align-items: center;
    background: rgba(167,139,250,0.2);
    border: 1.5px solid rgba(167,139,250,0.55);
    border-radius: 20px;
    padding: 0.3rem 1rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: rgba(255,255,255,0.92);
    margin: 0.2rem 0 0.8rem 0;
    box-shadow: 0 2px 12px rgba(139,92,246,0.2);
}}

/* ── Quick questions panel ── */
.qqpanel {{
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 0.8rem 1rem;
    margin: 0.6rem 0;
}}
.qq-btn > button {{
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 12px !important;
    padding: 0.5rem 0.8rem !important;
    font-size: 0.8rem !important;
    color: rgba(255,255,255,0.8) !important;
    text-align: left !important;
    width: 100% !important;
    margin-bottom: 0.3rem !important;
}}
.qq-btn > button:hover {{
    background: rgba(167,139,250,0.18) !important;
    border-color: rgba(167,139,250,0.35) !important;
}}

/* ── Chat messages ── */
.stChatMessage {{ background: transparent !important; }}
[data-testid="stChatMessageContent"] {{
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 14px !important;
    color: rgba(255,255,255,0.9) !important;
    backdrop-filter: blur(8px);
    font-size: 0.86rem !important;
}}

/* ── Hide Streamlit bottom bar ── */
.stChatInputContainer {{ display: none !important; }}

/* ── Query input section ── */
.query-section {{
    border-top: 1px solid rgba(255,255,255,0.07);
    padding-top: 0.9rem;
    margin-top: 0.8rem;
}}
.query-label {{
    color: rgba(255,255,255,0.38);
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}}
.stTextInput > div > div > input {{
    background: rgba(255,255,255,0.07) !important;
    border: 1.5px solid rgba(167,139,250,0.32) !important;
    border-radius: 14px !important;
    color: white !important;
    font-size: 0.88rem !important;
    padding: 0.6rem 1rem !important;
    caret-color: #c084fc;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}}
.stTextInput > div > div > input:focus {{
    border-color: rgba(192,132,252,0.7) !important;
    box-shadow: 0 0 0 3px rgba(192,132,252,0.12) !important;
    outline: none !important;
}}
.stTextInput > div > div > input::placeholder {{
    color: rgba(200,180,255,0.45) !important;
    font-style: italic;
}}
/* Hide form submit button */
.stFormSubmitButton {{ display: none !important; }}
/* Hide "Press Enter to submit form" helper text */
.stTextInput div[data-testid="InputInstructions"] {{ display: none !important; }}
small[data-testid="InputInstructions"] {{ display: none !important; }}
[data-testid="InputInstructions"] {{ display: none !important; }}
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"         not in st.session_state: st.session_state["messages"]         = []
if "active_category"  not in st.session_state: st.session_state["active_category"]  = None
if "pending_query"    not in st.session_state: st.session_state["pending_query"]     = None
if "selected_program" not in st.session_state: st.session_state["selected_program"]  = "B.Tech"
if "selected_batch"   not in st.session_state: st.session_state["selected_batch"]    = "2026"
if "show_questions"   not in st.session_state: st.session_state["show_questions"]    = True
if "auth_token"       not in st.session_state: st.session_state["auth_token"]       = None
if "username"         not in st.session_state: st.session_state["username"]         = None
if "role"             not in st.session_state: st.session_state["role"]             = None
if "is_mock_db"       not in st.session_state: st.session_state["is_mock_db"]       = is_mock_db

# Verify session token
if st.session_state["auth_token"]:
    payload = auth.verify_token(st.session_state["auth_token"])
    if not payload:
        st.session_state["auth_token"] = None
        st.session_state["username"] = None
        st.session_state["role"] = None
    else:
        st.session_state["username"] = payload.get("sub")
        st.session_state["role"] = payload.get("role")


# ── RAG function ──────────────────────────────────────────────────────────────
def ask(query: str, username: str, user_role: str):
    from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
    from langchain_mongodb import MongoDBAtlasVectorSearch
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough
    from datetime import datetime, timezone

    # 1. Access level hierarchy
    ROLE_HIERARCHY = {
        "public": ["public"],
        "student": ["public", "student"],
        "faculty": ["public", "student", "faculty"],
        "admin": ["public", "student", "faculty", "admin"]
    }
    allowed_levels = ROLE_HIERARCHY.get(user_role, ["public"])

    use_local_search = False
    col_local = None
    try:
        client_local = MongoClient(
            MONGO_URI, tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
            serverSelectionTimeoutMS=2000,
        )
        client_local.admin.command('ping')
        col_local = client_local[MONGO_DB_NAME][MONGO_COLLECTION_NAME]
    except Exception as conn_err:
        print(f"[DB] Atlas connection failed for query: {conn_err}. Using local search fallback.")
        use_local_search = True

    source_docs = []
    if not use_local_search:
        try:
            emb = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", google_api_key=GEMINI_API_KEY)
            vs  = MongoDBAtlasVectorSearch(collection=col_local, embedding=emb, index_name=ATLAS_INDEX)
            
            # Pre-filtering based on access level
            ret = vs.as_retriever(search_kwargs={
                "k": 4,
                "pre_filter": {
                    "access_level": {"$in": allowed_levels}
                }
            })
            source_docs = ret.invoke(query)
        except Exception as search_err:
            print(f"[DB] Atlas search execution failed: {search_err}. Falling back to local search.")
            use_local_search = True

    if use_local_search:
        import local_vector
        try:
            source_docs = local_vector.search_local(query, allowed_levels, GEMINI_API_KEY, k=4)
        except Exception as local_err:
            print(f"[LOCAL ERROR] Local search fallback failed: {local_err}")
            source_docs = []

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite", google_api_key=GEMINI_API_KEY, temperature=0.2)

    today = date.today().strftime("%B %d, %Y")
    prompt = ChatPromptTemplate.from_template(f"""\
You are AskIIITA, a helpful and friendly assistant for IIIT Allahabad students and faculty.
Today's date is {today}. Use this for time-aware answers (e.g. if an event passed, say so).
Use ONLY the context below to answer. If info is not in context, say so honestly.
Be concise, accurate, and friendly.

Context:
{{context}}

Question: {{question}}

Answer:""")

    def fmt(docs): return "\n\n".join(d.page_content for d in docs)

    sources = list({doc.metadata.get("source_file", doc.metadata.get("source", "Unknown")) for doc in source_docs})
    
    # We formulate context from retrieved docs or fallback message
    context_str = fmt(source_docs) if source_docs else "No relevant documents found for this query/role level."
    chain   = ({"context": lambda x: context_str, "question": RunnablePassthrough()} | prompt | llm | StrOutputParser())
    answer  = chain.invoke(query)
    
    # 2. Audit logging
    try:
        # If DB connection worked, log to Atlas, otherwise log to in-memory mock db
        db_audit = db if st.session_state.get("is_mock_db", False) else client_local[MONGO_DB_NAME]
        audit_col = db_audit["audit_logs"]
        audit_entry = {
            "user_id": username,
            "role": user_role,
            "query_text": query,
            "timestamp": datetime.now(timezone.utc),
            "retrieved_chunks": [
                {
                    "chunk_id": str(doc.metadata.get("_id") or ""),
                    "source_file": doc.metadata.get("source_file", "Unknown"),
                    "access_level": doc.metadata.get("access_level", "public"),
                    "content_snippet": doc.page_content[:200]
                } for doc in source_docs
            ]
        }
        audit_col.insert_one(audit_entry)
    except Exception as audit_err:
        print(f"[AUDIT ERROR] Failed to write audit log: {audit_err}")
        
    return answer, sources


# ── TOP TITLE BAR ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-title">
    <h1>🎓 AskIIITA</h1>
    <p>Your AI-Powered Campus Assistant &nbsp;&bull;&nbsp; IIIT Allahabad</p>
    <div class="title-bar"></div>
</div>
""", unsafe_allow_html=True)

# ── THREE-COLUMN LAYOUT ────────────────────────────────────────────────────────
left_col, center_col, right_col = st.columns([1, 1.6, 1])

# ── Left image
with left_col:
    img_left = b64_1 or b64_2
    if img_left:
        st.markdown(
            f'<div class="side-img-wrap"><img src="data:image/jpeg;base64,{img_left}"/></div>',
            unsafe_allow_html=True,
        )

# ── Right image
with right_col:
    img_right = b64_2 or b64_1
    if img_right:
        st.markdown(
            f'<div class="side-img-wrap"><img src="data:image/jpeg;base64,{img_right}"/></div>',
            unsafe_allow_html=True,
        )

# ── Center glass card
with center_col:

    # 1. Require Authentication
    if not st.session_state["auth_token"]:
        st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
        st.markdown('<p class="cat-label">Security Gate</p>', unsafe_allow_html=True)
        
        tab_login, tab_register, tab_guide = st.tabs(["🔐 Sign In", "📝 Create Account", "📖 Complete Guide"])
        
        with tab_login:
            with st.form("login_form"):
                login_user = st.text_input("Username")
                login_pass = st.text_input("Password", type="password", placeholder="••••••••")
                login_submit = st.form_submit_button("Sign In")
                
                if login_submit:
                    if not login_user or not login_pass:
                        st.error("Please enter both username and password.")
                    elif not db:
                        st.error("Cannot authenticate. Database is currently unreachable.")
                    else:
                        try:
                            user_doc = auth.get_user(db, login_user)
                            if user_doc and auth.verify_password(login_pass, user_doc["password_salt"], user_doc["password_hash"]):
                                token = auth.generate_token(login_user, user_doc["role"])
                                st.session_state["auth_token"] = token
                                st.session_state["username"] = login_user
                                st.session_state["role"] = user_doc["role"]
                                st.success("Access Granted! Loading assistant...")
                                st.rerun()
                            else:
                                st.error("Invalid username or password.")
                        except Exception as e:
                            st.error(f"Authentication Error: {e}")
        
        with tab_register:
            with st.form("register_form"):
                reg_user = st.text_input("Username", placeholder="e.g. janesmith")
                reg_pass = st.text_input("Password", type="password", placeholder="••••••••")
                reg_submit = st.form_submit_button("Create Account")
                
                if reg_submit:
                    if not reg_user or not reg_pass:
                        st.error("Please fill in all fields.")
                    elif len(reg_pass) < 6:
                        st.error("Password must be at least 6 characters.")
                    elif not db:
                        st.error("Cannot create account. Database is currently unreachable.")
                    else:
                        try:
                            success = auth.create_user(db, reg_user, reg_pass, "student")
                            if success:
                                st.success("Account created successfully! Please sign in under the 'Sign In' tab.")
                            else:
                                st.error("Username already exists.")
                        except Exception as e:
                            st.error(f"Registration Error: {e}")
                            
        with tab_guide:
            st.markdown('<p class="cat-label" style="margin-bottom: 0.5rem;">AskIIITA Complete Project Guide</p>', unsafe_allow_html=True)
            try:
                with open("index.html", "r", encoding="utf-8") as f:
                    guide_html = f.read()
                st.components.v1.html(guide_html, height=450, scrolling=True)
            except Exception as e:
                st.error(f"Failed to load complete guide: {e}")

        st.info("Create an account to get started. New accounts have the student role.")
        st.stop()

    # 2. Authenticated Header (User identity + Sign Out)
    c_user, c_logout = st.columns([3, 1])
    with c_user:
        role_emoji = "🛡️" if st.session_state["role"] == "admin" else ("👨‍🏫" if st.session_state["role"] == "faculty" else "🧑‍🎓")
        st.markdown(f'<p style="color: rgba(255,255,255,0.7); font-size: 0.82rem; margin: 0.3rem 0 0 0;">👤 <b>{st.session_state["username"]}</b> ({role_emoji} {st.session_state["role"]})</p>', unsafe_allow_html=True)
        if st.session_state.get("is_mock_db", False):
            st.markdown('<p style="color: #fbbf24; font-size: 0.78rem; margin: 0; font-weight: 500; letter-spacing: 0.02em;">⚠️ Running in Local Mock Database Fallback Mode</p>', unsafe_allow_html=True)
    with c_logout:
        if st.button("Sign Out", key="signout_btn"):
            st.session_state["auth_token"] = None
            st.session_state["username"] = None
            st.session_state["role"] = None
            st.session_state["messages"] = []
            st.session_state["active_category"] = None
            st.session_state["show_questions"] = True
            st.rerun()

    # 3. View Selection (Admin only)
    if st.session_state["role"] == "admin":
        admin_view = st.radio("Workspace View", ["💬 Chat Assistant", "📋 Audit Logs"], horizontal=True, label_visibility="collapsed")
    else:
        admin_view = "💬 Chat Assistant"

    if admin_view == "📋 Audit Logs":
        st.markdown('<p class="cat-label">System Audit History (Admin Only)</p>', unsafe_allow_html=True)
        with st.container(height=480, border=False):
            if not db:
                st.error("Database connection unavailable to retrieve logs.")
            else:
                try:
                    audit_col = db["audit_logs"]
                    logs = list(audit_col.find({}).sort("timestamp", -1).limit(50))
                    if not logs:
                        st.info("No queries logged yet.")
                    else:
                        for log in logs:
                            ts_str = log.get('timestamp')
                            if ts_str:
                                if hasattr(ts_str, 'strftime'):
                                    ts_display = ts_str.strftime('%Y-%m-%d %H:%M:%S')
                                else:
                                    ts_display = str(ts_str)
                            else:
                                ts_display = "Unknown Time"
                            with st.expander(f"🕒 {ts_display} | User: {log.get('user_id')} ({log.get('role')})"):
                                st.markdown(f"**Query:** `{log.get('query_text')}`")
                                st.markdown("**Retrieved Chunks:**")
                                chunks = log.get("retrieved_chunks", [])
                                if not chunks:
                                    st.markdown("*None*")
                                for idx, chunk in enumerate(chunks):
                                    st.markdown(f"{idx+1}. **Source:** `{chunk.get('source_file')}` | **Level:** `{chunk.get('access_level')}`")
                                    st.markdown(f"> *Snippet:* {chunk.get('content_snippet')}...")
                except Exception as e:
                    st.error(f"Failed to fetch audit logs: {e}")
        st.stop()

    # 4. Chat Assistant View
    # ─ Show all tags OR selected tag + questions (never both)
    active = st.session_state["active_category"]

    # Detect if a query is incoming in this run (either via quick button or text input)
    has_incoming_query = (
        st.session_state.get("pending_query") is not None or 
        st.session_state.get("user_query", "").strip() != ""
    )
    if has_incoming_query:
        st.session_state["show_questions"] = False

    if active is None:
        # Show all category tags (2 columns) with top padding to center vertically
        st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
        st.markdown('<p class="cat-label">What would you like to know?</p>', unsafe_allow_html=True)

        cat_names = list(CATEGORIES.keys())
        btn_cols = st.columns(2)
        for i, cat in enumerate(cat_names):
            with btn_cols[i % 2]:
                if st.button(cat, key=f"cat_{cat}"):
                    st.session_state["active_category"] = cat
                    st.session_state["show_questions"] = True
                    st.session_state["messages"] = []  # Clear previous chat on category switch
                    st.rerun()
    else:
        # Back button, Clear button + active tag badge
        c_back, c_clear, c_tag = st.columns([1, 1, 2])
        with c_back:
            if st.button("← Back", key="back_btn"):
                st.session_state["active_category"] = None
                st.session_state["show_questions"] = True
                st.session_state["messages"] = []  # Clear previous chat when going back to tags
                st.rerun()
        with c_clear:
            if st.button("🗑️ Clear", key="clear_btn"):
                st.session_state["messages"] = []
                st.session_state["show_questions"] = True
                st.rerun()
        with c_tag:
            st.markdown(f'<div class="active-tag-badge">{active}</div>', unsafe_allow_html=True)

        # Scrollable middle area (both questions and chat history live here)
        with st.container(height=380, border=False):
            
            # Show questions only if show_questions is True
            if st.session_state.get("show_questions", True):
                # Special case for Fees category to show Program & Batch selectors
                if active == "💰 Fees":
                    st.markdown('<p class="cat-label" style="text-align:left; margin:0.5rem 0 0.2rem;">1. Select Program</p>', unsafe_allow_html=True)
                    p_cols = st.columns(3)
                    programs = ["B.Tech", "M.Tech", "PhD"]
                    for p_idx, prog in enumerate(programs):
                        with p_cols[p_idx]:
                            label = f"🟢 {prog}" if st.session_state["selected_program"] == prog else prog
                            if st.button(label, key=f"btn_prog_{prog}"):
                                st.session_state["selected_program"] = prog
                                st.rerun()

                    st.markdown('<p class="cat-label" style="text-align:left; margin:0.5rem 0 0.2rem;">2. Select Batch</p>', unsafe_allow_html=True)
                    b_cols = st.columns(4)
                    batches = ["2023", "2024", "2025", "2026"]
                    for b_idx, bat in enumerate(batches):
                        with b_cols[b_idx]:
                            label = f"🟢 {bat}" if st.session_state["selected_batch"] == bat else bat
                            if st.button(label, key=f"btn_batch_{bat}"):
                                st.session_state["selected_batch"] = bat
                                st.rerun()

                    # Dynamic Fees questions based on selections
                    prog = st.session_state["selected_program"]
                    bat = st.session_state["selected_batch"]
                    fee_questions = [
                        f"What is the fee structure for {prog} {bat} batch?",
                        f"What are the semester fees for {prog} {bat} batch?",
                        f"What is the hostel fee for {prog} {bat} batch?",
                        f"What is the one time fee for {prog} {bat} batch?",
                    ]
                    st.markdown('<p class="cat-label" style="text-align:left; margin:0.6rem 0 0.2rem;">3. Choose a question</p>', unsafe_allow_html=True)
                    for j, q in enumerate(fee_questions):
                        st.markdown('<div class="qq-btn">', unsafe_allow_html=True)
                        if st.button(q, key=f"qq_{active}_{j}"):
                            st.session_state["pending_query"]   = q
                            st.session_state["show_questions"] = False
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    # Normal categories with standard static questions
                    info = CATEGORIES[active]
                    for j, q in enumerate(info["questions"]):
                        st.markdown('<div class="qq-btn">', unsafe_allow_html=True)
                        if st.button(q, key=f"qq_{active}_{j}"):
                            st.session_state["pending_query"]   = q
                            st.session_state["show_questions"] = False
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

            # Chat history messages
            if len(st.session_state["messages"]) > 0:
                c_clear_btn, _ = st.columns([1.2, 2.8])
                with c_clear_btn:
                    if st.button("🗑️ Clear Chat", key="clear_chat_global"):
                        st.session_state["messages"] = []
                        st.session_state["show_questions"] = True
                        st.rerun()
                
                for msg in st.session_state["messages"]:
                    with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🎓"):
                        st.markdown(msg["content"])
                        if msg.get("sources"):
                            st.caption(f"📄 {' · '.join(msg['sources'])}")


    # Handle pending query
    pending = st.session_state.pop("pending_query", None)

    # Query input box
    st.markdown(
        '<div class="query-section"><div class="query-label">✨ Ask anything</div></div>',
        unsafe_allow_html=True,
    )
    with st.form(key="query_form", clear_on_submit=True):
        prompt_input = st.text_input("Ask a question", placeholder="Or any Query type here...", key="user_query", label_visibility="collapsed")
        st.form_submit_button("Send")

    # Process query
    query = pending or prompt_input
    if query:
        st.session_state["show_questions"] = False
        
        # Add user query immediately to show inside scrollable list
        st.session_state["messages"].append({"role": "user", "content": query})
        
        # We process here and append assistant response
        with st.spinner("Thinking..."):
            try:
                answer, sources = ask(query, st.session_state["username"], st.session_state["role"])
            except Exception as e:
                err_msg = str(e)
                if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                    answer = (
                        "⚠️ **Gemini API Daily Quota Exceeded**\n\n"
                        "You have reached the daily limit of **1000 free embedding requests** "
                        "(this happens when the ingestion script is run several times to process new PDFs, as each chunk uses an API request).\n\n"
                        "Please **try again later** (after the daily limit resets) or configure a paid Google AI Studio API key in your `.env` file."
                    )
                else:
                    answer  = f"⚠️ **Error:** {err_msg}"
                sources = []
        
        st.session_state["messages"].append({
            "role": "assistant", "content": answer, "sources": sources,
        })
        st.rerun()
