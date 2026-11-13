"""
auth_service.py

Session-based authentication and role management for the RAG chatbot.
Supports 'admin' role (DataProp) with feature flag toggling and legacy tools,
and 'user' role with clean production chat and document querying.
"""
import hashlib
from typing import Optional, Dict, Any


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


USER_STORE: Dict[str, Dict[str, Any]] = {
    "DataProp": {
        "password_hash": _hash_password("admin2025"),
        "role": "admin",
        "display_name": "DataProp",
        "avatar_initials": "DP",
        "avatar_color": "#6366f1",
    },
    "demo": {
        "password_hash": _hash_password("demo123"),
        "role": "user",
        "display_name": "Demo User",
        "avatar_initials": "DU",
        "avatar_color": "#10b981",
    },
    "user": {
        "password_hash": _hash_password("user123"),
        "role": "user",
        "display_name": "Standard User",
        "avatar_initials": "SU",
        "avatar_color": "#0ea5e9",
    },
}


def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Validate credentials against USER_STORE.
    Returns user dict without password hash if valid, else None.
    """
    if not username or not password:
        return None
    user_rec = USER_STORE.get(username.strip())
    if not user_rec:
        return None
    if user_rec["password_hash"] == _hash_password(password):
        return {
            "username": username.strip(),
            "role": user_rec["role"],
            "display_name": user_rec["display_name"],
            "avatar_initials": user_rec["avatar_initials"],
            "avatar_color": user_rec["avatar_color"],
        }
    return None


def get_user(username: str) -> Optional[Dict[str, Any]]:
    rec = USER_STORE.get(username)
    if not rec:
        return None
    return {
        "username": username,
        "role": rec["role"],
        "display_name": rec["display_name"],
        "avatar_initials": rec["avatar_initials"],
        "avatar_color": rec["avatar_color"],
    }
