# Testing Quick Reference

## 🚀 Run All Tests (Fastest Way)

```bash
make test
```

That's it! This single command runs all 6 backend tests in an isolated Docker container.

---

## 📋 Common Commands

| Command | Description |
|---------|-------------|
| `make test` | Run all tests |
| `make test-shell` | Open interactive test shell |
| `make test-specific TEST=test_parser.py` | Run specific test file |
| `make test-coverage` | Run with coverage report |
| `make test-clean` | Clean up test files |

---

## 📂 What Tests Are Included?

1. ✅ Knowledge Base Parser
2. ✅ Tag Assignment Logic
3. ✅ Question Selection
4. ✅ Intake Workflow Integration
5. ✅ Parser Debug Utilities
6. ✅ Phase 3 E2E Experiments

---

## 🎯 Phase 3 Experiment Testing

```bash
# Run all Phase 3 scenarios
docker-compose -f docker-compose.test.yml run tests python test_phase3_experiments.py --test all

# Run specific scenario
docker-compose -f docker-compose.test.yml run tests python test_phase3_experiments.py --test 1

# Interactive mode
docker-compose -f docker-compose.test.yml run tests python test_phase3_experiments.py --interactive
```

---

## 🐛 Debugging Failed Tests

```bash
# 1. Check logs
make test-logs

# 2. Run in interactive shell
make test-shell

# 3. Run specific failing test
python test_parser.py
```

---

## 📊 Test Results

Results saved to: `test-results/test_results_<timestamp>.txt`

---

## ⚙️ Requirements

- Docker and Docker Compose installed
- `.env` file with API keys (OPENAI_API_KEY or GEMINI_API_KEY)

---

## 📖 Full Documentation

See `TEST_DOCKER_README.md` for complete guide.
