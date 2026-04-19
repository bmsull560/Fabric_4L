# Vault Policy for Value Fabric Admin Operations
# Full access for emergency operations and secret management

# Admin database role access
path "database/creds/admin-role" {
    capabilities = ["read"]
}

# Role rotation capability
path "database/rotate-role/*" {
    capabilities = ["update"]
}

# Root credential rotation
path "database/rotate-root/postgres" {
    capabilities = ["update"]
}

# Full access to all secrets
path "secret/*" {
    capabilities = ["create", "read", "update", "delete", "list"]
}

# System health and status
path "sys/health" {
    capabilities = ["read"]
}

path "sys/seal-status" {
    capabilities = ["read"]
}
