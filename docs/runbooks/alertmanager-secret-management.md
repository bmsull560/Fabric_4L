# Alertmanager Secret Management Runbook

**Task 63: Alert Rules & Routing**  
**Purpose:** Document secret management approaches for Alertmanager notifications (PagerDuty + Slack)

---

## Overview

This runbook describes two approaches for managing Alertmanager secrets:

1. **Current: SecretKeyRef-based** - Environment variables via Kubernetes Secrets
2. **Future: External Secrets Operator (ESO) + Vault** - Centralized secret management with automatic rotation

---

## Current Approach: SecretKeyRef

### Required Secrets

| Secret | Purpose | Source |
|--------|---------|--------|
| `PAGERDUTY_INTEGRATION_KEY` | Critical alerts to PagerDuty | PagerDuty Service Integration |
| `SLACK_WEBHOOK_URL` | Warning/info alerts to Slack | Slack App Incoming Webhook |

### Setup Steps

#### 1. Generate PagerDuty Integration Key

1. Log into PagerDuty
2. Navigate to **Services** → Select your service
3. Click **Integrations** tab
4. Click **Add Integration**
5. Choose **Events API v2**
6. Copy the **Integration Key** (looks like `r+xxxxxxxxxxxxxxxxxxxxxxxx`)

#### 2. Generate Slack Webhook URL

