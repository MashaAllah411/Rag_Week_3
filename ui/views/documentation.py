"""
ui/views/documentation.py

Documentation: how the app works, for the person using it (not the developer).
Sections: How it works (diagrams) · Pages guide · How do I... · Real vs simulated · Glossary
"""
import streamlit as st

from ui.components import info_card, page_header, pill

page_header(
    "Documentation",
    "📖",
    "How the app works, what each page is for, and step-by-step walkthroughs for the things you will actually want to do.",
    weeks=("1-12",),
)

# ── Diagrams (Graphviz DOT, rendered inline) ─────────────────

INGEST_DOT = """
digraph ingest {
  bgcolor="transparent"; fontcolor="#8b95a7"; rankdir=TB; fontname="Helvetica"; nodesep=0.3; ranksep=0.4;
  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=13, fillcolor="#eef1f6", color="#9aa7b8", fontcolor="#1b2430"];
  edge [fontname="Helvetica", fontsize=11, color="#6b7788", fontcolor="#8b95a7"];
  upload [label="Upload a PDF"];
  read   [label="Read the text\\n(+ OCR for text inside images)"];
  chunk  [label="Split into chunks"];
  embed  [label="Turn each chunk into numbers\\n(an embedding of its meaning)"];
  store  [label="ChromaDB\\nvector index", fillcolor="#e3f6e8"];
  bm25   [label="BM25\\nkeyword index", fillcolor="#e3f6e8"];
  upload -> read -> chunk -> embed -> store;
  chunk -> bm25;
}
"""

ASK_DOT = """
digraph ask {
  bgcolor="transparent"; fontcolor="#8b95a7"; rankdir=TB; fontname="Helvetica"; nodesep=0.3; ranksep=0.35;
  node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=13, fillcolor="#eef1f6", color="#9aa7b8", fontcolor="#1b2430"];
  edge [fontname="Helvetica", fontsize=11, color="#6b7788", fontcolor="#8b95a7"];
  q       [label="Your question"];
  scope   [label="Scope guard\\n(is it about insurance?)"];
  rewrite [label="Query rewrite\\n(optional, uses the LLM)"];
  retr    [label="Retrieval: semantic | hybrid | reranked", fillcolor="#e8f0fe"];
  store   [label="ChromaDB index\\n(meaning)", fillcolor="#e3f6e8"];
  bm25    [label="BM25 index\\n(exact words)", fillcolor="#e3f6e8"];
  scan    [label="Injection scan (optional)"];
  llm     [label="LLM answers using\\nonly the retrieved chunks"];
  resp    [label="Answer with citations\\nor 'I don't know'", fillcolor="#e3f6e8"];
  trace   [label="Trace: one span per step\\n(OpenTelemetry)", fillcolor="#fff3d6"];
  q -> scope -> rewrite -> retr -> scan -> llm -> resp;
  store -> retr; bm25 -> retr;
  resp -> trace [style=dashed];
}
"""

AGENT_DOT = """
digraph agents {
  bgcolor="transparent"; fontcolor="#8b95a7"; rankdir=LR; fontname="Helvetica"; nodesep=0.3; ranksep=0.5;
  node [shape=box, style="rounded,filled", fontname="Helvetica", fillcolor="#eef1f6", color="#9aa7b8", fontcolor="#1b2430"];
  edge [fontname="Helvetica", fontsize=10, color="#6b7788", fontcolor="#8b95a7"];

  claim [label="A claim"];
  subgraph cluster_single {
    label="Agent loop (Weeks 7-8)"; fontname="Helvetica"; style=dashed; color="#9aa7b8";
    agent  [label="Agent loop\\nstops at 4 budgets", fillcolor="#e8f0fe"];
    mcp    [label="MCP client\\n(JSON-RPC)"];
    tools  [label="Tools: get claim,\\nsearch policy, compute payout", fillcolor="#e3f6e8"];
    agent -> mcp -> tools;
  }
  subgraph cluster_squad {
    label="Squad (Week 10)"; fontname="Helvetica"; style=dashed; color="#9aa7b8";
    mgr  [label="Manager", fillcolor="#e8f0fe"];
    pol  [label="Policy specialist", fillcolor="#e3f6e8"];
    pay  [label="Payout specialist", fillcolor="#e3f6e8"];
    mgr -> pol [label="A2A task"];
    mgr -> pay [label="A2A task"];
  }
  decision [label="Decision + audit trail", fillcolor="#fff3d6"];
  claim -> agent; claim -> mgr;
  tools -> decision; pol -> decision; pay -> decision;
}
"""

