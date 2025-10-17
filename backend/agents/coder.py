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
    

    
    async def _generate_backend_main(self, architecture: Dict) -> str:
        """Generate FastAPI main.py"""
        prompt = f"""Generate a complete FastAPI main.py file for this architecture:

{json.dumps(architecture.get('backend', {}), indent=2)}

Include:
- FastAPI app initialization
- CORS middleware
- MongoDB connection
- API route imports
- Health check endpoint

Use best practices, async/await, and proper error handling."""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return self._extract_code_from_response(response.content)
    
    async def _generate_model_file(self, model: Dict) -> str:
        """Generate Pydantic model file"""
        prompt = f"""Generate a Pydantic model file for:

{json.dumps(model, indent=2)}

Include:
- Pydantic BaseModel classes
- Field validation
- UUID for IDs (not MongoDB ObjectId)
- Proper type hints
- ConfigDict for MongoDB compatibility"""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return self._extract_code_from_response(response.content)
    
    async def _generate_auth_routes(self, api_specs: List[Dict]) -> str:
        """Generate authentication API routes"""
        auth_specs = [spec for spec in api_specs if 'auth' in spec.get('path', '')]
        
        prompt = f"""Generate FastAPI authentication routes for:

{json.dumps(auth_specs, indent=2)}

Include:
- Register endpoint
- Login endpoint
- JWT token generation
- Password hashing with bcrypt
- Proper error handling
- Pydantic models for request/response"""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return self._extract_code_from_response(response.content)
    
    async def _generate_data_routes(self, api_specs: List[Dict]) -> str:
        """Generate data API routes"""
        data_specs = [spec for spec in api_specs if 'auth' not in spec.get('path', '')]
        
        prompt = f"""Generate FastAPI data routes for:

{json.dumps(data_specs, indent=2)}

Include:
- CRUD endpoints
- JWT authentication dependency
- MongoDB async operations
- Proper error handling
- Pydantic models"""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return self._extract_code_from_response(response.content)
    
    def _generate_requirements(self) -> str:
        """Generate requirements.txt"""
        return """fastapi==0.104.1
uvicorn==0.24.0
motor==3.3.2
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
python-dotenv==1.0.0
"""

    async def _generate_app_js(self, architecture: Dict) -> str:
        """Generate React App.js"""
        pages = architecture.get("frontend", {}).get("pages", [])
        routes = architecture.get("frontend", {}).get("routing", [])
        
        prompt = f"""Generate a complete React App.js with routing for:

Pages: {json.dumps(pages, indent=2)}
Routes: {json.dumps(routes, indent=2)}

Include:
- React Router v6
- Protected routes with authentication
- Navbar component
- Tailwind CSS styling
- Context for auth state"""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return self._extract_code_from_response(response.content)
    
    def _generate_index_js(self) -> str:
        """Generate React index.js"""
        return """import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""
    
    def _generate_index_css(self) -> str:
        """Generate Tailwind CSS index.css"""
        return """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
"""
    
    async def _generate_page_file(self, page: Dict, architecture: Dict) -> str:
        """Generate React page component"""
        prompt = f"""Generate a React page component for:

{json.dumps(page, indent=2)}

Include:
- Functional component with hooks
- Tailwind CSS styling
- API integration if needed
- Loading and error states
- Responsive design"""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return self._extract_code_from_response(response.content)
    
    async def _generate_navbar_component(self) -> str:
        """Generate Navbar component"""
        prompt = """Generate a React Navbar component with:
- Logo and app name
- Navigation links (Home, Dashboard, Logout)
- Responsive mobile menu
- Tailwind CSS styling
- Authentication-aware (show/hide based on login)"""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return self._extract_code_from_response(response.content)
    
    async def _generate_api_service(self, architecture: Dict) -> str:
        """Generate API service client"""
        endpoints = architecture.get("api_specs", [])
        
        prompt = f"""Generate a JavaScript API service client for:

{json.dumps(endpoints, indent=2)}

Include:
- Axios instance with interceptors
- JWT token handling
- All API methods
- Error handling
- Base URL from environment"""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return self._extract_code_from_response(response.content)
    
    def _generate_package_json(self, project_name: str) -> str:
        """Generate package.json"""
        return json.dumps({
            "name": project_name.lower().replace(" ", "-"),
            "version": "0.1.0",
            "private": True,
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.20.0",
                "axios": "^1.6.2",
                "react-scripts": "5.0.1"
            },
            "devDependencies": {
                "tailwindcss": "^3.3.5",
                "autoprefixer": "^10.4.16",
                "postcss": "^8.4.32"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build",
                "test": "react-scripts test",
                "eject": "react-scripts eject"
            }
        }, indent=2)
    
    def _generate_index_html(self, project_name: str) -> str:
        """Generate index.html"""
        return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="{project_name}" />
    <title>{project_name}</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
"""
    
    def _generate_backend_env(self) -> str:
        """Generate backend .env.example"""
        return """MONGO_URL=mongodb://localhost:27017
DB_NAME=myapp
JWT_SECRET_KEY=your-secret-key-change-this
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
"""
    
    def _generate_frontend_env(self) -> str:
        """Generate frontend .env.example"""
        return """REACT_APP_API_URL=http://localhost:8001/api
"""
    
    async def _generate_readme(self, architecture: Dict, project_name: str) -> str:
        """Generate README.md"""
        prompt = f"""Generate a comprehensive README.md for project: {project_name}

Architecture: {json.dumps(architecture.get('overview', {}), indent=2)}

Include:
- Project description
- Features list
- Tech stack
- Installation instructions (backend + frontend)
- Environment variables
- Running the app
- API documentation
- Project structure"""

        response = await self.llm_client.ainvoke([HumanMessage(content=prompt)])
        return response.content
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from LLM response (remove markdown code blocks)"""
        # Try to extract code from markdown code blocks
        code_pattern = r'```(?:python|javascript|jsx|js|typescript|tsx)?\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            # Return the first code block found
            return matches[0].strip()
        
        # If no code blocks, return the entire response
        return response.strip()
    
    async def _save_files_to_disk(
        self,
        project_name: str,
        all_files: Dict,
        task_id: Optional[str] = None
    ) -> int:
        """Save all generated files to disk"""
        saved_count = 0
        
        for category, files in all_files.items():
            for file_path, content in files.items():
                if self.file_service.write_file(project_name, file_path, content):
                    saved_count += 1
        
        if task_id:
            await self._log(task_id, f"💾 Saved {saved_count} files to disk")
        
        return saved_count
    
    async def _save_to_database(
        self,
        project_name: str,
        architecture: Dict,
        files: Dict,
        metadata: Dict
    ):
        """Save project data to database"""
        project_doc = {
            "project_name": project_name,
            "architecture": architecture,
            "files": files,
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.generated_projects.insert_one(project_doc)
        logger.info(f"Saved project {project_name} to database")

    async def _log(self, task_id: str, message: str):
        """Log agent activity"""
        log_doc = {
            "task_id": task_id,
            "agent_name": self.agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)


def get_coder_agent(llm_client, db, manager, file_service) -> CoderAgent:
    """Get CoderAgent instance"""
    return CoderAgent(llm_client, db, manager, file_service)

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
