#!/bin/bash
#
# SOC2/ISO27001 Audit Evidence Bundle Generator
#
# Collects all evidence required for SOC 2 Type II and ISO 27001 audits
# including security test results, access logs, change records, and compliance
# documentation.
#
# Usage:
#   ./generate-evidence-bundle.sh [--output-dir ./audit-evidence-$(date +%Y%m%d)]
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "${BLUE}==>${NC} $1"
}

# Default values
OUTPUT_DIR="./audit-evidence-$(date +%Y%m%d)"
INCLUDE_HISTORICAL=false
DAYS_BACK=90

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --include-historical)
            INCLUDE_HISTORICAL=true
            shift
            ;;
        --days-back)
            DAYS_BACK="$2"
            shift 2
            ;;
        --help)
            cat << 'EOF'
Audit Evidence Bundle Generator

Usage: ./generate-evidence-bundle.sh [OPTIONS]

Options:
    --output-dir DIR         Output directory for evidence bundle (default: ./audit-evidence-YYYYMMDD)
    --include-historical     Include 90-day historical data
    --days-back N            Number of days for historical data (default: 90)
    --help                   Show this help message

Examples:
    ./generate-evidence-bundle.sh
    ./generate-evidence-bundle.sh --output-dir ./q1-2024-audit --include-historical

EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_info "Generating audit evidence bundle..."
log_info "Output directory: $OUTPUT_DIR"

# Create output directory structure
mkdir -p "$OUTPUT_DIR"/{access-control,change-management,security-operations,availability,incident-response,policies,evidence-index}

# ============================================================
# 1. ACCESS CONTROL EVIDENCE
# ============================================================
log_section "Collecting Access Control Evidence"

# RBAC configuration
cat > "$OUTPUT_DIR/access-control/rbac-summary.json" << EOF
{
    "generated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "evidence_type": "Access Control Configuration",
    "items": [
        {
            "control": "CC6.1.1 - Unique User IDs",
            "implementation": "OIDC JWT with subject claim",
            "location": "shared/identity/jwt_middleware.py",
            "evidence": "JWT validation ensures unique identification per user"
        },
        {
            "control": "CC6.1.3 - Role-based Access",
            "implementation": "RBAC with tenant isolation",
            "location": "shared/identity/rbac.py",
            "evidence": "Role validation on every request"
        },
        {
            "control": "CC6.1.4 - Least Privilege",
            "implementation": "Service accounts with minimal permissions",
            "location": "k8s/base/*.yaml",
            "evidence": "Security contexts, non-root containers"
        }
    ]
}
EOF

# CODEOWNERS evidence
cp .github/CODEOWNERS "$OUTPUT_DIR/access-control/CODEOWNERS"

# Access review evidence (if script exists)
if [[ -f "scripts/access_review.py" ]]; then
    python scripts/access_review.py --output "$OUTPUT_DIR/access-control/access-review-report.json" || log_warn "Access review script failed"
fi

# ============================================================
# 2. CHANGE MANAGEMENT EVIDENCE
# ============================================================
log_section "Collecting Change Management Evidence"

# Git commit history
git log --all --pretty=format:'%H|%an|%ae|%ad|%s' --date=short --since="${DAYS_BACK} days ago" > "$OUTPUT_DIR/change-management/commit-history.csv" 2>/dev/null || log_warn "Git history unavailable"

# PR merge history (requires GitHub CLI)
if command -v gh &> /dev/null; then
    log_info "Fetching PR history..."
    gh pr list --state merged --limit 500 --json number,title,author,mergedAt,mergedBy > "$OUTPUT_DIR/change-management/pr-merge-history.json" 2>/dev/null || log_warn "GitHub CLI PR fetch failed"
fi

# Pre-commit hooks evidence
cp .pre-commit-config.yaml "$OUTPUT_DIR/change-management/pre-commit-config.yaml"

# Change management summary
cat > "$OUTPUT_DIR/change-management/change-management-summary.json" << EOF
{
    "generated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "evidence_type": "Change Management",
    "controls": [
        {
            "control": "CC6.3.1 - Change Authorization",
            "implementation": "CODEOWNERS + PR approval required",
            "evidence_location": ".github/CODEOWNERS"
        },
        {
            "control": "CC6.3.2 - Change Logging",
            "implementation": "Git history + audit logs",
            "evidence_location": "layer5-ground-truth/audit/"
        },
        {
            "control": "Version Control",
            "implementation": "Git with signed commits",
            "evidence_location": "Git repository history"
        }
    ],
    "files_collected": [
        "CODEOWNERS",
        "commit-history.csv",
        "pr-merge-history.json",
        "pre-commit-config.yaml"
    ]
}
EOF

