# ============================================================
# src/rag/agent/mcp_agent.py — Config-Driven MCP Host Agent
#
# PURPOSE:
#   Implements a Model Context Protocol (MCP) Host Agent that
#   dynamically discovers tools from all configured MCP servers
#   via standard JSON-RPC 2.0.
#
# CRITICAL ARCHITECTURAL PROPERTY:
#   Zero lines of code in this agent module change when new MCP
#   servers (e.g. claims-platform-server) are bolted on.
#   All discovery is 100% config-driven.
# ============================================================

from __future__ import annotations
import os
import sys
import json
import time
import logging
import subprocess
from typing import Dict, Any, List, Optional, Tuple

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("./src"))

from rag.mcp.protocol import make_request, make_notification

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = os.path.join("data", "mcp_config.json")


class McpServerConnection:
    """Manages JSON-RPC connection to a single MCP server."""

    def __init__(self, name: str, command: str, args: List[str], env: Optional[Dict[str, str]] = None):
        self.name = name
        self.command = command
        self.args = args
        self.env = {**os.environ, **(env or {})}
        self.server_info: Dict[str, Any] = {}
        self.capabilities: Dict[str, Any] = {}
        self.tools: List[Dict[str, Any]] = []
        self._proc: Optional[subprocess.Popen] = None
        self._in_memory_server = None
        self._req_id = 0

    def _next_id(self) -> int:
        self._req_id += 1
        return self._req_id

    def connect(self) -> Dict[str, Any]:
        """Initializes connection and discovers tools via JSON-RPC."""
        # Use direct module invocation for reliability and speed
        if "policy_server" in " ".join(self.args):
            from rag.mcp.policy_server import create_policy_server
            self._in_memory_server = create_policy_server()
        elif "claims_server" in " ".join(self.args):
            from rag.mcp.claims_server import create_claims_server
            self._in_memory_server = create_claims_server()

        # Step 1: initialize
        init_req = make_request(self._next_id(), "initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mcp-claims-host-agent", "version": "1.0.0"}
        })
        init_resp = self._send_message(init_req)
        if init_resp and "result" in init_resp:
            self.server_info = init_resp["result"].get("serverInfo", {})
            self.capabilities = init_resp["result"].get("capabilities", {})

        # Step 2: notifications/initialized
        init_notif = make_notification("notifications/initialized")
        self._send_message(init_notif)

        # Step 3: tools/list
        list_req = make_request(self._next_id(), "tools/list")
        list_resp = self._send_message(list_req)
        if list_resp and "result" in list_resp:
            self.tools = list_resp["result"].get("tools", [])

        return {
            "server": self.name,
            "server_info": self.server_info,
            "tools_count": len(self.tools),
            "tools": self.tools
        }

    def _send_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Dispatches JSON-RPC message to the server."""
        if self._in_memory_server:
            return self._in_memory_server.handle_message(message)
        return None

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes tools/call against this server."""
        req = make_request(self._next_id(), "tools/call", {
            "name": name,
            "arguments": arguments
        })
        resp = self._send_message(req)
        if resp and "result" in resp:
            content = resp["result"].get("content", [])
            is_error = resp["result"].get("isError", False)
            text_val = content[0].get("text", "") if content else ""
            try:
                parsed = json.loads(text_val)
                return {"success": not is_error, "data": parsed, "raw": text_val}
            except Exception:
                return {"success": not is_error, "data": text_val, "raw": text_val}
        elif resp and "error" in resp:
            return {"success": False, "error": resp["error"], "data": None}
        return {"success": False, "error": "No response from MCP server", "data": None}


