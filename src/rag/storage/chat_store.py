"""
chat_store.py

Persistent JSON storage for user chat sessions in data/chat_history/{username}/{chat_id}.json.
Allows saving, loading, listing, and deleting conversations with full message history and metadata.
"""
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from rag.config import DATA_DIR

CHAT_DIR = DATA_DIR / "chat_history"


def _user_dir(username: str) -> Path:
    safe_name = "".join(c for c in username if c.isalnum() or c in ("-", "_")) or "default"
    path = CHAT_DIR / safe_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_chats(username: str) -> List[Dict[str, Any]]:
    """List all chats for a given user, ordered by most recently modified first."""
    udir = _user_dir(username)
    chats = []
    for f in udir.glob("*.json"):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                chats.append({
                    "chat_id": data.get("chat_id", f.stem),
                    "title": data.get("title", "New Conversation"),
                    "created_at": data.get("created_at", ""),
                    "message_count": len(data.get("messages", [])),
                    "mtime": f.stat().st_mtime,
                })
        except Exception:
            continue
    chats.sort(key=lambda x: x.get("mtime", 0), reverse=True)
    return chats


def load_chat(username: str, chat_id: str) -> Optional[Dict[str, Any]]:
    """Load a specific chat by ID."""
    fpath = _user_dir(username) / f"{chat_id}.json"
    if not fpath.exists():
        return None
    try:
        with open(fpath, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except Exception:
        return None


def save_chat(
    username: str,
    chat_id: str,
    title: str,
    messages: List[Dict[str, Any]],
    created_at: Optional[str] = None
) -> Dict[str, Any]:
    """Persist conversation messages and metadata."""
    udir = _user_dir(username)
    fpath = udir / f"{chat_id}.json"

    data = {
        "chat_id": chat_id,
        "title": title[:60] if title else "New Conversation",
        "user": username,
        "created_at": created_at or datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "messages": messages,
    }
    with open(fpath, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, ensure_ascii=False)
    return data


def delete_chat(username: str, chat_id: str) -> bool:
    """Delete a chat file."""
    fpath = _user_dir(username) / f"{chat_id}.json"
    if fpath.exists():
        try:
            fpath.unlink()
            return True
        except Exception:
            return False
    return False


def create_new_chat(username: str, initial_title: str = "New Conversation") -> str:
    """Generate a new UUID chat ID and create empty initial structure."""
    new_id = f"chat_{uuid.uuid4().hex[:12]}"
    save_chat(username, new_id, initial_title, [])
    return new_id
