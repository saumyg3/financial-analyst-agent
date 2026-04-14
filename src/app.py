import os
import sys
import streamlit as st
from google import genai
from dotenv import load_dotenv

load_dotenv()
client_ai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

sys.path.append(os.path.dirname(__file__))
from ingest import fetch_and_save
from embed import ingest_file
from retriever import retrieve

st.set_page_config(
    page_title="Financial Analyst Agent",
    page_icon="📈",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; font-size: 16px !important; }
    .stApp { background-color: #0f1117 !important; }
    .block-container { padding-top: 2rem !important; padding-left: 8rem !important; padding-right: 8rem !important; max-width: 1000px !important; margin: 0 auto !important; }
    h1 { font-size: 2.2rem !important; font-weight: 600 !important; letter-spacing: -0.5px !important; color: #f1f1f1 !important; }
    h3 { font-size: 1.15rem !important; font-weight: 600 !important; color: #e0e0e0 !important; margin-top: 1rem !important; }
    .stCaption p { font-size: 0.95rem !important; color: #666 !important; margin-top: -0.4rem !important; }
    .stMarkdown p { font-size: 1rem !important; color: #ccc !important; font-weight: 400 !important; }
    div[data-testid="column"] .stButton > button {
        background: #1a1d27 !important; border: 1px solid #2a2d3a !important;
        border-radius: 12px !important; font-size: 0.92rem !important; color: #ccc !important;
        padding: 10px 14px !important; white-space: normal !important; font-weight: 400 !important;
        width: 100% !important; height: auto !important; line-height: 1.5 !important; text-align: center !important;
    }
    div[data-testid="column"] .stButton > button:hover { border-color: #4a6cf7 !important; color: #fff !important; background: #1e2235 !important; }
    .stTextInput input { background: #1a1d27 !important; border: 1px solid #2a2d3a !important; border-radius: 10px !important; color: #f1f1f1 !important; font-size: 1rem !important; padding: 12px 16px !important; font-family: 'Inter', sans-serif !important; }
    .stTextInput input:focus { border-color: #4a6cf7 !important; box-shadow: 0 0 0 2px rgba(74,108,247,0.15) !important; }
    .stTextInput label { font-size: 0.92rem !important; color: #888 !important; font-weight: 500 !important; }
    .stButton > button[kind="primary"] { background: #4a6cf7 !important; border: none !important; border-radius: 10px !important; font-weight: 500 !important; font-size: 0.95rem !important; padding: 10px 28px !important; color: white !important; }
    .stButton > button[kind="primary"]:hover { background: #3b5de8 !important; transform: translateY(-1px) !important; }
    .stAlert { border-radius: 10px !important; font-size: 0.95rem !important; }
    hr { border-color: #1e2130 !important; margin: 1rem 0 !important; }
    .streamlit-expanderHeader { background: #14161f !important; border: 1px solid #1e2130 !important; border-radius: 8px !important; font-size: 0.92rem !important; font-weight: 500 !important; color: #bbb !important; padding: 10px 14px !important; }
    .streamlit-expanderHeader:hover { border-color: #4a6cf7 !important; color: #fff !important; }
    .streamlit-expanderContent { background: #14161f !important; border: 1px solid #1e2130 !important; border-top: none !important; border-radius: 0 0 8px 8px !important; font-size: 0.9rem !important; color: #999 !important; line-height: 1.8 !important; padding: 10px 14px !important; }
    [data-testid="stSidebar"] { background: #0a0c13 !important; border-right: 1px solid #1e2130 !important; }
    [data-testid="stSidebar"] .stTextInput input { font-size: 0.95rem !important; }
    [data-testid="stSidebar"] label { font-size: 0.9rem !important; color: #888 !important; }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] { width: 100% !important; border-radius: 8px !important; font-size: 0.9rem !important; padding: 10px 8px !important; white-space: normal !important; height: auto !important; line-height: 1.4 !important; }
    [data-testid="stSidebar"] .stButton > button:not([kind="primary"]) { font-size: 0.9rem !important; color: #aaa !important; border: 1px solid #1e2130 !important; border-radius: 8px !important; background: #14161f !important; width: 100% !important; padding: 8px 12px !important; }
    .stSuccess { background: #0d1f0d !important; border: 1px solid #1a3d1a !important; border-radius: 8px !important; font-size: 0.9rem !important; }
    .stInfo { background: #0d1525 !important; border: 1px solid #1a2d4a !important; border-radius: 10px !important; font-size: 0.95rem !important; }
    .answer-box { background: #14161f; border: 1px solid #1e2130; border-radius: 12px; padding: 1.25rem 1.5rem; margin-top: 0.5rem; font-size: 1rem; color: #ddd; line-height: 1.8; }
    .company-tag { display: inline-block; background: #1e2235; border: 1px solid #4a6cf7; border-radius: 6px; padding: 4px 12px; font-size: 0.85rem; color: #4a6cf7; font-weight: 600; margin-bottom: 10px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ── session state defaults ──────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "active_ticker" not in st.session_state:
    st.session_state.active_ticker = "AAPL"
if "compare_mode" not in st.session_state:
    st.session_state.compare_mode = False
if "compare_ticker" not in st.session_state:
    st.session_state.compare_ticker = ""
if "show_sources" not in st.session_state:
    st.session_state.show_sources = True
if "selected_model" not in st.session_state:
    st.session_state.selected_model = "gemini-2.0-flash-lite"
if "last_question" not in st.session_state:
    st.session_state.last_question = ""


def get_indexed_tickers():
    try:
        import chromadb
        db = chromadb.PersistentClient(path="chroma_db")
        return [c.name.upper() for c in db.list_collections()]
    except:
        return []


def generate_answer(question, chunks, ticker, model):
    context = "\n\n---\n\n".join([
        f"[Excerpt {i+1} from {ticker} 10-K, section ~{c['chunk_index']}]\n{c['text']}"
        for i, c in enumerate(chunks)
    ])
    prompt = f"""You are a financial analyst assistant. Answer the question about {ticker}'s 10-K using ONLY the excerpts below.
Be specific, cite excerpts, and be concise. If excerpts lack info, say so clearly.

EXCERPTS:
{context}

QUESTION: {question}

ANSWER:"""
    response = client_ai.models.generate_content(model=model, contents=prompt)
    return response.text


def run_query(question, ticker, model):
    try:
        chunks = retrieve(question, ticker, top_k=5)
        answer = generate_answer(question, chunks, ticker, model)
        return answer, chunks
    except Exception as e:
        if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
            return "⚠️ Daily API limit reached — resets every 24 hours. Please check back tomorrow!", None
        return f"❌ Error: {str(e)}", None


# ── LEFT SIDEBAR ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📂 Load a Company")
    ticker_input = st.text_input("Stock Ticker", value="AAPL", max_chars=5).upper()

    if st.button("Fetch & Index 10-K", type="primary"):
        with st.spinner(f"Fetching {ticker_input} 10-K..."):
            try:
                filepath = fetch_and_save(ticker_input)
                st.success(f"Downloaded {ticker_input}")
            except Exception as e:
                st.error(f"Fetch failed: {e}")
                st.stop()
        with st.spinner("Embedding chunks (1-2 mins)..."):
            try:
                ingest_file(filepath, ticker_input)
                st.success(f"{ticker_input} indexed!")
                st.session_state.active_ticker = ticker_input
            except Exception as e:
                st.error(f"Index failed: {e}")
                st.stop()

    st.divider()
    st.markdown("### 🗂 Indexed Companies")
    tickers = get_indexed_tickers()
    if tickers:
        for t in tickers:
            if st.button(f"📊 {t}", key=f"switch_{t}"):
                st.session_state.active_ticker = t
                st.session_state.compare_mode = False
    else:
        st.caption("None yet")

    st.divider()
    st.markdown("### 💬 Chat History")
    if st.session_state.chat_history:
        for entry in reversed(st.session_state.chat_history[-8:]):
            with st.expander(f"{entry['ticker']}: {entry['question'][:30]}...", expanded=False):
                st.caption(entry['answer'][:250] + "...")
    else:
        st.caption("No history yet")


# ── MAIN AREA ───────────────────────────────────────────────────────────
active = st.session_state.active_ticker

st.title("📈 Financial Analyst Agent")
st.caption("Ask anything about a company's 10-K filing — powered by SEC EDGAR + Gemini")

st.divider()

# Compare toggle + active ticker header
header_col, toggle_col = st.columns([4, 1])
with header_col:
    compare_label = f"  vs  {st.session_state.compare_ticker}" if st.session_state.compare_mode and st.session_state.compare_ticker else ""
    st.subheader(f"Ask about {active}{compare_label}")
with toggle_col:
    btn_label = "⚖️ Compare: ON ✓" if st.session_state.compare_mode else "⚖️ Compare: OFF"
    if st.button(btn_label, key="toggle_compare"):
        st.session_state.compare_mode = not st.session_state.compare_mode

# Compare ticker selector
if st.session_state.compare_mode:
    all_tickers = get_indexed_tickers()
    other_tickers = [t for t in all_tickers if t != active]
    if other_tickers:
        st.session_state.compare_ticker = st.selectbox("Compare with:", other_tickers)
    else:
        st.warning("Index another company first to use compare mode.")
        st.session_state.compare_mode = False

# Suggested questions
st.markdown("**Try asking:**")
cols = st.columns(3)
suggestions = [
    "What are the main risk factors?",
    "How does the company describe its business?",
    "What is the revenue breakdown by segment?",
]
for i, s in enumerate(suggestions):
    if cols[i].button(s, key=f"sug_{i}"):
        st.session_state.question_input = s

# Question input
question = st.text_input(
    "Your question",
    value=st.session_state.get("question_input", ""),
    placeholder="e.g. What are the biggest risks to this company's business?",
    key="question_input",
)
ask_clicked = st.button("Ask", type="primary")

if ask_clicked and not question:
    st.warning("Please type a question first!")

elif ask_clicked and question:
    st.session_state.last_question = question

    if st.session_state.compare_mode and st.session_state.compare_ticker:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="company-tag">📊 {active}</div>', unsafe_allow_html=True)
            with st.spinner(f"Querying {active}..."):
                answer1, chunks1 = run_query(question, active, st.session_state.selected_model)
            st.markdown(f'<div class="answer-box">{answer1}</div>', unsafe_allow_html=True)
            if chunks1 and st.session_state.show_sources:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Sources**")
                for i, c in enumerate(chunks1):
                    with st.expander(f"Excerpt {i+1} — section ~{c['chunk_index']}"):
                        st.caption(c["text"])

        with col2:
            compare = st.session_state.compare_ticker
            st.markdown(f'<div class="company-tag">📊 {compare}</div>', unsafe_allow_html=True)
            with st.spinner(f"Querying {compare}..."):
                answer2, chunks2 = run_query(question, compare, st.session_state.selected_model)
            st.markdown(f'<div class="answer-box">{answer2}</div>', unsafe_allow_html=True)
            if chunks2 and st.session_state.show_sources:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("**Sources**")
                for i, c in enumerate(chunks2):
                    with st.expander(f"Excerpt {i+1} — section ~{c['chunk_index']}"):
                        st.caption(c["text"])

        st.session_state.chat_history.append({
            "ticker": f"{active} vs {compare}",
            "question": question,
            "answer": f"{active}: {answer1[:150]}... | {compare}: {answer2[:150]}..."
        })

    else:
        with st.spinner("Finding relevant sections..."):
            answer, chunks = run_query(question, active, st.session_state.selected_model)

        st.markdown("### Answer")
        st.markdown(f'<div class="answer-box">{answer}</div>', unsafe_allow_html=True)

        if chunks and st.session_state.show_sources:
            st.divider()
            st.markdown("### Source Excerpts")
            for i, chunk in enumerate(chunks):
                with st.expander(f"Excerpt {i+1} — section ~{chunk['chunk_index']}"):
                    st.caption(chunk["text"])

        st.session_state.chat_history.append({
            "ticker": active,
            "question": question,
            "answer": answer
        })
