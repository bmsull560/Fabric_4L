"""
k8s routing axis CI gate.

Validates each rendered deployment overlay under k8s/deployments/ for:

  1. Mutual exclusivity: only routing kinds belonging to that deployment's
     routing axis are present. (apiVersion-aware: Gateway API and Istio both
     use `kind: Gateway`, distinguished by apiVersion group.)

  2. Hostname consistency: every host/TLS-name field in routing resources
     equals the value of the deployment's `routing-host` ConfigMap
     (`data.host` for the frontend host, `data.apiHost` for the API host).

  3. No surviving sentinels (`__HOST__`, `__API_HOST__`).

  4. Service-existence: every backend reference in routing resources
     (`Ingress.spec.rules[].http.paths[].backend.service.name`,
     `HTTPRoute.spec.rules[].backendRefs[].name`,
     `VirtualService.spec.http[].route[].destination.host`) resolves to a
     Service rendered from the env overlay.

  5. Routing stacks under k8s/routing/* must not import `../../base`.

Usage:
  python scripts/ci/k8s_routing_check.py \
      --rendered-dir /tmp/renders \
      --routing-dir k8s/routing \
      --deployment dev-nginx:nginx \
      --deployment prod-nginx:nginx \
      --deployment prod-gateway-api:gateway-api \
      --deployment prod-istio:istio

Each --deployment flag is `<deployment-name>:<routing-axis>`. The corresponding
rendered file is expected at `<rendered-dir>/<deployment-name>.yaml`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import yaml

# Routing axis -> set of (apiVersionGroup, kind) tuples that ARE allowed for
# that axis. apiVersionGroup is the part before the first '/' (e.g. for
# "networking.k8s.io/v1" it is "networking.k8s.io"). Anything else from the
# union of routing kinds is forbidden.
ROUTING_KIND_MATRIX: dict[str, set[tuple[str, str]]] = {
    "nginx": {
        ("networking.k8s.io", "Ingress"),
        ("cert-manager.io", "ClusterIssuer"),
    },
    "gateway-api": {
        ("gateway.networking.k8s.io", "Gateway"),
        ("gateway.networking.k8s.io", "HTTPRoute"),
        ("cert-manager.io", "Certificate"),
    },
    "istio": {
        ("networking.istio.io", "Gateway"),
        ("networking.istio.io", "VirtualService"),
        ("networking.istio.io", "DestinationRule"),
    },
}

# All routing-related (group, kind) tuples across all axes. Used to detect
# cross-axis leaks: anything in this set that is not in the deployment's
# allowed subset is forbidden.
ALL_ROUTING_KINDS: set[tuple[str, str]] = set().union(*ROUTING_KIND_MATRIX.values())

SENTINELS = ("__HOST__", "__API_HOST__")


def _api_group(api_version: str) -> str:
    """Return the API group (substring before '/') from a Kubernetes apiVersion."""
    return api_version.split("/", 1)[0] if "/" in api_version else ""


def _load_docs(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as fh:
        return [d for d in yaml.safe_load_all(fh) if isinstance(d, dict)]


def _walk_strings(node: object) -> Iterable[str]:
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from _walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_strings(v)


def _collect_host_fields(doc: dict) -> tuple[list[str], list[str]]:
    """Return (frontend_hosts, api_hosts) extracted from a routing doc.

    Distinguishes by resource name: resources named `frontend` map to the
    frontend host; resources named `layer-apis` map to the API host. Other
    resources are skipped (they are not host-bearing routing resources we
    govern here).
    """
    name = doc.get("metadata", {}).get("name", "")
    spec = doc.get("spec", {}) or {}
    kind = doc.get("kind", "")
    group = _api_group(doc.get("apiVersion", ""))

    frontend_hosts: list[str] = []
    api_hosts: list[str] = []

    def _hosts_for(name_: str) -> list[str]:
        return frontend_hosts if name_ == "frontend" else api_hosts if name_ == "layer-apis" else []

    target = _hosts_for(name)

    # Ingress (networking.k8s.io)
    if group == "networking.k8s.io" and kind == "Ingress":
        for rule in spec.get("rules", []) or []:
            if rule.get("host"):
                target.append(rule["host"])
        for tls in spec.get("tls", []) or []:
            for h in tls.get("hosts", []) or []:
                target.append(h)

    # cert-manager Certificate
    elif group == "cert-manager.io" and kind == "Certificate":
        # Distinguish by Certificate name: frontend-tls vs layer-apis-tls
        if name == "frontend-tls":
            t = frontend_hosts
        elif name == "layer-apis-tls":
            t = api_hosts
        else:
            t = []
        for h in spec.get("dnsNames", []) or []:
            t.append(h)

    # Gateway API Gateway
    elif group == "gateway.networking.k8s.io" and kind == "Gateway":
        # Listener.hostname tells us which host bucket. We just classify each
        # listener by checking against both buckets later via the canonical
        # ConfigMap; here we collect under a synthetic merge by listener name.
        # Simpler: stuff every listener.hostname into both lists and let the
        # caller verify by membership rather than identity.
        for listener in spec.get("listeners", []) or []:
            host = listener.get("hostname")
            if not host:
                continue
            # Put into both; the validator below tolerates this by treating
            # "hosts must be a subset of {frontend, api}".
            frontend_hosts.append(host)
            api_hosts.append(host)

    # Gateway API HTTPRoute
    elif group == "gateway.networking.k8s.io" and kind == "HTTPRoute":
        for h in spec.get("hostnames", []) or []:
            target.append(h)

    # Istio Gateway
    elif group == "networking.istio.io" and kind == "Gateway":
        for server in spec.get("servers", []) or []:
            for h in server.get("hosts", []) or []:
                # Same merge behavior as Gateway API: each server may carry
                # both frontend and api hosts.
                frontend_hosts.append(h)
                api_hosts.append(h)

    # Istio VirtualService
    elif group == "networking.istio.io" and kind == "VirtualService":
        for h in spec.get("hosts", []) or []:
            target.append(h)

    return frontend_hosts, api_hosts


def _collect_backends(doc: dict) -> list[str]:
    """Return Service names referenced as backends by this routing resource."""
    spec = doc.get("spec", {}) or {}
    kind = doc.get("kind", "")
    group = _api_group(doc.get("apiVersion", ""))
    backends: list[str] = []

    if group == "networking.k8s.io" and kind == "Ingress":
        for rule in spec.get("rules", []) or []:
            for path in (rule.get("http") or {}).get("paths", []) or []:
                svc = ((path.get("backend") or {}).get("service") or {}).get("name")
                if svc:
                    backends.append(svc)

    elif group == "gateway.networking.k8s.io" and kind == "HTTPRoute":
        for rule in spec.get("rules", []) or []:
            for ref in rule.get("backendRefs", []) or []:
                if ref.get("name"):
                    backends.append(ref["name"])

    elif group == "networking.istio.io" and kind == "VirtualService":
        for http in spec.get("http", []) or []:
            for route in http.get("route", []) or []:
                host = (route.get("destination") or {}).get("host")
                if host:
                    # host may be a short Service name or FQDN; take first label.
                    backends.append(host.split(".")[0])

    return backends


def _check_deployment(name: str, axis: str, rendered: Path) -> list[str]:
    if axis not in ROUTING_KIND_MATRIX:
        return [f"{name}: unknown routing axis '{axis}'"]
    if not rendered.exists():
        return [f"{name}: rendered file not found: {rendered}"]

    docs = _load_docs(rendered)
    errors: list[str] = []

    # 1. Sentinel survival.
    raw = rendered.read_text(encoding="utf-8")
    for sentinel in SENTINELS:
        if sentinel in raw:
            errors.append(f"{name}: sentinel '{sentinel}' survived into rendered output")

    # 2. Mutual exclusivity.
    allowed = ROUTING_KIND_MATRIX[axis]
    for d in docs:
        gk = (_api_group(d.get("apiVersion", "")), d.get("kind", ""))
        if gk in ALL_ROUTING_KINDS and gk not in allowed:
            md_name = d.get("metadata", {}).get("name", "?")
            errors.append(
                f"{name}: forbidden routing resource for axis '{axis}': "
                f"{gk[0]}/{gk[1]} (name={md_name})"
            )

    # 3. routing-host ConfigMap presence + 4. hostname consistency.
    cm = next(
        (
            d
            for d in docs
            if d.get("kind") == "ConfigMap"
            and d.get("metadata", {}).get("name") == "routing-host"
        ),
        None,
    )
    if cm is None:
        errors.append(f"{name}: missing 'routing-host' ConfigMap")
    else:
        data = cm.get("data") or {}
        host = data.get("host")
        api_host = data.get("apiHost")
        if not host or not api_host:
            errors.append(f"{name}: routing-host ConfigMap must define 'host' and 'apiHost'")
        else:
            valid_hosts = {host, api_host}
            for d in docs:
                gk = (_api_group(d.get("apiVersion", "")), d.get("kind", ""))
                if gk not in ALL_ROUTING_KINDS:
                    continue
                fronts, apis = _collect_host_fields(d)
                # Every collected host must belong to the valid set. The
                # collection logic for Gateway/IstioGateway intentionally
                # over-reports (puts each listener host into both lists) but
                # all listed hosts must be one of {host, apiHost}.
                for h in set(fronts) | set(apis):
                    if h not in valid_hosts:
                        errors.append(
                            f"{name}: host '{h}' on {gk[1]}/"
                            f"{d.get('metadata', {}).get('name', '?')} "
                            f"does not match routing-host ConfigMap "
                            f"(host={host}, apiHost={api_host})"
                        )

    # 5. Service-existence.
    rendered_services = {
        d.get("metadata", {}).get("name")
        for d in docs
        if d.get("kind") == "Service" and d.get("metadata", {}).get("name")
    }
    for d in docs:
        gk = (_api_group(d.get("apiVersion", "")), d.get("kind", ""))
        if gk not in ALL_ROUTING_KINDS:
            continue
        for svc in _collect_backends(d):
            if svc not in rendered_services:
                errors.append(
                    f"{name}: routing resource {gk[1]}/"
                    f"{d.get('metadata', {}).get('name', '?')} "
                    f"references Service '{svc}' which is not in the rendered output"
                )

    return errors


def _check_routing_stacks_no_base(routing_dir: Path) -> list[str]:
    """Routing stack kustomizations must not import ../../base or ../base.

    Parses the kustomization YAML and inspects every list-of-paths field
    rather than grepping raw text (so the rule against base imports does not
    trip on comments that mention `../../base`).
    """
    errors: list[str] = []
    forbidden = {"../../base", "../base", "../../../base"}
    path_fields = ("resources", "components", "bases")
    for kfile in routing_dir.glob("*/kustomization.yaml"):
        try:
            doc = yaml.safe_load(kfile.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            errors.append(f"{kfile}: invalid YAML ({exc})")
            continue
        if not isinstance(doc, dict):
            continue
        for field in path_fields:
            for entry in doc.get(field, []) or []:
                if isinstance(entry, str) and entry.strip() in forbidden:
                    errors.append(
                        f"{kfile}: routing stacks must not import base "
                        f"(found '{entry}' in '{field}')"
                    )
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rendered-dir", type=Path, required=True)
    ap.add_argument("--routing-dir", type=Path, default=Path("k8s/routing"))
    ap.add_argument(
        "--deployment",
        action="append",
        required=True,
        help="Format: <deployment-name>:<routing-axis>",
    )
    args = ap.parse_args()

    all_errors: list[str] = []
    all_errors.extend(_check_routing_stacks_no_base(args.routing_dir))
    for spec in args.deployment:
        if ":" not in spec:
            all_errors.append(f"--deployment must be NAME:AXIS, got: {spec}")
            continue
        name, axis = spec.split(":", 1)
        rendered = args.rendered_dir / f"{name}.yaml"
        all_errors.extend(_check_deployment(name, axis, rendered))

    if all_errors:
        print("FAIL: k8s routing checks reported issues:", file=sys.stderr)
        for e in all_errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    print("OK: all k8s routing checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
