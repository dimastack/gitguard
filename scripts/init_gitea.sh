#!/usr/bin/env bash
set -euo pipefail

GITEA_URL="${GITEA_URL:-http://gitea:3000}"
ADMIN_USER="${GITEA_ADMIN_USER:-admin}"
ADMIN_PASS="${GITEA_ADMIN_PASSWORD:-admin123}"
ADMIN_EMAIL="${GITEA_ADMIN_EMAIL:-admin@example.com}"
TOKEN_NAME="ci-token"
TOKEN_FILE="/data/gitea_admin_token"
ORG_NAME="test-org"
REPO_NAME="test-repo"
SSH_KEY_FILE="/etc/ssh_keys/id_rsa.pub"

echo "[init] Waiting for Gitea to be healthy..."
until curl -s -o /dev/null -w "%{http_code}" "${GITEA_URL}/api/healthz" | grep -q "200"; do
  sleep 2
done

echo "[init] Ensuring admin user exists..."
gitea admin user create \
  --username "${ADMIN_USER}" \
  --password "${ADMIN_PASS}" \
  --email "${ADMIN_EMAIL}" \
  --admin \
  || true

echo "[init] Generating API token..."
if ! gitea admin user generate-access-token \
  --username "${ADMIN_USER}" \
  --scopes all \
  --token-name "${TOKEN_NAME}" > /tmp/token_out; then
  echo "[init] Failed to generate token, maybe it already exists. Trying to fetch..."
fi

TOKEN=$(grep -oE "[a-f0-9]{40}" /tmp/token_out | head -n1 || true)
if [ -n "$TOKEN" ]; then
  echo "$TOKEN" > "$TOKEN_FILE"
  echo "[init] Token saved to $TOKEN_FILE"
else
  echo "[init] WARNING: Could not get token!"
fi

# Add SSH key to admin account if not already
if [ -f "$SSH_KEY_FILE" ]; then
  echo "[init] Adding SSH key for admin..."
  PUBKEY=$(cat "$SSH_KEY_FILE")
  curl -s -X POST "${GITEA_URL}/api/v1/admin/users/${ADMIN_USER}/keys" \
    -H "Content-Type: application/json" \
    -H "Authorization: token $(cat $TOKEN_FILE)" \
    -d "{\"title\": \"ci-key\", \"key\": \"${PUBKEY}\"}" || true
fi

echo "[init] Creating org $ORG_NAME..."
curl -s -X POST "${GITEA_URL}/api/v1/orgs" \
  -H "Content-Type: application/json" \
  -H "Authorization: token $(cat $TOKEN_FILE)" \
  -d "{\"username\": \"${ORG_NAME}\", \"full_name\": \"Test Organization\"}" || true

echo "[init] Creating repo $REPO_NAME in $ORG_NAME..."
curl -s -X POST "${GITEA_URL}/api/v1/orgs/${ORG_NAME}/repos" \
  -H "Content-Type: application/json" \
  -H "Authorization: token $(cat $TOKEN_FILE)" \
  -d "{\"name\": \"${REPO_NAME}\", \"private\": false}" || true

echo "[init] Initialization complete."
