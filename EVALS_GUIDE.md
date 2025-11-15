# LLM Evaluations Guide

## Overview

The Catalyst platform includes a comprehensive LLM evaluation system to measure and track the performance of AI agents on real-world tasks and bugs.

## Architecture

```
evals/
├── gold/                           # Gold standard test datasets
│   ├── tasks.jsonl                 # General tasks (code gen, refactoring, etc.)
│   ├── scenarios.jsonl             # Quick test scenarios
│   └── real_world_bugs.jsonl       # Production bugs and issues
├── promptfooconfig.yaml            # Promptfoo configuration
├── run.py                          # Main evaluation runner
├── compare_reports.py              # Report comparison tool
├── report.json                     # Latest evaluation report
└── baseline_report.json            # Baseline for comparisons
```

## Quick Start

### 1. Run Basic Evaluations

```bash
# Run all evaluations
make eval

# Or using npm
npm run eval
```

**Output:**
```
Running LLM evaluations...
✓ Evaluating task: code-gen-001 (code_generation)
  ✓ Score: 85% (6/7 checks)
✓ Evaluating task: bug-fix-001 (bug_fix)
  ✓ Score: 100% (5/5 checks)
...
✓ Evaluations complete
Report: evals/report.json
```

### 2. View Summary

```bash
# Show summary from last run
make eval-summary
```

### 3. Test Specific Category

```bash
# Test only code generation
make eval-category CATEGORY=code_generation

# Test only bug fixes
make eval-category CATEGORY=bug_fix
```

## Report Format

### Example Report (`evals/report.json`)

```json
{
  "summary": {
    "timestamp": "2025-01-09T12:00:00",
    "total_tasks": 20,
    "passed": 17,
    "failed": 3,
    "pass_rate": 0.85,
    "avg_score": 0.87,
    "avg_latency_ms": 3500,
    "total_time_seconds": 75.2,
    "tasks_per_second": 0.27
  },
  "by_category": {
    "code_generation": {
      "total": 3,
      "passed": 3,
      "failed": 0,
      "pass_rate": 1.0,
      "avg_score": 0.92,
      "avg_latency": 4200
    },
    "bug_fix": {
      "total": 5,
      "passed": 4,
      "failed": 1,
      "pass_rate": 0.8,
      "avg_score": 0.83,
      "avg_latency": 2800
    }
  },
  "results": [
    {
      "task_id": "code-gen-001",
      "category": "code_generation",
      "passed": true,
      "score": 0.86,
      "latency_ms": 4150,
      "expected_checks": {
        "FastAPI": true,
        "async def": true,
        "email": true,
        "password": true,
        "hash": true,
        "@app.post": true
      }
    }
  ]
}
```

## Task Categories

### 1. Code Generation
Generate complete, production-ready code from requirements.

**Example:**
```jsonl
{
  "task_id": "code-gen-001",
  "category": "code_generation",
  "prompt": "Create a Python FastAPI endpoint for user registration with email validation and password hashing",
  "expected_output": {
    "contains": ["FastAPI", "async def", "email", "password", "hash", "@app.post"],
    "structure": "complete_code",
    "language": "python"
  },
  "metadata": {
    "difficulty": "medium",
    "time_limit": 30
  }
}
```

### 2. Bug Fixes
Fix broken code with specific error symptoms.

**Example:**
```jsonl
{
  "task_id": "prod-bug-001",
  "category": "production_bug",
  "prompt": "Production incident: Users getting 500 errors on checkout. Logs show: 'float division by zero' in calculate_tax(). Fix:\n\ndef calculate_tax(subtotal, tax_rate):\n    return subtotal / tax_rate",
  "expected_output": {
    "contains": ["*", "multiply", "if tax_rate"],
    "fixes": ["wrong_operator", "zero_check"]
  }
}
```

### 3. Architecture Design
Design system architectures with multiple components.

### 4. Testing
Write comprehensive test suites for given code.

### 5. Refactoring
Improve code maintainability and structure.

### 6. Security
Identify and fix security vulnerabilities.

### 7. Performance
Optimize slow code and improve efficiency.

## Creating Gold Standard Tasks

### Task Format

```jsonl
{
  "task_id": "unique-id-001",
  "category": "bug_fix | code_generation | architecture | ...",
  "prompt": "Task description and context",
  "expected_output": {
    "contains": ["keyword1", "keyword2", "..."],
    "fixes": ["issue1", "issue2"],
    "structure": "complete_code | api_spec | ...",
    "language": "python | javascript | sql | ..."
  },
  "metadata": {
    "difficulty": "easy | medium | hard",
    "time_limit": 30,
    "severity": "low | medium | high | critical"
  }
}
```

