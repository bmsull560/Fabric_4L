# Deployment: dev-nginx

**Status: SUPPORTED.** Composes `envs/dev` + `routing/nginx`.

## Apply

```bash
kubectl apply -k k8s/deployments/dev-nginx
```

## Hosts

| Field | Value |
|---|---|
| Frontend host | `dev.value-fabric.local` |
| API host | `dev-api.value-fabric.local` |

Override by editing `hostname-config.yaml`. The `replacements:` block in
`kustomization.yaml` propagates the ConfigMap values into every Ingress host
and TLS field at render time. Do not hand-edit hosts in routing manifests.

## Validate render

```bash
kustomize build k8s/deployments/dev-nginx | kubeconform -strict -summary -
```

## Required cluster prerequisites

See `k8s/routing/nginx/README.md`.