EVAL_DOT = """
digraph evalloop {
  bgcolor="transparent"; fontcolor="#8b95a7"; rankdir=LR; fontname="Helvetica"; nodesep=0.3; ranksep=0.4;
  node [shape=box, style="rounded,filled", fontname="Helvetica", fillcolor="#eef1f6", color="#9aa7b8", fontcolor="#1b2430"];
  edge [fontname="Helvetica", fontsize=10, color="#6b7788", fontcolor="#8b95a7"];
  sample  [label="Sample ~20\\nreal traces"];
  notes   [label="Write one honest\\nnote per trace"];
  tax     [label="Group notes into\\nnamed problems"];
  rank    [label="Rank by how often\\nx how bad"];
  predict [label="Write a prediction,\\nthen change ONE thing", fillcolor="#e8f0fe"];
  evalrun [label="Evaluate before\\nand after", fillcolor="#e3f6e8"];
  regress [label="Failure becomes a\\npermanent regression test", fillcolor="#fff3d6"];
  sample -> notes -> tax -> rank -> predict -> evalrun -> regress;
  regress -> sample [style=dashed, label="repeat"];
}
"""


def _link(path: str, label: str, icon: str = "") -> None:
    """A link to another page; falls back to plain text if the page is not registered."""
    try:
        st.page_link(path, label=label, icon=icon or None)
    except Exception:
        st.markdown(f"**{icon} {label}**")


info_card("<b>New here?</b> 1) Open <b>Documents</b> and check a policy is indexed. 2) Ask a question on <b>Search &amp; Q&amp;A</b>. "
          "3) Read the <b>citations</b> under the answer to confirm where it came from. The rest of this page explains everything else.")

tab_flow, tab_pages, tab_how, tab_real, tab_gloss = st.tabs(
    ["🧭 How it works", "🗂️ Pages guide", "🙋 How do I...", "🔎 Real vs simulated", "📚 Glossary"])

# ── How it works ─────────────────────────────────────────────
with tab_flow:
    st.subheader("From PDF to answer")
    st.markdown("A document is prepared **once**. After that, every question follows the same path, and each step is recorded so you can inspect it later.")
    left, right = st.columns(2)
    with left:
        st.markdown("**1. Adding a document** (once per PDF)")
        st.graphviz_chart(INGEST_DOT, width="stretch")
    with right:
        st.markdown("**2. Answering a question** (every time)")
        st.graphviz_chart(ASK_DOT, width="stretch")
    st.markdown(
        "- **Chunks, not whole documents.** The model can only read so much at once, so documents are cut into small pieces and only the best-matching pieces are shown to it.\n"
        "- **Two ways to find the right piece.** *Meaning* search (embeddings) finds text that says the same thing in different words. "
        "*Keyword* search (BM25) finds exact terms such as a clause number. *Hybrid* uses both; *reranked* adds a second, slower check.\n"
        "- **Grounded answers.** The model is told to answer only from those pieces and to say it doesn't know otherwise. "
        "The pieces it used are shown as citations so you can check them."
    )

    st.subheader("Agents, tools and teams")
    st.graphviz_chart(AGENT_DOT, width="stretch")
    st.markdown(
        "An **agent loop** works step by step with limits on steps, tokens, cost and time so it cannot run forever. "
        "**MCP** is the standard way an agent finds and calls tools. **A2A** is the standard way one agent hands work to another."
    )

    st.subheader("How problems get found and fixed")
    st.graphviz_chart(EVAL_DOT, width="stretch")
    st.markdown("Read real answers, name the problems, fix the worst one with a single change, **measure** before and after, and keep every real failure as a test so it cannot return unnoticed.")

