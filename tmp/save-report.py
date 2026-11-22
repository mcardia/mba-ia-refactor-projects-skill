#!/usr/bin/env python3
"""Save the Phase 2 audit report, verbatim, from a stream-json transcript.

usage: save-report.py <transcript.jsonl> <output.md>
The report runs from the banner line before 'ARCHITECTURE AUDIT REPORT' to the confirmation prompt.
"""
import json
import sys

BANNER = "================================"
TITLE = "ARCHITECTURE AUDIT REPORT"
CONFIRM = "Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]"


def assistant_texts(path):
    with open(path, encoding="utf-8") as handle:
        for raw in handle:
            raw = raw.strip()
            if not raw:
                continue
            event = json.loads(raw)
            if event.get("type") != "assistant":
                continue
            for block in event["message"]["content"]:
                if block.get("type") == "text":
                    yield block["text"]


def main():
    source, target = sys.argv[1], sys.argv[2]
    for text in assistant_texts(source):
        if TITLE in text and CONFIRM in text:
            start = text.index(TITLE)
            start = text.rindex(BANNER, 0, start)
            end = text.index(CONFIRM) + len(CONFIRM)
            with open(target, "w", encoding="utf-8") as out:
                out.write(text[start:end] + "\n")
            print(f"saved {target}")
            return
    sys.exit("report not found in transcript")


if __name__ == "__main__":
    main()
