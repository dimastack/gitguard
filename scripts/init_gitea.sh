#!/usr/bin/env bash
set -euo pipefail

# Default config
GITEA_URL="${GITEA_URL:-http://localhost:3000}"
ADMIN_USER="${GITEA_ADMIN_USER:-gitadmin}"
ADMIN_PASS="${GITEA_ADMIN_PASSWORD:-gitadmin123}"
ADMIN_EMAIL="${GITEA_ADMIN_EMAIL:-gitadmin@example.com}"
TOKEN_NAME="ci-token"
TOKEN_FILE="/data/gitea_admin_token"
ORG_NAME="test-org"
REPO_NAME="test-repo"
SSH_KEY_FILE="/etc/ssh_keys/id_rsa.pub"

echo "[init] Waiting for Gitea to be healthy..."
until curl -sf -o /dev/null "${GITEA_URL}/api/healthz"; do
  sleep 2
done

echo "[init] Gitea is healthy."

# --- Create admin user if not exists ---
echo "[init] Ensuring admin user '${ADMIN_USER}' exists..."
if ! su git -c "gitea admin user list" | grep -q "^${ADMIN_USER}\b"; then
  su git -c "gitea admin user create \
      --username \"${ADMIN_USER}\" \
      --password \"${ADMIN_PASS}\" \
      --email \"${ADMIN_EMAIL}\" \
      --admin"
  echo "[init] Created admin user: ${ADMIN_USER}"
else
  echo "[init] Admin user '${ADMIN_USER}' already exists, skipping."
fi

# --- Generate or reuse API token ---
echo "[init] Generating or fetching API token..."
TOKEN=$(su git -c "gitea admin user generate-access-token \
    --username \"${ADMIN_USER}\" \
    --scopes all \
    --token-name \"${TOKEN_NAME}\"" 2>/dev/null \
  | grep -oE '[a-f0-9]{40}' | head -n1 || true)

if [ -z "$TOKEN" ] && [ -f "$TOKEN_FILE" ]; then
  TOKEN=$(cat "$TOKEN_FILE")
fi

if [ -z "$TOKEN" ]; then
  echo "[init] WARNING: Could not obtain API token!"
else
  echo "$TOKEN" > "$TOKEN_FILE"
  echo "[init] Token saved to $TOKEN_FILE"
fi

# --- Add SSH key if available ---
if [ -f "$SSH_KEY_FILE" ] && [ -n "$TOKEN" ]; then
  echo "[init] Adding SSH key for ${ADMIN_USER}..."
  PUBKEY=$(cat "$SSH_KEY_FILE")
  curl -s -X POST "${GITEA_URL}/api/v1/admin/users/${ADMIN_USER}/keys" \
    -H "Content-Type: application/json" \
    -H "Authorization: token ${TOKEN}" \
    -d "{\"title\": \"ci-key\", \"key\": \"${PUBKEY}\"}" || true
fi

# --- Create org and repo ---
if [ -n "$TOKEN" ]; then
  echo "[init] Creating org '${ORG_NAME}'..."
  curl -s -X POST "${GITEA_URL}/api/v1/orgs" \
    -H "Content-Type: application/json" \
    -H "Authorization: token ${TOKEN}" \
    -d "{\"username\": \"${ORG_NAME}\", \"full_name\": \"Test Organization\"}" || true

  echo "[init] Creating repo '${REPO_NAME}' in org '${ORG_NAME}'..."
  curl -s -X POST "${GITEA_URL}/api/v1/orgs/${ORG_NAME}/repos" \
    -H "Content-Type: application/json" \
    -H "Authorization: token ${TOKEN}" \
    -d "{\"name\": \"${REPO_NAME}\", \"private\": false}" || true
fi

echo "[init] Initialization complete."
