#!/usr/bin/env bash
# Pull the configured model into the Ollama container.
# Run this once after first `docker compose up`.
set -euo pipefail

MODEL="${OLLAMA_MODEL:-qwen2.5:7b}"
HOST="${OLLAMA_HOST:-http://localhost:11434}"

echo "Pulling model: $MODEL"
curl -sf "$HOST/api/pull" -d "{\"name\": \"$MODEL\"}" | while IFS= read -r line; do
    status=$(echo "$line" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || true)
    [ -n "$status" ] && echo "  $status"
done

echo "Done. Model $MODEL is ready."
