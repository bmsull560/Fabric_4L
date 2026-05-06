# Vault Policy for Value Fabric Admin Operations
# Least-privilege admin access for routine platform operations.
# Destructive operations are isolated in value-fabric-break-glass.hcl.

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

# Scoped KV access for platform-managed secrets
path "secret/data/value-fabric/*" {
    capabilities = ["create", "read", "update", "list"]
}

path "secret/metadata/value-fabric/*" {
    capabilities = ["read", "list"]
}

# System health and status
path "sys/health" {
    capabilities = ["read"]
}

path "sys/seal-status" {
    capabilities = ["read"]
}
