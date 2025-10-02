#!/usr/bin/env bash
set -euo pipefail

KEYS_DIR="/data/ssh_keys"
mkdir -p "$KEYS_DIR"

PRIVATE_KEY="$KEYS_DIR/id_rsa"
PUBLIC_KEY="$KEYS_DIR/id_rsa.pub"

# Якщо ключів ще нема → генеруємо
if [ ! -f "$PRIVATE_KEY" ]; then
  echo "Generating new SSH keypair..."
  ssh-keygen -t rsa -b 4096 -N "" -f "$PRIVATE_KEY"
  chmod 600 "$PRIVATE_KEY"
  chmod 644 "$PUBLIC_KEY"
else
  echo "SSH keys already exist, skipping generation."
fi
