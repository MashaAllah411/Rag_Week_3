# ============================================================
# src/rag/mcp/protocol.py — Standard MCP JSON-RPC 2.0 Protocol
#
# PURPOSE:
#   Implements standard Model Context Protocol (MCP) JSON-RPC 2.0
#   message parsing, formatting, and transport abstractions.
# ============================================================

from __future__ import annotations
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

MCP_PROTOCOL_VERSION = "2024-11-05"


class JsonRpcError(Exception):
    def __init__(self, code: int, message: str, data: Any = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self) -> Dict[str, Any]:
        err = {"code": self.code, "message": self.message}
        if self.data is not None:
            err["data"] = self.data
        return err


def make_response(req_id: Any, result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": result
    }


def make_error(req_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    err_body: Dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err_body["data"] = data
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": err_body
    }


def make_request(req_id: Any, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    req = {
        "jsonrpc": "2.0",
        "id": req_id,
        "method": method
    }
    if params is not None:
        req["params"] = params
    return req


def make_notification(method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    notif = {
        "jsonrpc": "2.0",
        "method": method
    }
    if params is not None:
        notif["params"] = params
    return notif


class BaseMcpServer:
    """Base class for standard MCP Stdio/JSON-RPC Servers."""

    def __init__(self, server_name: str, server_version: str = "1.0.0"):
        self.server_name = server_name
        self.server_version = server_version
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.tool_handlers = {}

    def register_tool(self, name: str, description: str, input_schema: Dict[str, Any], handler_fn):
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema
        }
        self.tool_handlers[name] = handler_fn

    def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if "method" not in message:
            return None

        method = message["method"]
        req_id = message.get("id")
        params = message.get("params", {})

        # 1. Initialize
        if method == "initialize":
            return make_response(req_id, {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False}
                },
                "serverInfo": {
                    "name": self.server_name,
                    "version": self.server_version
                }
            })

        # 2. Initialized Notification
        elif method == "notifications/initialized":
            return None

        # 3. tools/list
        elif method == "tools/list":
            return make_response(req_id, {
                "tools": list(self.tools.values())
            })

        # 4. tools/call
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name not in self.tool_handlers:
                return make_error(req_id, -32601, f"Tool '{tool_name}' not found on server '{self.server_name}'.")

            try:
                result_content = self.tool_handlers[tool_name](arguments)
                return make_response(req_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result_content) if isinstance(result_content, (dict, list)) else str(result_content)
                        }
                    ],
                    "isError": False if not isinstance(result_content, dict) or "error" not in result_content else True
                })
            except Exception as e:
                return make_response(req_id, {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Tool execution failed: {str(e)}"
                        }
                    ],
                    "isError": True
                })

        # Unknown method
        else:
            if req_id is not None:
                return make_error(req_id, -32601, f"Method '{method}' not supported.")
            return None

    def run_stdio(self):
        """Runs the JSON-RPC stdio message loop."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_message(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = make_error(None, -32700, f"Parse error: {str(e)}")
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