# ── Pages guide ──────────────────────────────────────────────
PAGES = [
    ("Start", [
        ("views/home.py", "🏠", "Home", "Overview and live status of the main components.", "Start of a session, to check everything is up.", "1-12"),
        ("views/documentation.py", "📖", "Documentation", "This page.", "Whenever you are unsure what something means or how to do it.", "12"),
    ]),
    ("Learn & Guardrails", [
        ("views/foundations.py", "🧪", "Foundations Lab", "Hands-on tokens, cost, sampling settings and embeddings.", "To see why wording, length and settings change cost and answers.", "1"),
        ("views/guardrails.py", "🛡️", "Guardrails & Security", "Fixed-format answers with validation and retry, the scope guard, prompt-injection scanning and tool permissions.", "To test how the app behaves with bad input or a poisoned document.", "2, 8"),
    ]),
    ("Documents & Answers", [
        ("views/documents.py", "📄", "Documents", "Upload, list and delete policies; inspect chunks and compare chunk sizes.", "Before asking questions, or when a document is added or changed.", "3"),
        ("views/search_qa.py", "🔍", "Search & Q&A", "Ask a question and see the answer, its citations and the retrieved chunks.", "To get an answer and check where it came from.", "3, 4"),
    ]),
    ("Evaluate", [
        ("views/evaluation.py", "🎯", "Evaluation", "Retrieval scores (hit-rate, MRR), assertions, the judge and its agreement with a human, and the failure-to-test loop.", "To prove a change helped, with a number.", "4, 6, 11"),
        ("views/error_analysis.py", "🔬", "Error Analysis", "Read a fair sample of real traces, write notes, group and rank the problems.", "To decide what to fix next from evidence.", "5"),
    ]),
    ("Agents", [
        ("views/agent_triage.py", "🤖", "Agent Triage", "Run a claim through the agent loop or a fixed workflow; see budgets, steps and trajectory scores; race them.", "To see how an agent stops safely and which design to ship.", "7, 8"),
        ("views/mcp.py", "🔌", "MCP Ecosystem", "See tools discovered over JSON-RPC, call them, and switch configurations.", "To understand how an agent finds tools.", "9"),
        ("views/multi_agent.py", "👥", "Multi-Agent Squad", "A manager and two specialists, the message audit trail, and a race against a single agent.", "To compare a team with one agent on quality, speed, tokens and cost.", "10"),
    ]),
    ("Production", [
        ("views/observability.py", "📊", "Observability", "Request traces by step, OpenTelemetry export, replay, the support drill and the cache benchmark.", "When an answer looks wrong, or to see what a request cost.", "5, 11"),
    ]),
    ("Capstone", [
        ("views/capstone.py", "🏁", "Capstone", "Run the full suite, read the known weak spots, and prepare an honest four-part demo.", "Before presenting or handing the app to someone else.", "12"),
    ]),
    ("System", [
        ("views/system.py", "⚙️", "System & Health", "Which tools are really active, a self-test, settings (secrets hidden) and logs.", "When something does not work.", "11, 12"),
    ]),
]

with tab_pages:
    st.subheader("What each page is for")
    for group, entries in PAGES:
        st.markdown(f"##### {group}")
        cols = st.columns(2)
        for i, (path, icon, title, what, when, weeks) in enumerate(entries):
            with cols[i % 2]:
                with st.container(border=True):
                    _link(path, title, icon)
                    st.write(what)
                    st.caption(f"Use it when: {when}")
                    st.markdown(pill(f"Week {weeks}", "week"), unsafe_allow_html=True)

