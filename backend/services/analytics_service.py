"""
Analytics Service
Tracks and analyzes metrics for performance, cost, and quality
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Provides analytics and insights"""
    
    def __init__(self, db):
        self.db = db
    
    async def track_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        tags: Optional[Dict] = None
    ):
        """Track a metric"""
        
        metric_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metric_name": metric_name,
            "value": value,
            "unit": unit,
            "tags": tags or {}
        }
        
        try:
            await self.db.metrics.insert_one(metric_record)
        except Exception as e:
            logger.error(f"Error tracking metric: {e}")
    
    async def get_performance_dashboard(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        timeframe_days: int = 30
    ) -> Dict:
        """Get performance dashboard data"""
        
        start_date = datetime.now(timezone.utc) - timedelta(days=timeframe_days)
        
        try:
            # Build query
            query = {"timestamp": {"$gte": start_date.isoformat()}}
            if user_id:
                query["tags.user_id"] = user_id
            if project_id:
                query["tags.project_id"] = project_id
            
            # Get task completion metrics
            completion_metrics = await self.db.metrics.find({
                **query,
                "metric_name": "task.completion_time"
            }).to_list(length=None)
            
            # Calculate stats
            if completion_metrics:
                completion_times = [m["value"] for m in completion_metrics]
                avg_completion = sum(completion_times) / len(completion_times)
                min_completion = min(completion_times)
                max_completion = max(completion_times)
            else:
                avg_completion = min_completion = max_completion = 0
            
            # Get success rate
            success_metrics = await self.db.metrics.find({
                **query,
                "metric_name": "task.success_rate"
            }).to_list(length=None)
            
            if success_metrics:
                success_rate = sum(m["value"] for m in success_metrics) / len(success_metrics)
            else:
                success_rate = 0
            
            # Get agent performance
            agent_metrics = await self.db.metrics.find({
                **query,
                "metric_name": "agent.response_time"
            }).to_list(length=None)
            
            agent_performance = defaultdict(list)
            for metric in agent_metrics:
                agent = metric["tags"].get("agent", "unknown")
                agent_performance[agent].append(metric["value"])
            
            agent_stats = {
                agent: {
                    "avg_response_time": sum(times) / len(times),
                    "requests": len(times)
                }
                for agent, times in agent_performance.items()
            }
            
            return {
                "timeframe_days": timeframe_days,
                "task_completion": {
                    "average_seconds": avg_completion,
                    "min_seconds": min_completion,
                    "max_seconds": max_completion,
                    "total_tasks": len(completion_metrics)
                },
                "success_rate": success_rate,
                "agent_performance": agent_stats,
                "total_metrics": len(completion_metrics) + len(success_metrics) + len(agent_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error getting performance dashboard: {e}")
            return {"error": str(e)}
    
    async def get_cost_dashboard(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        timeframe_days: int = 30
    ) -> Dict:
        """Get cost dashboard data"""
        
        start_date = datetime.now(timezone.utc) - timedelta(days=timeframe_days)
        
        try:
            query = {"timestamp": {"$gte": start_date.isoformat()}}
            if user_id:
                query["tags.user_id"] = user_id
            if project_id:
                query["tags.project_id"] = project_id
            
            # Get token usage
            token_metrics = await self.db.metrics.find({
                **query,
                "metric_name": "token.usage"
            }).to_list(length=None)
            
            total_tokens = sum(m["value"] for m in token_metrics)
            
            # Get costs
            cost_metrics = await self.db.metrics.find({
                **query,
                "metric_name": "token.cost"
            }).to_list(length=None)
            
            total_cost = sum(m["value"] for m in cost_metrics)
            
            # Group by day for trend
            daily_costs = defaultdict(float)
            for metric in cost_metrics:
                date = metric["timestamp"][:10]  # Get date part
                daily_costs[date] += metric["value"]
            
            # Calculate daily average
            daily_average = total_cost / timeframe_days if timeframe_days > 0 else 0
            
            # Group by model
            model_costs = defaultdict(float)
            model_tokens = defaultdict(int)
            
            for metric in cost_metrics:
                model = metric["tags"].get("model", "unknown")
                model_costs[model] += metric["value"]
            
            for metric in token_metrics:
                model = metric["tags"].get("model", "unknown")
                model_tokens[model] += metric["value"]
            
            return {
                "timeframe_days": timeframe_days,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "daily_average": daily_average,
                "daily_trend": [
                    {"date": date, "cost": cost}
                    for date, cost in sorted(daily_costs.items())
                ],
                "model_breakdown": {
                    model: {
                        "cost": cost,
                        "tokens": model_tokens.get(model, 0)
                    }
                    for model, cost in model_costs.items()
                },
                "average_cost_per_token": total_cost / total_tokens if total_tokens > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting cost dashboard: {e}")
            return {"error": str(e)}
    
    async def get_quality_dashboard(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        timeframe_days: int = 30
    ) -> Dict:
        """Get code quality dashboard data"""
        
        start_date = datetime.now(timezone.utc) - timedelta(days=timeframe_days)
        
        try:
            query = {"timestamp": {"$gte": start_date.isoformat()}}
            if user_id:
                query["tags.user_id"] = user_id
            if project_id:
                query["tags.project_id"] = project_id
            
            # Get quality scores
            quality_metrics = await self.db.metrics.find({
                **query,
                "metric_name": "code.quality_score"
            }).to_list(length=None)
            
            if quality_metrics:
                quality_scores = [m["value"] for m in quality_metrics]
                avg_quality = sum(quality_scores) / len(quality_scores)
                
                # Calculate trend
                quality_by_date = defaultdict(list)
                for metric in quality_metrics:
                    date = metric["timestamp"][:10]
                    quality_by_date[date].append(metric["value"])
                
                quality_trend = [
                    {
                        "date": date,
                        "score": sum(scores) / len(scores)
                    }
                    for date, scores in sorted(quality_by_date.items())
                ]
            else:
                avg_quality = 0
                quality_trend = []
            
            # Get test coverage
            coverage_metrics = await self.db.metrics.find({
                **query,
                "metric_name": "code.test_coverage"
            }).to_list(length=None)
            
            if coverage_metrics:
                avg_coverage = sum(m["value"] for m in coverage_metrics) / len(coverage_metrics)
            else:
                avg_coverage = 0
            
            return {
                "timeframe_days": timeframe_days,
                "average_quality_score": avg_quality,
                "average_test_coverage": avg_coverage,
                "quality_trend": quality_trend,
                "total_assessments": len(quality_metrics)
            }
            
        except Exception as e:
            logger.error(f"Error getting quality dashboard: {e}")
            return {"error": str(e)}
    
    async def generate_insights(
        self,
        user_id: str,
        timeframe_days: int = 30
    ) -> List[Dict]:
        """Generate AI-powered insights"""
        
        insights = []
        
        try:
            # Get performance data
            perf_data = await self.get_performance_dashboard(user_id=user_id, timeframe_days=timeframe_days)
            
            # Insight 1: Slow tasks
            avg_time = perf_data.get("task_completion", {}).get("average_seconds", 0)
            if avg_time > 1200:  # More than 20 minutes
                insights.append({
                    "type": "performance",
                    "severity": "medium",
                    "title": "Task Completion Time Above Average",
                    "description": f"Your tasks are taking {avg_time/60:.1f} minutes on average",
                    "recommendation": "Consider breaking down complex tasks or optimizing prompts",
                    "impact": "Could save 20-30% time"
                })
            
            # Insight 2: Success rate
            success_rate = perf_data.get("success_rate", 0)
            if success_rate < 0.85:
                insights.append({
                    "type": "quality",
                    "severity": "high",
                    "title": "Low Success Rate",
                    "description": f"Only {success_rate*100:.1f}% of tasks succeed on first attempt",
                    "recommendation": "Enable Learning Agent to improve from past failures",
                    "impact": "Could improve success rate to >90%"
                })
            
            # Get cost data
            cost_data = await self.get_cost_dashboard(user_id=user_id, timeframe_days=timeframe_days)
            
            # Insight 3: High costs
            daily_avg = cost_data.get("daily_average", 0)
            if daily_avg > 5:  # More than $5/day
                insights.append({
                    "type": "cost",
                    "severity": "high",
                    "title": "High Daily Costs",
                    "description": f"Spending ${daily_avg:.2f} per day on average",
                    "recommendation": "Enable caching and use cheaper models for simple tasks",
                    "impact": f"Could save ${daily_avg * 0.3:.2f}/day (30% reduction)"
                })
            
            # Insight 4: Model optimization
            model_breakdown = cost_data.get("model_breakdown", {})
            expensive_models = [
                model for model, data in model_breakdown.items()
                if data["cost"] > total_cost * 0.5
            ] if (total_cost := cost_data.get("total_cost", 0)) > 0 else []
            
            if expensive_models:
                insights.append({
                    "type": "optimization",
                    "severity": "medium",
                    "title": "Model Usage Not Optimized",
                    "description": f"Most costs from expensive model(s): {', '.join(expensive_models)}",
                    "recommendation": "Use Cost Optimizer to automatically select cheaper models",
                    "impact": "Could save 20-40% on costs"
                })
            
            # Get quality data
            quality_data = await self.get_quality_dashboard(user_id=user_id, timeframe_days=timeframe_days)
            
            # Insight 5: Code quality
            avg_quality = quality_data.get("average_quality_score", 0)
            if avg_quality < 80:
                insights.append({
                    "type": "quality",
                    "severity": "medium",
                    "title": "Code Quality Below Target",
                    "description": f"Average quality score is {avg_quality:.1f}/100",
                    "recommendation": "Enable code review agent and increase test coverage",
                    "impact": "Target: 85+ quality score"
                })
            
            # Insight 6: Test coverage
            avg_coverage = quality_data.get("average_test_coverage", 0)
            if avg_coverage < 70:
                insights.append({
                    "type": "testing",
                    "severity": "medium",
                    "title": "Low Test Coverage",
                    "description": f"Test coverage is only {avg_coverage:.1f}%",
                    "recommendation": "Use Testing Agent to generate missing tests",
                    "impact": "Target: 80%+ coverage"
                })
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return []
    
    async def export_analytics(
        self,
        format: str = "json",
        user_id: Optional[str] = None,
        timeframe_days: int = 30
    ) -> Dict:
        """Export analytics data"""
        
        try:
            data = {
                "performance": await self.get_performance_dashboard(user_id, timeframe_days=timeframe_days),
                "cost": await self.get_cost_dashboard(user_id, timeframe_days=timeframe_days),
                "quality": await self.get_quality_dashboard(user_id, timeframe_days=timeframe_days),
                "insights": await self.generate_insights(user_id, timeframe_days=timeframe_days),
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "timeframe_days": timeframe_days
            }
            
            return {
                "success": True,
                "data": data,
                "format": format
            }
            
        except Exception as e:
            logger.error(f"Error exporting analytics: {e}")
            return {"success": False, "error": str(e)}


def get_analytics_service(db) -> AnalyticsService:
    """Factory function to get analytics service"""
    return AnalyticsService(db)
