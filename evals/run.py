"""
LLM Evaluation Runner
Executes gold standard tasks against live API and generates accuracy reports

Usage:
    python -m evals.run
    python -m evals.run --tasks gold/tasks.jsonl --output report.json
    python -m evals.run --category code_generation --verbose
"""

import argparse
import asyncio
import json
import time
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EvalResult:
    """Result of a single evaluation"""
    
    def __init__(
        self,
        task_id: str,
        category: str,
        passed: bool,
        score: float,
        latency: float,
        actual_output: str,
        expected_checks: Dict[str, bool],
        error: Optional[str] = None
    ):
        self.task_id = task_id
        self.category = category
        self.passed = passed
        self.score = score
        self.latency = latency
        self.actual_output = actual_output
        self.expected_checks = expected_checks
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'category': self.category,
            'passed': self.passed,
            'score': self.score,
            'latency_ms': self.latency,
            'expected_checks': self.expected_checks,
            'error': self.error
        }


class TaskEvaluator:
    """Evaluates tasks against expected outputs"""
    
    def __init__(self, api_url: str = "http://localhost:8001"):
        self.api_url = api_url
    
    async def execute_task(self, task: Dict[str, Any]) -> str:
        """
        Execute a task against the live API
        
        Args:
            task: Task dictionary with prompt
            
        Returns:
            API response output
        """
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                payload = {
                    'message': task['prompt'],
                    'conversation_id': f"eval-{task['task_id']}"
                }
                
                async with session.post(
                    f"{self.api_url}/api/chat/send",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=task['metadata'].get('time_limit', 60))
                ) as response:
                    if response.status != 200:
                        raise Exception(f"API returned {response.status}")
                    
                    data = await response.json()
                    return data.get('response', data.get('message', str(data)))
                    
        except ImportError:
            logger.error("aiohttp not installed. Install with: pip install aiohttp")
            raise
        except Exception as e:
            logger.error(f"Failed to execute task {task['task_id']}: {e}")
            raise
    
    def check_contains(self, output: str, expected: List[str]) -> Dict[str, bool]:
        """Check if output contains expected strings"""
        output_lower = output.lower()
        return {
            term: term.lower() in output_lower
            for term in expected
        }
    
    def check_structure(self, output: str, expected: Dict[str, Any]) -> Dict[str, bool]:
        """Check if output matches expected structure"""
        checks = {}
        
        if 'contains' in expected:
            contains_checks = self.check_contains(output, expected['contains'])
            checks.update(contains_checks)
        
        if 'structure' in expected:
            structure_type = expected['structure']
            checks[f'structure_{structure_type}'] = len(output) > 50  # Basic check
        
        if 'language' in expected:
            lang = expected['language']
            # Simple heuristic checks
            if lang == 'python':
                checks['language_python'] = 'def ' in output or 'class ' in output
            elif lang == 'javascript':
                checks['language_javascript'] = 'function ' in output or '=>' in output or 'const ' in output
            elif lang == 'sql':
                checks['language_sql'] = 'SELECT ' in output.upper() or 'CREATE ' in output.upper()
        
        return checks
    
    async def evaluate_task(self, task: Dict[str, Any]) -> EvalResult:
        """
        Evaluate a single task
        
        Args:
            task: Task dictionary from gold file
            
        Returns:
            EvalResult with pass/fail and metrics
        """
        logger.info(f"Evaluating task: {task['task_id']} ({task['category']})")
        
        start_time = time.time()
        error = None
        actual_output = ""
        
        try:
            # Execute task
            actual_output = await self.execute_task(task)
            latency = (time.time() - start_time) * 1000  # ms
            
            # Check against expected output
            expected = task['expected_output']
            checks = self.check_structure(actual_output, expected)
            
            # Calculate score (% of checks passed)
            passed_count = sum(1 for v in checks.values() if v)
            total_count = len(checks)
            score = passed_count / total_count if total_count > 0 else 0.0
            
            # Task passes if score >= 0.7 (70% of checks)
            passed = score >= 0.7
            
            logger.info(f"  ✓ Score: {score:.2%} ({passed_count}/{total_count} checks)")
            
            return EvalResult(
                task_id=task['task_id'],
                category=task['category'],
                passed=passed,
                score=score,
                latency=latency,
                actual_output=actual_output[:500],  # Truncate for report
                expected_checks=checks,
                error=None
            )
            
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            error = str(e)
            logger.error(f"  ✗ Task failed: {error}")
            
            return EvalResult(
                task_id=task['task_id'],
                category=task['category'],
                passed=False,
                score=0.0,
                latency=latency,
                actual_output=actual_output[:500] if actual_output else "",
                expected_checks={},
                error=error
            )


