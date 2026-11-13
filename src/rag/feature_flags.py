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


def get_active_flags() -> Dict[str, bool]:
    """Return a fresh copy of current flags."""
    return dict(FEATURE_FLAGS)
