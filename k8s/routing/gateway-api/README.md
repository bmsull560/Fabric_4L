# Routing Stack: Gateway API (Conditionally Supported)

> **Status: Conditionally Supported.** This routing variant is ready for
> production use when the required cluster prerequisites are met. It is **not**
> the default production deployment path (use `prod-nginx` for that).
>
> **Prerequisites Required:** Gateway API CRDs v1.0+, a GatewayClass controller,
> and cert-manager with Gateway API support must be installed by the cluster
> operator before deployment.

## What this stack defines

- `gateway.networking.k8s.io/v1` `Gateway` with HTTP + HTTPS listeners for
  `__HOST__` (frontend) and `__API_HOST__` (layer APIs).
- `gateway.networking.k8s.io/v1` `HTTPRoute` resources binding listeners to
  Services rendered by the env overlay.
- cert-manager `Certificate` resources providing `frontend-tls` and `layer-apis-tls`.

This stack does **not** import `../../base`. It is composed under
`k8s/deployments/prod-gateway-api/`.

## Required Cluster Prerequisites

Before deploying this routing stack, verify all prerequisites are met:

### 1. Gateway API CRDs v1.0+

```bash
# Install standard channel (recommended)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml

# Verify CRDs are installed
kubectl get crd gateways.gateway.networking.k8s.io httproutes.gateway.networking.k8s.io
```

### 2. GatewayClass Controller

Choose and install a GatewayClass controller. The reference manifests default
to `envoy-gateway` but support `cilium`, `contour`, `istio`, or others.

| Controller | GatewayClass Name | Installation |
|---|---|---|
| Envoy Gateway | `envoy-gateway` | https://gateway.envoyproxy.io/ |
| Cilium | `cilium` | https://docs.cilium.io/en/stable/network/servicemesh/gateway-api/gateway-api/ |
| Contour | `contour` | https://projectcontour.io/docs/main/config/gateway-api/ |
| Istio | `istio` | https://istio.io/latest/docs/tasks/traffic-management/ingress/gateway-api/ |

**To use a different controller:** Edit `gateway.yaml` and change
`spec.gatewayClassName` from `envoy-gateway` to your controller's class name.

Verify the GatewayClass exists:
```bash
kubectl get gatewayclass
# Should show your chosen class (e.g., envoy-gateway) with AGE and CONTROLLER
```

### 3. cert-manager with Gateway API Support

```bash
# Install cert-manager v1.13+ with Gateway API support
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Verify cert-manager is running
kubectl get pods -n cert-manager

# If using versions prior to v1.12, enable Gateway API support:
# --feature-gates=ExperimentalGatewayAPISupport=true
```

### 4. DNS Configuration

After deployment, create DNS A records pointing to the Gateway's external IP:

```bash
# Wait for Gateway to be assigned an IP
kubectl wait -n value-fabric gateway/value-fabric-gateway --for=condition=Programmed

# Get the external IP
kubectl get gateway -n value-fabric value-fabric-gateway -o jsonpath='{.status.addresses[0].value}'

# Create DNS A records:
# app.value-fabric.example.com -> <GATEWAY_IP>
# api.value-fabric.example.com -> <GATEWAY_IP>
```

## Apply

```bash
kustomize build k8s/deployments/prod-gateway-api | kubectl apply -f -
```

## Validation

```bash
kustomize build k8s/deployments/prod-gateway-api | \
  kubeconform -strict -summary \
    -schema-location default \
    -schema-location 'https://raw.githubusercontent.com/datreeio/CRDs-catalog/main/{{.Group}}/{{.ResourceKind}}_{{.ResourceAPIVersion}}.json' \
    -

kubectl -n value-fabric get gateway,httproute,certificate
```

## Troubleshooting

### Gateway `Programmed: False` or `Programmed: Unknown`

The GatewayClass controller is not installed or not watching this namespace:

```bash
# Check GatewayClass exists
kubectl get gatewayclass

# Check Gateway status for details
kubectl describe gateway -n value-fabric value-fabric-gateway

# Verify controller pods are running (example for envoy-gateway)
kubectl get pods -n envoy-gateway-system

# Common fix: Install the GatewayClass controller for your chosen implementation
```

### HTTPRoute `Accepted: False`

Backend Service does not exist or cross-namespace references are not allowed:

```bash
# Verify Services exist
kubectl get services -n value-fabric

# Check HTTPRoute status
kubectl describe httproute -n value-fabric frontend
kubectl describe httproute -n value-fabric layer-apis

# Verify the env overlay rendered Services (should show frontend, layer1-ingestion, etc.)
kustomize build k8s/deployments/prod-gateway-api | grep -A5 "kind: Service"
```

### Certificate not issuing (TLS secrets not created)

```bash
# Check Certificate status
kubectl describe certificate -n value-fabric frontend-tls
kubectl describe certificate -n value-fabric layer-apis-tls

# Verify cert-manager is running
kubectl get pods -n cert-manager

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Common fix: Ensure cert-manager has Gateway API support enabled
```

### Sentinel `__HOST__` visible in cluster

The Kustomize `replacements:` did not run. This happens when the deployment overlay
is not used directly:

```bash
# Always use the deployment overlay, not the routing stack directly
# WRONG: kustomize build k8s/routing/gateway-api
# CORRECT: kustomize build k8s/deployments/prod-gateway-api
```

### DNS not resolving

```bash
# Get the actual Gateway IP
kubectl get gateway -n value-fabric value-fabric-gateway -o jsonpath='{.status.addresses[0].value}'

# Verify DNS records
nslookup app.value-fabric.example.com
nslookup api.value-fabric.example.com

# If using LoadBalancer, ensure the Service type is correct
kubectl get service -n envoy-gateway-system  # (or your controller's namespace)
```
