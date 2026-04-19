# Vault Policy for Value Fabric Layer Services
# Allows reading layer-specific dynamic database credentials

# Layer-specific database roles
path "database/creds/layer1-app" {
    capabilities = ["read"]
}

path "database/creds/layer2-app" {
    capabilities = ["read"]
}

path "database/creds/layer3-app" {
    capabilities = ["read"]
}

path "database/creds/layer4-app" {
    capabilities = ["read"]
}

# Shared auth secrets
path "secret/data/value-fabric/auth" {
    capabilities = ["read"]
}

# LLM API keys
path "secret/data/value-fabric/llm" {
    capabilities = ["read"]
}

# Database credentials (static fallback)
path "secret/data/value-fabric/database" {
    capabilities = ["read"]
}

# Infrastructure config (Redis, etc.)
path "secret/data/value-fabric/infrastructure" {
    capabilities = ["read"]
}

# Inter-layer API keys
path "secret/data/value-fabric/inter-layer" {
    capabilities = ["read"]
}