# ── How do I... ──────────────────────────────────────────────
HOWTO = [
    ("Upload a policy", [
        "Open **Documents** and choose the upload tab.",
        "Pick a PDF (up to 20 MB). Names must be new; an existing name is refused.",
        "Wait for indexing to finish. It runs in the background, so refresh the library after a few seconds.",
        "Go to **Search & Q&A** and, if you like, set *Target document* to your new file so answers come only from it.",
    ]),
    ("Ask a claims or policy question and read the citations", [
        "Open **Search & Q&A** and type a question in plain words, or pick a suggested one.",
        "Leave the mode on *hybrid* to start. It finds both meaning and exact terms.",
        "Read the answer, then open the retrieved chunks underneath. Each shows its source and score.",
        "Check that the answer's key facts (an amount, a day count, a clause) appear in those chunks.",
    ]),
    ("Tell whether an answer is trustworthy", [
        "Look at the **confidence** badge, but do not rely on it alone.",
        "Open the chunks and confirm the answer is supported by the quoted text, not just similar to it.",
        "If it says it doesn't know, that is a good sign: the documents do not contain the answer.",
        "Answer text needs the local LLM (Ollama). Without it you still see the retrieved chunks, which are the evidence.",
    ]),
    ("Compare chunk sizes", [
        "Open **Documents** and go to the chunk inspector / comparison.",
        "Enter a question and the exact phrase that answers it, and choose several sizes.",
        "Read the table: the best size keeps the answer in one chunk and ranks it near the top.",
        "Too small splits the answer; too large buries it among other text.",
    ]),
    ("Run an evaluation and read hit-rate and MRR", [
        "Open **Evaluation** and run the evaluation for *semantic*, then *hybrid*.",
        "**Hit-rate@3** is the share of questions where a chunk containing the answer was in the top 3.",
        "**MRR** rewards putting the right chunk first: 1.0 means always first, 0.5 means typically second.",
        "Look at which questions missed. A change that helps some questions can hurt others.",
        "The question set is small, so treat a one-question difference as noise.",
    ]),
    ("Read 20 traces and rank the problems (error analysis)", [
        "Open **Error Analysis** and load the sample (it is random but repeatable, so it is not cherry-picked).",
        "For each trace write one honest sentence about what went wrong, **before** thinking about categories.",
        "Then group your notes into a few named problems and give each a severity.",
        "The page ranks problems by how often they happen times how bad they are. Fix the top one first.",
        "Write down what you expect to happen before you change anything.",
    ]),
    ("Run claim triage", [
        "Open **Agent Triage**, pick a claim and choose the agent loop or the fixed workflow.",
        "Press run and read the payout decision, then the execution log.",
        "Use the stress-test dropdown to force a budget to fire and watch the agent stop cleanly.",
        "Try *Compare both* to see the two side by side.",
    ]),
    ("Inspect a trace and its spans", [
        "Open **Observability** and the *Request traces* tab. Choose *Real app requests*.",
        "Pick a trace. The table shows each step with its time, tokens and cost.",
        "If there are no real requests yet, ask a question on Search & Q&A first.",
        "Token counts are estimates and cost is an illustrative price, since the models run locally.",
    ]),
    ("Replay a trace", [
        "Open **Observability**, then *Trace replay*.",
        "Choose a saved trace. It re-runs the generation using only the context stored in that trace.",
        "Compare the original and replayed answers. This needs the local LLM (Ollama).",
    ]),
    ("Find the bad answer in the support drill", [
        "Open **Observability**, then *Support drill*.",
        "Describe the complaint in your own words, such as a flood claim that was approved.",
        "The drill searches 100 generated traces and points to the exact request, the faulty step, the root cause and a fix.",
        "The data is staged with one planted failure, so the drill tells you whether it found the planted trace.",
    ]),
    ("Test prompt injection", [
        "Open **Guardrails & Security** and the injection section.",
        "Scan the sample poisoned text, then paste your own hidden instruction such as 'ignore all previous instructions'.",
        "See which rules fire. You can also scan the chunks retrieved for a real question.",
        "On **Search & Q&A** you can turn on the injection scan so flagged chunks are removed before the model reads them.",
        "It is a first line of defence only: rewording or encoding can slip past it.",
    ]),
    ("Validate the judge", [
        "Open **Evaluation** and the judge section.",
        "A judge is an AI that grades answers. Before trusting its number, check how often it agrees with a human who graded the same cases.",
        "If agreement is low, do not use its scores to claim an improvement.",
        "Running the judge live needs the local LLM (Ollama).",
    ]),
    ("Run the full suite", [
        "Open **Capstone** and press *Run the full suite*.",
        "Read each line. **Passed** ran and succeeded; **Failed** ran and did not; **Skipped** did not run because something was not available, usually Ollama.",
        "A skipped line is not a pass. Start the missing component and run again.",
    ]),
]

