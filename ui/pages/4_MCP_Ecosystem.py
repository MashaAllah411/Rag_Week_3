"""
ui/pages/4_MCP_Ecosystem.py

Page 4: Model Context Protocol (MCP) Ecosystem (Week 9)
- Connected MCP Servers (Policy Server, Claims Server)
- Dynamically discovered tools via JSON-RPC 2.0
- Interactive tool execution
- End-to-end claim triage over MCP
- Dynamic MCP configuration file switching
"""
import json
import streamlit as st
from ui.api_client import api

st.set_page_config(page_title="MCP Ecosystem — Insurance RAG", page_icon="🔌", layout="wide")

st.title("🔌 Model Context Protocol (MCP) Ecosystem")
st.markdown(
    "Explore the MCP standard (JSON-RPC 2.0) powering dynamic tool discovery across decoupled servers. "
    "The host agent code never changes when new servers are bolted on."
)

tab_servers, tab_test_tool, tab_triage, tab_config = st.tabs([
    "🖥️ Connected Servers & Tools",
    "🧪 Test Discovered Tools",
    "⚡ MCP Claim Triage",
    "🔄 Switch MCP Config"
])

# ── Tab 1: Connected Servers & Tools ─────────────────────────
with tab_servers:
    st.subheader("Discovered MCP Servers & Tool Registry")

    try:
        servers_info = api.get_mcp_servers()
        st.info(f"Active Configuration: `{servers_info.get('active_config')}` | "
                f"Connected Servers: **{servers_info.get('servers_count')}** | "
                f"Discovered Tools: **{servers_info.get('total_tools_count')}**")

        for s in servers_info.get("servers", []):
            with st.container(border=True):
                st.markdown(f"### 🖥️ `{s.get('name')}`")
                s_info = s.get("server_info", {})
                st.caption(f"Server Implementation: {s_info.get('name')} v{s_info.get('version')} | Tools exposed: {s.get('tools_count')}")

                st.markdown("**Discovered Tools:**")
                for t in s.get("tools", []):
                    with st.expander(f"🛠️ `{t.get('name')}`: {t.get('description')}"):
                        st.json(t.get("inputSchema", {}))

    except Exception as e:
        st.error(f"Failed to load MCP servers: {e}")

# ── Tab 2: Test Discovered Tools ─────────────────────────────
with tab_test_tool:
    st.subheader("Execute Discovered Tool via JSON-RPC")

    try:
        servers_info = api.get_mcp_servers()
        tools = servers_info.get("discovered_tools", [])
        tool_names = [t["name"] for t in tools]

        if tool_names:
            selected_tname = st.selectbox("Select Tool to Call", tool_names)
            tool_meta = next(t for t in tools if t["name"] == selected_tname)
            st.caption(tool_meta.get("description", ""))

            # Default parameters
            default_args = {}
            if selected_tname in ["get_claim_status", "get_adjuster_notes"]:
                default_args = {"claim_id": "CLM-7002"}
            elif selected_tname == "search_policy":
                default_args = {"query": "flood rising water exclusion"}
            elif selected_tname == "get_policy_clause":
                default_args = {"clause_id": "Section 5.2"}

            args_str = st.text_area("Arguments (JSON)", value=json.dumps(default_args, indent=2), height=120)

            if st.button("📡 Send JSON-RPC tools/call", type="primary"):
                try:
                    parsed_args = json.loads(args_str)
                    with st.spinner(f"Calling `{selected_tname}`..."):
                        call_res = api.call_mcp_tool(selected_tname, parsed_args)
                        st.markdown("#### Tool Response")
                        if call_res.get("success"):
                            st.success("JSON-RPC Call Successful")
                            st.json(call_res.get("data"))
                        else:
                            st.error(f"Tool Error: {call_res.get('error')}")
                except json.JSONDecodeError:
                    st.error("Invalid JSON format in arguments.")
                except Exception as e:
                    st.error(f"Execution failed: {e}")
        else:
            st.warning("No tools discovered.")
    except Exception as e:
        st.error(f"Error: {e}")

# ── Tab 3: MCP Claim Triage ──────────────────────────────────
with tab_triage:
    st.subheader("End-to-End Triage via MCP Servers")
    st.markdown("Host agent dynamically uses MCP tools to fetch status, read adjuster notes, verify exclusions, and settle.")

    claim_to_triage = st.selectbox("Select Claim for MCP Triage", ["CLM-7001", "CLM-7002", "CLM-7003", "CLM-7007", "CLM-7010"], index=1)

    if st.button("⚡ Run MCP Triage", type="primary"):
        with st.spinner("Running triage across MCP servers..."):
            try:
                res = api.run_mcp_triage(claim_to_triage)
                st.markdown("---")
                m1, m2, m3 = st.columns(3)
                m1.metric("Final Status", res.get("final_status"))
                m2.metric("Payable Amount", f"${res.get('payable_amount', 0.0):,.2f}")
                m3.metric("Latency", f"{res.get('latency_seconds', 0.0):.4f}s")

                st.write(f"**Policy Exclusion Verified**: `{res.get('policy_verified')}`")
                st.write(f"**Tools Called**: `{', '.join(res.get('tools_called', []))}`")

                st.markdown("#### Execution Trace Log")
                for step in res.get("trace_log", []):
                    st.write(f"- {step}")
            except Exception as e:
                st.error(f"Triage failed: {e}")

# ── Tab 4: Switch MCP Config ─────────────────────────────────
with tab_config:
    st.subheader("Dynamic Configuration Swap")
    st.markdown("Demonstrate zero-code-change server addition by swapping between single-server and dual-server configuration files.")

    config_choice = st.radio("Active Config File", ["mcp_config.json (2 Servers)", "mcp_config_server1.json (1 Server)"], index=0)
    target_cfg = "mcp_config.json" if "mcp_config.json" in config_choice else "mcp_config_server1.json"

    if st.button("🔄 Apply Configuration"):
        with st.spinner("Re-initializing MCP host agent..."):
            try:
                switch_res = api.switch_mcp_config(target_cfg)
                st.success(f"Switched to `{target_cfg}`. Discovered {switch_res.get('total_tools_count')} tools across {switch_res.get('servers_count')} servers.")
                st.rerun()
            except Exception as e:
                st.error(f"Failed to switch configuration: {e}")
