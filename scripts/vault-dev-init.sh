#!/usr/bin/env bash
# Pre-seed a local Vault dev server with test secrets for development.
set -e

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-root}"

export VAULT_ADDR
export VAULT_TOKEN

echo "Waiting for Vault to be ready at ${VAULT_ADDR}..."
until vault status >/dev/null 2>&1; do
  sleep 1
done

# Enable KV v2 secrets engine if not already enabled
vault secrets enable -version=2 -path=secret kv || true

# Seed core secrets
vault kv put secret/value-fabric/llm \
  openai-api-key="sk-test-openai-key" \
  anthropic-api-key="sk-test-anthropic-key"

vault kv put secret/value-fabric/database \
  neo4j-auth="neo4j/valuefabric" \
  postgres-password="postgres"

vault kv put secret/value-fabric/auth \
  jwt-secret="changeme-in-production" \
  api-key-hmac-secret="test-hmac-secret"

# Optionally enable database secrets engine for dynamic cred smoke testing
vault secrets enable database || true

echo "Vault dev init complete."
