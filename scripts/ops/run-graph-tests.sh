#!/bin/bash
# Run Graph Module Test Suite
# Comprehensive 5-layer test runner
#
# Usage: ./scripts/run-graph-tests.sh [layer]
#   layer: unit | integration | property | performance | contract | all

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Print banner
print_banner() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          Graph Module Test Suite - 5 Layers                ║"
    echo "║                                                            ║"
    echo "║  L1: Unit Tests        (70%)  - Fast, isolated           ║"
    echo "║  L2: Integration Tests (20%)  - API boundaries             ║"
    echo "║  L3: Property Tests    (5%)   - Generative testing         ║"
    echo "║  L4: Performance Tests (5%)   - SLO validation             ║"
    echo "║  L5: Contract Tests    (─)    - Schema validation          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

# Run L1: Unit Tests
run_unit_tests() {
    log_info "Running L1: Unit Tests (70% of test count)"
    echo "─────────────────────────────────────────────"
    
    cd "${PROJECT_ROOT}/frontend"
    
    if pnpm test -- useGraphQuery.comprehensive.test.ts --reporter=verbose; then
        log_success "L1 Unit Tests passed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "L1 Unit Tests failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    echo ""
}

# Run L2: Integration Tests
run_integration_tests() {
    log_info "Running L2: Integration Tests (20% of test count)"
    echo "─────────────────────────────────────────────"
    
    cd "${PROJECT_ROOT}/frontend"
    
    if pnpm test -- useGraphQuery.integration.test.ts --reporter=verbose; then
        log_success "L2 Integration Tests passed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "L2 Integration Tests failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    echo ""
}

# Run L3: Property Tests
run_property_tests() {
    log_info "Running L3: Property Tests (5% of test count)"
    echo "─────────────────────────────────────────────"
    
    cd "${PROJECT_ROOT}/frontend"
    
    if pnpm test -- useGraphQuery.property.test.ts --reporter=verbose; then
        log_success "L3 Property Tests passed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "L3 Property Tests failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    echo ""
}

# Run L4: Performance Tests
run_performance_tests() {
    log_info "Running L4: Performance Tests (5% of test count)"
    echo "─────────────────────────────────────────────"
    echo "SLOs:"
    echo "  - Small graph:  p95 < 100ms"
    echo "  - Medium graph: p95 < 200ms"
    echo "  - Large graph:  p95 < 500ms"
    echo "  - State ops:    p95 < 1ms"
    echo ""
    
    cd "${PROJECT_ROOT}/frontend"
    
    if pnpm test -- useGraphQuery.performance.test.ts --reporter=verbose; then
        log_success "L4 Performance Tests passed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "L4 Performance Tests failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    echo ""
}

# Run L5: Contract Tests
run_contract_tests() {
    log_info "Running L5: Contract Tests"
    echo "─────────────────────────────────────────────"
    
    cd "${PROJECT_ROOT}"
    
    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        log_warn "pytest not found, attempting to run with python -m pytest"
        PYTEST_CMD="python -m pytest"
    else
        PYTEST_CMD="pytest"
    fi
    
    if $PYTEST_CMD tests/contract/test_graph_api_contract.py -v; then
        log_success "L5 Contract Tests passed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        log_error "L5 Contract Tests failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
    echo ""
}

# Run coverage report
run_coverage() {
    log_info "Running coverage report"
    echo "─────────────────────────────────────────────"
    
    cd "${PROJECT_ROOT}/frontend"
    
    pnpm test -- useGraphQuery.comprehensive.test.ts --coverage || true
    
    if [ -f "coverage/index.html" ]; then
        log_info "Coverage report generated: coverage/index.html"
    fi
    echo ""
}

# Print summary
print_summary() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                     Test Summary                           ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    TOTAL=$((TESTS_PASSED + TESTS_FAILED))
    
    echo "Results:"
    echo "  ✅ Passed:  ${TESTS_PASSED}/${TOTAL}"
    echo "  ❌ Failed:  ${TESTS_FAILED}/${TOTAL}"
    echo "  ⏭️  Skipped: ${TESTS_SKIPPED}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}Some tests failed.${NC}"
        return 1
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [layer]"
    echo ""
    echo "Arguments:"
    echo "  layer    Which test layer to run (default: all)"
    echo ""
    echo "Options:"
    echo "  unit         L1: Unit tests only"
    echo "  integration  L2: Integration tests only"
    echo "  property     L3: Property-based tests only"
    echo "  performance  L4: Performance tests only"
    echo "  contract     L5: Contract tests only"
    echo "  coverage     Generate coverage report"
    echo "  all          Run all test layers (default)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all tests"
    echo "  $0 unit              # Run only unit tests"
    echo "  $0 performance       # Run only performance tests"
    echo "  $0 coverage          # Generate coverage report"
}

# Main
main() {
    local LAYER=${1:-all}
    
    # Show usage if --help
    if [ "$LAYER" == "--help" ] || [ "$LAYER" == "-h" ]; then
        show_usage
        exit 0
    fi
    
    print_banner
    
    # Check prerequisites
    if [ ! -d "${PROJECT_ROOT}/frontend" ]; then
        log_error "Frontend directory not found at ${PROJECT_ROOT}/frontend"
        exit 1
    fi
    
    case "$LAYER" in
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        property)
            run_property_tests
            ;;
        performance)
            run_performance_tests
            ;;
        contract)
            run_contract_tests
            ;;
        coverage)
            run_coverage
            ;;
        all)
            run_unit_tests
            run_integration_tests
            run_property_tests
            run_performance_tests
            run_contract_tests
            ;;
        *)
            log_error "Unknown layer: $LAYER"
            show_usage
            exit 1
            ;;
    esac
    
    print_summary
    exit $TESTS_FAILED
}

# Run main
main "$@"