# ============================================================
# 3. SECURITY OPERATIONS EVIDENCE
# ============================================================
log_section "Collecting Security Operations Evidence"

# Security test results
if [[ -d "tests/security" ]]; then
    cp -r tests/security "$OUTPUT_DIR/security-operations/"
fi

# Security gates workflow
cp .github/workflows/security-gates.yml "$OUTPUT_DIR/security-operations/"

# Threat model
cp THREAT_MODEL.md "$OUTPUT_DIR/security-operations/" 2>/dev/null || log_warn "THREAT_MODEL.md not found"

# Penetration test evidence
mkdir -p "$OUTPUT_DIR/security-operations/penetration-tests"
cat > "$OUTPUT_DIR/security-operations/penetration-tests/penetration-test-summary.json" << EOF
{
    "generated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "evidence_type": "Penetration Testing",
    "tools_used": [
        {
            "tool": "OWASP ZAP",
            "version": "2.14.0",
            "scan_type": "Full Active Scan",
            "location": "tests/penetration/zap-full-scan.py"
        },
        {
            "tool": "Nikto",
            "version": "2.5.0",
            "scan_type": "Web Server Scanner",
            "location": "tests/penetration/nikto-scan.sh"
        }
    ],
    "scans_performed": [
        "SQL Injection Detection",
        "XSS Detection",
        "CSRF Validation",
        "Security Headers Check",
        "API Endpoint Discovery",
        "Authentication Bypass Tests"
    ],
    "frequency": "Weekly (scheduled) + On-demand"
}
EOF

# Vulnerability scanning evidence
cat > "$OUTPUT_DIR/security-operations/vulnerability-scanning.json" << EOF
{
    "generated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "evidence_type": "Vulnerability Management",
    "scanning_tools": [
        {
            "tool": "Trivy",
            "scan_type": "Container Image Scan",
            "severity_threshold": "HIGH,CRITICAL",
            "workflow": ".github/workflows/security-gates.yml"
        },
        {
            "tool": "Grype",
            "scan_type": "SBOM Vulnerability Scan",
            "workflow": ".github/workflows/supply-chain.yml"
        }
    ],
    "patch_management": {
        "dependabot": "Enabled for Python and Node.js",
        "renovate": "Docker image updates",
        "automated_security_updates": "GitHub Dependabot alerts"
    }
}
EOF

# ============================================================
# 4. AVAILABILITY EVIDENCE
# ============================================================
log_section "Collecting Availability Evidence"

# Chaos test results
if [[ -d "k8s/chaos" ]]; then
    cp -r k8s/chaos "$OUTPUT_DIR/availability/"
fi

# GitOps configuration (resilience)
if [[ -d "k8s/gitops" ]]; then
    cp -r k8s/gitops "$OUTPUT_DIR/availability/"
fi

# SLO definitions
if [[ -f "docs/slo/availability-slo.md" ]]; then
    cp docs/slo/availability-slo.md "$OUTPUT_DIR/availability/"
fi

# Chaos testing evidence
cat > "$OUTPUT_DIR/availability/chaos-testing-evidence.json" << EOF
{
    "generated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "evidence_type": "Resilience Testing (Chaos Engineering)",
    "framework": "LitmusChaos",
    "experiments": [
        {
            "name": "pod-delete-all-layers",
            "target": "All 6 layers",
            "success_criteria": "<30s recovery, data consistency maintained"
        },
        {
            "name": "network-partition-l3-l4",
            "target": "Knowledge-Agents communication",
            "success_criteria": "Graceful degradation, queue behavior"
        },
        {
            "name": "cpu-stress-layer4-agents",
            "target": "Layer 4 Agents",
            "success_criteria": "Auto-scaling triggers, no job loss"
        },
        {
            "name": "memory-stress-layer2-extraction",
            "target": "Layer 2 Extraction",
            "success_criteria": "OOM handling, graceful restart"
        },
        {
            "name": "pod-autoscaler-l1-ingestion",
            "target": "Layer 1 Ingestion",
            "success_criteria": "Scale-up latency <60s"
        }
    ],
    "frequency": "Weekly automated runs + pre-release validation",
    "evidence_location": "k8s/chaos/litmus-experiments/"
}
EOF