### Adding New Tasks

1. **Create task in appropriate JSONL file:**
   ```bash
   echo '{...task JSON...}' >> evals/gold/tasks.jsonl
   ```

2. **Run evaluations:**
   ```bash
   make eval
   ```

3. **No code changes needed!** The system automatically picks up new tasks.

## Scoring System

### Pass Criteria
A task **passes** if `score >= 0.7` (70% of checks passed).

### Score Calculation

```python
score = (checks_passed / total_checks)
```

### Expected Output Checks

1. **Contains Checks** - Output must contain specified keywords
2. **Structure Checks** - Output must match expected structure (e.g., complete code)
3. **Language Checks** - Output must be in expected programming language
4. **Fix Checks** - Output must address specified issues

### Example Scoring

```
Task: Fix authentication bug
Expected: ["validation", "if not email", "strip", "422"]

Output contains:
- ✅ "validation" → check passed
- ✅ "if not email" → check passed
- ❌ "strip" → check failed
- ✅ "422" → check passed

Score: 3/4 = 75% → PASSED
```

## Performance Tracking

### Save Baseline

```bash
# Run evals and save as baseline
make eval
make eval-baseline
```

### Compare Against Baseline

```bash
# Run new evals
make eval

# Compare with baseline
make eval-compare
```

**Output:**
```
📊 EVALUATION COMPARISON REPORT
========================================

🎯 Overall Performance:
  ✅ Pass Rate        Baseline:    80.0%  Current:    85.0%  Delta:   +5.0%
  ✅ Avg Score        Baseline:    82.5%  Current:    87.0%  Delta:   +4.5%
  ➡️  Avg Latency     Baseline:  3500ms   Current:  3480ms   Delta:   -20ms

📁 By Category:
  ✅ code_generation       Baseline:  90.0%  Current:  95.0%  Delta:   +5.0%
  ❌ bug_fix               Baseline:  80.0%  Current:  75.0%  Delta:   -5.0%
  ➡️  architecture          Baseline:  70.0%  Current:  72.0%  Delta:   +2.0%

⚠️  Regressions (2):
  ❌ bug-fix-002            (bug_fix)          80.0% → 65.0%
  ❌ security-001           (security)         90.0% → 60.0%

✨ Improvements (3):
  ✅ code-gen-003           (code_generation)  75.0% → 95.0%
  ✅ refactor-001           (refactoring)      70.0% → 85.0%
  ✅ test-001               (testing)          80.0% → 90.0%

========================================
🎉 Overall: IMPROVED - Performance has increased!
========================================
```

## Advanced Usage

### Custom API URL

```bash
# Test against staging API
cd backend && python -m evals.run --api-url http://staging.example.com
```

### Custom Output Path

```bash
# Save report to custom location
cd backend && python -m evals.run --output ../reports/eval_$(date +%Y%m%d).json
```

### Filter by Category

```bash
# Only test bug fixes
cd backend && python -m evals.run --category bug_fix
```

### Verbose Mode

```bash
# Show detailed output
cd backend && python -m evals.run --verbose
```

### Real-World Bugs Only

```bash
# Test on production bug scenarios
make eval-real-bugs
```

### All Suites

```bash
# Run all evaluation suites
make eval-all
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: LLM Evaluations

on:
  pull_request:
    branches: [main]

jobs:
  evals:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for API
        run: ./scripts/wait-for-api.sh
      
      - name: Run evaluations
        run: make eval
      
      - name: Compare with baseline
        run: make eval-compare
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: eval-report
          path: evals/report.json
      
      - name: Fail on regressions
        run: |
          if grep -q '"regressions".*[1-9]' evals/comparison.json; then
            echo "❌ Regressions detected!"
            exit 1
          fi
```

## Promptfoo Integration