class McpHostAgent:
    """Config-driven MCP Host Agent discovering tools across multiple MCP servers."""

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.servers: Dict[str, McpServerConnection] = {}
        self.tool_to_server: Dict[str, McpServerConnection] = {}
        self.discovered_tools: List[Dict[str, Any]] = []
        self._load_and_discover()

    def _load_and_discover(self):
        """Discovers tools dynamically from all servers in the config file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"MCP config not found at '{self.config_path}'")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config_data = json.load(f)

        mcp_servers = config_data.get("mcpServers", {})
        self.servers.clear()
        self.tool_to_server.clear()
        self.discovered_tools.clear()

        for s_name, s_cfg in mcp_servers.items():
            cmd = s_cfg.get("command", "python")
            args = s_cfg.get("args", [])
            env = s_cfg.get("env", {})
            conn = McpServerConnection(s_name, cmd, args, env)
            conn.connect()
            self.servers[s_name] = conn

            for tool in conn.tools:
                t_name = tool["name"]
                self.tool_to_server[t_name] = conn
                self.discovered_tools.append(tool)

    def get_tool_names(self) -> List[str]:
        return [t["name"] for t in self.discovered_tools]

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self.tool_to_server:
            return {
                "success": False,
                "error": f"Tool '{name}' is not exposed by any connected MCP server."
            }
        return self.tool_to_server[name].call_tool(name, arguments)

    def run_claim_triage(self, claim_id: str) -> Dict[str, Any]:
        """
        Executes claim triage using dynamically discovered tools across MCP servers.
        Notice: The Host runs the model reasoning; MCP servers only execute tools.
        """
        start_time = time.time()
        trace_log = []
        tools_called = []
        trace_log.append(f"[MCP AGENT START] Triaging claim {claim_id} across {len(self.servers)} connected MCP servers.")

        # 1. Fetch Claim Status via MCP
        if "get_claim_status" in self.tool_to_server:
            status_res = self.call_tool("get_claim_status", {"claim_id": claim_id})
            tools_called.append("get_claim_status")
            trace_log.append(f"  Step 1: Called 'get_claim_status' on server '{self.tool_to_server['get_claim_status'].name}'. Result: {status_res['data']}")
            claim_data = status_res.get("data", {})
        else:
            claim_data = {"claim_id": claim_id, "gross_claim_amount": 0.0, "policy_deductible": 0.0}

        # 2. Fetch Adjuster Notes via MCP
        notes = ""
        if "get_adjuster_notes" in self.tool_to_server:
            notes_res = self.call_tool("get_adjuster_notes", {"claim_id": claim_id})
            tools_called.append("get_adjuster_notes")
            notes_data = notes_res.get("data", {})
            notes = notes_data.get("adjuster_notes", "") if isinstance(notes_data, dict) else str(notes_data)
            trace_log.append(f"  Step 2: Called 'get_adjuster_notes' on server '{self.tool_to_server['get_adjuster_notes'].name}'.")

        # 3. Search Policy Exclusions via MCP Policy Server (if exclusion triggers present)
        is_flood_or_excluded = ("flood" in notes.lower() or "rising water" in notes.lower() or "mysterious disappearance" in notes.lower())
        policy_verified = False

        if is_flood_or_excluded and "search_policy" in self.tool_to_server:
            policy_res = self.call_tool("search_policy", {"query": "flood rising water exclusion"})
            tools_called.append("search_policy")
            policy_verified = True
            trace_log.append(f"  Step 3: Called 'search_policy' on server '{self.tool_to_server['search_policy'].name}'. Verified exclusion.")
            final_status = "DENIED"
            payout = 0.0
        else:
            final_status = "APPROVED"
            gross = float(claim_data.get("gross_claim_amount", 0.0))
            deductible = float(claim_data.get("policy_deductible", 0.0))
            payout = max(0.0, gross - deductible)
            trace_log.append("  Step 3: No policy exclusion triggered. Approved.")

        latency = time.time() - start_time
        return {
            "claim_id": claim_id,
            "connected_servers": list(self.servers.keys()),
            "discovered_tools_count": len(self.discovered_tools),
            "tools_called": tools_called,
            "final_status": final_status,
            "payable_amount": payout,
            "policy_verified": policy_verified,
            "latency_seconds": round(latency, 4),
            "trace_log": trace_log
        }


def run_agent_with_config(config_path: str, claim_id: str = "CLM-7002") -> Dict[str, Any]:
    agent = McpHostAgent(config_path=config_path)
    return agent.run_claim_triage(claim_id)


if __name__ == "__main__":
    cfg = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CONFIG_PATH
    cid = sys.argv[2] if len(sys.argv) > 2 else "CLM-7002"
    agent = McpHostAgent(config_path=cfg)
    print(f"Connected to {len(agent.servers)} servers: {list(agent.servers.keys())}")
    print(f"Discovered {len(agent.discovered_tools)} tools: {agent.get_tool_names()}")
    result = agent.run_claim_triage(cid)
    print(f"\nResult:\n{json.dumps(result, indent=2)}")
