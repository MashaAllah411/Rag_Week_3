"""
ui/views/mcp.py

MCP Ecosystem (Week 9)
- Host, client, server: where the AI runs
- Tool discovery over JSON-RPC (initialize, tools/list) and tool calls (tools/call)
- End-to-end claim triage that uses only discovered tools
- Switching between the two bundled configurations (one server vs both)
"""
import json

import streamlit as st

from ui.api_client import api
from ui.components import call, info_card, page_header, pill, simulated_notice

page_header(
    "MCP Ecosystem",
    "🔌",
    "See how an agent finds and calls tools through the Model Context Protocol instead of having each tool wired in by hand.",
    weeks=("9",),
)
simulated_notice(
    "The JSON-RPC handshake and tool discovery are real, and the host never hard-codes tool names. "
    "The two bundled servers run <b>in-process</b>, selected by module name, and the host calls them directly. "
    "The <code>command</code> and <code>args</code> listed in <code>data/mcp_config*.json</code> are not launched, so an external server "
    "cannot be added by editing the config alone; that needs a small change to the host's <code>connect()</code>. "
    "The triage decisions themselves are scripted."
)

tab_how, tab_servers, tab_test, tab_triage, tab_config = st.tabs([
    "🧭 How it works", "🖥️ Servers & tools", "🧪 Call a tool", "⚡ MCP claim triage", "🔄 Switch config",
])

# ── How it works ─────────────────────────────────────────────
with tab_how:
    st.subheader("Host, client, server: where the AI runs")
    left, right = st.columns([3, 2])
    with left:
        st.graphviz_chart(
            """
            digraph mcp {
              bgcolor="transparent"; fontcolor="#8b95a7"; rankdir=LR; node [shape=box, style="rounded,filled", fontname="Helvetica", fontcolor="#1b2430"]; edge [color="#6b7788", fontcolor="#8b95a7"];
              subgraph cluster_host { label="HOST (your app: the AI runs here)"; style=dashed;
                agent [label="Agent\\n(decides what to do)", fillcolor="#e8f0fe"];
                client [label="MCP client\\n(speaks JSON-RPC)", fillcolor="#eef1f6"];
              }
              subgraph cluster_srv { label="SERVERS (offer tools, no AI)"; style=dashed;
                pol [label="policy-document-server", fillcolor="#e3f6e8"];
                clm [label="claims-platform-server", fillcolor="#e3f6e8"];
              }
              agent -> client [label="use a tool"];
              client -> pol [label="tools/list, tools/call"];
              client -> clm [label="tools/list, tools/call"];
            }
            """
        )
    with right:
        st.markdown(
            "- The **host** is the application that contains the AI. It decides which tool to use.\n"
            "- The **client** inside the host speaks the protocol (JSON-RPC 2.0).\n"
            "- A **server** only offers tools. It has no idea which AI is calling it, and never runs the AI.\n"
            "- On start-up the client asks each server what it offers (`initialize`, then `tools/list`), so the host "
            "**discovers** tools instead of having them hard-coded."
        )
        st.caption("MCP connects an agent to tools. A2A (Multi-Agent Squad page) connects an agent to other agents.")

# ── Servers & tools ──────────────────────────────────────────
with tab_servers:
    st.subheader("Discovered servers and tools")
    ok, servers_info = call(api.get_mcp_servers, spinner="Connecting to MCP servers...")
    if ok:
        c1, c2, c3 = st.columns(3)
        c1.metric("Active config", servers_info.get("active_config", "?").split("/")[-1].split("\\")[-1])
        c2.metric("Servers connected", servers_info.get("servers_count"))
        c3.metric("Tools discovered", servers_info.get("total_tools_count"))

        for s in servers_info.get("servers", []):
            with st.container(border=True):
                s_info = s.get("server_info", {})
                st.markdown(f"#### 🖥️ `{s.get('name')}`")
                st.caption(f"Reported by the server at handshake: {s_info.get('name')} v{s_info.get('version')}  ·  "
                           f"{s.get('tools_count')} tools  ·  runs in-process")
                st.caption(f"Declared in config (not launched): `{s.get('command')} {' '.join(s.get('args', []))}`")
                for t in s.get("tools", []):
                    with st.expander(f"🛠️ `{t.get('name')}`: {t.get('description')}"):
                        st.json(t.get("inputSchema", {}))
                with st.expander("The tools/list exchange for this server"):
                    st.caption("The request shape is the standard MCP method. The result is the tool list this server returned (ids are illustrative).")
                    st.code(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}, indent=2), language="json")
                    st.code(json.dumps({"jsonrpc": "2.0", "id": 2, "result": {"tools": s.get("tools", [])}}, indent=2), language="json")

