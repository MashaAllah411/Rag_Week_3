#!/usr/bin/env python
# ============================================================
# run.py - The Unified One-Command Launcher
#
# USAGE (needs only Python 3.10+; nothing else installed):
#   python run.py                 first run: create .venv, install dependencies, create .env,
#                                 download models, check services, then start API + UI.
#                                 later runs: a fast check, then start.
#   python run.py --setup         do all of the above but do NOT start the servers
#   python run.py --setup --force reinstall dependencies and re-download models
#   python run.py --skip-setup    skip every check and start with the current interpreter
#
# The first part of this file uses only the Python standard library so it can run before
# anything is installed. It then re-runs itself with the project's own .venv interpreter,
# so no manual activation is ever required.
# ============================================================

from __future__ import annotations
import hashlib
import io
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from typing import List, Optional

# Fix Windows console encoding for Unicode output
for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream and hasattr(_stream, "buffer") and (_stream.encoding or "").lower() != "utf-8":
        try:
            setattr(sys, _stream_name, io.TextIOWrapper(_stream.buffer, encoding="utf-8", errors="replace"))
        except Exception:
            pass

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "src"))

LOGS_DIR = REPO_ROOT / "logs"
BACKEND_LOG_FILE = LOGS_DIR / "backend.log"
FRONTEND_LOG_FILE = LOGS_DIR / "frontend.log"

VENV_DIR = REPO_ROOT / ".venv"
REQUIREMENTS = REPO_ROOT / "requirements.txt"
PYPROJECT = REPO_ROOT / "pyproject.toml"
ENV_FILE = REPO_ROOT / ".env"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
DEPS_MARKER = VENV_DIR / ".rag-deps.json"
MODELS_MARKER = VENV_DIR / ".rag-models.json"
MIN_PYTHON = (3, 10)

USAGE = """python run.py                  set up anything missing, then start the API and the UI
python run.py --setup          set up only (venv, packages, .env, models, service checks); do not start
python run.py --setup --force  reinstall packages and re-download models
python run.py --skip-setup     skip every check; start with the current Python
"""

# Importable names that must exist for the app to run (checked cheaply with find_spec, no imports).
REQUIRED_MODULES = [
    "fastapi", "uvicorn", "multipart", "streamlit", "requests", "httpx", "numpy", "pandas", "dotenv",
    "pypdf", "PIL", "pytesseract", "chromadb", "rank_bm25", "sentence_transformers", "ollama",
    "opentelemetry.sdk", "pydantic",
]


def step(msg: str) -> None:
    print(f"[SETUP] {msg}", flush=True)


def ok(msg: str) -> None:
    print(f"  [ok]   {msg}", flush=True)


def warn(msg: str) -> None:
    print(f"  [warn] {msg}", flush=True)


# ══════════════════════════════════════════════════════════════
#  Bootstrap (stdlib only): venv -> dependencies -> .env -> models -> services
# ══════════════════════════════════════════════════════════════

def check_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        print(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or newer is required; this is "
              f"{sys.version_info.major}.{sys.version_info.minor}.\n"
              "Install a current Python from https://www.python.org/downloads/ and run `python run.py` again.")
        sys.exit(1)


def venv_python() -> Path:
    return VENV_DIR / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def inside_project_venv() -> bool:
    try:
        return Path(sys.prefix).resolve() == VENV_DIR.resolve()
    except OSError:
        return False


def ensure_venv() -> None:
    """Create .venv if it is missing or unusable."""
    py = venv_python()
    if py.exists():
        probe = subprocess.run([str(py), "-c", "import sys"], capture_output=True)
        if probe.returncode == 0:
            return
        warn(f"{VENV_DIR} exists but its Python does not run (moved or broken). Delete the .venv folder and run again.")
        sys.exit(1)
    step(f"Creating virtual environment at {VENV_DIR} ...")
    try:
        import venv
        venv.EnvBuilder(with_pip=True).create(str(VENV_DIR))
    except Exception as exc:
        print(f"Could not create a virtual environment: {exc}\n"
              "On Debian/Ubuntu install it with: sudo apt install python3-venv\n"
              "Then run `python run.py` again.")
        sys.exit(1)
    ok("virtual environment created")


