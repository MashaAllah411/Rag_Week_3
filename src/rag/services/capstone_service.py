"""Week 12 capstone: one-click full suite, known weak spots and the four-part demo.

Every number comes from a live run or a saved result file. Checks that need a component
that is not running (e.g. Ollama) are reported as "skipped", never as a pass.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Callable, Dict, List

from rag.config import DATA_DIR


def _ollama_up() -> bool:
    try:
        import ollama
        ollama.list()
        return True
    except Exception:
        return False


def _check(name: str, week: str, fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
    start = time.time()
    try:
        out = fn()
        status, detail = out["status"], out["detail"]
    except Exception as exc:
        status, detail = "fail", f"{type(exc).__name__}: {exc}"
    return {"check": name, "week": week, "status": status, "detail": detail,
            "ms": round((time.time() - start) * 1000, 1)}


def _passfail(ok: bool, detail: str) -> Dict[str, Any]:
    return {"status": "pass" if ok else "fail", "detail": detail}


# ── individual checks ────────────────────────────────────────

def _regression() -> Dict[str, Any]:
    from rag.evaluation.regression import run_all_regression_cases
    r = run_all_regression_cases()
    return _passfail(r["passed"] == r["total"], f"{r['passed']}/{r['total']} regression cases hold (planted drill failure stays DENIED)")


def _agents() -> Dict[str, Any]:
    from rag.services.agent_service import run_agent_benchmark
    r = run_agent_benchmark()
    a, w = r["agent"], r["workflow"]
    ok = a["passed"] == a["total_claims"] and w["passed"] == w["total_claims"]
    return _passfail(ok, f"agent {a['passed']}/{a['total_claims']}, fixed workflow {w['passed']}/{w['total_claims']} claims completed "
                         f"(scripted simulation: see weak spots)")


def _mcp() -> Dict[str, Any]:
    from rag.services.mcp_service import get_mcp_servers_info
    info = get_mcp_servers_info()
    return _passfail(info["servers_count"] >= 1 and info["total_tools_count"] >= 1,
                     f"{info['servers_count']} servers, {info['total_tools_count']} tools discovered over JSON-RPC")


def _squad() -> Dict[str, Any]:
    from rag.services.multi_agent_service import run_squad_triage
    r = run_squad_triage("CLM-7001")
    fd = r.get("final_decision") or {}
    ok = bool(r.get("hand_offs")) and bool(fd.get("status"))
    return _passfail(ok, f"{len(r.get('hand_offs', []))} A2A hand-offs, final status {fd.get('status')}")


def _retrieval() -> Dict[str, Any]:
    from rag.evaluation.retrieval_eval import run_text_evaluation
    sem = run_text_evaluation(mode="semantic", top_k=3)
    hyb = run_text_evaluation(mode="hybrid", top_k=3)
    ok = hyb["hit_rate"] >= sem["hit_rate"]
    return _passfail(ok, f"hit@3 semantic {sem['hit_rate']:.3f} -> hybrid {hyb['hit_rate']:.3f}; "
                         f"MRR {sem['mrr']:.3f} -> {hyb['mrr']:.3f} ({hyb['num_questions']} questions)")


def _injection() -> Dict[str, Any]:
    from rag.core.injection_guard import scan_text
    from rag.api.routes.guardrails import CLEAN_CHUNK, POISONED_CHUNK
    clean, poisoned = scan_text(CLEAN_CHUNK), scan_text(POISONED_CHUNK)
    return _passfail(poisoned["flagged"] and not clean["flagged"],
                     f"poisoned chunk flagged by {len(poisoned['matches'])} rule(s); clean chunk not flagged")


def _structured() -> Dict[str, Any]:
    from rag.generation.structured import validate_output
    good = validate_output('{"answer":"5%","citations":["insurancepolicy:chunk_17"],"confidence":"high","refused":false}')
    bad = validate_output('{"answer":"5%","confidence":"certain"}')
    return _passfail(good["ok"] and not bad["ok"], "valid reply accepted; reply with bad enum and no citations rejected")


def _selftest() -> Dict[str, Any]:
    from rag.services.health_service import run_selftest
    r = run_selftest(deep=False)
    failed = [c["check"] for c in r["checks"] if not c["ok"]]
    return _passfail(not failed, f"{r['passed']}/{r['total']} tool round-trips ok" + (f"; failed: {failed}" if failed else ""))


def _end_to_end() -> Dict[str, Any]:
    if not _ollama_up():
        return {"status": "skipped", "detail": "Ollama is not running, so generation was not exercised. Start Ollama and re-run."}
    from rag.services.pipeline import run_pipeline
    r = run_pipeline("What is the maximum cost for removal of a disabled vehicle after an accident?", mode="hybrid", top_k=3)
    ok = not r["answer"].startswith("LLM unavailable") and bool(r["retrieved_chunks"])
    return _passfail(ok, f"answered with {len(r['retrieved_chunks'])} chunks, confidence {r['confidence']}")


def run_full_suite() -> Dict[str, Any]:
    checks = [
        _check("Tool round-trips (ChromaDB, OpenTelemetry, OCR, embeddings)", "3, 11", _selftest),
        _check("Hybrid beats semantic on the current corpus", "3-4", _retrieval),
        _check("Structured output validation and retry", "2", _structured),
        _check("Prompt-injection scan", "8", _injection),
        _check("Agent loop vs fixed workflow (10 claims)", "7-8", _agents),
        _check("MCP tool discovery", "9", _mcp),
        _check("Multi-agent squad (A2A)", "10", _squad),
        _check("Failure-to-test regression cases", "11", _regression),
        _check("End-to-end grounded answer (needs Ollama)", "2-3", _end_to_end),
    ]
    counts = {s: sum(c["status"] == s for c in checks) for s in ("pass", "fail", "skipped")}
    return {"counts": counts, "total": len(checks), "checks": checks, "ran_at": time.strftime("%Y-%m-%d %H:%M:%S")}


# ── weak spots & demo ────────────────────────────────────────

def _load(path: str) -> Any:
    full = os.path.join(str(DATA_DIR), path)
    if os.path.exists(full):
        with open(full, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def known_weak_spots() -> List[Dict[str, str]]:
    """Honest list of what is simulated, unmeasured or limited. Authored from code review, with live facts filled in."""
    from rag.services.evaluation_service import get_judge_validation
    jv = get_judge_validation()
    ins = {m: _load(f"insurance_results_{m}.json") for m in ("semantic", "hybrid", "reranked")}
    spots = [
        {"area": "Agent loop (Weeks 7-8)", "severity": "high",
         "what": "The 'ReAct' agent follows a fixed, hard-coded step plan; no LLM decides the next step, and token/cost figures are estimates. It demonstrates budgets, stop conditions and trajectory scoring, not LLM planning.",
         "next": "Replace the scripted plan with an LLM tool-choosing loop behind the same budgets, then re-run the race."},
        {"area": "Cost savings (Week 11)", "severity": "high",
         "what": "The semantic-cache benchmark simulates latency (sleep) and uses a fixed 650-token cost per query, so its '% cost reduction' is not measured from real LLM usage. The tracer prices tokens at illustrative hosted rates although the models run locally for $0.",
         "next": "Measure real tokens and latency from Ollama usage fields and log them per request."},
        {"area": "Support drill data (Week 11)", "severity": "medium",
         "what": "The 100 'production' traces are generated, with one planted failure. Real requests are now traced separately, but the drill itself runs on synthetic data by design.",
         "next": "Run the drill on real traces once enough accumulate."},
        {"area": "Historical eval set (Weeks 4-6)", "severity": "medium",
         "what": "The original dataset targets a removed HR-policy PDF and old chunk ids, so it cannot be scored on the current index. It is kept for the historical record; a 12-question insurance set replaces it for live runs.",
         "next": "Grow the insurance set (aim for 50+) and have a second person verify the answers."},
        {"area": "Judge validation (Week 6)", "severity": "medium",
         "what": f"Judge V1 agreed with the human on {jv.get('judge_v1_agreement_pct', 'n/a')}% of {jv.get('total_cases', 'n/a')} cases; V2 per-case verdicts were not saved and the judge needs Ollama.",
         "next": "Persist per-case verdicts for each judge version and re-measure with Ollama running."},
        {"area": "Prompt-injection defence (Week 8)", "severity": "medium",
         "what": "The scanner is rule-based and off by default; it misses paraphrased or encoded attacks and can quarantine legitimate text.",
         "next": "Enable it in production traffic, log quarantines, and add an LLM-based second check."},
        {"area": "MCP servers (Week 9)", "severity": "medium",
         "what": "The JSON-RPC handshake and tool discovery are real, but the host calls the two bundled servers in-process by module name; the command/args in the MCP config files are never launched. Switching between the bundled configs works; a new external server cannot be added by configuration alone, and the fastmcp SDK is not used.",
         "next": "Spawn configured servers over stdio (or adopt the fastmcp / official MCP SDK client) so a third server really is 'bolt on without touching the agent'."},
        {"area": "Not implemented", "severity": "low",
         "what": "HyDE (Week 4), RAGAS metrics (Week 6), agent memory (Week 7), LiteLLM routing and rate-limit fallbacks (Week 11) are named in the task briefs but not built.",
         "next": "Prioritise by what the demo needs; none block the current flow."},
    ]
    if ins["hybrid"] and ins["reranked"] and ins["reranked"]["hit_rate"] < ins["hybrid"]["hit_rate"]:
        spots.insert(3, {"area": "Reranked mode (Week 4)", "severity": "medium",
                         "what": f"On the 12-question insurance set, reranked hit@3 is {ins['reranked']['hit_rate']:.3f} vs hybrid {ins['hybrid']['hit_rate']:.3f}. The cross-encoder plus MMR step pushed the answer chunk out of the top 3 for several questions.",
                         "next": "Inspect the missed questions on the Evaluation page; try a higher MMR lambda or skip MMR, change one thing, and re-measure."})
    return spots


def demo_script() -> Dict[str, Any]:
    ins = {m: _load(f"insurance_results_{m}.json") for m in ("semantic", "hybrid")}
    improved = None
    if ins["semantic"] and ins["hybrid"]:
        improved = {"metric": "hit-rate@3", "before": ins["semantic"]["hit_rate"], "after": ins["hybrid"]["hit_rate"],
                    "mrr_before": ins["semantic"]["mrr"], "mrr_after": ins["hybrid"]["mrr"],
                    "questions": ins["hybrid"]["num_questions"]}
    return {
        "parts": [
            {"part": "1. A real run", "where": "Search & Q&A",
             "do": "Ask: 'What is the maximum cost for removal of a disabled vehicle after an accident?' Show the answer, its citations and the retrieved chunks.",
             "needs": "Ollama running for the generated answer; retrieval and citations work without it."},
            {"part": "2. A real failure you caught", "where": "Observability > Support Triage Drill",
             "do": "Paste the vague complaint, let the drill find trace tr_drill_exclusion_7701 (approved despite the Section 5.2 flood exclusion), then show the failure-to-test regression now passing.",
             "needs": "Nothing external. State clearly that the drill data is planted."},
            {"part": "3. A number that improved", "where": "Evaluation",
             "do": "Show semantic vs hybrid on the current corpus.", "numbers": improved,
             "needs": "Nothing external. Say the set has only 12 questions."},
            {"part": "4. What is next", "where": "Capstone > Known weak spots",
             "do": "Name the top two weak spots and the first fix you would try.", "needs": "Nothing external."},
        ],
        "tough_questions": [
            "How much does a request cost? (Local models are $0 per token; the traced cost is an illustrative hosted-price equivalent.)",
            "How accurate is it? (Hit@3 on 12 questions; judge agreement on 25 labelled cases; both small.)",
            "What happens when it is wrong? (It refuses when context is missing; scope guard rejects off-topic input; regression cases guard known failures.)",
        ],
    }
