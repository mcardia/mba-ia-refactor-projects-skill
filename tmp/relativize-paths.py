#!/usr/bin/env python3
"""Rewrite absolute local paths in the committed run evidence into relative ones.

usage: relativize-paths.py <file>...
The repository root, the home directory and the user name are derived from the environment.
Order matters: scratch dirs first, then the repository root, then any other home path.
"""
import getpass
import os
import re
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HOME = os.path.expanduser("~")
HOME_KEY = HOME.replace("/", "-")  # how Claude Code encodes a path in a directory name
USER = getpass.getuser()

RULES = [
    (re.compile(r"/tmp/claude-\d+/[^/\"\\\s]+"), "<claude-tmp>"),
    (re.compile(re.escape(REPO) + "/"), "./"),
    (re.compile(re.escape(REPO)), "."),
    (re.compile(re.escape(HOME) + "/"), "~/"),
    (re.compile("/" + re.escape(HOME_KEY) + r"-[^/\"\\\s]+"), "/<project-key>"),
    (re.compile(r"(?<=\s)" + re.escape(USER) + r"(?=\s+\d{4}-\d{2}-\d{2})"), "user"),
]


def main():
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        updated = text
        for pattern, replacement in RULES:
            updated = pattern.sub(replacement, updated)
        if updated != text:
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(updated)
            print(f"rewritten {path}")


if __name__ == "__main__":
    main()
