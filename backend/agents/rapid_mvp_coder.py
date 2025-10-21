"""
Rapid MVP Coder Agent
Focused on building MVPs extremely quickly with max value features first
"""
from typing import Dict, List, Optional
import logging
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class RapidMVPCoderAgent:
    """
    Rapid MVP Coder Agent
    Builds functional MVPs quickly, focusing on core value and beautiful UI
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
        Generate MVP code focusing on max value features
        """
        
        logger.info(f"🚀 Rapid MVP generation for: {project_name}")
        
        if task_id:
            await self._log(task_id, "💻 Coder: Identifying max value feature...")
            await self._log(task_id, "🎯 Planning core user flow...")
        
        # Extract requirements
        user_requirements = architecture.get('metadata', {}).get('user_requirements', '')
        features = architecture.get('features', [])
        data_models = architecture.get('data_models', [])
        
        # Build rapid MVP prompt
        prompt = f"""You are a full-stack developer focused on building MVPs extremely quickly.

<Plan>
PROJECT: {project_name}
USER WANTS: {user_requirements}

MAX VALUE FEATURE: {features[0].get('name') if features and isinstance(features[0], dict) else 'Main functionality'}

RAPID BUILD STRATEGY:
1. Identify THE ONE feature that creates the "aha moment"
2. Build beautiful, functional UI for that feature
3. Minimal backend (FastAPI + MongoDB)
4. Skip: auth, validation, error handling details
5. Focus: Visual appeal + core functionality working

DATA: {[m if isinstance(m, str) else m.get('name') for m in data_models[:2]]}
</Plan>

Generate a complete working MVP with THREE files:

FILE 1: /app/backend/server.py
- FastAPI backend
- MongoDB connection (keep existing MONGO_URL setup)
- 3-5 essential API endpoints for max value feature
- Basic CRUD only
- CORS enabled
- Keep this structure intact:
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from motor.motor_asyncio import AsyncIOMotorClient
  import os
  
  mongo_url = os.environ['MONGO_URL']
  client = AsyncIOMotorClient(mongo_url)
  db = client[os.environ.get('DB_NAME', 'catalyst_db')]
  
  app = FastAPI()
  
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

FILE 2: /app/frontend/src/App.js
- React 19 functional component
- Beautiful UI with advanced Tailwind (gradients, shadows, animations)
- Main feature working end-to-end
- Axios for API calls
- useState/useEffect hooks
- Modern, impressive design
- Mobile responsive
- Must end with: export default App;

FILE 3: /app/frontend/src/App.css
- Tailwind imports
- Custom animations
- Advanced styling
- Gradient backgrounds
- Modern aesthetics

CRITICAL: Generate COMPLETE, WORKING code. No placeholders. No TODOs. Everything functional.
Make the UI absolutely beautiful with modern design trends.
Focus on the max value feature working perfectly.

Generate the code now:"""
        
        return prompt
    
    async def _parse_and_generate_files(
        self,
        llm_response: str,
        project_name: str,
        task_id: Optional[str]
    ) -> Dict:
        """Parse LLM response and extract file contents"""
        import re
        
        files = {"backend": {}, "frontend": {}, "config": {}}
        
        # Extract code blocks
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', llm_response, re.DOTALL)
        
        for lang, code in code_blocks:
            code = code.strip()
            
            # Determine file type from context
            if 'server.py' in llm_response[:llm_response.find(code)] or 'FastAPI' in code[:200] or 'app = FastAPI()' in code:
                files["backend"]["server.py"] = code
                if task_id:
                    await self._log(task_id, "🐍 Generated server.py with essential endpoints")
            
            elif 'App.js' in llm_response[:llm_response.find(code)] or 'function App()' in code or 'const App =' in code:
                files["frontend"]["App.js"] = code
                if task_id:
                    await self._log(task_id, "⚛️ Generated App.js with beautiful UI")
            
            elif 'App.css' in llm_response[:llm_response.find(code)] or '@tailwind' in code or '@import' in code:
                files["frontend"]["App.css"] = code
                if task_id:
                    await self._log(task_id, "🎨 Generated App.css with advanced styling")
        
        # Write files to disk
        for category, file_dict in files.items():
            for filename, content in file_dict.items():
                if category == "backend":
                    self.file_service.write_file(project_name, filename, content)
                elif category == "frontend":
                    self.file_service.write_file(project_name, f"src/{filename}", content)
        
        return files
    
    async def _save_to_database(
        self,
        project_name: str,
        architecture: Dict,
        files: Dict,
        metadata: Dict
    ):
        """Save project to database"""
        project_doc = {
            "name": project_name,
            "architecture": architecture,
            "files": files,
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.generated_projects.insert_one(project_doc)
        logger.info(f"Saved MVP project {project_name} to database")
    
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


def get_rapid_mvp_coder(llm_client, db, manager, file_service) -> RapidMVPCoderAgent:
    """Get RapidMVPCoderAgent instance"""
    return RapidMVPCoderAgent(llm_client, db, manager, file_service)