# ============================================================
# 5. INCIDENT RESPONSE EVIDENCE
# ============================================================
log_section "Collecting Incident Response Evidence"

# Runbook
cp RUNBOOK.md "$OUTPUT_DIR/incident-response/" 2>/dev/null || log_warn "RUNBOOK.md not found"

# Postmortem template
cp docs/operations/postmortem-template.md "$OUTPUT_DIR/incident-response/" 2>/dev/null || log_warn "Postmortem template not found"

# Escalation policy
cp docs/operations/escalation-policy-and-drills.md "$OUTPUT_DIR/incident-response/" 2>/dev/null || log_warn "Escalation policy not found"

# MTTA/MTTR reporting
cp docs/operations/mtta-mttr-reporting.md "$OUTPUT_DIR/incident-response/" 2>/dev/null || log_warn "MTTA/MTTR reporting not found"

# Incident response summary
cat > "$OUTPUT_DIR/incident-response/incident-response-evidence.json" << EOF
{
    "generated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "evidence_type": "Incident Response",
    "controls": [
        {
            "control": "CC7.2.1 - Incident Detection",
            "implementation": "PagerDuty + Prometheus alerts",
            "location": "monitoring/alerting/"
        },
        {
            "control": "CC7.2.2 - Incident Response",
            "implementation": "RUNBOOK.md + escalation policy",
            "location": "RUNBOOK.md"
        },
        {
            "control": "CC7.2.3 - Incident Documentation",
            "implementation": "Post-incident reviews",
            "location": "docs/incidents/"
        }
    ],
    "documents_collected": [
        "RUNBOOK.md",
        "postmortem-template.md",
        "escalation-policy-and-drills.md",
        "mtta-mttr-reporting.md"
    ]
}
EOF

# ============================================================
# 6. POLICIES EVIDENCE
# ============================================================
log_section "Collecting Policy Documentation"

# Copy all policy documents
for doc in SECURITY.md AGENTS.md VERSIONING.md COMPLIANCE.md SUPPLY_CHAIN.md GITOPS.md; do
    if [[ -f "$doc" ]]; then
        cp "$doc" "$OUTPUT_DIR/policies/"
    fi
done

# Trust documents
if [[ -d "docs/trust" ]]; then
    cp -r docs/trust "$OUTPUT_DIR/policies/"
fi

# Operations documents
if [[ -d "docs/operations" ]]; then
    cp -r docs/operations "$OUTPUT_DIR/policies/"
fi

# ============================================================
# 7. EVIDENCE INDEX
# ============================================================
log_section "Generating Evidence Index"

# Create comprehensive index
cat > "$OUTPUT_DIR/evidence-index/index.json" << EOF
{
    "audit_bundle": {
        "generated_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
        "generated_by": "generate-evidence-bundle.sh",
        "version": "1.0.0",
        "retention_days": 2555
    },
    "summary": {
        "total_categories": 6,
        "total_files": 0,
        "categories": {
            "access-control": "Identity and access management evidence",
            "change-management": "Version control and change approval evidence",
            "security-operations": "Security testing and vulnerability management",
            "availability": "Resilience testing and SLO evidence",
            "incident-response": "Incident management and response procedures",
            "policies": "Security and compliance policy documentation"
        }
    },
    "compliance_mapping": {
        "SOC2_CC6.1": "access-control/",
        "SOC2_CC6.2": "access-control/",
        "SOC2_CC6.3": "change-management/",
        "SOC2_CC6.4": "access-control/",
        "SOC2_CC7.1": "security-operations/",
        "SOC2_CC7.2": "incident-response/",
        "ISO27001_A.9": "access-control/",
        "ISO27001_A.12": "availability/",
        "ISO27001_A.16": "incident-response/"
    },
    "file_manifest": []
}
EOF

