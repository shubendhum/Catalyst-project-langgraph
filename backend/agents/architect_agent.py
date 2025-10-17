"""
Architect Agent
Designs the technical architecture and creates detailed specifications
"""
from typing import Dict, List, Optional
import logging
from datetime import datetime
from backend.llm_client import get_llm_client

logger = logging.getLogger(__name__)


class ArchitectAgent:
    """
    Agent responsible for creating detailed technical architecture
    """
    
    def __init__(self):
        self.llm_client = get_llm_client()
        self.agent_name = "Architect"
    
    async def design_architecture(
        self,
        plan: Dict,
        project_name: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Create detailed technical architecture from the plan
        
        Args:
            plan: Development plan from Planner Agent
            project_name: Name of the project
            context: Additional context
            
        Returns:
            Dictionary containing detailed architecture specifications
        """
        logger.info(f"Designing architecture for project: {project_name}")
        
        # Build architecture prompt
        arch_prompt = self._build_architecture_prompt(plan, project_name, context)
        
        try:
            # Get architecture from LLM
            llm_response = await self.llm_client.generate(
                prompt=arch_prompt,
                max_tokens=3000,
                temperature=0.5
            )
            
            # Parse response into structured architecture
            architecture = self._parse_architecture_response(llm_response, plan)
            
            # Add metadata
            architecture["metadata"] = {
                "project_name": project_name,
                "created_at": datetime.utcnow().isoformat(),
                "agent": self.agent_name,
                "based_on_plan": True
            }
            
            logger.info(f"Architecture designed successfully for {project_name}")
            return architecture
            
        except Exception as e:
            logger.error(f"Error designing architecture: {str(e)}")
            return self._create_fallback_architecture(plan, project_name)
    
    def _build_architecture_prompt(
        self,
        plan: Dict,
        project_name: str,
        context: Optional[Dict]
    ) -> str:
        """Build prompt for LLM to generate architecture"""
        
        prompt = f"""You are an expert software architect. Based on the following development plan, create a detailed technical architecture for a full-stack application.

PROJECT: {project_name}

DEVELOPMENT PLAN:
{self._format_plan_for_prompt(plan)}

"""
        
        if context:
            prompt += f"\nADDITIONAL CONTEXT:\n{context}\n"
        
        prompt += """
Please create a detailed technical architecture that includes:

1. **BACKEND ARCHITECTURE**
   - Project structure (directories and files)
   - API design (detailed endpoints with request/response schemas)
   - Database schema (models, fields, relationships)
   - Authentication/Authorization strategy
   - Error handling approach
   - Key business logic modules

2. **FRONTEND ARCHITECTURE**
   - Project structure (directories and files)
   - Component hierarchy
   - Pages and routing
   - State management approach
   - API integration strategy
   - UI/UX patterns

3. **DATA MODELS**
   - Define all database models
   - Field names, types, constraints
   - Relationships between models
   - Indexes for optimization

4. **API SPECIFICATIONS**
   - Detailed endpoint specifications
   - Request validation rules
   - Response formats
   - Error responses
   - Authentication requirements

5. **FILE STRUCTURE**
   - Complete file tree for backend
   - Complete file tree for frontend
   - Configuration files needed

6. **INTEGRATION POINTS**
   - How frontend calls backend
   - CORS configuration
   - Environment variables needed

Format response as JSON with this structure:
{
  "backend": {
    "structure": {...},
    "api_design": [...],
    "database_schema": [...],
    "auth_strategy": "...",
    "modules": [...]
  },
  "frontend": {
    "structure": {...},
    "components": [...],
    "pages": [...],
    "state_management": "...",
    "routing": [...]
  },
  "data_models": [...],
  "api_specs": [...],
  "file_structure": {
    "backend": {...},
    "frontend": {...}
  },
  "integration": {...}
}
"""
        return prompt
    
    def _format_plan_for_prompt(self, plan: Dict) -> str:
        """Format plan dict for LLM prompt"""
        import json
        return json.dumps(plan, indent=2)
    
    def _parse_architecture_response(self, llm_response: str, plan: Dict) -> Dict:
        """Parse LLM response into structured architecture"""
        import json
        import re
        
        try:
            # Try to extract JSON
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                arch = json.loads(json_match.group())
                return arch
            else:
                return self._create_default_architecture(plan)
        except json.JSONDecodeError:
            return self._create_default_architecture(plan)
    
    def _create_default_architecture(self, plan: Dict) -> Dict:
        """Create default architecture based on plan"""
        
        # Extract features and endpoints from plan
        features = plan.get('features', [])
        endpoints = plan.get('api_endpoints', [])
        
        return {
            "backend": {
                "structure": {
                    "main": "Main application entry point",
                    "api": "API routes and endpoints",
                    "models": "Database models",
                    "services": "Business logic services",
                    "middleware": "Authentication and validation",
                    "utils": "Utility functions"
                },
                "api_design": endpoints,
                "database_schema": self._generate_database_schema(features),
                "auth_strategy": "JWT tokens with bearer authentication",
                "modules": [
                    {"name": "auth", "description": "Authentication and authorization"},
                    {"name": "data", "description": "Core business logic"},
                    {"name": "utils", "description": "Helper functions"}
                ]
            },
            "frontend": {
                "structure": {
                    "components": "Reusable UI components",
                    "pages": "Application pages/views",
                    "services": "API client and services",
                    "hooks": "Custom React hooks",
                    "utils": "Utility functions",
                    "store": "State management"
                },
                "components": self._generate_components(features),
                "pages": self._generate_pages(features),
                "state_management": "React Context API or Zustand",
                "routing": self._generate_routes(features)
            },
            "data_models": self._generate_data_models(features),
            "api_specs": self._generate_api_specs(endpoints),
            "file_structure": self._generate_file_structure(),
            "integration": {
                "cors": "Configure CORS in FastAPI",
                "api_base_url": "http://localhost:8001/api",
                "authentication": "Bearer token in Authorization header",
                "error_handling": "Unified error response format"
            }
        }
    
    def _generate_database_schema(self, features: List[Dict]) -> List[Dict]:
        """Generate database schema from features"""
        schemas = [
            {
                "model": "User",
                "collection": "users",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True},
                    {"name": "email", "type": "string", "unique": True, "required": True},
                    {"name": "hashed_password", "type": "string", "required": True},
                    {"name": "is_active", "type": "boolean", "default": True},
                    {"name": "created_at", "type": "datetime", "auto_now_add": True}
                ]
            }
        ]
        
        # Add models based on features
        for feature in features[:3]:  # Limit to avoid too many models
            model_name = feature.get('name', 'Data').replace(' ', '')
            schemas.append({
                "model": model_name,
                "collection": model_name.lower() + "s",
                "fields": [
                    {"name": "id", "type": "uuid", "primary_key": True},
                    {"name": "user_id", "type": "uuid", "foreign_key": "User"},
                    {"name": "data", "type": "dict", "required": True},
                    {"name": "created_at", "type": "datetime", "auto_now_add": True},
                    {"name": "updated_at", "type": "datetime", "auto_now": True}
                ]
            })
        
        return schemas
    
    def _generate_components(self, features: List[Dict]) -> List[Dict]:
        """Generate React components from features"""
        components = [
            {"name": "Navbar", "type": "layout", "description": "Navigation bar"},
            {"name": "Sidebar", "type": "layout", "description": "Side menu"},
            {"name": "LoginForm", "type": "form", "description": "User login form"},
            {"name": "RegisterForm", "type": "form", "description": "User registration form"}
        ]
        
        for feature in features:
            feature_name = feature.get('name', 'Feature').replace(' ', '')
            components.append({
                "name": f"{feature_name}Card",
                "type": "display",
                "description": f"Card component for {feature.get('name')}"
            })
            components.append({
                "name": f"{feature_name}Form",
                "type": "form",
                "description": f"Form for creating/editing {feature.get('name')}"
            })
        
        return components[:15]  # Limit components
    
    def _generate_pages(self, features: List[Dict]) -> List[Dict]:
        """Generate pages from features"""
        pages = [
            {"name": "Home", "path": "/", "description": "Landing page"},
            {"name": "Login", "path": "/login", "description": "Login page"},
            {"name": "Register", "path": "/register", "description": "Registration page"},
            {"name": "Dashboard", "path": "/dashboard", "description": "Main dashboard"},
        ]
        
        for feature in features[:5]:
            feature_name = feature.get('name', 'Feature').replace(' ', '')
            pages.append({
                "name": feature_name,
                "path": f"/{feature_name.lower()}",
                "description": f"Page for {feature.get('name')}"
            })
        
        return pages
    
    def _generate_routes(self, features: List[Dict]) -> List[Dict]:
        """Generate routing structure"""
        routes = [
            {"path": "/", "component": "Home", "protected": False},
            {"path": "/login", "component": "Login", "protected": False},
            {"path": "/register", "component": "Register", "protected": False},
            {"path": "/dashboard", "component": "Dashboard", "protected": True}
        ]
        
        for feature in features[:5]:
            feature_name = feature.get('name', 'Feature').replace(' ', '')
            routes.append({
                "path": f"/{feature_name.lower()}",
                "component": feature_name,
                "protected": True
            })
        
        return routes
    
    def _generate_data_models(self, features: List[Dict]) -> List[Dict]:
        """Generate Pydantic models"""
        return self._generate_database_schema(features)
    
    def _generate_api_specs(self, endpoints: List[Dict]) -> List[Dict]:
        """Generate detailed API specifications"""
        specs = []
        
        for endpoint in endpoints:
            specs.append({
                "method": endpoint.get('method', 'GET'),
                "path": endpoint.get('path', '/api/endpoint'),
                "description": endpoint.get('description', ''),
                "request_body": endpoint.get('request', {}),
                "response_body": endpoint.get('response', {}),
                "status_codes": {
                    "200": "Success",
                    "400": "Bad Request",
                    "401": "Unauthorized",
                    "500": "Server Error"
                },
                "authentication": "Bearer token" if "auth" not in endpoint.get('path', '') else "None"
            })
        
        return specs
    
    def _generate_file_structure(self) -> Dict:
        """Generate complete file structure"""
        return {
            "backend": {
                "main.py": "FastAPI application entry point",
                "models/": {
                    "__init__.py": "Models package",
                    "user.py": "User model",
                    "data.py": "Data models"
                },
                "api/": {
                    "__init__.py": "API package",
                    "auth.py": "Authentication routes",
                    "data.py": "Data routes"
                },
                "services/": {
                    "__init__.py": "Services package",
                    "auth_service.py": "Authentication service",
                    "data_service.py": "Data service"
                },
                "middleware/": {
                    "__init__.py": "Middleware package",
                    "auth.py": "Auth middleware"
                },
                "requirements.txt": "Python dependencies"
            },
            "frontend": {
                "src/": {
                    "App.js": "Main App component",
                    "index.js": "Entry point",
                    "components/": {
                        "Navbar.js": "Navigation",
                        "forms/": {}
                    },
                    "pages/": {
                        "Home.js": "Home page",
                        "Login.js": "Login page",
                        "Dashboard.js": "Dashboard"
                    },
                    "services/": {
                        "api.js": "API client"
                    },
                    "hooks/": {},
                    "utils/": {}
                },
                "public/": {
                    "index.html": "HTML template"
                },
                "package.json": "npm dependencies"
            }
        }
    
    def _create_fallback_architecture(self, plan: Dict, project_name: str) -> Dict:
        """Create fallback architecture if LLM fails"""
        logger.warning("Using fallback architecture due to LLM error")
        
        arch = self._create_default_architecture(plan)
        arch["metadata"] = {
            "project_name": project_name,
            "created_at": datetime.utcnow().isoformat(),
            "agent": self.agent_name,
            "fallback": True
        }
        return arch


# Singleton instance
_architect_agent = None

def get_architect_agent() -> ArchitectAgent:
    """Get the singleton ArchitectAgent instance"""
    global _architect_agent
    if _architect_agent is None:
        _architect_agent = ArchitectAgent()
    return _architect_agent
