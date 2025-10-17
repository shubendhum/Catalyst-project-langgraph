"""
Planner Agent
Breaks down user requirements into actionable tasks for full-stack development
"""
from typing import Dict, List, Optional
import logging
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)


class PlannerAgent:
    """
    Agent responsible for analyzing requirements and creating development plans
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.agent_name = "Planner"
    
    async def create_plan(
        self, 
        user_requirements: str,
        project_name: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Create a development plan from user requirements
        
        Args:
            user_requirements: User's description of what they want to build
            project_name: Name for the project
            context: Additional context (existing code, constraints, etc.)
            
        Returns:
            Dictionary containing the plan with tasks, features, and architecture outline
        """
        logger.info(f"Creating plan for project: {project_name}")
        
        # Build the prompt for LLM
        planning_prompt = self._build_planning_prompt(
            user_requirements, 
            project_name, 
            context
        )
        
        try:
            # Get plan from LLM using ainvoke
            response = await self.llm_client.ainvoke(
                [HumanMessage(content=planning_prompt)]
            )
            
            llm_response = response.content
            
            # Parse LLM response into structured plan
            plan = self._parse_plan_response(llm_response, user_requirements)
            
            # Add metadata
            plan["metadata"] = {
                "project_name": project_name,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "agent": self.agent_name,
                "user_requirements": user_requirements
            }
            
            logger.info(f"Plan created successfully for {project_name}")
            return plan
            
        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            return self._create_fallback_plan(user_requirements, project_name)
    
    def _build_planning_prompt(
        self, 
        requirements: str, 
        project_name: str,
        context: Optional[Dict]
    ) -> str:
        """Build the prompt for LLM to generate a plan"""
        
        prompt = f"""You are an expert software architect and planner. Analyze the following requirements and create a detailed development plan for a full-stack application.

PROJECT NAME: {project_name}

USER REQUIREMENTS:
{requirements}

"""
        
        if context:
            prompt += f"\nADDITIONAL CONTEXT:\n{context}\n"
        
        prompt += """
Please create a comprehensive development plan that includes:

1. **PROJECT OVERVIEW**
   - Brief description of what the application does
   - Target users
   - Key value proposition

2. **FEATURES** (List 5-10 main features)
   - Feature name and description
   - Priority (High/Medium/Low)
   - Estimated complexity

3. **ARCHITECTURE**
   - Backend: API structure and endpoints needed
   - Frontend: Main pages/components needed
   - Database: Data models required
   - External integrations (if any)

4. **TECHNICAL STACK**
   - Backend: FastAPI + Python
   - Frontend: React + Tailwind CSS
   - Database: MongoDB
   - Other tools/libraries needed

5. **DEVELOPMENT TASKS** (Break into concrete tasks)
   - Backend tasks
   - Frontend tasks
   - Integration tasks
   - Testing tasks

6. **API ENDPOINTS** (List all REST endpoints)
   - Method, path, description, request/response

Format your response as structured JSON that can be parsed. Use this structure:
{
  "overview": {
    "description": "...",
    "target_users": "...",
    "value_proposition": "..."
  },
  "features": [
    {"name": "...", "description": "...", "priority": "High/Medium/Low", "complexity": "Simple/Medium/Complex"}
  ],
  "architecture": {
    "backend": {"description": "...", "key_components": ["..."]},
    "frontend": {"description": "...", "key_components": ["..."]},
    "database": {"models": ["..."]}
  },
  "tech_stack": {...},
  "tasks": {
    "backend": ["..."],
    "frontend": ["..."],
    "integration": ["..."],
    "testing": ["..."]
  },
  "api_endpoints": [
    {"method": "GET/POST/PUT/DELETE", "path": "/api/...", "description": "...", "request": {...}, "response": {...}}
  ]
}
"""
        return prompt
    
    def _parse_plan_response(self, llm_response: str, requirements: str) -> Dict:
        """Parse LLM response into structured plan"""
        import json
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                plan = json.loads(json_match.group())
                return plan
            else:
                # If no JSON found, create structured plan from text
                return self._create_structured_plan_from_text(llm_response, requirements)
        except json.JSONDecodeError:
            # Fallback to text-based plan
            return self._create_structured_plan_from_text(llm_response, requirements)
    
    def _create_structured_plan_from_text(self, text: str, requirements: str) -> Dict:
        """Create structured plan from unstructured text response"""
        
        # Basic structure extraction
        plan = {
            "overview": {
                "description": requirements,
                "target_users": "General users",
                "value_proposition": "Solve user needs efficiently"
            },
            "features": self._extract_features_from_text(text),
            "architecture": self._extract_architecture_from_text(text),
            "tech_stack": {
                "backend": "FastAPI + Python",
                "frontend": "React + Tailwind CSS",
                "database": "MongoDB",
                "additional": []
            },
            "tasks": self._extract_tasks_from_text(text),
            "api_endpoints": self._extract_endpoints_from_text(text)
        }
        
        return plan
    
    def _extract_features_from_text(self, text: str) -> List[Dict]:
        """Extract features from text"""
        # Simple extraction - look for feature keywords
        features = []
        lines = text.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['feature', 'capability', 'function']):
                features.append({
                    "name": line.strip('- *#123456789.'),
                    "description": line.strip('- *#123456789.'),
                    "priority": "Medium",
                    "complexity": "Medium"
                })
        
        # Default features if none found
        if not features:
            features = [
                {"name": "User Management", "description": "Handle user registration and authentication", "priority": "High", "complexity": "Medium"},
                {"name": "Core Functionality", "description": "Main business logic", "priority": "High", "complexity": "Complex"},
                {"name": "Data Management", "description": "CRUD operations for data", "priority": "High", "complexity": "Medium"}
            ]
        
        return features[:10]  # Limit to 10 features
    
    def _extract_architecture_from_text(self, text: str) -> Dict:
        """Extract architecture details from text"""
        return {
            "backend": {
                "description": "REST API built with FastAPI",
                "key_components": ["API Routes", "Business Logic", "Database Layer", "Authentication"]
            },
            "frontend": {
                "description": "React SPA with modern UI",
                "key_components": ["Pages", "Components", "State Management", "API Client"]
            },
            "database": {
                "models": ["User", "Data", "Settings"]
            }
        }
    
    def _extract_tasks_from_text(self, text: str) -> Dict:
        """Extract development tasks from text"""
        return {
            "backend": [
                "Setup FastAPI project structure",
                "Implement database models",
                "Create API endpoints",
                "Add authentication/authorization",
                "Implement business logic",
                "Add error handling and validation"
            ],
            "frontend": [
                "Setup React project with Vite/CRA",
                "Create routing structure",
                "Build UI components",
                "Implement state management",
                "Connect to backend API",
                "Add form validation"
            ],
            "integration": [
                "Connect frontend to backend",
                "Test end-to-end flows",
                "Handle CORS configuration"
            ],
            "testing": [
                "Write backend unit tests",
                "Write frontend component tests",
                "Perform integration testing"
            ]
        }
    
    def _extract_endpoints_from_text(self, text: str) -> List[Dict]:
        """Extract API endpoints from text"""
        return [
            {"method": "POST", "path": "/api/auth/register", "description": "Register new user", "request": {"email": "string", "password": "string"}, "response": {"id": "string", "token": "string"}},
            {"method": "POST", "path": "/api/auth/login", "description": "Login user", "request": {"email": "string", "password": "string"}, "response": {"token": "string", "user": "object"}},
            {"method": "GET", "path": "/api/data", "description": "Get all data items", "request": {}, "response": {"items": "array"}},
            {"method": "POST", "path": "/api/data", "description": "Create new data item", "request": {"data": "object"}, "response": {"id": "string", "data": "object"}},
            {"method": "GET", "path": "/api/data/{id}", "description": "Get data item by ID", "request": {}, "response": {"data": "object"}},
            {"method": "PUT", "path": "/api/data/{id}", "description": "Update data item", "request": {"data": "object"}, "response": {"data": "object"}},
            {"method": "DELETE", "path": "/api/data/{id}", "description": "Delete data item", "request": {}, "response": {"success": "boolean"}}
        ]
    
    def _create_fallback_plan(self, requirements: str, project_name: str) -> Dict:
        """Create a basic fallback plan if LLM fails"""
        logger.warning("Using fallback plan due to LLM error")
        
        return {
            "overview": {
                "description": requirements,
                "target_users": "General users",
                "value_proposition": "Efficient solution"
            },
            "features": [
                {"name": "User Authentication", "description": "Login/Register functionality", "priority": "High", "complexity": "Medium"},
                {"name": "Core Features", "description": "Main application features", "priority": "High", "complexity": "Complex"},
                {"name": "Data Management", "description": "CRUD operations", "priority": "High", "complexity": "Medium"}
            ],
            "architecture": {
                "backend": {
                    "description": "FastAPI REST API",
                    "key_components": ["API Routes", "Business Logic", "Database"]
                },
                "frontend": {
                    "description": "React SPA",
                    "key_components": ["Pages", "Components", "API Client"]
                },
                "database": {
                    "models": ["User", "Data"]
                }
            },
            "tech_stack": {
                "backend": "FastAPI + Python",
                "frontend": "React + Tailwind CSS",
                "database": "MongoDB"
            },
            "tasks": self._extract_tasks_from_text(""),
            "api_endpoints": self._extract_endpoints_from_text(""),
            "metadata": {
                "project_name": project_name,
                "created_at": datetime.utcnow().isoformat(),
                "agent": self.agent_name,
                "fallback": True
            }
        }


# Singleton instance
_planner_agent = None

def get_planner_agent() -> PlannerAgent:
    """Get the singleton PlannerAgent instance"""
    global _planner_agent
    if _planner_agent is None:
        _planner_agent = PlannerAgent()
    return _planner_agent
