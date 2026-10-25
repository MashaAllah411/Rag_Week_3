"""Prompt-injection scanner for retrieved context (Week 8: indirect prompt injection).

An indirect injection hides instructions inside a document the app retrieves, hoping the
LLM treats them as commands. This module scans text *before* it is placed in a prompt.

It is deterministic (regex rules, no model call), explainable (every hit names its rule),
and conservative: it reports and can quarantine, but it is a first line of defence, not a
guarantee. Known limits are listed in KNOWN_LIMITS and shown in the UI.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

# (rule id, severity 1-3, human description, compiled pattern)
_RULES: List[Tuple[str, int, str, "re.Pattern[str]"]] = [
    ("override_instructions", 3, "Tells the model to ignore or replace its instructions",
     re.compile(r"\b(ignore|disregard|forget|override|bypass)\b[^.\n]{0,40}\b(previous|prior|above|earlier|all|any|your|the)\b[^.\n]{0,30}"
                r"\b(instructions?|rules?|prompts?|guidelines?|constraints?)\b", re.I)),
    ("role_hijack", 3, "Tries to reassign the model's role or persona",
     re.compile(r"\b(you are now|from now on,? you|act as|pretend (to be|you are)|new (instructions|persona|role)\s*:)", re.I)),
    ("prompt_exfiltration", 3, "Asks the model to reveal its prompt, instructions or secrets",
     re.compile(r"\b(reveal|print|show|repeat|output|leak|display)\b[^.\n]{0,40}\b(system prompt|hidden prompt|instructions|api[ _-]?key|secret|password|credentials?)\b", re.I)),
    ("fake_system_message", 3, "Contains chat-template or system-role markers",
     re.compile(r"(<\|im_start\|>|<\|system\|>|\[/?INST\]|<<SYS>>|^\s*(system|assistant)\s*:)", re.I | re.M)),
    ("tool_abuse", 2, "Instructs the agent to take an action (approve, pay, delete, send)",
     re.compile(r"\b(approve|pay out|payout|transfer|wire|delete|send)\b[^.\n]{0,30}\b(this|the|all|every)\b[^.\n]{0,30}\b(claim|claims|funds?|money|records?|email|emails)\b", re.I)),
    ("exfil_link", 2, "Markdown image or link that could leak data to an external URL",
     re.compile(r"!\[[^\]]*\]\(https?://[^)]+\)", re.I)),
    ("hidden_text", 2, "Zero-width or bidirectional control characters hiding text",
     re.compile("[​‌‍⁠﻿‪-‮]")),
    ("conceal_from_user", 2, "Asks the model to hide something from the user",
     re.compile(r"\b(do not|don't|never)\b[^.\n]{0,30}\b(tell|mention|inform|reveal to)\b[^.\n]{0,20}\b(the )?user\b", re.I)),
]

KNOWN_LIMITS = [
    "Regex rules catch common phrasings, not novel or heavily obfuscated attacks (e.g. other languages, encodings, paraphrase).",
    "Scanning retrieved text does not protect against a malicious user typing the attack directly; the scope guard and tool permissions cover that.",
    "A determined attacker can split an instruction across several chunks; each piece may look harmless on its own.",
    "Quarantining a flagged chunk can also remove legitimate text that happens to match a rule (false positive).",
]

SEVERITY_LABEL = {1: "low", 2: "medium", 3: "high"}


def scan_text(text: str) -> Dict[str, Any]:
    """Return every rule that matches, with the matching snippet, and an overall verdict."""
    matches: List[Dict[str, Any]] = []
    for rule_id, severity, description, pattern in _RULES:
        for m in pattern.finditer(text or ""):
            start = max(0, m.start() - 30)
            snippet = (text[start:m.end() + 30]).replace("\n", " ")
            matches.append({"rule": rule_id, "severity": SEVERITY_LABEL[severity],
                            "description": description, "snippet": snippet.strip()})
            break  # one example per rule is enough to explain the verdict
    score = sum({"low": 1, "medium": 2, "high": 3}[m["severity"]] for m in matches)
    return {"flagged": bool(matches), "score": score, "matches": matches}


def filter_chunks(chunks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Split retrieved chunks into (safe, quarantined). Quarantined items carry their scan result."""
    safe: List[Dict[str, Any]] = []
    quarantined: List[Dict[str, Any]] = []
    for chunk in chunks:
        result = scan_text(chunk.get("text", ""))
        if result["flagged"]:
            quarantined.append({**chunk, "injection_scan": result})
        else:
            safe.append(chunk)
    return safe, quarantined