# ── Call a tool ──────────────────────────────────────────────
with tab_test:
    st.subheader("Call a discovered tool")
    ok, servers_info = call(api.get_mcp_servers, spinner="Loading tools...")
    tools = (servers_info or {}).get("discovered_tools", []) if ok else []
    if tools:
        names = [t["name"] for t in tools]
        selected = st.selectbox("Tool", names)
        meta = next(t for t in tools if t["name"] == selected)
        st.caption(meta.get("description", ""))

        defaults = {"claim_id": "CLM-7002", "query": "flood rising water exclusion", "clause_id": "Section 5.2"}
        props = meta.get("inputSchema", {}).get("properties", {})
        default_args = {k: defaults.get(k, "") for k in props}
        args_str = st.text_area("Arguments (JSON)", value=json.dumps(default_args, indent=2), height=120, key=f"mcp_args_{selected}")

        if st.button("📡 Send tools/call", type="primary"):
            try:
                parsed = json.loads(args_str)
            except json.JSONDecodeError:
                st.error("The arguments are not valid JSON. Check quotes and commas.")
            else:
                ok, res = call(api.call_mcp_tool, selected, parsed, spinner=f"Calling {selected}...")
                if ok:
                    st.markdown("**Request**")
                    st.code(json.dumps({"jsonrpc": "2.0", "method": "tools/call", "params": {"name": selected, "arguments": parsed}}, indent=2), language="json")
                    st.markdown("**Response**")
                    if res.get("success"):
                        st.markdown(pill("Call succeeded", "ok"), unsafe_allow_html=True)
                        st.json(res.get("data"))
                    else:
                        st.markdown(pill("Tool returned an error", "bad"), unsafe_allow_html=True)
                        st.error(res.get("error"))
                        st.caption("Tools return errors as data the agent can read and recover from, instead of crashing.")
    elif ok:
        st.warning("No tools were discovered.")

# ── MCP claim triage ─────────────────────────────────────────
with tab_triage:
    st.subheader("Claim triage using only discovered tools")
    st.markdown("The host fetches claim status, reads adjuster notes, checks policy exclusions and settles, calling each step through MCP.")
    ok, claims = call(api.list_claims, spinner="Loading claims...")
    ids = [c["claim_id"] for c in claims.get("claims", [])] if ok else ["CLM-7001", "CLM-7002"]
    claim_id = st.selectbox("Claim", ids, index=min(1, len(ids) - 1), help="CLM-7002 and CLM-7007 hit policy exclusions.")

    if st.button("⚡ Run MCP triage", type="primary"):
        ok, res = call(api.run_mcp_triage, claim_id, spinner="Running triage across MCP servers...")
        if ok:
            st.session_state["mcp_triage"] = res

    res = st.session_state.get("mcp_triage")
    if res:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Final status", res.get("final_status"))
        m2.metric("Payable", f"${res.get('payable_amount', 0.0):,.2f}")
        m3.metric("Tools discovered", res.get("discovered_tools_count"))
        m4.metric("Latency", f"{res.get('latency_seconds', 0.0):.4f}s")
        st.write(f"Policy exclusion verified: `{res.get('policy_verified')}`  ·  Servers: `{', '.join(res.get('connected_servers', []))}`")
        st.write("Tools called: " + " → ".join(f"`{t}`" for t in res.get("tools_called", [])))
        with st.expander("Execution trace", expanded=True):
            for step in res.get("trace_log", []):
                st.write(f"- {step}")

# ── Switch config ────────────────────────────────────────────
with tab_config:
    st.subheader("Switch between the bundled configurations")
    st.markdown(
        "Both configuration files ship with the app: one lists a single server, the other lists both. Switching re-runs "
        "discovery, so you can watch the host find more tools without any change to the agent's code."
    )
    info_card("This swaps between the two bundled servers only. Adding a third, external server would also need a small change "
              "to the host's <code>connect()</code>, because the config's launch command is not executed.")
    ok, current = call(api.get_mcp_servers, spinner="Reading current configuration...", show_error=False)
    active = (current or {}).get("active_config", "") if ok else ""
    options = {"mcp_config.json": "Both servers (policy + claims)", "mcp_config_server1.json": "One server (policy only)"}
    # A stable key, seeded once from the active config. A changing default index would make Streamlit
    # treat the radio as a new widget after every Apply and snap the choice back.
    if "mcp_cfg_choice" not in st.session_state:
        st.session_state["mcp_cfg_choice"] = "mcp_config_server1.json" if "server1" in active else "mcp_config.json"
    choice = st.radio("Configuration", list(options), key="mcp_cfg_choice", format_func=lambda k: f"{k}: {options[k]}")

    if st.button("🔄 Apply configuration"):
        ok, res = call(api.switch_mcp_config, choice, spinner="Re-initialising the MCP host...")
        if ok:
            st.success(f"Switched to `{choice}`: {res.get('total_tools_count')} tools discovered across {res.get('servers_count')} server(s).")
            st.cache_data.clear()
