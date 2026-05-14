#!/usr/bin/env bash
# Usage:
#   bash scripts/deploy-production.sh --tag <release-tag> [options]
#
# Options:
#   --tag <tag>           Release tag to deploy (required)
#   --dry-run             Print commands without executing
#   --skip-image-pull     Skip image pull verification (omits docker requirement)
#   --help                Show this help
#
# Namespace is always read from k8s/overlays/production/kustomization.yaml.
# The --namespace flag is intentionally not supported: the overlay controls
# the namespace and overriding it here would cause apply/rollout to diverge.
#
# Environment: fabric-4l-prod (from overlay)
# Registry:    ghcr.io/bmsull560/fabric_4l

set -euo pipefail

# ---------------------------------------------------------------------------
# Colours / helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; RESET='\033[0m'
pass()  { echo -e "${GREEN}  ✓ $*${RESET}"; }
fail()  { echo -e "${RED}  ✗ $*${RESET}"; }
warn()  { echo -e "${YELLOW}  ⚠ $*${RESET}"; }
info()  { echo -e "${BLUE}  → $*${RESET}"; }
phase() { echo -e "\n${BLUE}━━━ $* ━━━${RESET}"; }

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
RELEASE_TAG=""
DRY_RUN=false
SKIP_IMAGE_PULL=false
REGISTRY="ghcr.io/bmsull560/fabric_4l"

SERVICES=(
  layer1-ingestion layer2-extraction layer3-knowledge
  layer4-agents layer5-ground-truth layer6-benchmarks frontend
)

OVERLAY="k8s/overlays/production"

# ---------------------------------------------------------------------------
# Arg parsing — guard against missing value for flags that require one
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag)
      if [[ $# -lt 2 ]]; then echo "Error: --tag requires a value"; exit 1; fi
      RELEASE_TAG="$2"; shift 2 ;;
    --dry-run)       DRY_RUN=true;         shift ;;
    --skip-image-pull) SKIP_IMAGE_PULL=true; shift ;;
    --help)
      sed -n '/^# Usage:/,/^[^#]/p' "$0" | grep '^#' | sed 's/^# \?//'
      exit 0 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# ---------------------------------------------------------------------------
# Derive namespace from the overlay — single source of truth
# ---------------------------------------------------------------------------
NAMESPACE=$(grep -m1 '^namespace:' "${OVERLAY}/kustomization.yaml" | awk '{print $2}')
if [[ -z "$NAMESPACE" ]]; then
  echo "Error: could not read namespace from ${OVERLAY}/kustomization.yaml"
  exit 1
fi

# ---------------------------------------------------------------------------
# Dry-run wrapper
# ---------------------------------------------------------------------------
run() {
  if [[ "$DRY_RUN" == "true" ]]; then
    echo -e "${YELLOW}[DRY-RUN]${RESET} $*"
  else
    "$@"
  fi
}

# ---------------------------------------------------------------------------
# Phase 0 — Tooling preflight
# ---------------------------------------------------------------------------
phase "Phase 0 — Tooling preflight"

# docker is only required when image pull verification is enabled
if [[ "$SKIP_IMAGE_PULL" == "true" ]]; then
  REQUIRED_TOOLS=(git kubectl curl kustomize)
else
  REQUIRED_TOOLS=(git docker kubectl curl kustomize)
fi

MISSING=()
for tool in "${REQUIRED_TOOLS[@]}"; do
  if command -v "$tool" &>/dev/null; then
    pass "$tool: $(command -v "$tool")"
  else
    fail "$tool: not found"
    MISSING+=("$tool")
  fi
done

