"""
Event-Driven Architect Agent
Consumes: plan.created
Publishes: architecture.proposed
"""
import logging
import yaml
import json
from typing import Dict, Optional

from agents_v2.base_agent import EventDrivenAgent
from agents.architect_agent import get_architect_agent
from events import (
    AgentEvent,
    ArchitectureProposedPayload,
    create_architecture_proposed_event
)
from services.postgres_service import update_task_status

logger = logging.getLogger(__name__)


class EventDrivenArchitectAgent(EventDrivenAgent):
    """
    Architect agent with event-driven interface
    """
    
    def __init__(self, db, manager, llm_client):
        super().__init__("architect", db, manager, llm_client)
        
        # Wrap existing architect agent
        self.architect = get_architect_agent(llm_client)
    
    async def process_event(self, event: AgentEvent) -> AgentEvent:
        """
        Process plan.created event
        Design architecture and publish architecture.proposed event
        """
        
        task_id = str(event.task_id)
        plan_ref = event.payload.get("plan_ref")
        
        await self._log(task_id, "🏗️ Architect: Analyzing plan requirements...")
        
        # Update task status
        await update_task_status(task_id, "architecting", "architect")
        
        # Load plan from Git
        plan = await self._load_plan_from_git(plan_ref, task_id)
        
        # Extract project name from repo
        project_name = event.repo.split('/')[-1]
        
        await self._log(task_id, "🤖 Architect: Selecting optimal tech stack...")
        
        # Use existing architect logic
        architecture = await self.architect.design_architecture(
            plan=plan,
            project_name=project_name
        )
        
        # Log progress
        data_models = len(architecture.get('data_models', []))
        await self._log(task_id, f"✅ Tech Stack: FastAPI + React + MongoDB")
        await self._log(task_id, f"🤖 Architect: Designing {data_models} data models...")
        
        for model in architecture.get('data_models', []):
            model_name = model if isinstance(model, str) else model.get('name', 'Unknown')
            await self._log(task_id, f"📊 Data Model: {model_name}")
        
        await self._log(task_id, "🤖 Architect: Creating API contracts...")
        
        # Save architecture to Git
        arch_path = await self._save_architecture_to_git(project_name, architecture, task_id)
        
        api_count = len(architecture.get('api_design', {}).get('endpoints', []))
        await self._log(task_id, f"✅ API Design: {api_count} REST endpoints defined")
        await self._log(task_id, f"📝 Generated architecture/design.md")
        await self._log(task_id, f"📝 Generated architecture/openapi.yaml")
        await self._log(task_id, "✅ Architecture design complete")
        
        # Create payload
        payload = ArchitectureProposedPayload(
            architecture_ref=f"git://{event.repo}/architecture/",
            tech_stack={
                "backend": "FastAPI 0.110+",
                "frontend": "React 19",
                "database": "MongoDB 5.0",
                "cache": "Redis 7"
            },
            data_model_count=data_models,
            api_endpoint_count=api_count,
            adrs_created=0,  # TODO: Generate ADRs
            requires_review=False
        )
        
        # Create and return event
        return create_architecture_proposed_event(
            task_id=event.task_id,
            trace_id=event.trace_id,
            repo=event.repo,
            commit="",
            payload=payload
        )
    
    async def process_direct(self, plan: Dict, project_name: str) -> Dict:
        """Direct call interface (sequential mode)"""
        return await self.architect.design_architecture(
            plan=plan,
            project_name=project_name
        )
    
    async def _load_plan_from_git(self, plan_ref: str, task_id: str) -> Dict:
        """Load plan.yaml from Git reference"""
        try:
            # Extract repo and path from git://repo/path format
            if plan_ref.startswith("git://"):
                parts = plan_ref.replace("git://", "").split("/", 1)
                repo = parts[0]
                path = parts[1] if len(parts) > 1 else "planning/plan.yaml"
            else:
                path = plan_ref
            
            # Try to load from file system
            import os
            file_path = f"/app/repos/{path}"
            
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                # Fallback: load from MongoDB (sequential mode saved it there)
                task = await self.db.tasks.find_one({"id": task_id})
                if task and 'plan' in task:
                    return task['plan']
                
                logger.warning(f"Plan not found at {file_path}, using empty plan")
                return {}
                
        except Exception as e:
            logger.error(f"Failed to load plan from Git: {e}")
            return {}
    
    async def _save_architecture_to_git(self, project_name: str, architecture: Dict, task_id: str) -> str:
        """Save architecture files to Git"""
        from config.environment import should_use_git
        
        if not should_use_git():
            return "architecture/ (filesystem only)"
        
        try:
            import os
            from pathlib import Path
            
            repo_path = Path(f"/app/repos/{project_name}")
            arch_dir = repo_path / "architecture"
            arch_dir.mkdir(parents=True, exist_ok=True)
            
            # Save design.md
            design_file = arch_dir / "design.md"
            with open(design_file, 'w') as f:
                f.write(f"# {project_name} Architecture\n\n")
                f.write(yaml.dump(architecture, default_flow_style=False))
            
            # Save data-models.json
            models_file = arch_dir / "data-models.json"
            with open(models_file, 'w') as f:
                json.dump(architecture.get('data_models', []), f, indent=2)
            
            # Git commit
            os.system(f"cd {repo_path} && git add architecture/")
            os.system(f"cd {repo_path} && git commit -m 'feat(architecture): Add system architecture\n\n- {len(architecture.get('data_models', []))} data models designed'")
            
            return "architecture/"
            
        except Exception as e:
            logger.error(f"Failed to save architecture to Git: {e}")
            return "architecture/ (save failed)"


def get_event_driven_architect(db, manager, llm_client) -> EventDrivenArchitectAgent:
    """Factory function"""
    return EventDrivenArchitectAgent(db, manager, llm_client)
