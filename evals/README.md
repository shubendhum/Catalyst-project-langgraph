# LLM Evaluations

Comprehensive evaluation system for testing Catalyst AI agents against real-world tasks and bugs.

## Quick Start

```bash
# Run all evaluations
make eval

# View summary
make eval-summary

# Test specific category
make eval-category CATEGORY=bug_fix
```

## What's Included

### Gold Standard Datasets

- **`gold/tasks.jsonl`** - 20 general tasks covering code generation, bug fixes, architecture, testing, refactoring, security, and optimization
- **`gold/scenarios.jsonl`** - Quick test scenarios for basic functionality
- **`gold/real_world_bugs.jsonl`** - 10 production bug scenarios based on actual issues

### Evaluation Tools

- **`run.py`** - Main evaluation runner (Python)
- **`compare_reports.py`** - Compare eval results over time
- **`promptfooconfig.yaml`** - Configuration for promptfoo integration

### Reports

- **`report.json`** - Latest evaluation results
- **`baseline_report.json`** - Baseline for performance comparisons

## Task Categories

| Category | Count | Description |
|----------|-------|-------------|
| `code_generation` | 3 | Generate complete production code |
| `bug_fix` | 5 | Fix broken code with errors |
| `production_bug` | 10 | Real-world production incidents |
| `architecture` | 1 | Design system architectures |
| `testing` | 1 | Write test suites |
| `refactoring` | 1 | Improve code quality |
| `security_vulnerability` | 2 | Fix security issues |
| `optimization` | 2 | Improve performance |
| `integration` | 1 | Third-party API integration |
| `api_design` | 1 | Design RESTful APIs |
| `error_handling` | 1 | Add error handling |
| `concurrency` | 1 | Fix race conditions |
| `observability` | 1 | Add monitoring/logging |
| `accessibility` | 1 | Improve accessibility |

**Total: 30+ tasks**

## Example Report

```json
{
  "summary": {
    "total_tasks": 20,
    "passed": 17,
    "failed": 3,
    "pass_rate": 0.85,
    "avg_score": 0.87,
    "avg_latency_ms": 3500
  },
  "by_category": {
    "code_generation": {
      "pass_rate": 1.0,
      "avg_score": 0.92
    },
    "bug_fix": {
      "pass_rate": 0.8,
      "avg_score": 0.83
    }
  }
}
```

## Commands

### Makefile Commands

```bash
make eval                   # Run all evaluations
make eval-summary          # Show summary from last run
make eval-category CATEGORY=bug_fix  # Test specific category
make eval-real-bugs        # Test production bugs
make eval-all              # Run all suites
make eval-compare          # Compare with baseline
make eval-baseline         # Save current as baseline
make eval-promptfoo        # Run promptfoo evals
```

### npm Commands

```bash
npm run eval               # Run all evaluations
npm run eval:summary       # Show summary
npm run eval:promptfoo     # Run promptfoo
```

### Python Commands

```bash
# Basic usage
python -m evals.run

# Custom options
python -m evals.run --tasks gold/tasks.jsonl --output report.json
python -m evals.run --category bug_fix --verbose
python -m evals.run --api-url http://localhost:8001

# Compare reports
python -m evals.compare_reports baseline_report.json report.json
```

## Adding New Tasks

1. **Add to appropriate JSONL file:**
   ```jsonl
   {"task_id": "new-001", "category": "bug_fix", "prompt": "...", "expected_output": {...}, "metadata": {...}}
   ```

2. **Run evaluations:**
   ```bash
   make eval
   ```

3. **No code changes needed!**

## Scoring

- **Pass threshold:** 70% of checks must pass
- **Checks:** Keywords, structure, language, fixes
- **Score:** `checks_passed / total_checks`

## Performance Tracking

```bash
# 1. Run initial evals and save as baseline
make eval
make eval-baseline

# 2. Make changes to prompts/agents

# 3. Run evals again
make eval

# 4. Compare
make eval-compare
```

**Output shows:**
- Overall performance delta
- Per-category changes
- Regressions (tasks that got worse)
- Improvements (tasks that got better)

## Integration

### CI/CD Example

```yaml
- name: Run evaluations
  run: make eval

- name: Check for regressions
  run: make eval-compare
```

### Pre-Deployment

```bash
# Block deployment if critical tests fail
make eval-category CATEGORY=security
make eval-category CATEGORY=bug_fix
```

## Files

```
evals/
├── gold/                    # Test datasets
│   ├── tasks.jsonl         # General tasks
│   ├── scenarios.jsonl     # Quick scenarios
│   └── real_world_bugs.jsonl  # Production bugs
├── run.py                  # Evaluation runner
├── compare_reports.py      # Report comparison
├── promptfooconfig.yaml    # Promptfoo config
├── report.json            # Latest results
├── baseline_report.json   # Baseline
└── README.md              # This file
```

## Full Documentation

See [EVALS_GUIDE.md](/app/EVALS_GUIDE.md) for comprehensive documentation including:
- Detailed task format specification
- Custom evaluator creation
- CI/CD integration examples
- Troubleshooting guide
- Best practices

---

**Quick Links:**
- Full Guide: `/app/EVALS_GUIDE.md`
- Runner: `evals/run.py`
- Comparator: `evals/compare_reports.py`
- Tasks: `evals/gold/*.jsonl`
