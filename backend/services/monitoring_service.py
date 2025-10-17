"""
Production Monitoring Service
Tracks agent performance, errors, costs, and metrics
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Service for monitoring agent execution and system health
    """
    
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
        
        # In-memory metrics for fast access
        self.metrics = {
            "agent_executions": defaultdict(int),
            "agent_errors": defaultdict(int),
            "agent_success_rate": defaultdict(float),
            "average_execution_time": defaultdict(float),
            "llm_token_usage": defaultdict(int),
            "total_cost": 0.0
        }
        
        # Real-time monitoring
        self.active_tasks = {}
        self.performance_data = []
    
    async def track_agent_start(self, agent_name: str, task_id: str, context: Dict):
        """Track when an agent starts execution"""
        try:
            start_event = {
                "agent_name": agent_name,
                "task_id": task_id,
                "event": "start",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": context
            }
            
            # Store in database
            await self.db.monitoring_events.insert_one(start_event)
            
            # Track active task
            self.active_tasks[task_id] = {
                "agent": agent_name,
                "start_time": datetime.now(timezone.utc),
                "context": context
            }
            
            # Update metrics
            self.metrics["agent_executions"][agent_name] += 1
            
        except Exception as e:
            logger.error(f"Error tracking agent start: {str(e)}")
    
    async def track_agent_complete(
        self,
        agent_name: str,
        task_id: str,
        result: Dict,
        execution_time: float
    ):
        """Track when an agent completes execution"""
        try:
            complete_event = {
                "agent_name": agent_name,
                "task_id": task_id,
                "event": "complete",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "execution_time": execution_time,
                "result": result,
                "status": result.get("status", "unknown")
            }
            
            await self.db.monitoring_events.insert_one(complete_event)
            
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            # Update performance metrics
            self._update_performance_metrics(agent_name, execution_time, result)
            
        except Exception as e:
            logger.error(f"Error tracking agent complete: {str(e)}")
    
    async def track_agent_error(self, agent_name: str, task_id: str, error: str):
        """Track when an agent encounters an error"""
        try:
            error_event = {
                "agent_name": agent_name,
                "task_id": task_id,
                "event": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": error
            }
            
            await self.db.monitoring_events.insert_one(error_event)
            
            # Update error metrics
            self.metrics["agent_errors"][agent_name] += 1
            
            # Remove from active tasks
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
        except Exception as e:
            logger.error(f"Error tracking agent error: {str(e)}")
    
    async def track_llm_usage(self, tokens: int, cost: float, model: str):
        """Track LLM token usage and cost"""
        try:
            usage_event = {
                "event": "llm_usage",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tokens": tokens,
                "cost": cost,
                "model": model
            }
            
            await self.db.monitoring_events.insert_one(usage_event)
            
            # Update metrics
            self.metrics["llm_token_usage"]["total"] += tokens
            self.metrics["llm_token_usage"][model] += tokens
            self.metrics["total_cost"] += cost
            
        except Exception as e:
            logger.error(f"Error tracking LLM usage: {str(e)}")
    
    async def get_agent_metrics(self, agent_name: Optional[str] = None) -> Dict:
        """Get metrics for a specific agent or all agents"""
        try:
            if agent_name:
                return {
                    "agent": agent_name,
                    "executions": self.metrics["agent_executions"][agent_name],
                    "errors": self.metrics["agent_errors"][agent_name],
                    "success_rate": self.metrics["agent_success_rate"][agent_name],
                    "avg_execution_time": self.metrics["average_execution_time"][agent_name]
                }
            else:
                # Return all agents
                all_metrics = {}
                for agent in self.metrics["agent_executions"].keys():
                    all_metrics[agent] = await self.get_agent_metrics(agent)
                return all_metrics
                
        except Exception as e:
            logger.error(f"Error getting agent metrics: {str(e)}")
            return {}
    
    async def get_system_health(self) -> Dict:
        """Get overall system health status"""
        try:
            total_executions = sum(self.metrics["agent_executions"].values())
            total_errors = sum(self.metrics["agent_errors"].values())
            
            overall_success_rate = (
                ((total_executions - total_errors) / total_executions * 100)
                if total_executions > 0 else 100.0
            )
            
            return {
                "status": "healthy" if overall_success_rate > 90 else "degraded",
                "total_executions": total_executions,
                "total_errors": total_errors,
                "success_rate": overall_success_rate,
                "active_tasks": len(self.active_tasks),
                "total_cost": self.metrics["total_cost"],
                "llm_tokens_used": self.metrics["llm_token_usage"]["total"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    async def get_performance_report(self, time_range: str = "24h") -> Dict:
        """Generate performance report for specified time range"""
        try:
            # Parse time range
            hours = int(time_range.rstrip("h"))
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            # Query database for events in time range
            events = await self.db.monitoring_events.find({
                "timestamp": {"$gte": start_time.isoformat()}
            }).to_list(length=None)
            
            # Aggregate data
            report = {
                "time_range": time_range,
                "total_events": len(events),
                "events_by_agent": defaultdict(int),
                "errors_by_agent": defaultdict(int),
                "avg_execution_time_by_agent": defaultdict(list)
            }
            
            for event in events:
                agent = event.get("agent_name")
                if agent:
                    report["events_by_agent"][agent] += 1
                    
                    if event.get("event") == "error":
                        report["errors_by_agent"][agent] += 1
                    
                    if event.get("event") == "complete" and "execution_time" in event:
                        report["avg_execution_time_by_agent"][agent].append(event["execution_time"])
            
            # Calculate averages
            for agent, times in report["avg_execution_time_by_agent"].items():
                if times:
                    report["avg_execution_time_by_agent"][agent] = sum(times) / len(times)
            
            return dict(report)
            
        except Exception as e:
            logger.error(f"Error generating performance report: {str(e)}")
            return {"error": str(e)}
    
    async def get_cost_analysis(self) -> Dict:
        """Get cost breakdown and analysis"""
        try:
            # Query LLM usage events
            llm_events = await self.db.monitoring_events.find({
                "event": "llm_usage"
            }).to_list(length=None)
            
            cost_by_model = defaultdict(float)
            tokens_by_model = defaultdict(int)
            
            for event in llm_events:
                model = event.get("model", "unknown")
                cost_by_model[model] += event.get("cost", 0)
                tokens_by_model[model] += event.get("tokens", 0)
            
            return {
                "total_cost": sum(cost_by_model.values()),
                "cost_by_model": dict(cost_by_model),
                "tokens_by_model": dict(tokens_by_model),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cost analysis: {str(e)}")
            return {"error": str(e)}
    
    async def get_active_tasks(self) -> List[Dict]:
        """Get currently active tasks"""
        return [
            {
                "task_id": task_id,
                "agent": data["agent"],
                "start_time": data["start_time"].isoformat(),
                "duration": (datetime.now(timezone.utc) - data["start_time"]).total_seconds()
            }
            for task_id, data in self.active_tasks.items()
        ]
    
    async def alert_on_threshold(self, metric: str, threshold: float):
        """Send alert if metric exceeds threshold"""
        try:
            current_value = None
            
            if metric == "error_rate":
                total = sum(self.metrics["agent_executions"].values())
                errors = sum(self.metrics["agent_errors"].values())
                current_value = (errors / total * 100) if total > 0 else 0
            elif metric == "cost":
                current_value = self.metrics["total_cost"]
            elif metric == "active_tasks":
                current_value = len(self.active_tasks)
            
            if current_value and current_value > threshold:
                alert = {
                    "type": "threshold_exceeded",
                    "metric": metric,
                    "current_value": current_value,
                    "threshold": threshold,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                await self.db.alerts.insert_one(alert)
                logger.warning(f"Alert: {metric} exceeded threshold: {current_value} > {threshold}")
                
                return alert
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking alert threshold: {str(e)}")
            return None
    
    def _update_performance_metrics(self, agent_name: str, execution_time: float, result: Dict):
        """Update performance metrics for an agent"""
        try:
            # Update average execution time
            current_avg = self.metrics["average_execution_time"][agent_name]
            executions = self.metrics["agent_executions"][agent_name]
            
            new_avg = ((current_avg * (executions - 1)) + execution_time) / executions
            self.metrics["average_execution_time"][agent_name] = new_avg
            
            # Update success rate
            errors = self.metrics["agent_errors"][agent_name]
            success_rate = ((executions - errors) / executions * 100) if executions > 0 else 100.0
            self.metrics["agent_success_rate"][agent_name] = success_rate
            
        except Exception as e:
            logger.error(f"Error updating performance metrics: {str(e)}")


# Global monitoring service instance
_monitoring_service = None


def get_monitoring_service(db, manager) -> MonitoringService:
    """Get or create monitoring service singleton"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService(db, manager)
    return _monitoring_service
