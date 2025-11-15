"""
Compare two evaluation reports to track performance improvements/regressions

Usage:
    python -m evals.compare_reports baseline.json current.json
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any


class ReportComparator:
    """Compare two evaluation reports"""
    
    def __init__(self, baseline_path: str, current_path: str):
        self.baseline = self.load_report(baseline_path)
        self.current = self.load_report(current_path)
    
    def load_report(self, path: str) -> Dict[str, Any]:
        """Load report JSON"""
        with open(path, 'r') as f:
            return json.load(f)
    
    def compare(self) -> Dict[str, Any]:
        """Compare reports and generate diff"""
        
        baseline_summary = self.baseline['summary']
        current_summary = self.current['summary']
        
        # Calculate deltas
        pass_rate_delta = current_summary['pass_rate'] - baseline_summary['pass_rate']
        score_delta = current_summary['avg_score'] - baseline_summary['avg_score']
        latency_delta = current_summary['avg_latency_ms'] - baseline_summary['avg_latency_ms']
        
        # Compare by category
        category_comparison = {}
        baseline_cats = self.baseline.get('by_category', {})
        current_cats = self.current.get('by_category', {})
        
        all_categories = set(baseline_cats.keys()) | set(current_cats.keys())
        
        for cat in all_categories:
            baseline_cat = baseline_cats.get(cat, {})
            current_cat = current_cats.get(cat, {})
            
            if baseline_cat and current_cat:
                category_comparison[cat] = {
                    'baseline_pass_rate': baseline_cat.get('pass_rate', 0),
                    'current_pass_rate': current_cat.get('pass_rate', 0),
                    'delta': current_cat.get('pass_rate', 0) - baseline_cat.get('pass_rate', 0),
                    'status': self._get_status(current_cat.get('pass_rate', 0) - baseline_cat.get('pass_rate', 0))
                }
            elif current_cat:
                category_comparison[cat] = {
                    'baseline_pass_rate': 0,
                    'current_pass_rate': current_cat.get('pass_rate', 0),
                    'delta': current_cat.get('pass_rate', 0),
                    'status': 'NEW'
                }
            else:
                category_comparison[cat] = {
                    'baseline_pass_rate': baseline_cat.get('pass_rate', 0),
                    'current_pass_rate': 0,
                    'delta': -baseline_cat.get('pass_rate', 0),
                    'status': 'REMOVED'
                }
        
        # Find regressions (tasks that went from pass to fail)
        baseline_results = {r['task_id']: r for r in self.baseline['results']}
        current_results = {r['task_id']: r for r in self.current['results']}
        
        regressions = []
        improvements = []
        
        for task_id in set(baseline_results.keys()) & set(current_results.keys()):
            baseline_task = baseline_results[task_id]
            current_task = current_results[task_id]
            
            if baseline_task['passed'] and not current_task['passed']:
                regressions.append({
                    'task_id': task_id,
                    'category': current_task['category'],
                    'baseline_score': baseline_task['score'],
                    'current_score': current_task['score']
                })
            elif not baseline_task['passed'] and current_task['passed']:
                improvements.append({
                    'task_id': task_id,
                    'category': current_task['category'],
                    'baseline_score': baseline_task['score'],
                    'current_score': current_task['score']
                })
        
        comparison = {
            'overall': {
                'pass_rate': {
                    'baseline': baseline_summary['pass_rate'],
                    'current': current_summary['pass_rate'],
                    'delta': pass_rate_delta,
                    'status': self._get_status(pass_rate_delta)
                },
                'avg_score': {
                    'baseline': baseline_summary['avg_score'],
                    'current': current_summary['avg_score'],
                    'delta': score_delta,
                    'status': self._get_status(score_delta)
                },
                'avg_latency_ms': {
                    'baseline': baseline_summary['avg_latency_ms'],
                    'current': current_summary['avg_latency_ms'],
                    'delta': latency_delta,
                    'status': self._get_latency_status(latency_delta)
                }
            },
            'by_category': category_comparison,
            'regressions': regressions,
            'improvements': improvements
        }
        
        return comparison
    
    def _get_status(self, delta: float) -> str:
        """Get status based on delta"""
        if delta > 0.05:
            return 'IMPROVED'
        elif delta < -0.05:
            return 'REGRESSED'
        else:
            return 'STABLE'
    
    def _get_latency_status(self, delta: float) -> str:
        """Get latency status (lower is better)"""
        if delta < -100:  # 100ms improvement
            return 'IMPROVED'
        elif delta > 100:  # 100ms regression
            return 'REGRESSED'
        else:
            return 'STABLE'
    
    def print_comparison(self, comparison: Dict[str, Any]):
        """Print comparison in human-readable format"""
        
        print("\n" + "=" * 70)
        print("📊 EVALUATION COMPARISON REPORT")
        print("=" * 70)
        
        # Overall comparison
        print("\n🎯 Overall Performance:")
        overall = comparison['overall']
        
        self._print_metric(
            "Pass Rate",
            overall['pass_rate']['baseline'],
            overall['pass_rate']['current'],
            overall['pass_rate']['delta'],
            overall['pass_rate']['status'],
            format_pct=True
        )
        
        self._print_metric(
            "Avg Score",
            overall['avg_score']['baseline'],
            overall['avg_score']['current'],
            overall['avg_score']['delta'],
            overall['avg_score']['status'],
            format_pct=True
        )
        
        self._print_metric(
            "Avg Latency",
            overall['avg_latency_ms']['baseline'],
            overall['avg_latency_ms']['current'],
            overall['avg_latency_ms']['delta'],
            overall['avg_latency_ms']['status'],
            format_ms=True
        )
        
        # Category comparison
        print("\n📁 By Category:")
        for cat, metrics in comparison['by_category'].items():
            status_emoji = self._get_status_emoji(metrics['status'])
            print(f"  {status_emoji} {cat:25s} "
                  f"Baseline: {metrics['baseline_pass_rate']:5.1%}  "
                  f"Current: {metrics['current_pass_rate']:5.1%}  "
                  f"Delta: {metrics['delta']:+6.1%}")
        
        # Regressions
        if comparison['regressions']:
            print(f"\n⚠️  Regressions ({len(comparison['regressions'])}):")
            for reg in comparison['regressions']:
                print(f"  ❌ {reg['task_id']:25s} ({reg['category']:15s}) "
                      f"{reg['baseline_score']:.1%} → {reg['current_score']:.1%}")
        
        # Improvements
        if comparison['improvements']:
            print(f"\n✨ Improvements ({len(comparison['improvements'])}):")
            for imp in comparison['improvements']:
                print(f"  ✅ {imp['task_id']:25s} ({imp['category']:15s}) "
                      f"{imp['baseline_score']:.1%} → {imp['current_score']:.1%}")
        
        print("\n" + "=" * 70)
        
        # Overall verdict
        overall_status = overall['pass_rate']['status']
        if overall_status == 'IMPROVED':
            print("🎉 Overall: IMPROVED - Performance has increased!")
        elif overall_status == 'REGRESSED':
            print("⚠️  Overall: REGRESSED - Performance has decreased")
        else:
            print("➡️  Overall: STABLE - Performance is consistent")
        
        print("=" * 70)
    
    def _print_metric(self, name, baseline, current, delta, status, format_pct=False, format_ms=False):
        """Print a single metric comparison"""
        status_emoji = self._get_status_emoji(status)
        
        if format_pct:
            baseline_str = f"{baseline:.1%}"
            current_str = f"{current:.1%}"
            delta_str = f"{delta:+.1%}"
        elif format_ms:
            baseline_str = f"{baseline:.0f}ms"
            current_str = f"{current:.0f}ms"
            delta_str = f"{delta:+.0f}ms"
        else:
            baseline_str = f"{baseline:.2f}"
            current_str = f"{current:.2f}"
            delta_str = f"{delta:+.2f}"
        
        print(f"  {status_emoji} {name:15s} "
              f"Baseline: {baseline_str:>8s}  "
              f"Current: {current_str:>8s}  "
              f"Delta: {delta_str:>8s}")
    
    def _get_status_emoji(self, status: str) -> str:
        """Get emoji for status"""
        status_map = {
            'IMPROVED': '✅',
            'REGRESSED': '❌',
            'STABLE': '➡️ ',
            'NEW': '🆕',
            'REMOVED': '🗑️ '
        }
        return status_map.get(status, '❓')


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Compare evaluation reports')
    parser.add_argument('baseline', help='Path to baseline report JSON')
    parser.add_argument('current', help='Path to current report JSON')
    parser.add_argument('--output', help='Save comparison to JSON file')
    
    args = parser.parse_args()
    
    # Check files exist
    if not Path(args.baseline).exists():
        print(f"❌ Baseline report not found: {args.baseline}")
        sys.exit(1)
    
    if not Path(args.current).exists():
        print(f"❌ Current report not found: {args.current}")
        sys.exit(1)
    
    # Compare reports
    comparator = ReportComparator(args.baseline, args.current)
    comparison = comparator.compare()
    
    # Print comparison
    comparator.print_comparison(comparison)
    
    # Save if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(comparison, f, indent=2)
        print(f"\n💾 Comparison saved to: {args.output}")
    
    # Exit with error code if regressions found
    if comparison['regressions']:
        sys.exit(1)


if __name__ == '__main__':
    main()
