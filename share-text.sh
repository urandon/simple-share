#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  ./share-text.sh "text to publish"
  ./share-text.sh -f /path/to/file.txt
  printf 'hello' | ./share-text.sh

Requirements:
  - cloudflared
  - python3
EOF
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Missing required command: %s\n' "$1" >&2
    exit 1
  fi
}

cleanup() {
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${TMP_DIR:-}" && -d "$TMP_DIR" ]]; then
    rm -rf "$TMP_DIR"
  fi
}

trap cleanup EXIT INT TERM

require_cmd cloudflared
require_cmd python3

TMP_DIR="$(mktemp -d)"
HTML_FILE="$TMP_DIR/index.html"
PORT="${PORT:-8787}"
TITLE="${TITLE:-shared text}"

input_mode=""
input_value=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--file)
      [[ $# -ge 2 ]] || { usage; exit 1; }
      input_mode="file"
      input_value="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$input_mode" ]]; then
        input_mode="text"
        input_value="$1"
      else
        input_value="$input_value $1"
      fi
      shift
      ;;
  esac
done

if [[ -z "$input_mode" ]]; then
  if [[ ! -t 0 ]]; then
    input_mode="stdin"
  else
    usage
    exit 1
  fi
fi

case "$input_mode" in
  file)
    [[ -f "$input_value" ]] || { printf 'File not found: %s\n' "$input_value" >&2; exit 1; }
    content="$(<"$input_value")"
    ;;
  stdin)
    content="$(cat)"
    ;;
  text)
    content="$input_value"
    ;;
  *)
    usage
    exit 1
    ;;
esac

python3 - <<'PY' "$HTML_FILE" "$TITLE" "$content"
import html
import sys
from pathlib import Path

out = Path(sys.argv[1])
title = sys.argv[2]
content = sys.argv[3]
page = f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>{html.escape(title)}</title>
    <style>
      :root {{ color-scheme: light dark; }}
      body {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; margin: 2rem; line-height: 1.5; }}
      main {{ max-width: 960px; }}
      pre {{ white-space: pre-wrap; word-break: break-word; padding: 1rem; border: 1px solid #8884; border-radius: 8px; }}
    </style>
  </head>
  <body>
    <main>
      <pre>{html.escape(content)}</pre>
    </main>
  </body>
</html>
"""
out.write_text(page, encoding="utf-8")
PY

python3 -m http.server "$PORT" --directory "$TMP_DIR" >/dev/null 2>&1 &
SERVER_PID=$!

sleep 1

printf 'Serving on http://127.0.0.1:%s\n' "$PORT"
printf 'Press Ctrl+C to stop.\n\n'
exec cloudflared tunnel --url "http://127.0.0.1:$PORT"
