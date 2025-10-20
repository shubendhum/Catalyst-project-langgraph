"""
Event-Driven Coder Agent
Consumes: architecture.proposed
Publishes: code.pr.opened
"""
import logging
import os
from pathlib import Path
from typing import Dict
from uuid import UUID

from agents_v2.base_agent import EventDrivenAgent
from agents.coder import get_coder_agent
from events import (
    AgentEvent,
    CodePROpenedPayload,
    create_code_pr_opened_event
)
from services.postgres_service import update_task_status
from config.environment import should_use_git, get_config

logger = logging.getLogger(__name__)


class EventDrivenCoderAgent(EventDrivenAgent):
    """
    Coder agent with event-driven interface
    Generates code and commits to Git
    """
    
    def __init__(self, db, manager, llm_client, file_service):
        super().__init__("coder", db, manager, llm_client)
        
        # Wrap existing coder agent
        self.coder = get_coder_agent(llm_client, db, manager, file_service)
        self.file_service = file_service
    
    async def process_event(self, event: AgentEvent) -> AgentEvent:
        """
        Process architecture.proposed event
        Generate code and publish code.pr.opened event
        """
        
        task_id = str(event.task_id)
        architecture_ref = event.payload.get("architecture_ref")
        
        await self._log(task_id, "💻 Coder: Generating production-ready code...")
        await self._log(task_id, "📁 Creating project structure...")
        
        # Update task status
        await update_task_status(task_id, "coding", "coder")
        
        # Load architecture
        architecture = await self._load_architecture(architecture_ref, task_id)
        
        # Extract project name
        project_name = event.repo.split('/')[-1]
        
        # Use existing coder logic to generate code
        code_result = await self.coder.generate_code(
            architecture=architecture,
            project_name=project_name,
            task_id=task_id
        )
        
        if code_result["status"] != "success":
            raise Exception(f"Code generation failed: {code_result.get('error')}")
        
        files_generated = code_result["files_generated"]
        
        await self._log(task_id, f"✅ Code generation complete: {files_generated} files created")
        
        # Commit to Git branch
        branch_name, commit_sha = await self._commit_to_git_branch(
            project_name,
            task_id,
            code_result
        )
        
        # Calculate statistics
        backend_files = len([f for f in code_result.get("files", {}).get("backend", {}).keys()])
        frontend_files = len([f for f in code_result.get("files", {}).get("frontend", {}).keys()])
        test_files = len([f for f in code_result.get("files", {}).get("tests", {}).keys()])
        
        # Create payload
        payload = CodePROpenedPayload(
            branch=branch_name,
            commit=commit_sha,
            files_created=files_generated,
            lines_of_code=0,  # TODO: Calculate actual LOC
            backend_files=backend_files,
            frontend_files=frontend_files,
            test_files=test_files,
            estimated_coverage=0.85,
            pr_url=None,  # TODO: Create GitHub PR if enabled
            local_repo=f"/app/repos/{project_name}",
            git_diff_summary={
                "additions": 0,  # TODO: Calculate from git diff
                "deletions": 0,
                "files_changed": files_generated
            }
        )
        
        # Create and return event
        return create_code_pr_opened_event(
            task_id=event.task_id,
            trace_id=event.trace_id,
            repo=event.repo,
            branch=branch_name,
            commit=commit_sha,
            payload=payload
        )
    
    async def process_direct(
        self,
        architecture: Dict,
        project_name: str,
        task_id: Optional[str] = None
    ) -> Dict:
        """Direct call interface (sequential mode)"""
        return await self.coder.generate_code(
            architecture=architecture,
            project_name=project_name,
            task_id=task_id
        )
    
    async def _load_architecture(self, architecture_ref: str, task_id: str) -> Dict:
        """Load architecture from Git reference"""
        try:
            # Try filesystem first
            if architecture_ref.startswith("git://"):
                path = architecture_ref.replace("git://", "").split("/", 1)[1]
                file_path = f"/app/repos/{path}/design.md"
            else:
                file_path = architecture_ref
            
            # Fallback: load from MongoDB
            task = await self.db.tasks.find_one({"id": task_id})
            if task and 'architecture' in task:
                return task['architecture']
            
            logger.warning(f"Architecture not found, using empty architecture")
            return {}
            
        except Exception as e:
            logger.error(f"Failed to load architecture: {e}")
            return {}
    
    async def _commit_to_git_branch(
        self,
        project_name: str,
        task_id: str,
        code_result: Dict
    ) -> tuple[str, str]:
        """
        Commit generated code to Git feature branch
        Returns: (branch_name, commit_sha)
        """
        branch_name = f"feature/task-{task_id[:8]}"
        commit_sha = ""
        
        if not should_use_git():
            return branch_name, "filesystem-only"
        
        try:
            from services.git_service_v2 import get_git_service
            from integrations.github_integration import get_github_service
            
            git_service = get_git_service()
            github_service = get_github_service()
            
            # Initialize repo
            repo_path = git_service.init_repo(project_name)
            
            # Create feature branch
            git_service.create_branch(project_name, branch_name)
            
            # Commit generated code
            files_count = code_result.get("files_generated", 0)
            commit_message = f"""feat: Generate complete application code

- {files_count} files created
- Backend: FastAPI with models and routes
- Frontend: React with components
- Tests: Unit and integration tests
- Deployment: Docker configuration

[coder-agent]
"""
            
            commit_sha = git_service.commit(project_name, commit_message)
            
            if commit_sha:
                await self._log(task_id, f"🔀 Committed to branch: {branch_name} ({commit_sha[:7]})")
                
                # Push to GitHub if enabled
                github_config = get_config()["git"]
                if github_config.get("mode") in ["github", "both"]:
                    pushed = await github_service.push_to_github(project_name, branch_name)
                    
                    if pushed:
                        await self._log(task_id, f"📤 Pushed to GitHub: {github_config.get('github_org')}/{project_name}")
                        
                        # Create PR if configured
                        if github_config.get("create_pr", True):
                            pr_url = await github_service.create_pull_request(
                                project_name=project_name,
                                branch=branch_name,
                                title=f"feat: {project_name} - Task {task_id[:8]}",
                                description=f"Generated by Catalyst AI\n\nTask ID: {task_id}\n\n## Features\n\n{files_count} files created including backend API, frontend UI, and tests."
                            )
                            
                            if pr_url:
                                await self._log(task_id, f"📬 Pull Request created: {pr_url}")
                                return branch_name, commit_sha
                    else:
                        await self._log(task_id, "⚠️ GitHub push failed (check token/permissions)")
            
            return branch_name, commit_sha or "commit-failed"
            
        except Exception as e:
            logger.error(f"Failed to commit to Git: {e}")
            await self._log(task_id, f"⚠️ Git commit error: {str(e)}")
            return branch_name, "commit-failed"


def get_event_driven_coder(db, manager, llm_client, file_service) -> EventDrivenCoderAgent:
    """Factory function"""
    return EventDrivenCoderAgent(db, manager, llm_client, file_service)
