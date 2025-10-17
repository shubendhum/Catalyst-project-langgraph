"""
Coder Agent
Generates complete code files for full-stack applications based on architecture
"""
import os
import logging
import json
import re
from typing import Dict, List, Optional
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class CoderAgent:
    """
    Agent responsible for generating complete code implementation
    """
    
    def __init__(self, llm_client, db, manager, file_service):
        self.llm_client = llm_client
        self.db = db
        self.manager = manager
        self.file_service = file_service
        self.agent_name = "Coder"
    
    async def generate_code(
        self,
        architecture: Dict,
        project_name: str,
        task_id: Optional[str] = None
    ) -> Dict:
        """
        Generate complete code files based on architecture
        
        Args:
            architecture: Technical architecture from Architect Agent
            project_name: Name of the project
            task_id: Task ID for logging
            
        Returns:
            Dictionary containing generated files and status
        """
        logger.info(f"Generating code for project: {project_name}")
        
        if task_id:
            await self._log(task_id, "💻 Starting code generation...")
        
        # Create project structure
        project_path = self.file_service.create_project(project_name)
        
        # Generate backend files
        backend_files = await self._generate_backend_files(architecture, project_name, task_id)
        
        # Generate frontend files
        frontend_files = await self._generate_frontend_files(architecture, project_name, task_id)
        
        # Generate configuration files
        config_files = await self._generate_config_files(architecture, project_name, task_id)
        
        all_files = {
            "backend": backend_files,
            "frontend": frontend_files,
            "config": config_files
        }
        
        # Save all files to disk
        saved_count = await self._save_files_to_disk(project_name, all_files, task_id)
        
        # Save metadata
        metadata = {
            "project_name": project_name,
            "architecture": architecture,
            "files_generated": saved_count,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "agent": self.agent_name
        }
        self.file_service.save_metadata(project_name, metadata)
        
        # Store in database
        await self._save_to_database(project_name, architecture, all_files, metadata)
        
        if task_id:
            await self._log(task_id, f"✅ Code generation complete! {saved_count} files created")
        
        return {
            "status": "success",
            "project_path": project_path,
            "files_generated": saved_count,
            "files": all_files,
            "metadata": metadata
        }
    
    async def _generate_backend_files(
        self,
        architecture: Dict,
        project_name: str,
        task_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate all backend files"""
        
        if task_id:
            await self._log(task_id, "📦 Generating backend files...")
        
        backend_files = {}
        
        # Generate main.py
        backend_files["backend/main.py"] = await self._generate_backend_main(architecture)
        
        # Generate models
        for model in architecture.get("data_models", [])[:3]:  # Limit to 3 models
            model_name = model.get("model", "Data").lower()
            backend_files[f"backend/models/{model_name}.py"] = await self._generate_model_file(model)
        
        # Generate API routes
        api_specs = architecture.get("api_specs", [])
        backend_files["backend/api/auth.py"] = await self._generate_auth_routes(api_specs)
        backend_files["backend/api/data.py"] = await self._generate_data_routes(api_specs)
        
        # Generate requirements.txt
        backend_files["backend/requirements.txt"] = self._generate_requirements()
        
        # Generate __init__.py files
        backend_files["backend/__init__.py"] = ""
        backend_files["backend/models/__init__.py"] = ""
        backend_files["backend/api/__init__.py"] = ""
        
        return backend_files
    
    async def _generate_frontend_files(
        self,
        architecture: Dict,
        project_name: str,
        task_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate all frontend files"""
        
        if task_id:
            await self._log(task_id, "⚛️  Generating frontend files...")
        
        frontend_files = {}
        
        # Generate main files
        frontend_files["frontend/src/App.js"] = await self._generate_app_js(architecture)
        frontend_files["frontend/src/index.js"] = self._generate_index_js()
        frontend_files["frontend/src/index.css"] = self._generate_index_css()
        
        # Generate pages
        pages = architecture.get("frontend", {}).get("pages", [])
        for page in pages[:5]:  # Limit to 5 pages
            page_name = page.get("name", "Page")
            frontend_files[f"frontend/src/pages/{page_name}.js"] = await self._generate_page_file(page, architecture)
        
        # Generate components
        frontend_files["frontend/src/components/Navbar.js"] = await self._generate_navbar_component()
        
        # Generate API service
        frontend_files["frontend/src/services/api.js"] = await self._generate_api_service(architecture)
        
        # Generate package.json
        frontend_files["frontend/package.json"] = self._generate_package_json(project_name)
        
        # Generate public/index.html
        frontend_files["frontend/public/index.html"] = self._generate_index_html(project_name)
        
        return frontend_files
    
    async def _generate_config_files(
        self,
        architecture: Dict,
        project_name: str,
        task_id: Optional[str] = None
    ) -> Dict[str, str]:
        """Generate configuration files"""
        
        config_files = {}
        
        # Generate .env files
        config_files["backend/.env.example"] = self._generate_backend_env()
        config_files["frontend/.env.example"] = self._generate_frontend_env()
        
        # Generate README
        config_files["README.md"] = await self._generate_readme(architecture, project_name)
        
        return config_files

    async def _log(self, task_id: str, agent_name: str, message: str):
        log_doc = {
            "task_id": task_id,
            "agent_name": agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)