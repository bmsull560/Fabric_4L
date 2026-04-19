# Vault Policy for External Secrets Operator
# Allows reading dynamic database credentials and static secrets

# Database dynamic credentials - read access to all credential paths
path "database/creds/+" {
    capabilities = ["read"]
}

# Static secrets for Value Fabric
path "secret/data/value-fabric/*" {
    capabilities = ["read", "list"]
}

# Allow checking Vault health (no token needed but good for monitoring)
path "sys/health" {
    capabilities = ["read"]
}