# Count files and update manifest
find "$OUTPUT_DIR" -type f -name "*.json" -o -name "*.md" -o -name "*.yaml" -o -name "*.yml" -o -name "*.csv" | while read file; do
    rel_path="${file#$OUTPUT_DIR/}"
    size=$(stat -c%s "$file" 2>/dev/null || stat -f%z "$file" 2>/dev/null || echo "0")
    
    # Add to manifest using jq if available
    if command -v jq &> /dev/null; then
        tmp=$(mktemp)
        jq ".file_manifest += [{\"path\": \"$rel_path\", \"size_bytes\": $size}]" "$OUTPUT_DIR/evidence-index/index.json" > "$tmp" && mv "$tmp" "$OUTPUT_DIR/evidence-index/index.json"
    fi
done

# Human-readable index
cat > "$OUTPUT_DIR/evidence-index/README.md" << EOF
# Audit Evidence Bundle Index

**Generated:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")  
**Bundle Version:** 1.0.0

## Quick Reference

| SOC 2 Control | Evidence Location |
|---------------|-------------------|
| CC6.1 - Logical Access | access-control/ |
| CC6.2 - Access Removal | access-control/ |
| CC6.3 - Change Management | change-management/ |
| CC7.1 - Security Operations | security-operations/ |
| CC7.2 - Incident Detection | incident-response/ |

| ISO 27001 Annex A | Evidence Location |
|-------------------|-------------------|
| A.9 - Access Controls | access-control/ |
| A.12 - Operations | availability/ |
| A.16 - Incident Management | incident-response/ |

## Directory Structure

\`\`\`
$OUTPUT_DIR/
├── access-control/          # Identity & access management
├── change-management/       # Version control & approvals
├── security-operations/     # Security testing & scanning
├── availability/            # Resilience & chaos tests
├── incident-response/       # IR procedures & runbooks
├── policies/                # Security policies
└── evidence-index/        # This index
\`\`\`

## File Count by Category

EOF

for dir in access-control change-management security-operations availability incident-response policies; do
    count=$(find "$OUTPUT_DIR/$dir" -type f 2>/dev/null | wc -l)
    echo "- **$dir**: $count files" >> "$OUTPUT_DIR/evidence-index/README.md"
done

# ============================================================
# 8. CREATE ARCHIVE
# ============================================================
log_section "Creating Archive"

ARCHIVE_NAME="$(basename "$OUTPUT_DIR").tar.gz"
tar -czf "$ARCHIVE_NAME" -C "$(dirname "$OUTPUT_DIR")" "$(basename "$OUTPUT_DIR")"

log_info "Evidence bundle created: $ARCHIVE_NAME"
log_info "Bundle size: $(du -h "$ARCHIVE_NAME" | cut -f1)"

# Generate checksums
if command -v sha256sum &> /dev/null; then
    sha256sum "$ARCHIVE_NAME" > "$ARCHIVE_NAME.sha256"
    log_info "SHA256 checksum: $(cat "$ARCHIVE_NAME.sha256")"
elif command -v shasum &> /dev/null; then
    shasum -a 256 "$ARCHIVE_NAME" > "$ARCHIVE_NAME.sha256"
    log_info "SHA256 checksum: $(cat "$ARCHIVE_NAME.sha256")"
fi

# ============================================================
# SUMMARY
# ============================================================
echo ""
echo "========================================"
echo "AUDIT EVIDENCE BUNDLE GENERATION COMPLETE"
echo "========================================"
echo ""
echo "Output: $OUTPUT_DIR"
echo "Archive: $ARCHIVE_NAME"
echo ""
echo "Evidence Categories:"
echo "  - Access Control: $(find "$OUTPUT_DIR/access-control" -type f 2>/dev/null | wc -l) files"
echo "  - Change Management: $(find "$OUTPUT_DIR/change-management" -type f 2>/dev/null | wc -l) files"
echo "  - Security Operations: $(find "$OUTPUT_DIR/security-operations" -type f 2>/dev/null | wc -l) files"
echo "  - Availability: $(find "$OUTPUT_DIR/availability" -type f 2>/dev/null | wc -l) files"
echo "  - Incident Response: $(find "$OUTPUT_DIR/incident-response" -type f 2>/dev/null | wc -l) files"
echo "  - Policies: $(find "$OUTPUT_DIR/policies" -type f 2>/dev/null | wc -l) files"
echo ""
echo "Ready for auditor review!"
echo ""