class EvalRunner:
    """Main evaluation runner"""
    
    def __init__(
        self,
        tasks_file: str = "evals/gold/tasks.jsonl",
        output_file: str = "evals/report.json",
        api_url: str = "http://localhost:8001",
        category: Optional[str] = None
    ):
        self.tasks_file = Path(tasks_file)
        self.output_file = Path(output_file)
        self.api_url = api_url
        self.category = category
        self.evaluator = TaskEvaluator(api_url)
    
    def load_tasks(self) -> List[Dict[str, Any]]:
        """Load tasks from JSONL file"""
        if not self.tasks_file.exists():
            raise FileNotFoundError(f"Tasks file not found: {self.tasks_file}")
        
        tasks = []
        with open(self.tasks_file, 'r') as f:
            for line in f:
                if line.strip():
                    task = json.loads(line)
                    
                    # Filter by category if specified
                    if self.category and task.get('category') != self.category:
                        continue
                    
                    tasks.append(task)
        
        logger.info(f"Loaded {len(tasks)} tasks from {self.tasks_file}")
        return tasks
    
    async def run_evaluations(self) -> Dict[str, Any]:
        """
        Run all evaluations and generate report
        
        Returns:
            Report dictionary with results and metrics
        """
        logger.info("=" * 60)
        logger.info("Starting LLM Evaluations")
        logger.info("=" * 60)
        
        # Load tasks
        tasks = self.load_tasks()
        if not tasks:
            raise ValueError("No tasks to evaluate")
        
        # Run evaluations
        results = []
        start_time = time.time()
        
        for task in tasks:
            result = await self.evaluator.evaluate_task(task)
            results.append(result)
        
        total_time = time.time() - start_time
        
        # Generate report
        report = self.generate_report(results, total_time)
        
        # Save report
        self.save_report(report)
        
        return report
    
    def generate_report(
        self,
        results: List[EvalResult],
        total_time: float
    ) -> Dict[str, Any]:
        """Generate evaluation report"""
        
        # Calculate metrics
        total_tasks = len(results)
        passed_tasks = sum(1 for r in results if r.passed)
        failed_tasks = total_tasks - passed_tasks
        pass_rate = passed_tasks / total_tasks if total_tasks > 0 else 0.0
        
        avg_latency = sum(r.latency for r in results) / total_tasks if total_tasks > 0 else 0.0
        avg_score = sum(r.score for r in results) / total_tasks if total_tasks > 0 else 0.0
        
        # Group by category
        by_category = {}
        for result in results:
            cat = result.category
            if cat not in by_category:
                by_category[cat] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'avg_score': 0.0,
                    'avg_latency': 0.0
                }
            
            by_category[cat]['total'] += 1
            if result.passed:
                by_category[cat]['passed'] += 1
            else:
                by_category[cat]['failed'] += 1
        
        # Calculate category averages
        for cat in by_category:
            cat_results = [r for r in results if r.category == cat]
            by_category[cat]['avg_score'] = sum(r.score for r in cat_results) / len(cat_results)
            by_category[cat]['avg_latency'] = sum(r.latency for r in cat_results) / len(cat_results)
            by_category[cat]['pass_rate'] = by_category[cat]['passed'] / by_category[cat]['total']
        
        report = {
            'summary': {
                'timestamp': datetime.now().isoformat(),
                'total_tasks': total_tasks,
                'passed': passed_tasks,
                'failed': failed_tasks,
                'pass_rate': pass_rate,
                'avg_score': avg_score,
                'avg_latency_ms': avg_latency,
                'total_time_seconds': total_time,
                'tasks_per_second': total_tasks / total_time if total_time > 0 else 0
            },
            'by_category': by_category,
            'results': [r.to_dict() for r in results]
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any]):
        """Save report to file"""
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("EVALUATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tasks:    {report['summary']['total_tasks']}")
        logger.info(f"Passed:         {report['summary']['passed']}")
        logger.info(f"Failed:         {report['summary']['failed']}")
        logger.info(f"Pass Rate:      {report['summary']['pass_rate']:.1%}")
        logger.info(f"Avg Score:      {report['summary']['avg_score']:.1%}")
        logger.info(f"Avg Latency:    {report['summary']['avg_latency_ms']:.0f}ms")
        logger.info(f"Total Time:     {report['summary']['total_time_seconds']:.1f}s")
        logger.info("")
        logger.info("By Category:")
        for cat, metrics in report['by_category'].items():
            logger.info(f"  {cat:20s} - Pass: {metrics['pass_rate']:5.1%} ({metrics['passed']}/{metrics['total']})")
        logger.info("=" * 60)
        logger.info(f"Report saved to: {self.output_file}")
        logger.info("=" * 60)
    
    def print_summary(self):
        """Print summary from saved report"""
        if not self.output_file.exists():
            logger.error(f"Report not found: {self.output_file}")
            return
        
        with open(self.output_file, 'r') as f:
            report = json.load(f)
        
        self.save_report(report)  # Reuse save_report for printing


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run LLM evaluations')
    parser.add_argument(
        '--tasks',
        default='evals/gold/tasks.jsonl',
        help='Path to tasks JSONL file (default: evals/gold/tasks.jsonl)'
    )
    parser.add_argument(
        '--output',
        default='evals/report.json',
        help='Path to output report JSON (default: evals/report.json)'
    )
    parser.add_argument(
        '--api-url',
        default='http://localhost:8001',
        help='API base URL (default: http://localhost:8001)'
    )
    parser.add_argument(
        '--category',
        help='Filter by category (e.g., code_generation, bug_fix)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Print summary from existing report'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    runner = EvalRunner(
        tasks_file=args.tasks,
        output_file=args.output,
        api_url=args.api_url,
        category=args.category
    )
    
    if args.summary:
        runner.print_summary()
    else:
        try:
            await runner.run_evaluations()
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
