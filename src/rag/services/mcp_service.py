"""
mcp_service.py

Service layer orchestrating:
- MCP Server discovery (JSON-RPC 2.0 initialize + tools/list)
- Dynamic tool execution (tools/call)
- Config switching (single-server vs multi-server)
- End-to-end claim triage over MCP
"""
from __future__ import annotations
import os
import json
from typing import Dict, Any, List, Optional

from rag.agent.mcp_agent import McpHostAgent, DEFAULT_CONFIG_PATH
from rag.mcp.protocol import make_request

_active_agent: Optional[McpHostAgent] = None
_active_config_path: str = DEFAULT_CONFIG_PATH


def get_mcp_host(config_path: Optional[str] = None) -> McpHostAgent:
    """Return singleton or freshly configured MCP Host Agent."""
    global _active_agent, _active_config_path
    target_path = config_path or _active_config_path
    if _active_agent is None or target_path != _active_config_path:
        _active_config_path = target_path
        _active_agent = McpHostAgent(config_path=target_path)
    return _active_agent


def get_mcp_servers_info(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Return overview of connected MCP servers and discovered tools."""
    agent = get_mcp_host(config_path)
    servers_summary = []

    for name, conn in agent.servers.items():
        servers_summary.append({
            "name": name,
            "command": conn.command,
            "args": conn.args,
            "server_info": conn.server_info,
            "tools_count": len(conn.tools),
            "tools": conn.tools
        })

    return {
        "active_config": _active_config_path,
        "servers_count": len(agent.servers),
        "total_tools_count": len(agent.discovered_tools),
        "servers": servers_summary,
        "discovered_tools": agent.discovered_tools
    }


def execute_mcp_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a single dynamically discovered tool via MCP tools/call."""
    agent = get_mcp_host()
    return agent.call_tool(tool_name, arguments)


def run_mcp_claim_triage(claim_id: str, config_path: Optional[str] = None) -> Dict[str, Any]:
    """Execute full claim triage over the MCP layer."""
    agent = get_mcp_host(config_path)
    return agent.run_claim_triage(claim_id)


def switch_mcp_config(config_filename: str) -> Dict[str, Any]:
    """
    Switch active MCP configuration file (e.g. mcp_config.json vs mcp_config_server1.json).
    Re-discovers tools automatically.
    """
    global _active_config_path, _active_agent
    candidate = os.path.join("data", config_filename)
    if not os.path.exists(candidate):
        raise FileNotFoundError(f"Configuration file '{config_filename}' not found in data/ folder.")
    _active_config_path = candidate
    _active_agent = McpHostAgent(config_path=candidate)
    return get_mcp_servers_info(_active_config_path)
