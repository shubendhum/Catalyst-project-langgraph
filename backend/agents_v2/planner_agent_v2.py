"""
Event-Driven Planner Agent
Consumes: task.initiated
Publishes: plan.created
"""
import logging
import yaml
from uuid import UUID
from typing import Dict

from agents_v2.base_agent import EventDrivenAgent
from agents.planner_agent import get_planner_agent
from events import (
    AgentEvent,
    PlanCreatedPayload,
    create_plan_created_event
)
from services.postgres_service import update_task_status

logger = logging.getLogger(__name__)


class EventDrivenPlannerAgent(EventDrivenAgent):
    """
    Planner agent with event-driven interface
    Falls back to direct calls in sequential mode
    """
    
    def __init__(self, db, manager, llm_client):
        super().__init__("planner", db, manager, llm_client)
        
        # Wrap existing planner agent
        self.planner = get_planner_agent(llm_client)
    
    async def process_event(self, event: AgentEvent) -> AgentEvent:
        """
        Process task.initiated event
        Create development plan and publish plan.created event
        """
        
        # Extract data from event
        task_id = str(event.task_id)
        project_id = event.payload.get("project_id")
        user_requirements = event.payload.get("user_requirements")
        
        await self._log(task_id, "📋 Planner: Analyzing your requirements...")
        
        # Update task status in Postgres
        await update_task_status(task_id, "planning", "planner")
        
        # Get project name from database
        project = await self.db.projects.find_one({"id": project_id})
        project_name = project.get("name", f"Project-{project_id[:8]}") if project else f"Project-{project_id[:8]}"
        
        # Use existing planner logic
        plan = await self.planner.create_plan(
            user_requirements=user_requirements,
            project_name=project_name
        )
        
        # Log detailed progress
        feature_count = len(plan.get('features', []))
        task_count = len(plan.get('tasks', {}).get('backend', [])) + len(plan.get('tasks', {}).get('frontend', []))
        api_count = len(plan.get('api_endpoints', []))
        
        await self._log(task_id, f"🤖 Planner: Identified {feature_count} core features")
        await self._log(task_id, f"🤖 Planner: Breaking down into {task_count} development tasks")
        await self._log(task_id, f"🤖 Planner: Defining {api_count} API endpoints")
        await self._log(task_id, "🤖 Planner: Assessing risks and dependencies")
        
        # Save plan to Git (in Docker mode)
        plan_file_path = await self._save_plan_to_git(project_name, plan, task_id)
        
        await self._log(task_id, f"✅ Planning complete: {feature_count} features, {task_count} tasks")
        await self._log(task_id, f"📄 Generated {plan_file_path}")
        
        # Estimate complexity
        complexity_score = self._calculate_complexity(plan)
        risk_level = self._assess_risk(plan)
        estimated_hours = task_count * 2  # Rough estimate
        
        # Create payload
        payload = PlanCreatedPayload(
            plan_ref=f"git://{event.repo}/planning/plan.yaml",
            feature_count=feature_count,
            task_count=task_count,
            api_endpoint_count=api_count,
            estimated_hours=estimated_hours,
            risk_level=risk_level,
            complexity_score=complexity_score
        )
        
        # Create and return event
        return create_plan_created_event(
            task_id=event.task_id,
            trace_id=event.trace_id,
            repo=event.repo,
            commit="",  # Will be updated after Git commit
            payload=payload
        )
    
    async def process_direct(
        self,
        user_requirements: str,
        project_name: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Direct call interface (sequential mode)
        """
        return await self.planner.create_plan(
            user_requirements=user_requirements,
            project_name=project_name,
            context=context
        )
    
    async def _save_plan_to_git(self, project_name: str, plan: Dict, task_id: str) -> str:
        """
        Save plan.yaml to Git repository
        """
        from config.environment import should_use_git
        
        if not should_use_git():
            return "planning/plan.yaml (filesystem only)"
        
        try:
            import os
            from pathlib import Path
            
            # Create repo directory
            repo_path = Path(f"/app/repos/{project_name}")
            repo_path.mkdir(parents=True, exist_ok=True)
            
            planning_dir = repo_path / "planning"
            planning_dir.mkdir(exist_ok=True)
            
            # Save plan.yaml
            plan_file = planning_dir / "plan.yaml"
            with open(plan_file, 'w') as f:
                yaml.dump(plan, f, default_flow_style=False, sort_keys=False)
            
            await self._log(task_id, f"📄 Saved plan to {plan_file}")
            
            # Initialize Git repo if needed
            if not (repo_path / ".git").exists():
                os.system(f"cd {repo_path} && git init")
                os.system(f"cd {repo_path} && git config user.name 'Catalyst AI'")
                os.system(f"cd {repo_path} && git config user.email 'ai@catalyst.dev'")
            
            # Git add and commit
            os.system(f"cd {repo_path} && git add planning/")
            os.system(f"cd {repo_path} && git commit -m 'feat(planning): Add development plan\n\n- {plan.get('features', []).__len__()} features defined'")
            
            return f"planning/plan.yaml"
            
        except Exception as e:
            logger.error(f"Failed to save plan to Git: {e}")
            return "planning/plan.yaml (save failed)"
    
    def _calculate_complexity(self, plan: Dict) -> float:
        """Calculate overall complexity score (0-1)"""
        features = plan.get('features', [])
        
        complexity_map = {"Simple": 0.3, "Medium": 0.6, "Complex": 0.9}
        
        if not features:
            return 0.5
        
        total = sum(complexity_map.get(f.get('complexity', 'Medium'), 0.6) for f in features)
        return total / len(features)
    
    def _assess_risk(self, plan: Dict) -> str:
        """Assess risk level based on plan"""
        features = plan.get('features', [])
        high_priority = sum(1 for f in features if f.get('priority') == 'High')
        
        if high_priority >= 5:
            return "high"
        elif high_priority >= 3:
            return "medium"
        else:
            return "low"


def get_event_driven_planner(db, manager, llm_client) -> EventDrivenPlannerAgent:
    """Factory function"""
    return EventDrivenPlannerAgent(db, manager, llm_client)
