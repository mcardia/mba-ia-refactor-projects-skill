#!/usr/bin/env python3
"""Print the assistant text blocks of a `claude -p --output-format stream-json` transcript, in order.

usage: extract-text.py <transcript.jsonl> [--tools]
  --tools  also print one line per tool call (name + short input) and tool errors
"""
import json
import sys


def short(value, limit=160):
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + "..."


def main():
    path = sys.argv[1]
    show_tools = "--tools" in sys.argv[2:]
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            event = json.loads(raw)
            kind = event.get("type")
            if kind == "assistant":
                for block in event["message"]["content"]:
                    if block.get("type") == "text" and block["text"].strip():
                        print(block["text"])
                        print()
                    elif block.get("type") == "tool_use" and show_tools:
                        print(f"[tool] {block['name']} {short(block['input'])}")
            elif kind == "user" and show_tools:
                content = event["message"]["content"]
                if isinstance(content, list):
                    for block in content:
                        if block.get("type") == "tool_result" and block.get("is_error"):
                            print(f"[tool-error] {short(block.get('content'))}")
            elif kind == "result":
                print(f"[result] subtype={event.get('subtype')} turns={event.get('num_turns')} "
                      f"cost_usd={event.get('total_cost_usd')} duration_ms={event.get('duration_ms')}")


if __name__ == "__main__":
    main()
