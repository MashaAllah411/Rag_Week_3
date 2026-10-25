# Setup

Everything runs on your machine. No account or API key is required. On a fresh machine you need Python and nothing else: `python run.py` sets up the rest by itself.

- [Architecture](architecture.md) · [Features](features.md) · [Legacy index](legacy.md) · [Technical reference](technical-reference.md)

## On a fresh machine

1. **Install Python 3.10 or newer** from <https://www.python.org/downloads/> (tick *Add python.exe to PATH* on Windows). The project was developed and tested on Python 3.12 on Windows 11.
2. **Get the code** (`git clone ...` or unzip it) and open a terminal in the project folder (`Rag_Week_3/`).
3. **Run one command:**

   ```powershell
   python run.py
   ```

4. **If it stops and lists keys to fill in, edit `.env`** and run `python run.py` again. *This project currently requires no keys, so you will not normally be asked.* (See [what is required](#env-and-required-keys).)

That is all. There is no `pip install`, no virtual-environment activation and no `.env` copying to do by hand.

### What `python run.py` does the first time

| Step | What happens | Skipped next time? |
|---|---|---|
| 1. Python check | Stops with a clear message if Python is older than 3.10 | runs every time (instant) |
| 2. Virtual environment | Creates `.venv/` in the project folder if it is missing, then **re-runs itself with the venv's Python**, so you never activate anything | yes, once `.venv` exists |
| 3. Dependencies | Installs `requirements.txt` into `.venv`, with pip's progress shown. A marker file (`.venv/.rag-deps.json`) records a hash of `requirements.txt` and the dependency list in `pyproject.toml` | yes, unless those files change or a package goes missing; then only pip runs again |
| 4. `.env` | Creates `.env` from `.env.example` if missing. If any key marked `[required]` is empty, it lists them and exits so you can fill them in | file is kept; check is instant |
| 5. Models | Downloads the embedding and reranker models once (about 200 MB total) so your first search is not slow | yes, once downloaded |
| 6. Service check | Looks for Ollama (and the model), Tesseract OCR, and a writable vector-store folder. **Missing optional pieces produce a warning with the exact install or start command and the app continues** | runs every time (about a second) |
| 7. Start | Starts the API, waits for `/health` to answer, starts the UI, waits for it to answer, opens the browser | |

Later runs go straight from the quick checks to starting the servers.

First-run time depends on your connection: the download is dominated by PyTorch (pulled in by sentence-transformers). If a download fails, fix your connection and run `python run.py` again; it resumes.

### Explicit setup, without starting anything

```powershell
python run.py --setup            # do steps 1-6 only, then exit
python run.py --setup --force    # reinstall packages and re-download models
python run.py --skip-setup       # skip every check and start with the current Python (for CI or when you manage the environment yourself)
python run.py --help
```

Use `--setup` to prepare a machine ahead of time, or after pulling changes that touched `requirements.txt` (a normal `python run.py` also notices and updates).

To use your own interpreter instead of `.venv`, set `RAG_IN_VENV=1` before running; the launcher then uses the interpreter you started it with.

## Optional extras

| Extra | Needed for | Without it |
|---|---|---|
| [Ollama](https://ollama.com/download) with `llama3.2` (`ollama serve`, then `ollama pull llama3.2`) | written answers, query rewriting, the LLM judge, live structured output, trace replay | retrieval, citations, chunking, evaluation, agents, MCP and tracing all still work; answers say the LLM is unavailable |
| [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) | reading text inside images embedded in PDFs | OCR is off; normal PDF text is still read |

The service check in step 6 tells you which of these are missing and how to add them.

## `.env` and required keys

The defaults work as they are, so `.env` is just a copy of `.env.example` unless you change something. `.env` is ignored by git.

A key is *required* when the comment line directly above it in `.env.example` contains `[required]`. If such a key is empty in `.env`, `python run.py` prints it and exits with code 2 instead of starting a broken app. Nothing is marked required today.

| Setting | Default | Meaning |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.2` | local model used for generation, rewriting and judging |
| `OLLAMA_HOST` | `http://localhost:11434` | where Ollama listens (used by the service check; the Ollama client reads it too) |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | sentence-transformers model (384 dimensions) |
| `RERANKER_MODEL` | `cross-encoder/ms-marco-MiniLM-L-6-v2` | cross-encoder for reranked mode |
| `VECTOR_STORE_DIR` | `data/vectorstore` | where ChromaDB keeps its files (created automatically) |
| `VECTOR_STORE_COLLECTION` | `insurance_rag` | collection name (3+ characters, letters, digits, `. _ -`) |
| `OTEL_SERVICE_NAME` | `insurance-rag` | service name on exported spans |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | empty | e.g. `http://localhost:6006/v1/traces` to also send spans to a self-hosted Phoenix or Jaeger |
| `TESSERACT_PATH` | auto-detected | path to `tesseract.exe` if it is not on `PATH` |
| `RAG_DOCUMENT` | `InsurancePolicy.pdf` | default document in `resources/` |
| `BACKEND_PORT` / `FRONTEND_PORT` | `8000` / `8501` | if a port is busy, the launcher picks the next free one |
| `BACKEND_HOST` | `127.0.0.1` | the API listens on this machine only; set `0.0.0.0` only if you deliberately want it reachable from the network (it has no authentication) |
| `FRONTEND_ORIGINS` | localhost origins | CORS allow-list |

## Running

`python run.py` starts everything and prints the addresses: UI `http://localhost:8501`, API `http://localhost:8000`, interactive API docs `http://localhost:8000/api/docs`. Logs go to `logs/backend.log` and `logs/frontend.log`.

Press `Ctrl+C` to stop. Both servers and their child processes are stopped; closing the console window or `Ctrl+Break` does the same.

If the vector store is empty (first start), the backend indexes the PDFs in `resources/` in the background. The Home and System pages show progress; search works as soon as it finishes (a few seconds to about 15 seconds for the two shipped PDFs).

## Check that it works

1. Open **System & Health**. Under *Open-source stack* every tool should be Active (the LLM row shows Inactive until Ollama is running).
2. Click **Run self-test**. It writes, queries and deletes vectors in ChromaDB, exports a real OpenTelemetry span, reads rendered text with OCR and embeds a sentence.
3. Open **Search & Q&A**, ask *"What is the maximum cost for removal of a disabled vehicle after an accident?"* Among the top three sources you should see `insurancepolicy:chunk_10`, the passage containing Rs 1500 (the first source may be the similar commercial-vehicles policy).
4. Open **Capstone** and click **Run the full suite**.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q        # macOS/Linux: .venv/bin/python -m pytest tests -q
```

The suite runs against the real shipped PDFs, real models and a real ChromaDB (in temporary folders where it writes). It does not need Ollama.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Python 3.10 or newer is required` | Install a current Python and run again |
| "Could not create a virtual environment" (Debian/Ubuntu) | `sudo apt install python3-venv`, then run again |
| Dependency install fails | Check your internet connection or proxy and run `python run.py` again; it resumes. Other Python versions than 3.12 may lack prebuilt wheels for PyTorch |
| `.venv` "exists but its Python does not run" | The folder was moved or copied from another machine; delete `.venv` and run again |
| "Can't reach the backend" in the UI | Start everything with `python run.py`; check `logs/backend.log` |
| Answers say "LLM unavailable" | Start Ollama and pull the model; retrieved chunks are still shown |
| OCR shows Inactive | Install Tesseract, or set `TESSERACT_PATH` |
| Port already in use | The launcher falls back to the next free port and prints it |
| Search returns nothing right after first start | Indexing is still running; watch the System page |
| Rebuild the index | Documents page > Re-index, or delete `data/vectorstore/` and restart |
| `huggingface_hub` symlink warning on Windows | Harmless; the launcher already hides it for the servers |

## Security note: rotate the old Pinecone key

Commit `c89c8cc` added a real Pinecone API key to `.env.example`. Commit `cddf0e8` removed it from that file but added the first 21 characters of it to `tests/test_health_smoke.py`. The repository is public, so the key must be treated as exposed. The working tree from this consolidation no longer contains any part of it, but the committed history still does. **Revoke the key in the Pinecone console.** The application no longer uses Pinecone, so nothing needs it. Rewriting git history is a separate decision for the repository owner.