with tab_how:
    st.subheader("Step-by-step walkthroughs")
    for title, steps in HOWTO:
        with st.expander(title):
            for n, step in enumerate(steps, start=1):
                st.markdown(f"{n}. {step}")

# ── Real vs simulated ────────────────────────────────────────
with tab_real:
    st.subheader("What is real, what is simulated, what needs the LLM")
    st.markdown("Know which results to trust as measurements and which only demonstrate a mechanism.")

    st.markdown(pill("LIVE: measured or computed for real", "ok"), unsafe_allow_html=True)
    st.dataframe([
        {"Capability": "Retrieval (semantic, BM25, hybrid, reranked, MMR)", "What that means": "Runs on the actual indexed documents every time."},
        {"Capability": "Embeddings and ChromaDB vector store", "What that means": "Open-source model and a local, persistent index. No account or key."},
        {"Capability": "OCR", "What that means": "Tesseract reads text inside images in PDFs."},
        {"Capability": "Request tracing and OpenTelemetry export", "What that means": "Real spans per step, exported by the real SDK."},
        {"Capability": "Evaluation scores (hit-rate, MRR)", "What that means": "Computed live, on a small question set."},
        {"Capability": "Regression cases, structured-output validation, injection scan", "What that means": "Deterministic checks that really run."},
        {"Capability": "Agent budgets, stop conditions, trajectory scoring", "What that means": "The limits and the scoring are real, even though the plan they apply to is scripted."},
        {"Capability": "MCP: JSON-RPC handshake and tool discovery", "What that means": "Real protocol messages. The two bundled servers run in-process and are chosen by module name; the config's launch command is not executed, so an external server needs a small change to the host's connect()."},
        {"Capability": "A2A: message envelopes and audit trail", "What that means": "Real message records for every hand-off."},
        {"Capability": "Token counter and cost calculator (Foundations Lab)", "What that means": "Computed from a real tokenizer and the prices you enter."},
    ], hide_index=True, width="stretch")

    st.markdown(pill("SIMULATED or SCRIPTED: demonstrates a mechanism", "sim"), unsafe_allow_html=True)
    st.dataframe([
        {"Capability": "The agent's plan", "What that means": "A fixed step order (get claim, search policy, compute payout). No LLM chooses the next step."},
        {"Capability": "Squad decisions", "What that means": "Scripted rules in the specialists. The messages between them are real."},
        {"Capability": "Token and cost figures for agents and traces", "What that means": "Estimates (about 4 characters per token) priced at illustrative hosted rates; local models actually cost $0 per token."},
        {"Capability": "Support-drill traces", "What that means": "Generated, with one planted failure."},
        {"Capability": "Semantic-cache benchmark", "What that means": "Simulated latency and a fixed 650-token cost per query. The % saving shows the mechanism, not measured savings."},
    ], hide_index=True, width="stretch")

    st.markdown(pill("NEEDS OLLAMA (the local LLM)", "warn"), unsafe_allow_html=True)
    st.dataframe([
        {"Capability": "Answer text on Search & Q&A", "What that means": "Without Ollama you still get the retrieved chunks and citations, but not a written answer."},
        {"Capability": "Query rewriting", "What that means": "Skipped automatically if the LLM is unavailable."},
        {"Capability": "Trace replay", "What that means": "Re-generates the answer, so it needs the LLM."},
        {"Capability": "LLM judge", "What that means": "Grading needs the LLM."},
        {"Capability": "Live structured-output generation", "What that means": "Pasting a reply to validate works without it."},
        {"Capability": "Scope guard on ambiguous questions", "What that means": "Obvious cases are decided without the LLM; if it is down, ambiguous questions are allowed through."},
    ], hide_index=True, width="stretch")
    info_card("The System &amp; Health page shows live whether Ollama and every other tool is reachable, and can run a self-test.")
    _link("views/system.py", "Open System & Health", "⚙️")