def _run_in_venv(argv: List[str]) -> "int":
    """Re-run this script with the venv interpreter. Windows: wait for the child; POSIX: replace the process."""
    py = str(venv_python())
    cmd = [py, str(Path(__file__).resolve())] + argv
    env = {**os.environ, "RAG_IN_VENV": "1"}
    if sys.platform != "win32":
        os.execve(py, cmd, env)          # does not return
    child = subprocess.Popen(cmd, cwd=str(REPO_ROOT), env=env)
    if hasattr(signal, "SIGBREAK"):
        # Ctrl+Break also reaches the child; ignore it here so we outlive it and report its exit code.
        signal.signal(signal.SIGBREAK, lambda *_: None)
    interrupts = 0
    while True:
        try:
            return child.wait()
        except KeyboardInterrupt:
            # The console already delivered Ctrl+C to the child, which shuts the servers down.
            # Keep waiting so its cleanup finishes; a second Ctrl+C within the wait force-stops it.
            interrupts += 1
            if interrupts >= 2:
                kill_process_tree(child)
                return 130


def _dependency_fingerprint() -> str:
    """Hash of everything that decides which packages must be installed."""
    h = hashlib.sha256()
    h.update(REQUIREMENTS.read_bytes() if REQUIREMENTS.exists() else b"")
    if PYPROJECT.exists():
        match = re.search(r"dependencies\s*=\s*\[(.*?)\n\]", PYPROJECT.read_text(encoding="utf-8"), re.S)
        h.update((match.group(1) if match else "").encode("utf-8"))
    h.update(f"py{sys.version_info.major}.{sys.version_info.minor}".encode())
    return h.hexdigest()


def _missing_modules() -> List[str]:
    import importlib.util
    missing = []
    for name in REQUIRED_MODULES:
        try:
            if importlib.util.find_spec(name) is None:
                missing.append(name)
        except (ImportError, ValueError):
            missing.append(name)
    return missing