[Promptfoo](https://promptfoo.dev) is an advanced LLM evaluation tool that we've integrated.

### Run Promptfoo Evals

```bash
# Run promptfoo evaluations
make eval-promptfoo

# Or directly
cd evals && npx promptfoo eval
```

### View Results in UI

```bash
# View in browser
cd evals && npx promptfoo view
```

### Configure Promptfoo

Edit `evals/promptfooconfig.yaml` to:
- Add/modify test cases
- Change providers (OpenAI, Anthropic, etc.)
- Adjust assertions and thresholds
- Configure output format

## Best Practices

### 1. **Start with Small Test Sets**
Begin with 5-10 representative tasks to establish baseline.

### 2. **Regularly Update Gold Standards**
Add new tasks as you encounter production issues.

### 3. **Track Trends Over Time**
Run evals weekly and compare against baseline.

### 4. **Focus on Critical Categories**
Prioritize evaluations for high-impact categories (security, production bugs).

### 5. **Use Real Production Scenarios**
Base test tasks on actual bugs and feature requests.

### 6. **Set Pass Rate Targets**
Define acceptable pass rates per category:
- Code generation: 90%+
- Bug fixes: 85%+
- Security: 95%+

### 7. **Monitor Latency**
Track response times to ensure acceptable user experience.

### 8. **Investigate Regressions Immediately**
When pass rate drops, investigate and fix promptly.

## Troubleshooting

### Issue: API Connection Failed

**Solution:**
```bash
# Check backend is running
curl http://localhost:8001/api/health

# Start backend if needed
docker-compose up -d backend
```

### Issue: No Tasks Found

**Check:**
```bash
# Verify JSONL files exist
ls -la evals/gold/*.jsonl

# Verify file format
cat evals/gold/tasks.jsonl | head -1 | jq .
```

### Issue: Low Pass Rate

**Debug:**
```bash
# Run with verbose output
cd backend && python -m evals.run --verbose

# Check specific failing task
grep "task-id-001" evals/report.json
```

### Issue: Timeout Errors

**Solution:**
```bash
# Increase time limits in task metadata
# Edit gold/*.jsonl and increase "time_limit" value

# Or adjust in code
# Edit evals/run.py, modify timeout in execute_task()
```

## Metrics Glossary

| Metric | Description | Good Value |
|--------|-------------|------------|
| **Pass Rate** | % of tasks that pass (score >= 0.7) | 85%+ |
| **Avg Score** | Average score across all tasks | 80%+ |
| **Avg Latency** | Average response time | <5000ms |
| **Tasks/Second** | Throughput | 0.2-0.5 |

## Examples

### Example 1: Daily Eval Run

```bash
#!/bin/bash
# daily_evals.sh

echo "Running daily evaluations..."

# Run evaluations
make eval

# Compare with yesterday
make eval-compare

# Send report
python scripts/send_report.py evals/report.json
```

### Example 2: Pre-Deploy Check

```bash
#!/bin/bash
# pre_deploy.sh

echo "Pre-deployment evaluation check..."

# Run critical tests only
cd backend && python -m evals.run \
  --category bug_fix \
  --category security \
  --output ../evals/pre_deploy_report.json

# Compare
make eval-compare

# Block deploy on regressions
if [ $? -ne 0 ]; then
  echo "❌ Regressions detected. Blocking deployment."
  exit 1
fi

echo "✅ All checks passed. Safe to deploy."
```

### Example 3: Category-Specific Testing

```bash
# Test all bug fix scenarios
make eval-category CATEGORY=bug_fix

# Test security vulnerabilities
make eval-category CATEGORY=security_vulnerability

# Test performance optimizations
make eval-category CATEGORY=performance
```

## Available Commands

| Command | Description |
|---------|-------------|
| `make eval` | Run all evaluations |
| `make eval-summary` | Show last report summary |
| `make eval-category CATEGORY=X` | Test specific category |
| `make eval-real-bugs` | Test real-world bugs |
| `make eval-all` | Run all eval suites |
| `make eval-compare` | Compare with baseline |
| `make eval-baseline` | Save current as baseline |
| `make eval-promptfoo` | Run promptfoo evals |
| `npm run eval` | Run evaluations (npm) |
| `npm run eval:summary` | Show summary (npm) |

## Adding Custom Evaluators

To add custom evaluation logic:

1. **Extend TaskEvaluator class:**
```python
# evals/custom_evaluator.py
from evals.run import TaskEvaluator

class CustomEvaluator(TaskEvaluator):
    def check_custom_criteria(self, output, expected):
        # Your custom logic here
        pass
```

2. **Use in run.py:**
```python
# Modify evals/run.py
evaluator = CustomEvaluator(api_url)
```

## Resources

- **Gold Tasks:** `/app/evals/gold/*.jsonl`
- **Runner Script:** `/app/evals/run.py`
- **Comparison Tool:** `/app/evals/compare_reports.py`
- **Promptfoo Config:** `/app/evals/promptfooconfig.yaml`
- **Makefile Commands:** `/app/Makefile` (search for `##@ Evaluations`)

---

**For questions or issues, check:**
- Backend logs: `docker logs catalyst-backend`
- Report files: `evals/*.json`
- Verbose output: `cd backend && python -m evals.run --verbose`
