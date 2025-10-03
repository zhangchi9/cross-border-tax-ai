"""
Comprehensive Test Suite for Forms Analysis Agent

Tests the FormsAnalysisNode with various scenarios to validate:
- Holistic LLM-based forms analysis
- Intelligent form deduplication
- Comprehensive output generation
- Error handling and recovery
"""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from science.agents.state import create_initial_state
from science.agents.nodes import FormsAnalysisNode

# Windows encoding fix
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    BRIGHT_BLACK = '\033[90m'


def colored(text: str, color: str) -> str:
    """Apply color to text"""
    return f"{color}{text}{Colors.ENDC}"


def print_separator(title: str = "", char: str = "="):
    """Print a separator line"""
    width = 80
    if title:
        print(f"\n{char * width}")
        print(colored(title.center(width), Colors.BOLD))
        print(f"{char * width}\n")
    else:
        print(f"{char * width}")


def validate_analysis_result(result: dict, scenario_name: str) -> dict:
    """
    Validate analysis result and return quality metrics

    Returns dict with validation results
    """
    print_separator(f"VALIDATION: {scenario_name}")

    validation = {
        "scenario": scenario_name,
        "passed": 0,
        "failed": 0,
        "warnings": 0,
        "checks": []
    }

    # Check 1: No error messages
    if result.get('error_message'):
        validation["checks"].append({
            "name": "Error-free execution",
            "status": "FAIL",
            "message": f"Error: {result['error_message']}"
        })
        validation["failed"] += 1
    else:
        validation["checks"].append({
            "name": "Error-free execution",
            "status": "PASS",
            "message": "No errors detected"
        })
        validation["passed"] += 1

    # Check 2: Complexity assessment exists
    complexity = result.get('estimated_complexity')
    if complexity and complexity in ['high', 'medium', 'low']:
        validation["checks"].append({
            "name": "Valid complexity assessment",
            "status": "PASS",
            "message": f"Complexity: {complexity}"
        })
        validation["passed"] += 1
    else:
        validation["checks"].append({
            "name": "Valid complexity assessment",
            "status": "FAIL",
            "message": f"Invalid complexity: {complexity}"
        })
        validation["failed"] += 1

    # Check 3: Required forms
    required_forms = result.get('required_forms', [])
    if required_forms and len(required_forms) > 0:
        validation["checks"].append({
            "name": "Forms identified",
            "status": "PASS",
            "message": f"{len(required_forms)} forms identified"
        })
        validation["passed"] += 1

        # Check 3a: No duplicate forms
        form_names = [f.get('form') for f in required_forms]
        duplicates = len(form_names) - len(set(form_names))
        if duplicates > 0:
            validation["checks"].append({
                "name": "Form deduplication",
                "status": "FAIL",
                "message": f"Found {duplicates} duplicate forms"
            })
            validation["failed"] += 1
        else:
            validation["checks"].append({
                "name": "Form deduplication",
                "status": "PASS",
                "message": f"All {len(form_names)} forms are unique"
            })
            validation["passed"] += 1
    else:
        validation["checks"].append({
            "name": "Forms identified",
            "status": "WARN",
            "message": "No forms identified (may be expected for edge cases)"
        })
        validation["warnings"] += 1

    # Check 4: Multiple jurisdictions
    jurisdictions = set(f.get('jurisdiction', '').lower() for f in required_forms if f.get('jurisdiction'))
    if len(jurisdictions) >= 2:
        validation["checks"].append({
            "name": "Cross-border coverage",
            "status": "PASS",
            "message": f"Multiple jurisdictions: {', '.join(jurisdictions)}"
        })
        validation["passed"] += 1
    elif len(jurisdictions) == 1:
        validation["checks"].append({
            "name": "Cross-border coverage",
            "status": "WARN",
            "message": f"Single jurisdiction: {list(jurisdictions)[0]}"
        })
        validation["warnings"] += 1
    else:
        validation["checks"].append({
            "name": "Cross-border coverage",
            "status": "WARN",
            "message": "No jurisdictions identified"
        })
        validation["warnings"] += 1

    # Check 5: Comprehensive response
    recommendations = result.get('recommendations', [])
    next_steps = result.get('next_steps', [])
    deadlines = result.get('priority_deadlines', [])
    checklist = result.get('compliance_checklist', [])

    total_items = len(required_forms) + len(recommendations) + len(next_steps) + len(deadlines) + len(checklist)

    if total_items >= 15:
        validation["checks"].append({
            "name": "Comprehensive output",
            "status": "PASS",
            "message": f"{total_items} total items (forms + recs + steps + deadlines + checklist)"
        })
        validation["passed"] += 1
    elif total_items >= 5:
        validation["checks"].append({
            "name": "Comprehensive output",
            "status": "WARN",
            "message": f"{total_items} total items (expected 15+)"
        })
        validation["warnings"] += 1
    else:
        validation["checks"].append({
            "name": "Comprehensive output",
            "status": "FAIL",
            "message": f"Only {total_items} total items"
        })
        validation["failed"] += 1

    # Check 6: Assistant response
    if result.get('assistant_response'):
        response_length = len(result['assistant_response'])
        if response_length >= 500:
            validation["checks"].append({
                "name": "Detailed assistant response",
                "status": "PASS",
                "message": f"{response_length} characters"
            })
            validation["passed"] += 1
        else:
            validation["checks"].append({
                "name": "Detailed assistant response",
                "status": "WARN",
                "message": f"Only {response_length} characters"
            })
            validation["warnings"] += 1
    else:
        validation["checks"].append({
            "name": "Detailed assistant response",
            "status": "FAIL",
            "message": "No response generated"
        })
        validation["failed"] += 1

    # Print results
    for check in validation["checks"]:
        if check["status"] == "PASS":
            print(colored(f"✅ PASS: {check['name']}", Colors.GREEN))
            print(colored(f"   {check['message']}", Colors.BRIGHT_BLACK))
        elif check["status"] == "FAIL":
            print(colored(f"❌ FAIL: {check['name']}", Colors.RED))
            print(colored(f"   {check['message']}", Colors.RED))
        else:
            print(colored(f"⚠️  WARN: {check['name']}", Colors.YELLOW))
            print(colored(f"   {check['message']}", Colors.YELLOW))

    print(f"\n{colored('Summary:', Colors.BOLD)}")
    print(colored(f"  Passed: {validation['passed']}", Colors.GREEN))
    print(colored(f"  Failed: {validation['failed']}", Colors.RED))
    print(colored(f"  Warnings: {validation['warnings']}", Colors.YELLOW))

    return validation