# ── Glossary ─────────────────────────────────────────────────
GLOSSARY = [
    ("Token", "A chunk of text, roughly part of a word. Models read and are priced in tokens."),
    ("Context window", "How much text a model can read at once. Longer prompts use more of it."),
    ("Temperature", "A setting that makes the same question give more varied answers when higher, and more repeatable ones when lower."),
    ("Embedding", "A list of numbers that captures the meaning of a piece of text, so similar meanings can be matched."),
    ("Chunk", "A small piece of a document. Search works on chunks, not whole files."),
    ("Vector store", "A database of embeddings that finds the closest matches quickly. Here it is ChromaDB."),
    ("BM25", "Classic keyword search. It scores chunks by how well they match the exact words in the question."),
    ("Hybrid search", "Using meaning search and keyword search together so you catch both paraphrases and exact terms."),
    ("RRF (reciprocal rank fusion)", "The simple rule used to merge two ranked lists: items ranked high in either list rise."),
    ("Reranker", "A second, slower model that re-orders the top results by reading the question and each chunk together."),
    ("MMR", "A step that avoids returning several near-identical chunks by favouring variety."),
    ("Hit-rate@k", "The share of questions where a chunk containing the answer appeared in the top k results."),
    ("MRR", "Mean reciprocal rank: rewards ranking the right chunk first. 1.0 is always first."),
    ("Citation", "The chunk an answer relied on, shown so you can check the claim yourself."),
    ("Trace", "A full record of one request: the question, what was fetched, the answer and the steps taken."),
    ("Span", "One timed step inside a trace, such as retrieval or generation, with its own duration, tokens and cost."),
    ("OpenTelemetry", "An open standard for recording traces, so they can be sent to many tools."),
    ("Budget", "A hard limit on an agent: steps, tokens, cost or time. When one is hit the agent stops."),
    ("Trajectory", "The path an agent took, as opposed to just its final answer."),
    ("MCP", "Model Context Protocol: a standard way for an AI application to discover and call tools."),
    ("A2A", "Agent-to-Agent: a standard way for one agent to hand work to another."),
    ("Prompt injection", "Hidden instructions inside text the AI reads, trying to make it do something it should not."),
    ("LLM judge", "An AI used to grade another AI's answer. It must be checked against a human before it is trusted."),
    ("Regression test", "A test created from a real failure so the same mistake cannot quietly return."),
]

with tab_gloss:
    st.subheader("Glossary")
    query = st.text_input("Search terms", placeholder="e.g. chunk, trace, budget").strip().lower()
    shown = [(t, d) for t, d in GLOSSARY if not query or query in t.lower() or query in d.lower()]
    if not shown:
        st.info("No terms match that search.")
    for term, meaning in shown:
        st.markdown(f"**{term}**: {meaning}")
