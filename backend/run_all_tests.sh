#!/bin/bash
# Run all backend tests for cross-border tax consultation

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test result tracking
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
START_TIME=$(date +%s)

echo "================================================================================"
echo "CROSS-BORDER TAX CONSULTATION - BACKEND TEST SUITE"
echo "================================================================================"
echo ""
echo "Test Environment:"
echo "  Python Version: $(python --version)"
echo "  Working Directory: $(pwd)"
echo "  Timestamp: $(date)"
echo ""

# Function to run a test and track results
run_test() {
    local test_name=$1
    local test_command=$2
    local test_number=$3
    local total=$4

    echo ""
    echo "--------------------------------------------------------------------------------"
    printf "${BLUE}[%d/%d] Running: %s${NC}\n" "$test_number" "$total" "$test_name"
    echo "--------------------------------------------------------------------------------"

    # Run the test and capture output
    if eval "$test_command"; then
        printf "${GREEN}✓ PASSED${NC} - %s\n" "$test_name"
        ((PASSED_TESTS++))
        return 0
    else
        printf "${RED}✗ FAILED${NC} - %s\n" "$test_name"
        ((FAILED_TESTS++))
        return 1
    fi
}

# Test suite
TOTAL=6

# Test 1: Parser Tests
run_test "Knowledge Base Parser" \
    "python test_parser.py" \
    1 $TOTAL

# Test 2: Tag Assignment Tests
run_test "Tag Assignment Logic" \
    "python test_tag_assignment.py" \
    2 $TOTAL

# Test 3: Question Selection Tests
run_test "Question Selection Logic" \
    "python test_question_selection.py" \
    3 $TOTAL

# Test 4: Intake Workflow Integration Tests
run_test "Intake Workflow Integration" \
    "python test_intake_workflow.py" \
    4 $TOTAL

# Test 5: Parser Debug Tests
run_test "Parser Debug Utilities" \
    "python test_parser_debug.py" \
    5 $TOTAL

# Test 6: Phase 3 E2E Experiments (Run test 1 only for speed)
run_test "Phase 3 E2E Experiments (Quick)" \
    "python test_phase3_experiments.py --test 1" \
    6 $TOTAL

# Calculate duration
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Print summary
echo ""
echo "================================================================================"
echo "TEST SUMMARY"
echo "================================================================================"
echo ""
printf "Total Tests:     %d\n" "$TOTAL"
printf "${GREEN}Passed:          %d${NC}\n" "$PASSED_TESTS"
if [ $FAILED_TESTS -gt 0 ]; then
    printf "${RED}Failed:          %d${NC}\n" "$FAILED_TESTS"
else
    printf "Failed:          %d\n" "$FAILED_TESTS"
fi
printf "Duration:        %ds\n" "$DURATION"
echo ""

# Save results to file
RESULTS_FILE="test-results/test_results_$(date +%Y%m%d_%H%M%S).txt"
mkdir -p test-results
{
    echo "Test Results - $(date)"
    echo "===================="
    echo "Total: $TOTAL"
    echo "Passed: $PASSED_TESTS"
    echo "Failed: $FAILED_TESTS"
    echo "Duration: ${DURATION}s"
} > "$RESULTS_FILE"

echo "Results saved to: $RESULTS_FILE"
echo ""

# Exit with appropriate code
if [ $FAILED_TESTS -eq 0 ]; then
    printf "${GREEN}✅ ALL TESTS PASSED${NC}\n"
    echo "================================================================================"
    exit 0
else
    printf "${RED}❌ SOME TESTS FAILED${NC}\n"
    echo "================================================================================"
    exit 1
fi
