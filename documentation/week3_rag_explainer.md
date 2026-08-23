# 🧠 How Our RAG System Works — Complete Explainer

> **RAG = Retrieval-Augmented Generation**
> Instead of asking an AI to "remember" everything, we **store knowledge in a database** and **retrieve only what's relevant** before generating an answer.

---

## 🤔 Why No OpenAI API Key?

Most RAG tutorials use OpenAI for **two things**:
1. **Embedding** — converting text into numbers (vectors)
2. **Generation** — producing the final answer

We replaced **both** with free, local alternatives:

| Component | OpenAI (paid ❌) | Our Approach (free ✅) |
|---|---|---|
| Embeddings | `text-embedding-3-small` | `sentence-transformers` (local) |
| LLM | `gpt-4` / `gpt-3.5` | `llama3.2` via Ollama (local) |
| Cost | 💰 Per token | 🆓 Completely free |
| Internet needed? | ✅ Always | ❌ After first download |

---

## 📦 Packages Installed & Their Purpose

### 1. `pypdf`
- **What it does:** Reads `.pdf` files and extracts raw text from each page
- **Used in:** `pdfreader.py`
- **Think of it as:** A PDF-to-text converter

### 2. `sentence-transformers`
- **What it does:** Converts text into **384-dimensional vectors** (lists of 384 numbers) that capture the *meaning* of the text — all running locally on your CPU
- **Model used:** `all-MiniLM-L6-v2` (~90MB, downloaded from HuggingFace once, cached forever after)
- **Used in:** `embedder.py`
- **Think of it as:** A translator that turns words into math

### 3. `pinecone`
- **What it does:** A **vector database** in the cloud — stores your vectors and can instantly find the most similar ones to a query
- **Used in:** `vectorstore.py`
- **Think of it as:** Google Search, but for *meaning/concepts* instead of keywords

### 4. `python-dotenv`
- **What it does:** Reads your `.env` file and loads `PINECONE_API_KEY`, `PINECONE_INDEX_NAME` as environment variables — so secrets are never hardcoded
- **Think of it as:** A secure key holder

### 5. `ollama` (Python package)
- **What it does:** A Python library that sends requests to the **Ollama local server** running on your machine via `http://localhost:11434`
- **Used in:** `llm.py`
- **Think of it as:** A remote control for your locally running AI model

### 6. Ollama (Desktop App)
- **What it does:** Runs open-source LLMs like `llama3.2` **on your own computer** as a server — no cloud, no API costs, no internet after setup
- **`ollama pull llama3.2`** — downloads the model weights (~2GB) to your hard drive
- **Think of it as:** A local version of ChatGPT running entirely on your PC

---

## 🏗️ System Architecture — Two Phases

### Phase 1: Data Ingestion (Run once — `dataprocessor.py`)

```
HRPolicy.pdf
     │
     ▼
┌─────────────┐
│  pdfreader  │  pypdf extracts raw text from every page
└─────────────┘
     │  List of page strings
     ▼
┌─────────────┐
│   chunker   │  Splits text into ~900-char chunks
│             │  with 150-char overlap between chunks
└─────────────┘
     │  List of ~50 text chunks
     ▼
┌─────────────┐
│   embedder  │  sentence-transformers converts each chunk
│             │  "Staff must work 9AM..." → [0.12, -0.34, 0.89, ...]
└─────────────┘
     │  List of 384-dim float vectors
     ▼
┌─────────────┐
│  Pinecone   │  Stores each vector + its original text
│  (cloud DB) │  in index "rag-week-3-py"
└─────────────┘
     ✅ Done! Knowledge is stored and searchable
```

### Phase 2: Query & Answer (Run anytime — `queryprocessor.py`)

```
User: "What is the work timing policy?"
     │
     ▼
┌──────────────────┐
│ embed_user_query │  Same model converts the question
│                  │  → [0.45, -0.12, 0.77, ...] (384 numbers)
└──────────────────┘
     │  Query vector
     ▼
┌──────────────────┐
│ search_in_pinecone│  Pinecone finds the 4 stored chunks
│                  │  with the closest vectors (cosine similarity)
└──────────────────┘
     │  Top 4 matching text chunks (the "context")
     ▼
┌──────────────────┐
│     llm.py       │  Sends to Ollama (llama3.2 on your PC):
│                  │  System: "Answer using only this context..."
│                  │  User: "Query: [question] + Context: [chunks]"
└──────────────────┘
     │
     ▼
💬 "According to the HR policy, staff are required to
     work normal working hours of 40 hours per week..."
```

---

## 🔍 How Sentence Transformers Work

When you write a sentence, the model converts it into 384 numbers that represent its **meaning**:

```
"What is the work timing policy?"  → [0.12, -0.34, 0.89, ..., 0.67]
"Staff must work 9AM to 6PM"      → [0.11, -0.31, 0.91, ..., 0.65]  ← very similar!
"The weather is sunny today"      → [0.78,  0.52, -0.23, ..., -0.12] ← very different
```

Sentences about the **same topic** produce **similar numbers**.
Pinecone measures this similarity (cosine similarity) and returns the best matches.

> This is why it "understands" meaning — not just matching keywords like a search engine!

---

## 🖥️ What is Ollama & Why Did We Pull the Model?

**Ollama** is a local AI server that:
- Runs on your PC at `http://localhost:11434`
- Hosts open-source models: `llama3.2`, `mistral`, `phi3`, etc.
- Works **completely offline** after the model is downloaded

```bash
ollama pull llama3.2
```
Downloads ~2GB of model weights to your hard drive. After that, `ollama.chat()` in
your Python code sends the question to this server — it's like ChatGPT but on your own machine.

### Why not just use ChatGPT directly?
| Reason | Explanation |
|---|---|
| 🔐 Privacy | HR documents never leave your machine |
| 💰 Cost | Completely free, no per-token billing |
| 🌐 Offline | Works without internet after setup |
| 🏎️ Speed | No network latency to external servers |

---

## 🗂️ File-by-File Summary

| File | Role | Pipeline Phase |
|---|---|---|
| `pdfreader.py` | Extracts text from PDF pages | Ingestion |
| `chunker.py` | Splits text into overlapping chunks | Ingestion |
| `embedder.py` | Converts text ↔ 384-dim vectors (both ways) | Both |
| `vectorstore.py` | Stores & searches vectors in Pinecone | Both |
| `dataprocessor.py` | Runs the full Phase 1 pipeline | Ingestion |
| `llm.py` | Sends query + context to Ollama/llama3.2 | Query |
| `queryprocessor.py` | Runs the full Phase 2 pipeline | Query |
| `.env` | Stores API keys securely | Config |

---

## ✅ Why This Stack Is Powerful

```
100% Free  +  100% Private  +  Runs Locally  =  Production-Ready RAG
```

- No OpenAI credits needed — ever
- HR documents never sent to any external AI
- Works on any PDF, any domain, any question
- Can run fully offline after the one-time model downloads