def _read_marker(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def ensure_dependencies(force: bool) -> bool:
    """Install requirements when missing or changed. Returns True if pip ran."""
    fingerprint = _dependency_fingerprint()
    previous = _read_marker(DEPS_MARKER)
    missing = _missing_modules()
    if not force and previous.get("fingerprint") == fingerprint and not missing:
        return False                                     # fast path: nothing to do

    if force:
        reason = "forced"
    elif not previous:
        reason = "first run"
    elif missing:
        reason = f"missing packages ({', '.join(missing[:4])}{'...' if len(missing) > 4 else ''})"
    else:
        reason = "requirements changed"
    step(f"Installing dependencies ({reason}). The first install downloads a few hundred MB "
         "(PyTorch is the largest) and can take several minutes ...")
    if not REQUIREMENTS.exists():
        print("requirements.txt is missing; cannot install dependencies.")
        sys.exit(1)

    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-r", str(REQUIREMENTS)]
    if previous or force:
        cmd.append("--upgrade")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        print("\nDependency installation failed (see the pip output above).\n"
              "Common causes: no internet connection, a proxy, or a Python version without prebuilt wheels\n"
              "(this project was tested on Python 3.12). Fix the cause and run `python run.py` again;\n"
              "it resumes where it stopped.")
        sys.exit(1)
    still_missing = _missing_modules()
    if still_missing:
        print(f"pip finished but these modules are still missing: {', '.join(still_missing)}")
        sys.exit(1)
    DEPS_MARKER.write_text(json.dumps({"fingerprint": fingerprint, "python": sys.version.split()[0],
                                       "installed_at": time.strftime("%Y-%m-%d %H:%M:%S")}), encoding="utf-8")
    ok("dependencies installed")
    return True


def _required_env_keys() -> List[str]:
    """Keys in .env.example whose preceding comment says [required]."""
    required, flag = [], False
    for raw in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("#"):
            flag = "[required]" in line.lower()
            continue
        if "=" in line and not line.startswith("#"):
            if flag:
                required.append(line.split("=", 1)[0].strip())
            flag = False
        elif not line:
            flag = False
    return required


def ensure_env_file() -> None:
    """Create .env from the template; stop if a [required] key is still empty."""
    if not ENV_EXAMPLE.exists() and not ENV_FILE.exists():
        warn(".env.example is missing, so no .env was created. Defaults will be used.")
        return
    if not ENV_FILE.exists():
        shutil.copyfile(ENV_EXAMPLE, ENV_FILE)
        step("Created .env from .env.example")
    required = _required_env_keys() if ENV_EXAMPLE.exists() else []
    values = {}
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if "=" in raw and not raw.strip().startswith("#"):
            key, _, value = raw.partition("=")
            values[key.strip()] = value.split(" #")[0].strip()
    missing = [k for k in required if not values.get(k)]
    if missing:
        print("\n" + "=" * 65)
        print("  Action needed: fill in these keys in .env, then run `python run.py` again")
        print("=" * 65)
        for key in missing:
            print(f"   - {key}")
        print(f"\n  File: {ENV_FILE}")
        sys.exit(2)
    ok(".env present" + ("" if required else " (no secrets are required; defaults work)"))


def prefetch_models(force: bool) -> None:
    """Download the embedding and reranker models once so the first query does not stall."""
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
    emb = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    rer = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    wanted = {"embedding": emb, "reranker": rer}
    if not force and _read_marker(MODELS_MARKER) == wanted:
        return
    step(f"Downloading models once (about 200 MB): {emb} and {rer} ...")
    code = ("from sentence_transformers import SentenceTransformer, CrossEncoder;"
            f"SentenceTransformer({emb!r});CrossEncoder({rer!r});print('models ready')")
    env = {**os.environ, "HF_HUB_DISABLE_SYMLINKS_WARNING": "1"}
    result = subprocess.run([sys.executable, "-c", code], cwd=str(REPO_ROOT), env=env)
    if result.returncode != 0:
        warn("Could not download the models (offline?). They will be fetched on first use instead, "
             "so the first search or index may be slow or fail until you are online.")
        return
    MODELS_MARKER.write_text(json.dumps(wanted), encoding="utf-8")
    ok("models downloaded")


def _http_json(url: str, timeout: float = 1.5):
    """GET JSON, failing fast when nothing is listening (a refused connection can otherwise stall for seconds)."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        host = "127.0.0.1" if parsed.hostname in ("localhost", None) else parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=0.4):
            pass
        url = url.replace("//localhost", "//127.0.0.1", 1)
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def preflight_services() -> None:
    """Check external pieces. Warnings only: the app degrades gracefully without them."""
    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)
    print("[PREFLIGHT] Checking services ...", flush=True)

    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    if "://" not in host:
        host = "http://" + host
    model = os.getenv("OLLAMA_MODEL", "llama3.2")
    tags = _http_json(host.rstrip("/") + "/api/tags")
    if tags is None:
        warn(f"Ollama is not reachable at {host}.\n"
             "         Needed for: written answers, query rewriting, the LLM judge, live structured output.\n"
             "         Works without it: retrieval + citations, chunking, evaluation, agents, MCP, tracing.\n"
             f"         Install: https://ollama.com/download   Start: ollama serve   Model: ollama pull {model}\n"
             "         Continuing without it.")
    else:
        names = [m.get("name", "") for m in tags.get("models", [])]
        if any(n == model or n.startswith(model + ":") for n in names):
            ok(f"Ollama reachable, model '{model}' available")
        else:
            warn(f"Ollama is running but model '{model}' is not pulled.\n"
                 f"         Run: ollama pull {model}\n         Continuing; answers will say the LLM is unavailable until then.")

    candidates = [os.environ.get("TESSERACT_PATH", ""), shutil.which("tesseract") or "",
                  r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                  r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]
    if any(c and os.path.isfile(c) for c in candidates):
        ok("Tesseract OCR found")
    else:
        warn("Tesseract OCR not found, so text inside images embedded in PDFs will not be read (normal PDF text is fine).\n"
             "         Windows: https://github.com/UB-Mannheim/tesseract/wiki   macOS: brew install tesseract   "
             "Debian/Ubuntu: sudo apt install tesseract-ocr\n         Continuing without OCR.")

    store = Path(os.getenv("VECTOR_STORE_DIR", str(REPO_ROOT / "data" / "vectorstore")))
    if not store.is_absolute():
        store = REPO_ROOT / store
    try:
        store.mkdir(parents=True, exist_ok=True)
        probe = store / ".write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        ok(f"vector store folder writable ({store}); ChromaDB is embedded, nothing to start")
    except OSError as exc:
        print(f"The vector store folder {store} is not writable: {exc}\nSet VECTOR_STORE_DIR in .env to a folder you can write to.")
        sys.exit(1)


def ensure_dirs() -> None:
    for d in ("logs", "traces", "data", "resources"):
        (REPO_ROOT / d).mkdir(parents=True, exist_ok=True)


def bootstrap(argv: List[str]) -> None:
    """Make a clean machine ready. Cheap when everything is already in place."""
    check_python_version()
    if "--skip-setup" in argv:
        return
    force = "--force" in argv

    if not inside_project_venv() and os.environ.get("RAG_IN_VENV") != "1":
        ensure_venv()
        sys.exit(_run_in_venv(argv))                     # re-run with the venv's Python; no activation needed

    installed = ensure_dependencies(force)
    ensure_env_file()
    ensure_dirs()
    prefetch_models(force or installed)
    preflight_services()


# ══════════════════════════════════════════════════════════════
#  Launcher
# ══════════════════════════════════════════════════════════════

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently open and bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def find_free_port(start_port: int, max_attempts: int = 10) -> int:
    for p in range(start_port, start_port + max_attempts):
        if not is_port_in_use(p):
            return p
    raise RuntimeError(f"Could not find an available port in range {start_port}-{start_port + max_attempts}")


def http_ok(url: str, timeout: float = 1.5) -> bool:
    """True when the URL answers HTTP 200 (a bound port alone does not mean the app is ready)."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def stream_process_output(process: subprocess.Popen, prefix: str, log_file: Path) -> None:
    """Pipes stdout/stderr to console with prefix and writes to log file."""
    with open(log_file, "a", encoding="utf-8", errors="replace") as f_out:
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            clean_line = line.rstrip()
            if clean_line:
                try:
                    print(f"{prefix} {clean_line}")
                except Exception:
                    safe = clean_line.encode("ascii", errors="replace").decode("ascii")
                    print(f"{prefix} {safe}")
                f_out.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {clean_line}\n")
                f_out.flush()


def kill_process_tree(proc: subprocess.Popen) -> None:
    """Terminates process and all its child processes on Windows or POSIX."""
    if proc is None or proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        else:
            proc.terminate()
            proc.wait(timeout=2.0)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def child_env() -> dict:
    """Environment for the API and UI processes: the package and the ui folder must be importable."""
    parts = [str(REPO_ROOT / "src"), str(REPO_ROOT)]
    if os.environ.get("PYTHONPATH"):
        parts.append(os.environ["PYTHONPATH"])
    return {**os.environ, "PYTHONPATH": os.pathsep.join(parts), "PYTHONIOENCODING": "utf-8",
            "HF_HUB_DISABLE_SYMLINKS_WARNING": "1"}


def main() -> None:
    argv = sys.argv[1:]
    if "-h" in argv or "--help" in argv:
        print(USAGE)
        return

    bootstrap(argv)

    if "--setup" in argv:
        print("\n[SETUP] Environment is ready. Start the app with:  python run.py")
        return

    from dotenv import load_dotenv
    load_dotenv(ENV_FILE)

    backend_port = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port = int(os.getenv("FRONTEND_PORT", "8501"))
    backend_host = os.getenv("BACKEND_HOST", "127.0.0.1")     # local only unless you opt in

    if is_port_in_use(backend_port):
        print(f"[PORT] Backend port {backend_port} is busy. Finding fallback port...")
        backend_port = find_free_port(8001)
    if is_port_in_use(frontend_port):
        print(f"[PORT] Frontend port {frontend_port} is busy. Finding fallback port...")
        frontend_port = find_free_port(8502)

    os.environ["BACKEND_PORT"] = str(backend_port)
    os.environ["FRONTEND_PORT"] = str(frontend_port)
    os.environ["BACKEND_URL"] = f"http://localhost:{backend_port}"
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 65)
    print("  Insurance Policy & Claims RAG Platform")
    print("  Unified Stack (Weeks 1-12)")
    print("=" * 65)
    print(f"  Backend API : http://localhost:{backend_port}")
    print(f"  API Docs    : http://localhost:{backend_port}/api/docs")
    print(f"  Frontend UI : http://localhost:{frontend_port}")
    print("=" * 65 + "\n")

    backend_proc: Optional[subprocess.Popen] = None
    frontend_proc: Optional[subprocess.Popen] = None

    shutting_down = {"done": False}

    def cleanup_and_exit(signum=None, frame=None):
        if shutting_down["done"]:                       # a signal handler plus the finally block can both land here
            sys.exit(0)
        shutting_down["done"] = True
        print("\n\n[SHUTDOWN] Stopping all services cleanly...")
        if frontend_proc:
            print("   Stopping Streamlit frontend...")
            kill_process_tree(frontend_proc)
        if backend_proc:
            print("   Stopping FastAPI backend...")
            kill_process_tree(backend_proc)
        print("[SHUTDOWN] All services stopped. Goodbye!\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup_and_exit)
    signal.signal(signal.SIGTERM, cleanup_and_exit)
    if hasattr(signal, "SIGBREAK"):                     # Windows: Ctrl+Break or closing the console
        signal.signal(signal.SIGBREAK, cleanup_and_exit)

    # ── 1. Start FastAPI Backend ─────────────────────────────
    print("[STARTUP] Starting FastAPI backend (uvicorn)...")
    backend_cmd = [sys.executable, "-m", "uvicorn", "rag.api.main:app",
                   "--host", backend_host, "--port", str(backend_port), "--log-level", "info"]
    backend_proc = subprocess.Popen(backend_cmd, cwd=str(REPO_ROOT), env=child_env(),
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                    bufsize=1, encoding="utf-8", errors="replace")
    threading.Thread(target=stream_process_output, args=(backend_proc, "[BACKEND]", BACKEND_LOG_FILE),
                     daemon=True).start()

    # ── 2. Wait for Backend /health to Pass ──────────────────
    health_url = f"http://127.0.0.1:{backend_port}/health"
    print(f"[HEALTH] Polling {health_url} ...")
    health_ok = False
    start_poll = time.time()
    while time.time() - start_poll < 90.0:
        if backend_proc.poll() is not None:
            print("[STARTUP] FastAPI backend process exited unexpectedly (see logs/backend.log).")
            cleanup_and_exit()
        if http_ok(health_url):
            health_ok = True
            break
        time.sleep(0.5)
    if not health_ok:
        print("[HEALTH] Timed out waiting for backend /health.")
        cleanup_and_exit()
    print(f"[HEALTH] Backend is healthy and ready on port {backend_port}!")

    # ── 3. Start Streamlit Frontend ──────────────────────────
    print(f"[STARTUP] Starting Streamlit UI on port {frontend_port}...")
    frontend_cmd = [sys.executable, "-m", "streamlit", "run", str(REPO_ROOT / "ui" / "app.py"),
                    "--server.port", str(frontend_port), "--server.headless", "true",
                    "--browser.gatherUsageStats", "false"]
    frontend_proc = subprocess.Popen(frontend_cmd, cwd=str(REPO_ROOT), env=child_env(),
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                     bufsize=1, encoding="utf-8", errors="replace")
    threading.Thread(target=stream_process_output, args=(frontend_proc, "[FRONTEND]", FRONTEND_LOG_FILE),
                     daemon=True).start()

    ui_url = f"http://localhost:{frontend_port}"
    ui_health = f"http://127.0.0.1:{frontend_port}/_stcore/health"
    start_ui = time.time()
    while time.time() - start_ui < 60.0 and not http_ok(ui_health):
        if frontend_proc.poll() is not None:
            print("[STARTUP] Streamlit exited unexpectedly (see logs/frontend.log).")
            cleanup_and_exit()
        time.sleep(0.5)
    print("\n[READY] Stack is fully online!")
    print(f"   Opening {ui_url} in your default browser...")
    try:
        webbrowser.open(ui_url)
    except Exception:
        pass
    print("\nPress Ctrl+C at any time to shut down both backend and frontend cleanly.\n")

    try:
        while True:
            if backend_proc.poll() is not None:
                print("[WARNING] Backend process stopped.")
                break
            if frontend_proc.poll() is not None:
                print("[WARNING] Frontend process stopped.")
                break
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup_and_exit()


if __name__ == "__main__":
    main()