if [[ ${#MISSING[@]} -gt 0 ]]; then
  echo -e "\n${RED}Missing required tools: ${MISSING[*]}${RESET}"
  exit 1
fi

# ---------------------------------------------------------------------------
# Phase 1 — Validate inputs
# ---------------------------------------------------------------------------
phase "Phase 1 — Validate inputs"

if [[ -z "$RELEASE_TAG" ]]; then
  fail "--tag is required"
  exit 1
fi

if [[ "$RELEASE_TAG" == "latest" ]] || [[ "$RELEASE_TAG" =~ ^(main|master|develop|dev|staging|production)$ ]]; then
  fail "Mutable tag '$RELEASE_TAG' is not allowed for production deploys"
  exit 1
fi

pass "Release tag: $RELEASE_TAG"
pass "Namespace:   $NAMESPACE (from $OVERLAY/kustomization.yaml)"
pass "Overlay:     $OVERLAY"
[[ "$DRY_RUN" == "true" ]]       && warn "DRY-RUN mode — no changes will be applied"
[[ "$SKIP_IMAGE_PULL" == "true" ]] && warn "Image pull verification skipped"

# ---------------------------------------------------------------------------
# Phase 2 — CI gate (requires gh CLI)
# ---------------------------------------------------------------------------
phase "Phase 2 — CI gate"

if ! command -v gh &>/dev/null; then
  fail "gh CLI not found — CI gate cannot be verified"
  echo "Install gh: https://cli.github.com/"
  exit 1
fi

# Resolve the commit SHA the tag points to so we can query runs by commit.
COMMIT_SHA=$(git rev-list -n1 "$RELEASE_TAG" 2>/dev/null || echo "")
if [[ -z "$COMMIT_SHA" ]]; then
  fail "Tag $RELEASE_TAG not found in local git history — cannot resolve commit SHA"
  exit 1
fi
info "Resolved $RELEASE_TAG → $COMMIT_SHA"

ALL_PASSED=true
WORKFLOWS=("PR Checks" "Security Gates" "Smoke Gate")
for wf in "${WORKFLOWS[@]}"; do
  STATUS=$(gh run list --workflow="$wf" --commit="$COMMIT_SHA" --limit=1 --json conclusion --jq '.[0].conclusion' 2>/dev/null || echo "")
  if [[ "$STATUS" == "success" ]]; then
    pass "$wf: success"
  elif [[ -z "$STATUS" ]]; then
    fail "$wf: no workflow run found for commit $COMMIT_SHA ($RELEASE_TAG)"
    ALL_PASSED=false
  else
    fail "$wf: $STATUS"
    ALL_PASSED=false
  fi
done

if [[ "$ALL_PASSED" != "true" ]]; then
  echo -e "\n${RED}CI gate failed — aborting deploy${RESET}"
  exit 1
fi

CI_GATE_STATUS="passed"

# ---------------------------------------------------------------------------
# Phase 3 — Image pull verification
# ---------------------------------------------------------------------------
phase "Phase 3 — Image pull verification"

IMAGE_PULL_STATUS="skipped"
if [[ "$SKIP_IMAGE_PULL" == "false" ]]; then
  for svc in "${SERVICES[@]}"; do
    IMAGE="${REGISTRY}/${svc}:${RELEASE_TAG}"
    info "Pulling $IMAGE ..."
    if run docker pull "$IMAGE" > /dev/null; then
      pass "$svc"
    else
      fail "$svc: pull failed"
      exit 1
    fi
  done
  IMAGE_PULL_STATUS="passed"
else
  warn "Skipping image pull verification (--skip-image-pull)"
fi

# ---------------------------------------------------------------------------
# Phase 4 — Working tree cleanliness
# ---------------------------------------------------------------------------
phase "Phase 4 — Working tree cleanliness"

# Use porcelain to catch untracked files as well as tracked changes
DIRTY=$(git status --porcelain)
if [[ -z "$DIRTY" ]]; then
  pass "Working tree is clean"
else
  fail "Working tree has uncommitted or untracked changes:"
  echo "$DIRTY"
  exit 1
fi

# ---------------------------------------------------------------------------
# Phase 5 — Version alignment: all services must match RELEASE_TAG
# ---------------------------------------------------------------------------
phase "Phase 5 — Version alignment"

KUSTOMIZATION="${OVERLAY}/kustomization.yaml"
MISMATCHED=()
ALL_TAGS=()

while IFS= read -r tag; do
  ALL_TAGS+=("$tag")
  if [[ "$tag" != "$RELEASE_TAG" ]]; then
    MISMATCHED+=("$tag")
  fi
done < <(grep 'newTag:' "$KUSTOMIZATION" | awk '{print $2}')

if [[ ${#ALL_TAGS[@]} -eq 0 ]]; then
  fail "No newTag entries found in $KUSTOMIZATION — cannot verify version alignment (overlay may use digest pinning)"
  exit 1
fi

if [[ ${#MISMATCHED[@]} -gt 0 ]]; then
  fail "Version mismatch in $KUSTOMIZATION — expected all newTag entries to be $RELEASE_TAG, found: ${MISMATCHED[*]}"
  exit 1
fi

pass "All ${#ALL_TAGS[@]} service image tags in overlay match $RELEASE_TAG"

# ---------------------------------------------------------------------------
# Phase 6 — Deploy
# ---------------------------------------------------------------------------
phase "Phase 6 — Deploy"

info "Creating namespace $NAMESPACE if it does not exist ..."
if [[ "$DRY_RUN" == "true" ]]; then
  echo -e "${YELLOW}[DRY-RUN]${RESET} kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -"
else
  kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
fi

info "Applying $OVERLAY ..."
run kubectl apply -k "$OVERLAY"

info "Waiting for rollouts (10m timeout each) ..."
ROLLOUT_ERRORS=()
for deploy in "${SERVICES[@]}"; do
  echo -n "  $deploy ... "
  if run kubectl rollout status "deployment/$deploy" -n "$NAMESPACE" --timeout=10m 2>&1; then
    echo -e "${GREEN}OK${RESET}"
  else
    echo -e "${RED}FAILED${RESET}"
    ROLLOUT_ERRORS+=("$deploy")
  fi
done

if [[ ${#ROLLOUT_ERRORS[@]} -gt 0 ]]; then
  fail "Rollout failed for: ${ROLLOUT_ERRORS[*]}"
  exit 1
fi

pass "All rollouts healthy in namespace $NAMESPACE"

# ---------------------------------------------------------------------------
# Phase 7 — Health checks
# ---------------------------------------------------------------------------
phase "Phase 7 — Health checks"

BASE_URL="https://api.production.value-fabric.com"
ENDPOINTS=("/health" "/health/version" "/api/v1/health")

for ep in "${ENDPOINTS[@]}"; do
  url="${BASE_URL}${ep}"
  info "Checking $url ..."
  if run curl -fsS --max-time 30 "$url" > /dev/null; then
    pass "$ep"
  else
    fail "$ep: health check failed"
    exit 1
  fi
done

# ---------------------------------------------------------------------------
# Phase 8 — Evidence
# ---------------------------------------------------------------------------
phase "Phase 8 — Evidence"

DEPLOY_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
COMMIT_SHA=$(git rev-parse HEAD)
DEPLOYER="${USER:-unknown}"
# Sanitize tag for use in filename (replace : with - for digest refs)
SAFE_TAG="${RELEASE_TAG//:/- }"
SAFE_TAG="${SAFE_TAG// /}"
EVIDENCE_FILE=".deployments/$(date -u +%Y-%m-%d)-${SAFE_TAG}.md"

mkdir -p .deployments

cat > "$EVIDENCE_FILE" << EOF
# Deployment Evidence — ${RELEASE_TAG}

Date:      ${DEPLOY_TIME}
Tag:       ${RELEASE_TAG}
Commit:    ${COMMIT_SHA}
Namespace: ${NAMESPACE}
Deployer:  ${DEPLOYER}

## Gates

- Phase 2 CI gate:          ${CI_GATE_STATUS}
- Phase 3 image pull:       ${IMAGE_PULL_STATUS}
- Phase 5 version alignment: passed
- Phase 6 rollout:          passed
- Phase 7 health checks:    passed

## Services deployed

$(for svc in "${SERVICES[@]}"; do echo "- ${REGISTRY}/${svc}:${RELEASE_TAG}"; done)
EOF

pass "Evidence written to $EVIDENCE_FILE"

echo -e "\n${GREEN}━━━ Deploy complete: $RELEASE_TAG → $NAMESPACE ━━━${RESET}\n"