1. Go to [Slack API Apps](https://api.slack.com/apps)
2. Create New App → From scratch
3. Navigate to **Incoming Webhooks**
4. Toggle **On** to activate
5. Click **Add New Webhook to Workspace**
6. Select channel (#vf-alerts-warning or create it)
7. Copy the **Webhook URL** (looks like `https://hooks.slack.com/services/T.../B.../...`)

#### 3. Create Kubernetes Secret

```bash
# Set environment variables (DO NOT commit these values)
export PAGERDUTY_INTEGRATION_KEY="r+xxxxxxxxxxxxxxxxxxxxxxxx"
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# Create the secret in Kubernetes
kubectl create secret generic alertmanager-secrets \
  --from-literal=pagerduty-integration-key="${PAGERDUTY_INTEGRATION_KEY}" \
  --from-literal=slack-webhook-url="${SLACK_WEBHOOK_URL}" \
  -n value-fabric

# Verify the secret was created
kubectl get secret alertmanager-secrets -n value-fabric
```

#### 4. Mount Secret in Alertmanager Deployment

The Alertmanager deployment (`k8s/base/alertmanager.yml`) mounts the secret as files:

```yaml
volumeMounts:
  - name: alertmanager-secrets
    mountPath: /etc/alertmanager/secrets
    readOnly: true

volumes:
  - name: alertmanager-secrets
    secret:
      secretName: alertmanager-secrets
      items:
        - key: pagerduty-integration-key
          path: pagerduty_integration_key
        - key: slack-webhook-url
          path: slack_webhook_url
```

The alertmanager.yml configuration references these files:

```yaml
global:
  slack_api_url_file: '/etc/alertmanager/secrets/slack_webhook_url'

receivers:
  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key_file: '/etc/alertmanager/secrets/pagerduty_integration_key'
```

### Rotating Secrets

```bash
# Update PagerDuty key
kubectl patch secret alertmanager-secrets -n value-fabric \
  --type='json' \
  -p='[{"op": "replace", "path": "/data/pagerduty-integration-key", "value":"'$(echo -n "new-key" | base64)'"}]'

# Rollout restart to pick up new secret
kubectl rollout restart deployment/alertmanager -n value-fabric
```

---

## Future Approach: External Secrets Operator + Vault

### Prerequisites

1. **Vault** running and configured
2. **External Secrets Operator (ESO)** installed in cluster
3. **ClusterSecretStore** configured for Vault backend

### Migration Steps

#### 1. Store Secrets in Vault

```bash
# Write secrets to Vault
vault kv put secret/alertmanager \
  pagerduty-integration-key="r+xxxxxxxxxxxxxxxxxxxxxxxx" \
  slack-webhook-url="https://hooks.slack.com/services/..."

# Verify
vault kv get secret/alertmanager
```

#### 2. Create ClusterSecretStore

```yaml
# k8s/external-secrets/vault-store.yml
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault-backend
spec:
  provider:
    vault:
      server: "http://vault.value-fabric.svc:8200"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "external-secrets"
          serviceAccountRef:
            name: external-secrets-sa
            namespace: value-fabric
```

```bash
kubectl apply -f k8s/external-secrets/vault-store.yml
```

#### 3. Create ExternalSecret Resource

```yaml
# k8s/base/alertmanager-externalsecret.yml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: alertmanager-secrets
  namespace: value-fabric
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault-backend
  target:
    name: alertmanager-secrets
    creationPolicy: Owner
  data:
    - secretKey: pagerduty-integration-key
      remoteRef:
        key: secret/alertmanager
        property: pagerduty-integration-key
    - secretKey: slack-webhook-url
      remoteRef:
        key: secret/alertmanager
        property: slack-webhook-url
```

```bash
kubectl apply -f k8s/base/alertmanager-externalsecret.yml

# Verify ESO created the secret
kubectl get externalsecret alertmanager-secrets -n value-fabric
kubectl get secret alertmanager-secrets -n value-fabric
```

#### 4. Remove Manual Secret

```bash
# Once ExternalSecret is working, delete the manually managed secret
kubectl delete secret alertmanager-secrets -n value-fabric

# ESO will recreate it automatically from Vault
```

### Benefits of ESO + Vault

| Feature | SecretKeyRef | ESO + Vault |
|---------|--------------|-------------|
| **Secret Rotation** | Manual | Automatic (refreshInterval) |
| **Audit Trail** | Limited | Full Vault audit logs |
| **Access Control** | RBAC only | Vault policies + RBAC |
| **Versioning** | No | Yes (Vault versioning) |
| **Multi-cluster** | Copy secrets | Single Vault source |
| **Dynamic Secrets** | No | Yes (database creds, etc.) |

---

## Troubleshooting

### PagerDuty alerts not firing

```bash
# Check Alertmanager logs
kubectl logs -n value-fabric deployment/alertmanager

# Verify secret is mounted
kubectl exec -n value-fabric deployment/alertmanager -- \
  cat /etc/alertmanager/secrets/pagerduty_integration_key

# Test PagerDuty integration manually
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -H "Content-Type: application/json" \
  -d '{
    "routing_key": "YOUR_INTEGRATION_KEY",
    "event_action": "trigger",
    "payload": {
      "summary": "Test alert from Value Fabric",
      "severity": "critical"
    }
  }'
```

### Slack alerts not firing

```bash
# Verify webhook URL is valid
curl -X POST YOUR_SLACK_WEBHOOK_URL \
  -H 'Content-type: application/json' \
  -d '{"text":"Test message from Value Fabric"}'

# Check Alertmanager config is valid
kubectl exec -n value-fabric deployment/alertmanager -- \
  amtool check-config /etc/alertmanager/alertmanager.yml
```

### Alertmanager not starting

```bash
# Check config syntax
kubectl logs -n value-fabric deployment/alertmanager | head -50

# Validate config locally (requires amtool)
amtool check-config monitoring/alertmanager/alertmanager.yml

# Check secret exists
kubectl get secret alertmanager-secrets -n value-fabric -o yaml
```

---

## Security Best Practices

1. **Never commit secrets to git** - Use environment variables or Vault
2. **Rotate secrets regularly** - Set calendar reminders quarterly
3. **Use least privilege** - Alertmanager only needs read access to secrets
4. **Enable audit logging** - Track secret access in Vault or Kubernetes
5. **Encrypt at rest** - Ensure etcd encryption is enabled for Kubernetes secrets

---

## References

- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [External Secrets Operator](https://external-secrets.io/)
- [Vault Kubernetes Auth](https://developer.hashicorp.com/vault/docs/auth/kubernetes)
- [PagerDuty Events API v2](https://developer.pagerduty.com/docs/events-api-v2-overview/)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
