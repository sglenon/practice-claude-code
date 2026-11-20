#!/usr/bin/env python3
"""PreToolUse hook: block Bash commands that touch secret or production paths.

Standard library only. No jq. Works on Windows, macOS, Linux.

Exit 2 blocks the tool call. The reason goes to stderr.
Exit 0 allows the tool call to continue.

This hook FAILS CLOSED: any problem reading or parsing the input blocks the
call (exit 2) instead of letting it through.

Usage: python3 course/s3/block_secrets.py
Config: add to .claude/settings.json hooks.PreToolUse — see settings.with-hook.json
"""
from __future__ import annotations

import json
import re
import sys

# Demo pattern. Tune it for your project.
# Matches: .env, secrets/, id_rsa, .pem files, paths or commands containing
# -prod- or /prod/ etc.
PATTERN = re.compile(r"\.env|secrets/|id_rsa|\.pem$|[-_/.]prod([-_/.]|$)")


def main() -> int:
    try:
        raw = sys.stdin.read()
    except Exception as exc:  # noqa: BLE001 - fail closed on any read error
        print(f"Blocked: could not read hook input: {exc}", file=sys.stderr)
        return 2

    if not raw.strip():
        print("Blocked: empty hook input", file=sys.stderr)
        return 2

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Blocked: hook input is not valid JSON: {exc}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("Blocked: hook input is not a JSON object", file=sys.stderr)
        return 2

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        print("Blocked: hook input has no tool_input object", file=sys.stderr)
        return 2

    command = tool_input.get("command") or ""
    file_path = tool_input.get("file_path") or ""

    if file_path and PATTERN.search(str(file_path)):
        print(f"Blocked: command matches protected pattern", file=sys.stderr)
        return 2
    if command and PATTERN.search(str(command)):
        print("Blocked: command matches protected pattern", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
