# 📈 Financial Analyst Agent

> Ask anything about a public company's annual 10-K filing — get grounded, cited answers powered by SEC EDGAR + Google Gemini.

---

## 🧠 What Is This?

**Financial Analyst Agent** is a Retrieval-Augmented Generation (RAG) pipeline that lets you query real SEC 10-K filings using natural language. Instead of asking an LLM to recall financial data from memory (and risk hallucination), this system:

1. **Fetches** the actual 10-K filing directly from SEC EDGAR
2. **Chunks and embeds** the document into a local vector database
3. **Retrieves** the most semantically relevant sections for any question
4. **Generates** a grounded, cited answer using Google Gemini

No hallucinations. Every answer is traceable back to a real excerpt from the filing.

---

## 🎬 Demo

```
User: "What are Apple's main risk factors?"

Agent: Based on Excerpt 3 (Risk Factors section), Apple identifies several
key risks including: heavy dependence on a single product category (iPhone),
global semiconductor supply chain constraints, and exposure to macroeconomic
conditions affecting consumer spending. Excerpt 1 further notes that...
```

Try it with any public US company — AAPL, NVDA, MSFT, TSLA, and more.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INGESTION PIPELINE                        │
│                                                                  │
│   SEC EDGAR API  ──►  Raw 10-K Text  ──►  500-word Chunks       │
│                                               │                  │
│                                               ▼                  │
│                                    Gemini Embeddings API         │
│                                               │                  │
│                                               ▼                  │
│                                        ChromaDB (local)          │
└─────────────────────────────────────────────────────────────────┘
                                               │
                                               │  (one-time setup per ticker)
                                               │
┌─────────────────────────────────────────────────────────────────┐
│                         QUERY PIPELINE                           │
│                                                                  │
│   User Question  ──►  Gemini Embedding  ──►  Vector Search       │
│                                               │                  │
│                                               ▼                  │
│                                      Top-5 Relevant Chunks       │
│                                               │                  │
│                                               ▼                  │
│                              Gemini Flash (Grounded Generation)  │
│                                               │                  │
│                                               ▼                  │
│                              Answer + Source Citations in UI     │
└─────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

- **🔍 Semantic Search** — finds relevant filing sections by meaning, not keyword matching
- **📊 Multi-Company Support** — index any public US company and switch between them
- **⚖️ Compare Mode** — ask the same question about two companies side by side
- **📄 Source Citations** — every answer shows which filing excerpt it came from
- **💬 Chat History** — persistent session history in the sidebar
- **⚙️ Settings Panel** — switch between Gemini models, toggle source display, re-run queries
- **🆓 100% Free** — uses Google Gemini's free tier (1,500 requests/day), no paid API needed

---

## 🗂️ Project Structure

```
financial-analyst-agent/
├── src/
│   ├── ingest.py       # Fetches 10-K filings from SEC EDGAR API
│   ├── embed.py        # Chunks text + embeds into ChromaDB
│   ├── retriever.py    # Semantic search over stored vectors
│   └── app.py          # Streamlit UI + Gemini answer generation
├── data/               # Downloaded 10-K text files (auto-created)
├── chroma_db/          # Local vector database (auto-created)
├── .env                # API keys (not committed)
├── requirements.txt    # Python dependencies
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- A free [Google Gemini API key](https://aistudio.google.com) (no credit card needed)

### 1. Clone the repo

```bash
git clone https://github.com/saumyg3/financial-analyst-agent.git
cd financial-analyst-agent
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate       # Mac/Linux
# venv\Scripts\activate        # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up your API key

```bash
echo "GEMINI_API_KEY=your_key_here" > .env
```

### 5. Run the app

```bash
streamlit run src/app.py
```

Open [http://localhost:8501](http://localhost:8501) — AAPL is already indexed if you've run the setup before, otherwise use the sidebar to fetch your first company.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `google-genai` | Gemini embeddings + text generation |
| `chromadb` | Local vector database |
| `streamlit` | Web UI |
| `requests` | SEC EDGAR API calls |
| `python-dotenv` | Environment variable management |
| `tiktoken` | Token counting utilities |

Install all at once:
```bash
pip install google-genai chromadb streamlit requests python-dotenv tiktoken
```

---

## 🔧 How Each File Works

### `ingest.py`
Talks to the SEC EDGAR API to:
- Convert a stock ticker (e.g. `AAPL`) to a CIK number
- Find the most recent 10-K filing
- Download and strip the HTML to plain text
- Save to `data/TICKER_DATE.txt`

### `embed.py`
Processes the raw text:
- Splits into 500-word chunks with 50-word overlap (so context isn't lost at boundaries)
- Sends each chunk to Gemini's embedding API to get a vector representation
- Stores all vectors + text in ChromaDB under a collection named after the ticker
- Rate-limit safe — automatically retries on 429 errors

### `retriever.py`
Handles semantic search:
- Embeds the user's question using the same Gemini embedding model
- Queries ChromaDB for the top-k most similar chunks
- Returns the raw text + metadata for each match

### `app.py`
The full Streamlit UI:
- Sidebar for loading companies and viewing chat history
- Main area for querying with suggested questions
- Compare mode for side-by-side analysis
- Settings panel for model selection and preferences

---

## 💡 Example Questions to Try

**Risk Analysis**
```
What are the main risk factors facing this company?
How does the company manage supply chain risk?
What regulatory risks does the company mention?
```

**Business Overview**
```
How does the company describe its core business?
What products or services generate the most revenue?
What markets does the company operate in?
```

**Financial Insights**
```
What is the revenue breakdown by segment?
How has the company's profitability trended?
What capital allocation priorities does management describe?
```

**Competitive Position**
```
How does the company describe its competitive advantages?
What does the company say about its market position?
```

---

## ⚠️ Limitations

- **Free tier rate limits** — Gemini's free tier allows ~1,500 embedding requests/day. Large filings may require retries across multiple sessions.
- **Text-only extraction** — Financial tables in 10-Ks are sometimes embedded as images and won't be captured by the text parser.
- **Chunk boundary artifacts** — Some excerpts may begin mid-sentence due to chunking. The LLM handles this gracefully but raw excerpts may look truncated.
- **US companies only** — SEC EDGAR covers US public companies. International companies file differently.

---

## 🗺️ Roadmap

- [ ] PDF parsing for better table extraction
- [ ] Multi-year comparison (e.g. 2022 vs 2023 10-K)
- [ ] Export answers to PDF report
- [ ] Persistent storage across sessions (PostgreSQL backend)
- [ ] Support for 10-Q (quarterly) filings
- [ ] Deployed hosted version

---

## 👤 Author

**Saumya Goyal**
- GitHub: [@saumyg3](https://github.com/saumyg3)
- LinkedIn: [https://www.linkedin.com/in/saumyagoyal](https://www.linkedin.com/in/saumya-goyal-8a8005327/)
- Email: saumyg3@uci.edu

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with SEC EDGAR public API, Google Gemini, ChromaDB, and Streamlit.*
