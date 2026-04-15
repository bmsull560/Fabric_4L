#!/bin/bash
#
# Nikto Web Server Scanner Integration
#
# Performs comprehensive web server vulnerability scanning including:
# - Dangerous files/CGI detection
# - Outdated server software
# - Config problems
# - Injection vulnerabilities
# - Cross-site scripting
# - Authentication issues
#
# Usage:
#   ./nikto-scan.sh --target http://localhost:8000 --output nikto-results.json
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Default values
TARGET=""
OUTPUT_DIR="nikto-results"
TIMEOUT=300
NIKTO_OPTIONS="-C all -maxtime ${TIMEOUT}s"
USE_DOCKER=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --no-docker)
            USE_DOCKER=false
            shift
            ;;
        --help)
            cat << 'EOF'
Nikto Scan Wrapper

Usage: ./nikto-scan.sh [OPTIONS]

Options:
    --target URL        Target URL to scan (required)
    --output DIR        Output directory for results (default: nikto-results)
    --timeout SECONDS   Scan timeout (default: 300)
    --no-docker         Use local Nikto instead of Docker
    --help              Show this help message

Examples:
    ./nikto-scan.sh --target http://localhost:8000
    ./nikto-scan.sh --target https://api.example.com --output audit-results

EOF
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Validate target
if [[ -z "$TARGET" ]]; then
    log_error "Target is required. Use --target URL"
    exit 1
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"
OUTPUT_PATH=$(cd "$OUTPUT_DIR" && pwd)

log_info "Starting Nikto scan against: $TARGET"
log_info "Output directory: $OUTPUT_PATH"

if [[ "$USE_DOCKER" == true ]]; then
    log_info "Using Docker Nikto"
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Install Docker or use --no-docker"
        exit 1
    fi
    
    # Run Nikto in Docker
    docker run --rm \
        -v "${OUTPUT_PATH}:/output:rw" \
        hysnsec/nikto:latest \
        -h "$TARGET" \
        -output /output/nikto-report.txt \
        -Format txt \
        -maxtime "${TIMEOUT}s" \
        -C all \
        2>&1 | tee "${OUTPUT_PATH}/nikto-stdout.log"
    
    # Generate JSON version for CI integration
    docker run --rm \
        -v "${OUTPUT_PATH}:/output:rw" \
        hysnsec/nikto:latest \
        -h "$TARGET" \
        -output /output/nikto-report.json \
        -Format json \
        -maxtime "${TIMEOUT}s" \
        -C all \
        2>&1 | tee -a "${OUTPUT_PATH}/nikto-stdout.log"
else
    log_info "Using local Nikto"
    
    if ! command -v nikto &> /dev/null; then
        log_error "Nikto not found. Install Nikto or use Docker (default)"
        exit 1
    fi
    
    # Run Nikto locally
    nikto -h "$TARGET" \
        -output "${OUTPUT_PATH}/nikto-report.txt" \
        -Format txt \
        -maxtime "${TIMEOUT}s" \
        -C all \
        2>&1 | tee "${OUTPUT_PATH}/nikto-stdout.log"
    
    # Generate JSON version
    nikto -h "$TARGET" \
        -output "${OUTPUT_PATH}/nikto-report.json" \
        -Format json \
        -maxtime "${TIMEOUT}s" \
        -C all \
        2>&1 | tee -a "${OUTPUT_PATH}/nikto-stdout.log"
fi

log_info "Nikto scan completed"

# Parse results and create summary
if [[ -f "${OUTPUT_PATH}/nikto-report.json" ]]; then
    log_info "Generating summary..."
    
    # Count vulnerabilities by severity
    HIGH_COUNT=$(grep -c '"severity".*"High"' "${OUTPUT_PATH}/nikto-report.json" 2>/dev/null || echo "0")
    MEDIUM_COUNT=$(grep -c '"severity".*"Medium"' "${OUTPUT_PATH}/nikto-report.json" 2>/dev/null || echo "0")
    LOW_COUNT=$(grep -c '"severity".*"Low"' "${OUTPUT_PATH}/nikto-report.json" 2>/dev/null || echo "0")
    
    cat > "${OUTPUT_PATH}/summary.json" << EOF
{
    "scan_target": "$TARGET",
    "scan_time": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "scanner": "Nikto",
    "vulnerabilities": {
        "high": $HIGH_COUNT,
        "medium": $MEDIUM_COUNT,
        "low": $LOW_COUNT
    },
    "files": {
        "txt_report": "nikto-report.txt",
        "json_report": "nikto-report.json",
        "stdout_log": "nikto-stdout.log"
    }
}
EOF
    
    log_info "Vulnerability Summary:"
    echo "  High: $HIGH_COUNT"
    echo "  Medium: $MEDIUM_COUNT"
    echo "  Low: $LOW_COUNT"
    
    # Exit with error if high severity found
    if [[ $HIGH_COUNT -gt 0 ]]; then
        log_error "Found $HIGH_COUNT HIGH severity vulnerabilities!"
        exit 1
    fi
else
    log_warn "JSON report not generated"
fi

log_info "Results saved to: $OUTPUT_PATH"
log_info "Text report: ${OUTPUT_PATH}/nikto-report.txt"
log_info "JSON report: ${OUTPUT_PATH}/nikto-report.json"

exit 0