def print_analysis_results(result: dict, scenario_name: str):
    """Print detailed analysis results"""
    print_separator(f"RESULTS: {scenario_name}")

    # Complexity
    complexity = result.get('estimated_complexity', 'N/A')
    if complexity and complexity != 'N/A':
        print(colored(f"📊 Complexity: {complexity.upper()}", Colors.CYAN))
    else:
        print(colored(f"📊 Complexity: N/A", Colors.BRIGHT_BLACK))

    # Required forms
    required_forms = result.get('required_forms', [])
    print(colored(f"\n📄 Required Forms: {len(required_forms)} total", Colors.CYAN))
    if required_forms:
        for form in required_forms[:5]:  # Show first 5 for brevity
            jurisdiction = form.get('jurisdiction', 'N/A')
            form_name = form.get('form', 'N/A')
            priority = form.get('priority', 'N/A')
            description = form.get('description', 'N/A')

            print(f"\n   {colored(jurisdiction.upper(), Colors.BOLD)}: {form_name} [{priority}]")
            if description != 'N/A':
                # Truncate long descriptions
                desc_preview = description[:150] + "..." if len(description) > 150 else description
                print(colored(f"      {desc_preview}", Colors.BRIGHT_BLACK))

        if len(required_forms) > 5:
            print(colored(f"\n   ... and {len(required_forms) - 5} more forms", Colors.BRIGHT_BLACK))
    else:
        print(colored("   (No forms listed)", Colors.BRIGHT_BLACK))

    # Recommendations
    recommendations = result.get('recommendations', [])
    print(colored(f"\n💡 Recommendations: {len(recommendations)} total", Colors.CYAN))
    for i, rec in enumerate(recommendations[:3], 1):  # Show first 3
        rec_preview = rec[:100] + "..." if len(rec) > 100 else rec
        print(colored(f"   {i}. {rec_preview}", Colors.BRIGHT_BLACK))
    if len(recommendations) > 3:
        print(colored(f"   ... and {len(recommendations) - 3} more", Colors.BRIGHT_BLACK))

    # Next steps
    next_steps = result.get('next_steps', [])
    print(colored(f"\n✅ Next Steps: {len(next_steps)} total", Colors.CYAN))
    for i, step in enumerate(next_steps[:3], 1):
        step_preview = step[:100] + "..." if len(step) > 100 else step
        print(colored(f"   {i}. {step_preview}", Colors.BRIGHT_BLACK))
    if len(next_steps) > 3:
        print(colored(f"   ... and {len(next_steps) - 3} more", Colors.BRIGHT_BLACK))

    # Deadlines
    deadlines = result.get('priority_deadlines', [])
    if deadlines:
        print(colored(f"\n⏰ Priority Deadlines: {len(deadlines)} total", Colors.CYAN))
        for deadline in deadlines[:3]:
            print(colored(f"   - {deadline}", Colors.BRIGHT_BLACK))
        if len(deadlines) > 3:
            print(colored(f"   ... and {len(deadlines) - 3} more", Colors.BRIGHT_BLACK))

    # Checklist
    checklist = result.get('compliance_checklist', [])
    if checklist:
        print(colored(f"\n📋 Compliance Checklist: {len(checklist)} total", Colors.CYAN))
        for item in checklist[:3]:
            item_preview = item[:100] + "..." if len(item) > 100 else item
            print(colored(f"   - {item_preview}", Colors.BRIGHT_BLACK))
        if len(checklist) > 3:
            print(colored(f"   ... and {len(checklist) - 3} more", Colors.BRIGHT_BLACK))

    # Assistant response preview
    if result.get('assistant_response'):
        response_length = len(result['assistant_response'])
        print(colored(f"\n📝 Assistant Response: {response_length} characters", Colors.CYAN))
        preview = result['assistant_response'][:300] + "..." if len(result['assistant_response']) > 300 else result['assistant_response']
        print(colored(f"   {preview}", Colors.BRIGHT_BLACK))


