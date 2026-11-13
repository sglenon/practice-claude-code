#!/usr/bin/env python3
"""Minimal MCP server over stdio. Python 3 standard library only.

Course reference for Session 2, Exercise 6. One tool: get_status.
Each request and each reply is one line of JSON-RPC 2.0.
"""
import json
import sys
from pathlib import Path

STATUS_FILE = Path(__file__).with_name("status.json")

TOOLS = [
    {
        "name": "get_status",
        "description": "Return the project status from status.json.",
        "inputSchema": {"type": "object", "properties": {}},
    }
]


def handle(request):
    method = request.get("method")
    params = request.get("params") or {}
    if method == "initialize":
        return {
            "protocolVersion": params.get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "project-status", "version": "0.1.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        if params.get("name") == "get_status":
            text = STATUS_FILE.read_text()
            return {"content": [{"type": "text", "text": text}]}
        raise ValueError(f"Unknown tool: {params.get('name')}")
    raise NotImplementedError(method)


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        request = json.loads(line)
        if "id" not in request:
            continue  # A notification. MCP expects no reply.
        try:
            reply = {"jsonrpc": "2.0", "id": request["id"], "result": handle(request)}
        except NotImplementedError as exc:
            reply = {"jsonrpc": "2.0", "id": request["id"],
                     "error": {"code": -32601, "message": f"Method not found: {exc}"}}
        except Exception as exc:
            reply = {"jsonrpc": "2.0", "id": request["id"],
                     "error": {"code": -32603, "message": str(exc)}}
        print(json.dumps(reply), flush=True)


if __name__ == "__main__":
    main()
