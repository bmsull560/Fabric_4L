# Deployment: prod-nginx

**Status: SUPPORTED — DEFAULT PRODUCTION PATH.** Composes `envs/prod` + `routing/nginx`.

## Apply

```bash
kubectl apply -k k8s/deployments/prod-nginx
```

## Hosts

| Field | Value |
|---|---|
| Frontend host | `app.value-fabric.example.com` |
| API host | `api.value-fabric.example.com` |

Override the production domain by editing `hostname-config.yaml`. The
`replacements:` block propagates the ConfigMap values into every Ingress host
and TLS field at render time.

## Validate render

```bash
kustomize build k8s/deployments/prod-nginx | kubeconform -strict -summary -
kustomize build k8s/deployments/prod-nginx | kubectl apply --dry-run=server -f -
```

## Required cluster prerequisites

See `k8s/routing/nginx/README.md`. In addition, the prod env overlay assumes
ExternalSecrets/Vault integration is installed (see `k8s/external-secrets/`).
