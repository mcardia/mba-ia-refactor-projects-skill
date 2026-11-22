#!/usr/bin/env python3
"""Replay a request spec against a running server and record status + top-level JSON keys.

usage:
  smoke.py run  <base_url> <spec.json> <out.json>
  smoke.py diff <before.json> <after.json>
"""
import json
import sys
import urllib.error
import urllib.request


def call(base, step):
    headers = dict(step.get("headers", {}))
    data = None
    if "body" in step:
        data = json.dumps(step["body"]).encode()
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(base + step["p"], data=data, method=step["m"], headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=15)
        status, raw, ctype = response.status, response.read(), response.headers.get("Content-Type", "")
    except urllib.error.HTTPError as err:
        status, raw, ctype = err.code, err.read(), err.headers.get("Content-Type", "")
    keys = "text"
    if "json" in ctype:
        try:
            body = json.loads(raw)
            keys = sorted(body) if isinstance(body, dict) else f"list[{len(body)}]"
        except ValueError:
            keys = "invalid-json"
    return {"step": f"{step['m']} {step['p']} {step.get('label', '')}".strip(), "status": status, "keys": keys,
            "snippet": raw[:140].decode("utf-8", "replace")}


def run(base, spec_path, out_path):
    with open(spec_path, encoding="utf-8") as handle:
        steps = json.load(handle)
    results = [call(base, step) for step in steps]
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, ensure_ascii=False, indent=1)
    for item in results:
        print(item["status"], item["step"], item["keys"])


def diff(before_path, after_path):
    with open(before_path, encoding="utf-8") as handle:
        before = json.load(handle)
    with open(after_path, encoding="utf-8") as handle:
        after = json.load(handle)
    same = 0
    for old, new in zip(before, after):
        if old["status"] == new["status"] and old["keys"] == new["keys"]:
            same += 1
            continue
        print(f"DIFF {old['step']}\n   before: {old['status']} {old['keys']}\n   after:  {new['status']} {new['keys']}")
    print(f"identical: {same}/{len(before)}")


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "run":
        run(*sys.argv[2:5])
    elif command == "diff":
        diff(*sys.argv[2:4])
    else:
        sys.exit(__doc__)
