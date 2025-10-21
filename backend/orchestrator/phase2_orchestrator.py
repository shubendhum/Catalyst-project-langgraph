"""
Phase 2 Orchestrator - Complete Agent Suite
Planner → Architect → Coder → Tester → Reviewer → Deployer
Plus standalone Explorer Agent
"""
import logging
import subprocess
import os
import asyncio
from typing import Dict, Optional
from datetime import datetime, timezone

from agents.planner_agent import get_planner_agent
from agents.architect_agent import get_architect_agent
from agents.rapid_mvp_coder import get_rapid_mvp_coder
from agents.tester_agent import get_tester_agent
from agents.reviewer_agent import get_reviewer_agent
from agents.deployer_agent import get_deployer_agent
from agents.explorer_agent import get_explorer_agent
from services.file_system_service import get_file_system_service
from services.github_service import get_github_service
from llm_client import get_llm_client
from services.optimized_llm_client import get_optimized_llm_client

logger = logging.getLogger(__name__)


class Phase2Orchestrator:
    """
    Complete orchestrator with full agent suite
    Includes feedback loops and Explorer capability
    """
    
    def __init__(self, db, manager, config: Optional[Dict] = None):
        self.db = db
        self.manager = manager
        self.config = config or {}
        
        # Initialize LLM client - use OptimizedLLMClient for cost savings
        self.optimized_llm_client = get_optimized_llm_client(
            db=db,
            project_id=None,  # Will be set per task
            default_model=self.config.get("model", "claude-3-7-sonnet-20250219")
        )
        self.llm_client = get_llm_client(self.config)
        
        # Initialize services
        self.file_service = get_file_system_service()
        self.github_service = get_github_service()
        
        # Initialize all agents - using optimized client for better cost management
        self.planner = get_planner_agent(self.optimized_llm_client)
        self.architect = get_architect_agent(self.optimized_llm_client)
        self.coder = get_rapid_mvp_coder(self.optimized_llm_client, db, manager, self.file_service)
        self.tester = get_tester_agent(self.optimized_llm_client, db, manager, self.file_service)
        self.reviewer = get_reviewer_agent(self.optimized_llm_client, db, manager, self.file_service)
        self.deployer = get_deployer_agent(self.optimized_llm_client, db, manager, self.file_service)
        self.explorer = get_explorer_agent(self.optimized_llm_client, db, manager, self.file_service)
        
        # Track cost savings
        self.total_cost_saved = 0.0
    
    async def execute_task(
        self,
        task_id: str,
        project_id: str,
        user_requirements: str
    ) -> Dict:
        """
        Execute complete agent workflow with testing and review
        
        Args:
            task_id: Task identifier
            project_id: Project identifier  
            user_requirements: User's description
            
        Returns:
            Dictionary with results
        """
        logger.info(f"Starting Phase 2 execution for task {task_id}")
        
        try:
            await self._update_task_status(task_id, "planning")
            await self._log(task_id, "🚀 Starting complete application development workflow...")
            
            # Get project info
            project = await self.db.projects.find_one({"id": project_id})
            project_name = project.get("name", f"Project_{project_id[:8]}") if project else f"Project_{project_id[:8]}"
            
            # STEP 1: Planning
            await self._log(task_id, "📋 Planner Agent: Creating comprehensive development plan...")
            plan = await self.planner.create_plan(
                user_requirements=user_requirements,
                project_name=project_name
            )
            await self._log(task_id, f"✅ Plan created with {len(plan.get('features', []))} features and {len(plan.get('api_endpoints', []))} API endpoints")
            await self._save_task_data(task_id, {"plan": plan, "status": "architecting"})
            
            # STEP 2: Architecture Design
            await self._update_task_status(task_id, "architecting")
            await self._log(task_id, "🏗️  Architect Agent: Designing scalable architecture...")
            
            architecture = await self.architect.design_architecture(
                plan=plan,
                project_name=project_name
            )
            data_models = len(architecture.get('data_models', []))
            await self._log(task_id, f"✅ Architecture designed: {data_models} data models, API structure defined")
            await self._save_task_data(task_id, {"architecture": architecture, "status": "coding"})
            
            # STEP 3: Code Generation
            await self._update_task_status(task_id, "coding")
            await self._log(task_id, "💻 Coder Agent: Generating production-ready code...")
            await self._log(task_id, "📁 Creating project structure...")
            
            code_result = await self.coder.generate_code(
                architecture=architecture,
                project_name=project_name,
                task_id=task_id
            )
            
            if code_result["status"] != "success":
                raise Exception(f"Code generation failed: {code_result.get('error')}")
            
            files_generated = code_result['files_generated']
            await self._log(task_id, f"✅ Code generation complete: {files_generated} files created")
            await self._save_task_data(task_id, {"code_result": code_result, "status": "testing_and_reviewing"})
            
            # STEP 4 & 5: Testing and Review in PARALLEL (both analyze generated code)
            await self._update_task_status(task_id, "testing_and_reviewing")
            await self._log(task_id, "⚡ Running quality checks in parallel...")
            await self._log(task_id, "🧪 Tester: Analyzing code for test coverage...")
            await self._log(task_id, "🔍 Reviewer: Checking code quality and security...")
            
            # Run Tester and Reviewer concurrently
            test_task = self.tester.test_application(
                project_name=project_name,
                architecture=architecture,
                code_files=code_result["files"],
                task_id=task_id
            )
            
            review_task = self.reviewer.review_code(
                project_name=project_name,
                architecture=architecture,
                code_files=code_result["files"],
                task_id=task_id
            )
            
            # Wait for both to complete
            test_results, review_results = await asyncio.gather(test_task, review_task)
            
            await self._log(task_id, f"✅ Testing complete: {test_results['overall_status']}")
            await self._log(task_id, f"✅ Review complete: Score {review_results['overall_score']}/100")
            await self._save_task_data(task_id, {
                "test_results": test_results,
                "review_results": review_results,
                "status": "deploying"
            })
            
            # Check if tests failed and need rework
            if test_results["overall_status"] == "failed":
                await self._log(task_id, "⚠️  Tests failed. Continuing to deployment configuration...")
                # Note: In a full implementation, we'd loop back to Coder here
            
            # STEP 6: Deployment Configuration
            await self._update_task_status(task_id, "deploying")
            
            # Get deployment target from config (default to docker)
            deployment_target = self.config.get("deployment_target", "docker")
            deployment_config = self.config.get("deployment_config", {})
            
            await self._log(task_id, f"🚀 Deployer Agent: Creating {deployment_target.upper()} deployment files...")
            
            deployment_result = await self.deployer.deploy_application(
                project_name=project_name,
                architecture=architecture,
                deployment_target=deployment_target,
                deployment_config=deployment_config,
                task_id=task_id
            )
            
            if deployment_result["status"] != "success":
                raise Exception(f"Deployment configuration failed: {deployment_result.get('error')}")
            
            await self._log(task_id, "✅ Deployment configuration complete!")
            await self._log(task_id, f"📦 Generated Dockerfile, docker-compose.yml, and deployment scripts")
            await self._save_task_data(task_id, {"deployment_result": deployment_result, "status": "completed"})
            
            # Mark as completed
            await self._update_task_status(task_id, "completed")
            await self._log(task_id, "🎉 Complete workflow finished successfully!")
            
            await self.db.tasks.update_one(
                {"id": task_id},
                {
                    "$set": {
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "project_path": code_result["project_path"],
                        "cost_stats": self.optimized_llm_client.get_stats()
                    }
                }
            )
            
            # Log cost savings
            cost_stats = self.optimized_llm_client.get_stats()
            await self._log(
                task_id, 
                f"💰 Cost Stats: {cost_stats['calls_made']} LLM calls, "
                f"{cost_stats['cache_hit_rate']:.1f}% cache hit rate, "
                f"${cost_stats['total_cost']:.4f} total cost"
            )
            
            return {
                "status": "success",
                "task_id": task_id,
                "project_name": project_name,
                "project_path": code_result["project_path"],
                "summary": {
                    "files_generated": code_result["files_generated"],
                    "test_status": test_results["overall_status"],
                    "review_score": review_results["overall_score"],
                    "recommendations": len(review_results.get("recommendations", []))
                },
                "cost_stats": self.optimized_llm_client.get_stats(),
                "plan": plan,
                "architecture": architecture,
                "code_result": code_result,
                "test_results": test_results,
                "review_results": review_results,
                "deployment_result": deployment_result
            }
            
        except Exception as e:
            logger.error(f"Error in Phase 2 execution: {str(e)}")
            await self._log(task_id, f"❌ Error: {str(e)}")
            await self._update_task_status(task_id, "failed")
            
            await self.db.tasks.update_one(
                {"id": task_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": str(e),
                        "failed_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            return {
                "status": "failed",
                "task_id": task_id,
                "error": str(e)
            }
    
    async def explore_target(
        self,
        target: str,
        target_type: str,
        credentials: Optional[Dict] = None,
        task_id: Optional[str] = None
    ) -> Dict:
        """
        Execute Explorer agent to analyze a target
        
        Args:
            target: URL, GitHub repo, or connection string
            target_type: "github", "url", "deployment", "database", "bigdata"
            credentials: Optional credentials
            task_id: Optional task ID for logging
            
        Returns:
            Exploration results
        """
        logger.info(f"Exploring {target_type}: {target}")
        
        if task_id:
            await self._log(task_id, f"🔍 Explorer Agent: Analyzing {target_type}...")
        
        exploration_result = await self.explorer.explore(
            target=target,
            target_type=target_type,
            credentials=credentials,
            task_id=task_id
        )
        
        # Save exploration results to database
        await self.db.explorations.insert_one({
            "target": target,
            "target_type": target_type,
            "result": exploration_result,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        return exploration_result
    
    async def push_to_github(
        self,
        project_name: str,
        github_repo_url: str,
        github_token: str,
        branch: str = "catalyst-generated",
        task_id: Optional[str] = None
    ) -> Dict:
        """
        Push generated code to GitHub
        
        Args:
            project_name: Name of the project
            github_repo_url: GitHub repository URL
            github_token: GitHub token
            branch: Branch to push to
            task_id: Optional task ID for logging
            
        Returns:
            Push result
        """
        if task_id:
            await self._log(task_id, "📤 Pushing code to GitHub...")
        
        project_path = str(self.file_service.base_projects_dir / project_name)
        
        # Initialize git repo if not exists
        git_dir = f"{project_path}/.git"
        if not os.path.exists(git_dir):
            subprocess.run(["git", "init"], cwd=project_path, check=True)
            subprocess.run(
                ["git", "remote", "add", "origin", github_repo_url],
                cwd=project_path,
                check=True
            )
        
        # Create branch
        branch_result = self.github_service.create_branch(
            local_path=project_path,
            branch_name=branch,
            from_branch="main"
        )
        
        if branch_result["status"] != "success":
            if task_id:
                await self._log(task_id, f"⚠️  Branch already exists or error: {branch_result.get('error')}")
        
        # Push code
        push_result = self.github_service.push_to_github(
            local_path=project_path,
            repo_url=github_repo_url,
            token=github_token,
            branch=branch,
            commit_message="Generated by Catalyst AI"
        )
        
        if task_id:
            if push_result["status"] == "success":
                await self._log(task_id, f"✅ Code pushed to GitHub branch: {branch}")
            else:
                await self._log(task_id, f"❌ Failed to push: {push_result.get('error')}")
        
        return push_result
    
    async def _update_task_status(self, task_id: str, status: str):
        """Update task status"""
        await self.db.tasks.update_one(
            {"id": task_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
    
    async def _save_task_data(self, task_id: str, data: Dict):
        """Save task data"""
        await self.db.tasks.update_one(
            {"id": task_id},
            {"$set": data}
        )
    
    async def _log(self, task_id: str, message: str):
        """Log orchestrator activity"""
        log_doc = {
            "task_id": task_id,
            "agent_name": "Orchestrator",
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)


def get_phase2_orchestrator(db, manager, config: Optional[Dict] = None) -> Phase2Orchestrator:
    """Get Phase2Orchestrator instance"""
    return Phase2Orchestrator(db, manager, config)
