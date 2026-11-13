#!/bin/bash
# Source: claude-code-facts.md §10 (hooks-guide.md)
# Blocks Bash commands and file reads that touch secret or production paths.
# Exit 2 blocks the tool call. The reason goes to stderr.
# Exit 0 allows the tool call to continue.
#
# Usage: chmod +x block-secrets.sh
# Config: add to settings.json hooks.PreToolUse — see settings-hooks.json
#
# Note: "Read" as a matcher is UNVERIFIED — test with /hooks and debug log.
# permissions.deny rules in settings.json are the primary documented control
# for blocking file reads. This hook is a second check for Bash commands.

input=$(cat)
cmd=$(jq -r '.tool_input.command // empty' <<<"$input")
path=$(jq -r '.tool_input.file_path // empty' <<<"$input")

# Demo pattern. Tune it for your project.
# Matches: .env, secrets/, id_rsa, .pem files, paths containing -prod- or /prod/ etc.
PATTERN='\.env|secrets/|id_rsa|\.pem$|[-_/.]prod([-_/.]|$)'

if [[ -n "$path" ]] && grep -Eq "$PATTERN" <<<"$path"; then
  echo "Blocked: file path matches protected pattern: $path" >&2
  exit 2
fi
if [[ -n "$cmd" ]] && grep -Eq "$PATTERN" <<<"$cmd"; then
  echo "Blocked: command matches protected pattern" >&2
  exit 2
fi
exit 0
