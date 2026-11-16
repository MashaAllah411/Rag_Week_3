"""
feature_flags.py

Central feature flags for the RAG platform.
Controls visibility of legacy sections vs new production ChatGPT-style interface.
All legacy developer and evaluation tabs are OFF by default.
Admin (DataProp) can toggle flags at runtime.
"""
from typing import Dict, Any

DEFAULT_FEATURE_FLAGS: Dict[str, bool] = {
    # Legacy sections — all OFF by default for normal users
    "show_evaluation_tab": False,
    "show_error_analysis_tab": False,
    "show_agent_triage_tab": False,
    "show_mcp_ecosystem_tab": False,
    "show_multi_agent_tab": False,
    "show_observability_tab": False,
    "show_foundations_lab_tab": False,
    "show_guardrails_tab": False,
    "show_hr_policy_desk_tab": False,
    "show_capstone_tab": False,
    "show_chunk_inspector": False,
    "show_advanced_search_modes": False,
    # Production features — ON for everyone
    "show_chat_interface": True,
    "show_document_upload": True,
    "show_configuration_panel": True,
    "show_chat_history": True,
    "show_context_window": True,
    "show_thinking_steps": True,
    # Admin-only extras
    "admin_can_toggle_flags": True,
    "admin_show_legacy_sections": True,
    "admin_show_config_advanced": True,
}

FEATURE_FLAGS = dict(DEFAULT_FEATURE_FLAGS)

import json
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "system_config.json"


def get_active_flags() -> Dict[str, bool]:
    """Return a fresh copy of current flags, updated from persistent storage if available."""
    flags = dict(DEFAULT_FEATURE_FLAGS)
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if "flags" in saved and isinstance(saved["flags"], dict):
                    flags.update(saved["flags"])
        except Exception:
            pass
    return flags


def save_system_flags(flags: Dict[str, bool], user_config: Any = None) -> None:
    """Save feature flags and workspace configuration to disk so all users inherit it."""
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    data["flags"] = flags
    if user_config:
        data["config"] = user_config
    with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