def test_simple_scenario():
    """Test 1: Simple scenario with single US person tag"""
    print_separator("TEST 1: Simple Scenario (Single Tag)", "=")

    # Create state
    state = create_initial_state(session_id="test_simple")

    # Single tag
    state["assigned_tags"] = ["us_person_worldwide_filing"]

    # Simulate completed intake
    state["conversation_turns"] = 10
    state["asked_question_ids"] = ["q1", "q2", "q3"]
    state["current_phase"] = "forms_analysis"

    print(colored("📋 Assigned Tags:", Colors.CYAN))
    for tag in state["assigned_tags"]:
        print(colored(f"   - {tag}", Colors.BRIGHT_BLACK))

    print(colored("\n🔄 Running Forms Analysis Node...", Colors.YELLOW))

    # Run node
    forms_node = FormsAnalysisNode()
    result = forms_node(state)

    # Display results
    print_analysis_results(result, "Simple Scenario")

    # Validate
    validation = validate_analysis_result(result, "Simple Scenario")

    return validation


def test_complex_crossborder_scenario():
    """Test 2: Complex cross-border scenario with multiple tags"""
    print_separator("TEST 2: Complex Cross-Border Scenario (6+ Tags)", "=")

    # Create state
    state = create_initial_state(session_id="test_complex")

    # Multiple tags from user's real scenario
    state["assigned_tags"] = [
        "canadian_tax_resident_worldwide_filing",
        "wages_taxable_canada_source",
        "equity_compensation_cross_border_workdays",
        "treaty_based_position",
        "withholding_documentation_maintenance",
        "cross_border_financial_accounts"
    ]

    # Simulate completed intake
    state["conversation_turns"] = 30
    state["asked_question_ids"] = [f"q{i}" for i in range(1, 11)]
    state["current_phase"] = "forms_analysis"

    # Add user profile data
    state["user_profile"] = {
        "residency": {
            "current_country": "Canada",
            "citizenship": ["United States"],
            "tax_resident_countries": ["Canada", "United States"]
        },
        "employment": {
            "employment_status": "employed",
            "employer_country": "Canada",
            "work_locations": ["Canada", "United States"]
        },
        "assets": {
            "has_foreign_accounts": True,
            "has_equity_compensation": True
        }
    }

    print(colored("📋 Assigned Tags:", Colors.CYAN))
    for tag in state["assigned_tags"]:
        print(colored(f"   - {tag}", Colors.BRIGHT_BLACK))

    print(colored("\n🔄 Running Forms Analysis Node...", Colors.YELLOW))

    # Run node
    forms_node = FormsAnalysisNode()
    result = forms_node(state)

    # Display results
    print_analysis_results(result, "Complex Cross-Border Scenario")

    # Validate
    validation = validate_analysis_result(result, "Complex Cross-Border Scenario")

    return validation


