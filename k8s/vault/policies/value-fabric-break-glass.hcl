# Vault Break-Glass Policy for Value Fabric
# Purpose: Emergency-only destructive operations.
# Controls:
# - Issue via dedicated role with short TTL (<=15m) and low max TTL (<=1h)
# - Multi-party approval and incident ticket required
# - Full audit trail review after use

# Destructive KV actions (restricted to Value Fabric namespace)
path "secret/data/value-fabric/*" {
    capabilities = ["delete"]
}

# Broad metadata listing for incident discovery
path "secret/metadata/value-fabric/*" {
    capabilities = ["list"]
}

# Emergency-wide list (platform incident use only)
path "secret/metadata/*" {
    capabilities = ["list"]
}
