#!/usr/bin/env bash
# Thin orchestration: run the refactor-arch skill through the real Claude Code CLI inside a project.
# usage: run-skill.sh <project-dir> <log-name> <prompt> <readonly|edit> [continue]
set -u
repo=/home/mario/Documentos/MBA/mba-ia-refactor-projects-skill
proj="$1"; name="$2"; prompt="$3"; mode="$4"; cont="${5:-}"

read_tools='Read Grep Glob Bash(wc:*) Bash(ls:*) Bash(find:*) Bash(cat:*) Bash(head:*) Bash(tail:*) Bash(grep:*) Bash(nl:*)'
edit_tools="$read_tools Write Edit Bash(python3:*) Bash(python:*) Bash(pip:*) Bash(.venv/bin/python:*) Bash(.venv/bin/pip:*) Bash(./.venv/bin/python:*) Bash(npm:*) Bash(node:*) Bash(curl:*) Bash(cp:*) Bash(mkdir:*) Bash(mv:*) Bash(sleep:*) Bash(kill:*) Bash(nohup:*) Bash(timeout:*) Bash(echo:*) Bash(ps:*) Bash(ss:*) Bash(rm -f *.db)"

if [ "$mode" = "edit" ]; then tools="$edit_tools"; perm=acceptEdits; else tools="$read_tools"; perm=default; fi

extra=()
[ "$cont" = "continue" ] && extra=(--continue)

hint="Non-interactive test harness. A virtualenv exists at .venv inside Python projects (use .venv/bin/python and .venv/bin/pip); node_modules is installed for Node projects. Any scratch or baseline copy of the project MUST be created under $repo/tmp/ (never /tmp). Follow the refactor-arch skill exactly."

cd "$repo/$proj" || exit 1
CLAUDE_CODE_DISABLE_CLAUDE_MDS=1 claude -p "$prompt" "${extra[@]}" \
  --setting-sources project,local \
  --permission-mode "$perm" \
  --allowedTools "$tools" \
  --append-system-prompt "$hint" \
  --output-format stream-json --verbose \
  > "$repo/tmp/$name.jsonl" 2> "$repo/tmp/$name.err"
echo "exit=$?" >> "$repo/tmp/$name.err"
