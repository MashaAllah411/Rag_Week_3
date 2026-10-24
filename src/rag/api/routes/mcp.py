# ============================================================
# src/rag/api/routes/mcp.py
#
# Endpoints for Model Context Protocol (MCP) Ecosystem (Week 9)
# ============================================================

from fastapi import APIRouter, HTTPException
from rag.models.schemas import McpToolCallRequest, McpTriageRequest, McpConfigSwitchRequest
from rag.services.mcp_service import (
    get_mcp_servers_info,
    execute_mcp_tool,
    run_mcp_claim_triage,
    switch_mcp_config
)

router = APIRouter()


@router.get("/servers", summary="List connected MCP servers and discovered tools")
async def list_servers():
    """Returns connected MCP servers and all dynamically discovered tools."""
    try:
        return get_mcp_servers_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query MCP servers: {e}")


@router.post("/call", summary="Execute an MCP tool directly")
async def call_tool(request: McpToolCallRequest):
    """Executes a discovered tool on its respective MCP server via JSON-RPC 2.0."""
    try:
        return execute_mcp_tool(request.tool_name, request.arguments)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool call failed: {e}")


@router.post("/triage", summary="Run claim triage over MCP")
async def triage(request: McpTriageRequest):
    """Orchestrates claim triage calling tools across MCP servers."""
    try:
        return run_mcp_claim_triage(request.claim_id, config_path=request.config_filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP triage failed: {e}")


@router.post("/config", summary="Switch active MCP configuration file")
async def switch_config(request: McpConfigSwitchRequest):
    """Switches active MCP configuration (e.g. 1-server vs 2-server) and re-discovers tools."""
    try:
        return switch_mcp_config(request.config_filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