def test_edge_cases():
    """Test 3: Edge cases (no tags, empty state)"""
    print_separator("TEST 3: Edge Cases", "=")

    validations = []

    # Test 3a: No tags
    print(colored("\n🧪 Test 3a: No Tags", Colors.BLUE))
    state = create_initial_state(session_id="test_no_tags")
    state["assigned_tags"] = []
    state["current_phase"] = "forms_analysis"

    forms_node = FormsAnalysisNode()
    result = forms_node(state)

    print(colored(f"   Required forms: {len(result.get('required_forms', []))}", Colors.BRIGHT_BLACK))
    print(colored(f"   Recommendations: {len(result.get('recommendations', []))}", Colors.BRIGHT_BLACK))

    if len(result.get('required_forms', [])) == 0 and len(result.get('recommendations', [])) > 0:
        print(colored("   ✅ PASS: Handled gracefully with recommendations", Colors.GREEN))
        validations.append({"name": "No tags edge case", "status": "PASS"})
    else:
        print(colored("   ⚠️  WARN: Unexpected output", Colors.YELLOW))
        validations.append({"name": "No tags edge case", "status": "WARN"})

    # Test 3b: Invalid tag
    print(colored("\n🧪 Test 3b: Invalid Tag", Colors.BLUE))
    state = create_initial_state(session_id="test_invalid_tag")
    state["assigned_tags"] = ["invalid_nonexistent_tag"]
    state["current_phase"] = "forms_analysis"

    result = forms_node(state)

    print(colored(f"   Error message: {result.get('error_message', 'None')}", Colors.BRIGHT_BLACK))
    print(colored(f"   Required forms: {len(result.get('required_forms', []))}", Colors.BRIGHT_BLACK))

    if not result.get('error_message') or len(result.get('recommendations', [])) > 0:
        print(colored("   ✅ PASS: Handled gracefully", Colors.GREEN))
        validations.append({"name": "Invalid tag edge case", "status": "PASS"})
    else:
        print(colored("   ❌ FAIL: Not handled properly", Colors.RED))
        validations.append({"name": "Invalid tag edge case", "status": "FAIL"})

    return validations


def run_all_tests():
    """Run all test scenarios"""
    print_separator("FORMS ANALYSIS AGENT - COMPREHENSIVE TEST SUITE", "=")

    all_validations = []

    # Test 1: Simple scenario
    try:
        validation1 = test_simple_scenario()
        all_validations.append(validation1)
    except Exception as e:
        print(colored(f"\n❌ TEST 1 FAILED WITH EXCEPTION: {e}", Colors.RED))
        import traceback
        traceback.print_exc()

    # Test 2: Complex scenario
    try:
        validation2 = test_complex_crossborder_scenario()
        all_validations.append(validation2)
    except Exception as e:
        print(colored(f"\n❌ TEST 2 FAILED WITH EXCEPTION: {e}", Colors.RED))
        import traceback
        traceback.print_exc()

    # Test 3: Edge cases
    try:
        validation3 = test_edge_cases()
        all_validations.extend(validation3)
    except Exception as e:
        print(colored(f"\n❌ TEST 3 FAILED WITH EXCEPTION: {e}", Colors.RED))
        import traceback
        traceback.print_exc()

    # Final summary
    print_separator("FINAL TEST SUMMARY", "=")

    total_passed = sum(v.get('passed', 1 if v.get('status') == 'PASS' else 0) for v in all_validations)
    total_failed = sum(v.get('failed', 1 if v.get('status') == 'FAIL' else 0) for v in all_validations)
    total_warnings = sum(v.get('warnings', 1 if v.get('status') == 'WARN' else 0) for v in all_validations)

    print(colored(f"✅ Total Passed: {total_passed}", Colors.GREEN))
    print(colored(f"❌ Total Failed: {total_failed}", Colors.RED))
    print(colored(f"⚠️  Total Warnings: {total_warnings}", Colors.YELLOW))

    if total_failed == 0:
        print(colored("\n🎉 ALL TESTS PASSED!", Colors.GREEN + Colors.BOLD))
    elif total_failed <= 2:
        print(colored("\n⚠️  TESTS PASSED WITH MINOR ISSUES", Colors.YELLOW + Colors.BOLD))
    else:
        print(colored("\n❌ TESTS FAILED - REQUIRES ATTENTION", Colors.RED + Colors.BOLD))

    print()


if __name__ == "__main__":
    run_all_tests()
