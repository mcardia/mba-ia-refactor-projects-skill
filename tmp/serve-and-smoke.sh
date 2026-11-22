#!/usr/bin/env bash
# Thin orchestration: start a server, replay a spec against it, stop it.
# usage: serve-and-smoke.sh <dir> <spec.json> <out.json> <port> -- <command> [args...]
set -u
tools="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
dir="$1"; spec="$2"; out="$3"; port="$4"; shift 5
cd "$dir" || exit 1
"$@" > "$out.log" 2>&1 &
pid=$!
ready=0
for _ in $(seq 1 60); do
  if curl -s -o /dev/null "http://127.0.0.1:$port/"; then ready=1; break; fi
  sleep 0.5
done
if [ "$ready" = 1 ]; then
  python3 -I "$tools/smoke.py" run "http://127.0.0.1:$port" "$spec" "$out"
else
  echo "SERVER DID NOT START"; tail -n 20 "$out.log"
fi
kill "$pid" 2>/dev/null
wait "$pid" 2>/dev/null
echo "server log: $out.log"
