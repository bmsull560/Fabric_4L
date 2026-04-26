# Routing Stack: NGINX Ingress

Default supported production routing path for Value Fabric.

## What this stack defines

- `Ingress` resources for the frontend (host `__HOST__`) and layer APIs (host `__API_HOST__`, path-prefixed `/layer1`..`/layer6`).
- `ClusterIssuer` resources for cert-manager Let's Encrypt (prod + staging).

This stack does **not** import `../../base`. It is composed with an env overlay
under `k8s/deployments/<env>-nginx/`, which also provides the `routing-host`
ConfigMap used to substitute `__HOST__` / `__API_HOST__`.

## Required cluster prerequisites

- **NGINX Ingress Controller** with `IngressClass: nginx` available.
  - Typical install: `helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace`.
- **cert-manager** v1.13+ installed cluster-wide.
  - Typical install: `helm upgrade --install cert-manager jetstack/cert-manager -n cert-manager --create-namespace --set installCRDs=true`.
- DNS A records for `__HOST__` and `__API_HOST__` pointing at the NGINX controller's external LoadBalancer IP.

## Apply (via deployment overlay)

```bash
# Supported deployments:
kubectl apply -k k8s/deployments/dev-nginx
kubectl apply -k k8s/deployments/prod-nginx
```

Do not `kubectl apply -k k8s/routing/nginx` directly — it is missing the application workloads.

## Validation

```bash
# Render only:
kustomize build k8s/deployments/prod-nginx | kubeconform -strict -summary -

# Verify TLS certificate issuance:
kubectl -n value-fabric get certificate
kubectl -n value-fabric describe certificate frontend-tls

# Verify ingress is reachable:
curl -I https://<your-host>
```

## Troubleshooting

- **Cert stuck in `Pending`**: confirm the `ClusterIssuer` solver reaches the cluster's external IP and the DNS record exists. `kubectl describe certificaterequest` shows ACME challenge state.
- **404 from NGINX**: confirm Service names in `ingress.yaml` match the rendered Services from the env overlay (`kubectl -n value-fabric get svc`).
- **Sentinel `__HOST__` visible in cluster**: deployment overlay's `replacements:` did not run. Re-render with `kustomize build` and grep the output.
