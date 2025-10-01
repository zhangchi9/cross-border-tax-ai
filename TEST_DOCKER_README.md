# Docker Test Container Guide

Run all backend tests in an isolated Docker container with a single command.

## Quick Start

```bash
# Run all tests
make test

# Or use docker-compose directly
docker-compose -f docker-compose.test.yml up --build
```

## What Tests Are Run?

The test container runs all backend tests in sequence:

1. **Knowledge Base Parser** - Validates markdown → JSON conversion
2. **Tag Assignment Logic** - Tests LLM-based tag assignment
3. **Question Selection** - Validates question flow logic
4. **Intake Workflow Integration** - Tests complete intake process
5. **Parser Debug Utilities** - Validates parser debugging tools
6. **Phase 3 E2E Experiments** - Tests Phase 3 enhancements (quick mode)

## Available Commands

### Basic Testing

```bash
# Run all tests (recommended)
make test

# Build test container without running
make test-build

# View test logs
make test-logs
```

### Advanced Testing

```bash
# Interactive shell for manual testing
make test-shell

# Run specific test file
make test-specific TEST=test_phase3_experiments.py

# Run with coverage report
make test-coverage

# Clean up test containers and results
make test-clean
```

### Docker Compose Commands

```bash
# Run all tests
docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

# Interactive shell
docker-compose -f docker-compose.test.yml run tests bash

# Run specific test
docker-compose -f docker-compose.test.yml run tests python test_parser.py

# Run Phase 3 experiments with specific test
docker-compose -f docker-compose.test.yml run tests python test_phase3_experiments.py --test 1

# Run Phase 3 interactive mode
docker-compose -f docker-compose.test.yml run tests python test_phase3_experiments.py --interactive
```

## Expected Output

```
================================================================================
CROSS-BORDER TAX CONSULTATION - BACKEND TEST SUITE
================================================================================

Test Environment:
  Python Version: Python 3.11.x
  Working Directory: /app/backend
  Timestamp: 2025-10-01 10:30:45

--------------------------------------------------------------------------------
[1/6] Running: Knowledge Base Parser
--------------------------------------------------------------------------------
✓ PASSED - Knowledge Base Parser

--------------------------------------------------------------------------------
[2/6] Running: Tag Assignment Logic
--------------------------------------------------------------------------------
✓ PASSED - Tag Assignment Logic

--------------------------------------------------------------------------------
[3/6] Running: Question Selection Logic
--------------------------------------------------------------------------------
✓ PASSED - Question Selection Logic

--------------------------------------------------------------------------------
[4/6] Running: Intake Workflow Integration
--------------------------------------------------------------------------------
✓ PASSED - Intake Workflow Integration

--------------------------------------------------------------------------------
[5/6] Running: Parser Debug Utilities
--------------------------------------------------------------------------------
✓ PASSED - Parser Debug Utilities

--------------------------------------------------------------------------------
[6/6] Running: Phase 3 E2E Experiments (Quick)
--------------------------------------------------------------------------------
✓ PASSED - Phase 3 E2E Experiments (Quick)

================================================================================
TEST SUMMARY
================================================================================

Total Tests:     6
Passed:          6
Failed:          0
Duration:        45s

Results saved to: test-results/test_results_20251001_103045.txt

✅ ALL TESTS PASSED
================================================================================
```

## Test Results

Test results are saved to `test-results/` directory on your host machine:

```
test-results/
├── test_results_20251001_103045.txt
├── test_results_20251001_104522.txt
└── ...
```

Each result file contains:
- Timestamp
- Total tests run
- Passed/Failed counts
- Duration

## Interactive Testing

For manual testing and debugging:

```bash
# Access test shell
make test-shell

# Inside the container, you can run:
python test_parser.py
python test_phase3_experiments.py --test 1
python test_phase3_experiments.py --interactive
pytest --cov
```

## Configuration

### Environment Variables

Set in `.env` file at project root:

```env
OPENAI_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

### Test Configuration

Edit `backend/pytest.ini` to customize pytest behavior:

```ini
[pytest]
python_files = test_*.py
testpaths = .
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
```

### Test Script

Modify `backend/run_all_tests.sh` to add/remove tests or change execution order.

## Troubleshooting

### Tests Fail to Start

**Issue:** Container exits immediately

**Solution:**
```bash
# Check logs
docker-compose -f docker-compose.test.yml logs

# Rebuild container
make test-build
```

### API Key Errors

**Issue:** `AuthenticationError` or missing API keys

**Solution:**
1. Check `.env` file exists at project root
2. Verify API keys are valid
3. Ensure `docker-compose.test.yml` references `.env`

```bash
# Verify environment
docker-compose -f docker-compose.test.yml run tests env | grep API_KEY
```

### Permission Errors

**Issue:** Cannot write test results

**Solution:**
```bash
# Create test-results directory
mkdir -p test-results

# Fix permissions
chmod 777 test-results
```

### Knowledge Base Not Found

**Issue:** Parser tests fail with "markdown files not found"

**Solution:**
The knowledge base is parsed during Docker build. Rebuild:

```bash
make test-build
```

## CI/CD Integration

Use in GitHub Actions, GitLab CI, or other CI/CD:

```yaml
# .github/workflows/test.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Create .env file
        run: |
          echo "OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }}" >> .env
          echo "GEMINI_API_KEY=${{ secrets.GEMINI_API_KEY }}" >> .env

      - name: Run tests
        run: make test

      - name: Upload test results
        uses: actions/upload-artifact@v2
        with:
          name: test-results
          path: test-results/
```

## Performance Tips

### Faster Test Runs

1. **Skip slow tests** - Comment out Phase 3 E2E in `run_all_tests.sh`
2. **Use cached images** - Don't use `--build` flag if code hasn't changed
3. **Parallel execution** - Use pytest-xdist:

```bash
docker-compose -f docker-compose.test.yml run tests pytest -n auto
```

### Reduce Build Time

1. **Use Docker layer cache** - Don't modify Dockerfile unless needed
2. **Pre-built base image** - Create custom base image with dependencies

## File Structure

```
.
├── backend/
│   ├── Dockerfile.test           # Test container definition
│   ├── requirements-test.txt     # Test dependencies
│   ├── pytest.ini                # Pytest configuration
│   ├── run_all_tests.sh          # Test runner script
│   ├── test_parser.py            # Parser tests
│   ├── test_tag_assignment.py    # Tag assignment tests
│   ├── test_question_selection.py # Question selection tests
│   ├── test_intake_workflow.py   # Workflow tests
│   └── test_phase3_experiments.py # E2E tests
├── docker-compose.test.yml       # Test orchestration
├── test-results/                 # Test output (gitignored)
├── Makefile                      # Convenience commands
└── TEST_DOCKER_README.md         # This file
```

## Best Practices

✅ **Run tests before committing** - Catch issues early
✅ **Use interactive shell for debugging** - `make test-shell`
✅ **Check test results directory** - Review detailed output
✅ **Keep tests fast** - Skip slow E2E tests during development
✅ **Update tests with code changes** - Keep tests in sync

## Next Steps

- Set up CI/CD pipeline with `make test`
- Add more test coverage
- Create frontend test container
- Add integration tests between backend/frontend

## Support

For issues or questions:
1. Check logs: `make test-logs`
2. Review test output in `test-results/`
3. Run interactive shell: `make test-shell`
4. Check GitHub issues: https://github.com/your-repo/issues
