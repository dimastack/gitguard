#!/usr/bin/env bash
set -euo pipefail

# By default inside docker-compose network it's gitea:3000, but from CI runner it's localhost:3000
# Locally override with: GITEA_URL=http://localhost:3000
GITEA_URL="${GITEA_URL:-http://localhost:3000}"
MAX_RETRIES="${MAX_RETRIES:-90}"   # up to 180s
SLEEP_INTERVAL="${SLEEP_INTERVAL:-2}"

echo "[wait] Waiting for Gitea at ${GITEA_URL} ..."

for i in $(seq 1 "${MAX_RETRIES}"); do
  status=$(curl -s -o /dev/null -w "%{http_code}" "${GITEA_URL}/api/v1/version" || echo "000")
  if [ "$status" == "200" ]; then
    echo "[wait] Gitea is up and running! (HTTP 200)"
    exit 0
  fi
  echo "[wait] Attempt $i/${MAX_RETRIES}: Gitea not ready (status=$status). Retrying in ${SLEEP_INTERVAL}s..."
  sleep "${SLEEP_INTERVAL}"
done

echo "[wait] ERROR: Gitea did not become ready after ${MAX_RETRIES} attempts."
exit 1
