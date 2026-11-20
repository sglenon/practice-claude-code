#!/usr/bin/env python3
"""MCP server over stdio for ops/ops.db. Python 3 standard library only.

Finished reference for Session 2, Exercise 6. Fallback: `cp course/s2/ops_db_server.py server/`.
Two tools: list_tables, run_select.

Protocol notes:
- One JSON-RPC 2.0 message per line, newline-delimited UTF-8, on stdin/stdout.
- Nothing but JSON-RPC messages goes to stdout. Logs go to stderr only.
- A line that is not valid JSON is ignored, with a note on stderr. The
  server keeps running.
- "initialize" answers with a protocol version this server supports.
- "notifications/initialized" gets no reply (it has no "id").
- "ping" replies with an empty result.
- "tools/list" lists the tools below.
- "tools/call" runs a tool and returns {"content": [...], "isError": bool}.
- An unknown tool name is a JSON-RPC error -32602 (Invalid params).

Windows: if `python3` is not found, use `python` instead.
"""
import json
import os
import sqlite3
import sys
from pathlib import Path


def _resolve_db_path() -> Path:
    """Find ops/ops.db from this file's location, not the working directory.

    This lets the server run from any folder, including after
    `cp course/s2/ops_db_server.py server/`, and from a copy used in a test.
    OPS_DB_PATH, if set, overrides the search (used by server/test_ops_db.py
    when it copies the server to a temporary location).
    """
    override = os.environ.get("OPS_DB_PATH")
    if override:
        return Path(override).resolve()
    here = Path(__file__).resolve().parent
    for candidate in [here, *here.parents]:
        guess = candidate / "ops" / "ops.db"
        if guess.exists():
            return guess
    # Fallback: assume this file sits one folder below the repo root.
    return here.parent / "ops" / "ops.db"


# Resolve the database path from this file's location, not the current
# working directory. This lets the server run from any folder.
DB_PATH = _resolve_db_path()

PROTOCOL_VERSION = "2025-11-25"

TOOLS = [
    {
        "name": "list_tables",
        "description": "List the table names in ops/ops.db.",
        "inputSchema": {"type": "object", "additionalProperties": False},
    },
    {
        "name": "run_select",
        "description": "Run one read-only SELECT (or WITH) query against ops/ops.db.",
        "inputSchema": {
            "type": "object",
            "properties": {"sql": {"type": "string"}},
            "required": ["sql"],
            "additionalProperties": False,
        },
    },
]


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def text_result(text: str, is_error: bool = False) -> dict:
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def tool_list_tables() -> dict:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
    finally:
        conn.close()
    names = [row[0] for row in rows]
    return text_result("\n".join(names) if names else "No tables.")


MAX_ROWS = 200


def _strip_sql_comments(sql: str) -> str:
    """Remove -- line comments and /* */ block comments, for the statement check."""
    out = []
    i = 0
    n = len(sql)
    while i < n:
        if sql[i : i + 2] == "--":
            j = sql.find("\n", i)
            i = n if j == -1 else j + 1
            continue
        if sql[i : i + 2] == "/*":
            j = sql.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        out.append(sql[i])
        i += 1
    return "".join(out)


REFUSAL = "Only SELECT is allowed. Nothing was run."


def tool_run_select(sql: str) -> dict:
    stripped = _strip_sql_comments(sql).strip()
    if not stripped:
        return text_result(REFUSAL, is_error=True)

    # Exactly one statement: at most one non-empty statement once a single
    # trailing semicolon is removed. More than one ";"-separated non-empty
    # part means more than one statement.
    body = stripped[:-1] if stripped.endswith(";") else stripped
    parts = [p for p in body.split(";") if p.strip()]
    if len(parts) != 1:
        return text_result(REFUSAL, is_error=True)

    first_word = stripped.split(None, 1)[0].upper() if stripped.split(None, 1) else ""
    if first_word not in ("SELECT", "WITH"):
        return text_result(REFUSAL, is_error=True)

    uri = f"file:{DB_PATH}?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
        conn.execute("PRAGMA query_only = ON")
        cursor = conn.execute(stripped)
        columns = [d[0] for d in cursor.description] if cursor.description else []
        rows = cursor.fetchmany(MAX_ROWS)
    except sqlite3.Error as exc:
        return text_result(f"SQL error: {exc}", is_error=True)
    finally:
        try:
            conn.close()
        except Exception:  # noqa: BLE001
            pass

    if not columns:
        return text_result("Query ran. No rows returned.")

    lines = [" | ".join(columns)]
    for row in rows:
        lines.append(" | ".join("" if v is None else str(v) for v in row))
    return text_result("\n".join(lines))


def handle_tools_call(params: dict) -> dict:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if name == "list_tables":
        return tool_list_tables()
    if name == "run_select":
        return tool_run_select(arguments.get("sql", ""))
    raise InvalidParams(f"Unknown tool: {name}")


class InvalidParams(Exception):
    """Raised for an unknown tool name or bad params. Maps to JSON-RPC -32602."""


def handle(request: dict):
    method = request.get("method")
    params = request.get("params") or {}
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "ops-db", "version": "0.1.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        return handle_tools_call(params)
    raise MethodNotFound(method)


class MethodNotFound(Exception):
    """Raised for an unrecognized JSON-RPC method. Maps to JSON-RPC -32601."""


def main() -> None:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            log(f"Ignoring non-JSON line: {exc}")
            continue

        if not isinstance(request, dict):
            log("Ignoring JSON line that is not an object.")
            continue

        if request.get("method") == "notifications/initialized":
            continue  # A notification. No "id". MCP expects no reply.

        request_id = request.get("id")
        if request_id is None:
            # Any other notification: no reply expected.
            continue

        try:
            result = handle(request)
            reply = {"jsonrpc": "2.0", "id": request_id, "result": result}
        except InvalidParams as exc:
            reply = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32602, "message": str(exc)},
            }
        except MethodNotFound as exc:
            reply = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {exc}"},
            }
        except Exception as exc:  # noqa: BLE001 - last-resort guard, keep server alive
            log(f"Internal error handling {request.get('method')}: {exc}")
            reply = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": str(exc)},
            }

        print(json.dumps(reply), flush=True)


if __name__ == "__main__":
    main()
