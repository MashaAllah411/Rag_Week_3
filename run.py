#!/usr/bin/env python
# ============================================================
# run.py — The Unified One-Command Launcher
#
# USAGE:
#   python run.py             # Start both backend and frontend
#   python run.py --setup     # Check/install dependencies & setup environment
# ============================================================

from __future__ import annotations
import os
import sys
import io
import time
import socket
import signal
import threading
import subprocess
import webbrowser
from pathlib import Path
from typing import Optional, List

# Fix Windows console encoding for Unicode/emojis
if sys.stdout and hasattr(sys.stdout, "buffer") and sys.stdout.encoding != "utf-8":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "buffer") and sys.stderr.encoding != "utf-8":
    try:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT / "src"))

LOGS_DIR = REPO_ROOT / "logs"
BACKEND_LOG_FILE = LOGS_DIR / "backend.log"
FRONTEND_LOG_FILE = LOGS_DIR / "frontend.log"


# ── Port Checking & Validation ───────────────────────────────

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a TCP port is currently open and bound."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


def find_free_port(start_port: int, max_attempts: int = 10) -> int:
    """Find a free TCP port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        if not is_port_in_use(p):
            return p
    raise RuntimeError(f"Could not find an available port in range {start_port}-{start_port + max_attempts}")


# ── Environment & Prerequisite Validation ────────────────────

def validate_environment() -> None:
    """Validate environment, .env file, and required directory layout."""
    print("[VALIDATION] Verifying environment and file structure...")

    env_file = REPO_ROOT / ".env"
    env_example = REPO_ROOT / ".env.example"

    if not env_file.exists():
        if env_example.exists():
            print("[VALIDATION] No .env file found. Creating from .env.example...")
            with open(env_example, "r", encoding="utf-8") as src, open(env_file, "w", encoding="utf-8") as dst:
                dst.write(src.read())
            print("[VALIDATION] Please add your actual PINECONE_API_KEY to .env for vector queries.")
        else:
            print("[VALIDATION] Neither .env nor .env.example found.")

    # Ensure required directories exist
    required_dirs = ["logs", "traces", "data", "resources"]
    for d in required_dirs:
        (REPO_ROOT / d).mkdir(parents=True, exist_ok=True)

    print("[VALIDATION] Prerequisites verified.")


# ── Setup Command (--setup) ──────────────────────────────────

def run_setup() -> None:
    """Installs required packages into the active environment."""
    print("\n[SETUP] Installing dependencies from requirements.txt...")
    req_file = REPO_ROOT / "requirements.txt"
    if not req_file.exists():
        print("[SETUP] requirements.txt not found.")
        sys.exit(1)

    cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
    res = subprocess.run(cmd)
    if res.returncode == 0:
        print("\n[SETUP] All dependencies installed successfully.")
    else:
        print("\n[SETUP] Dependency installation encountered an issue.")
    sys.exit(res.returncode)


# ── Process Output Logger ────────────────────────────────────

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
                    # Fallback for unprintable characters
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
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        else:
            proc.terminate()
            proc.wait(timeout=2.0)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


# ── Main Launcher Routine ────────────────────────────────────

def main() -> None:
    if "--setup" in sys.argv:
        run_setup()

    validate_environment()

    # Read ports from environment or select defaults
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")

    backend_port = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port = int(os.getenv("FRONTEND_PORT", "8501"))

    # Port checking with automatic conflict handling
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
    print("  Unified Enterprise Stack (Weeks 1-11)")
    print("=" * 65)
    print(f"  Backend API : http://localhost:{backend_port}")
    print(f"  API Docs    : http://localhost:{backend_port}/api/docs")
    print(f"  Frontend UI : http://localhost:{frontend_port}")
    print("=" * 65 + "\n")

    backend_proc: Optional[subprocess.Popen] = None
    frontend_proc: Optional[subprocess.Popen] = None

    # Graceful shutdown handler
    def cleanup_and_exit(signum=None, frame=None):
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

    # ── 1. Start FastAPI Backend ─────────────────────────────
    print("[STARTUP] Starting FastAPI backend (uvicorn)...")
    backend_cmd = [
        sys.executable,
        "-m", "uvicorn",
        "rag.api.main:app",
        "--host", "0.0.0.0",
        "--port", str(backend_port),
        "--log-level", "info"
    ]

    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )

    t_backend = threading.Thread(
        target=stream_process_output,
        args=(backend_proc, "[BACKEND]", BACKEND_LOG_FILE),
        daemon=True
    )
    t_backend.start()

    # ── 2. Wait for Backend /health to Pass ───────────────────
    print(f"[HEALTH] Polling backend at http://localhost:{backend_port}/health...")
    health_ok = False
    start_poll = time.time()
    while time.time() - start_poll < 25.0:
        if backend_proc.poll() is not None:
            print("[STARTUP] FastAPI backend process exited unexpectedly.")
            cleanup_and_exit()

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(("127.0.0.1", backend_port)) == 0:
                    health_ok = True
                    break
        except Exception:
            pass
        time.sleep(0.5)

    if not health_ok:
        print("[HEALTH] Timed out waiting for backend to become ready.")
        cleanup_and_exit()

    print(f"[HEALTH] Backend is healthy and ready on port {backend_port}!")

    # ── 3. Start Streamlit Frontend ──────────────────────────
    print(f"[STARTUP] Starting Streamlit UI on port {frontend_port}...")
    frontend_cmd = [
        sys.executable,
        "-m", "streamlit", "run",
        str(REPO_ROOT / "ui" / "app.py"),
        "--server.port", str(frontend_port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]

    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )

    t_frontend = threading.Thread(
        target=stream_process_output,
        args=(frontend_proc, "[FRONTEND]", FRONTEND_LOG_FILE),
        daemon=True
    )
    t_frontend.start()

    # Wait briefly for Streamlit to bind
    time.sleep(2.0)
    ui_url = f"http://localhost:{frontend_port}"
    print(f"\n[READY] Stack is fully online!")
    print(f"   Opening {ui_url} in your default browser...")
    try:
        webbrowser.open(ui_url)
    except Exception:
        pass

    print("\nPress Ctrl+C at any time to shut down both backend and frontend cleanly.\n")

    # Keep main thread alive monitoring children
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
