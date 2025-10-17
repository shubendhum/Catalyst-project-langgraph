"""
Tester Agent
Validates generated code with unit tests, integration tests, and API testing
"""
import logging
import subprocess
import os
from typing import Dict, List, Optional
from datetime import datetime, timezone
from langchain_core.messages import HumanMessage
import json

logger = logging.getLogger(__name__)


class TesterAgent:
    """
    Agent responsible for testing generated code
    """
    
    def __init__(self, llm_client, db, manager, file_service):
        self.llm_client = llm_client
        self.db = db
        self.manager = manager
        self.file_service = file_service
        self.agent_name = "Tester"
    
    async def test_application(
        self,
        project_name: str,
        architecture: Dict,
        code_files: Dict,
        task_id: Optional[str] = None
    ) -> Dict:
        """
        Test the generated application
        
        Args:
            project_name: Name of the project
            architecture: Technical architecture
            code_files: Generated code files
            task_id: Task ID for logging
            
        Returns:
            Dictionary with test results and status
        """
        logger.info(f"Testing application: {project_name}")
        
        if task_id:
            await self._log(task_id, "🧪 Starting comprehensive testing...")
        
        test_results = {
            "backend_tests": {},
            "frontend_tests": {},
            "integration_tests": {},
            "api_tests": {},
            "overall_status": "pending"
        }
        
        try:
            # Generate test files
            if task_id:
                await self._log(task_id, "📝 Generating test files...")
            
            test_files = await self._generate_test_files(architecture, project_name)
            
            # Save test files
            await self._save_test_files(project_name, test_files)
            
            # Run backend tests
            if task_id:
                await self._log(task_id, "🐍 Running backend tests (pytest)...")
            
            backend_result = await self._run_backend_tests(project_name)
            test_results["backend_tests"] = backend_result
            
            # Run frontend tests
            if task_id:
                await self._log(task_id, "⚛️  Running frontend tests (Jest)...")
            
            frontend_result = await self._run_frontend_tests(project_name)
            test_results["frontend_tests"] = frontend_result
            
            # Run API tests
            if task_id:
                await self._log(task_id, "🌐 Running API endpoint tests...")
            
            api_result = await self._run_api_tests(project_name, architecture)
            test_results["api_tests"] = api_result
            
            # Calculate overall status
            all_passed = (
                backend_result.get("status") == "passed" and
                frontend_result.get("status") == "passed" and
                api_result.get("status") == "passed"
            )
            
            test_results["overall_status"] = "passed" if all_passed else "failed"
            test_results["timestamp"] = datetime.now(timezone.utc).isoformat()
            
            if task_id:
                if all_passed:
                    await self._log(task_id, "✅ All tests passed!")
                else:
                    await self._log(task_id, "⚠️  Some tests failed. Review needed.")
            
            return test_results
            
        except Exception as e:
            logger.error(f"Error during testing: {str(e)}")
            test_results["overall_status"] = "error"
            test_results["error"] = str(e)
            
            if task_id:
                await self._log(task_id, f"❌ Testing error: {str(e)}")
            
            return test_results
    
    async def _generate_test_files(self, architecture: Dict, project_name: str) -> Dict:
        """Generate test files using LLM"""
        
        test_files = {}
        
        # Generate backend test files
        backend_tests = await self._generate_backend_tests(architecture)
        test_files["backend/tests/test_api.py"] = backend_tests["api"]
        test_files["backend/tests/test_models.py"] = backend_tests["models"]
        test_files["backend/tests/__init__.py"] = ""
        test_files["backend/pytest.ini"] = self._generate_pytest_config()
        
        # Generate frontend test files
        frontend_tests = await self._generate_frontend_tests(architecture)
        test_files["frontend/src/tests/App.test.js"] = frontend_tests["app"]
        test_files["frontend/src/tests/components.test.js"] = frontend_tests["components"]
        
        return test_files
    
    async def _generate_backend_tests(self, architecture: Dict) -> Dict:
        """Generate backend test files"""
        
        api_specs = architecture.get("api_specs", [])
        models = architecture.get("data_models", [])
        
        # Generate API tests
        api_test_prompt = f"""Generate comprehensive pytest test file for FastAPI application.

API Endpoints to test:
{json.dumps(api_specs, indent=2)}

Include:
- Test fixtures for database setup
- Test authentication endpoints
- Test CRUD operations
- Test error handling (400, 401, 404, 500)
- Use pytest fixtures
- Use httpx.AsyncClient for async testing
- Mock database operations
- Assert status codes and response structure

Generate complete test file with all imports."""

        api_response = await self.llm_client.ainvoke([HumanMessage(content=api_test_prompt)])
        api_tests = self._extract_code_from_response(api_response.content)
        
        # Generate model tests
        model_test_prompt = f"""Generate pytest test file for Pydantic models.

Models to test:
{json.dumps(models, indent=2)}

Include:
- Test model validation
- Test field constraints
- Test relationships
- Test serialization/deserialization
- Test edge cases

Generate complete test file."""

        model_response = await self.llm_client.ainvoke([HumanMessage(content=model_test_prompt)])
        model_tests = self._extract_code_from_response(model_response.content)
        
        return {
            "api": api_tests,
            "models": model_tests
        }
    
    async def _generate_frontend_tests(self, architecture: Dict) -> Dict:
        """Generate frontend test files"""
        
        pages = architecture.get("frontend", {}).get("pages", [])
        components = architecture.get("frontend", {}).get("components", [])
        
        # Generate App tests
        app_test_prompt = f"""Generate Jest + React Testing Library test file for App.js

Pages: {json.dumps(pages, indent=2)}

Include:
- Test routing
- Test navigation
- Test authentication flow
- Test protected routes
- Use @testing-library/react
- Mock API calls

Generate complete test file."""

        app_response = await self.llm_client.ainvoke([HumanMessage(content=app_test_prompt)])
        app_tests = self._extract_code_from_response(app_response.content)
        
        # Generate component tests
        comp_test_prompt = f"""Generate Jest test file for React components.

Components: {json.dumps(components[:5], indent=2)}

Include:
- Test rendering
- Test user interactions
- Test props
- Test state changes
- Mock API calls

Generate complete test file."""

        comp_response = await self.llm_client.ainvoke([HumanMessage(content=comp_test_prompt)])
        comp_tests = self._extract_code_from_response(comp_response.content)
        
        return {
            "app": app_tests,
            "components": comp_tests
        }
    
    def _generate_pytest_config(self) -> str:
        """Generate pytest.ini configuration"""
        return """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
"""
    
    async def _save_test_files(self, project_name: str, test_files: Dict):
        """Save test files to disk"""
        for file_path, content in test_files.items():
            self.file_service.write_file(project_name, file_path, content)
    
    async def _run_backend_tests(self, project_name: str) -> Dict:
        """Run backend tests using pytest"""
        
        project_path = self.file_service.base_projects_dir / project_name / "backend"
        
        if not (project_path / "tests").exists():
            return {
                "status": "skipped",
                "message": "No test directory found"
            }
        
        try:
            # Run pytest
            result = subprocess.run(
                ["pytest", "-v", "--tb=short"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "errors": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "message": "Tests exceeded 60 second timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _run_frontend_tests(self, project_name: str) -> Dict:
        """Run frontend tests using Jest"""
        
        project_path = self.file_service.base_projects_dir / project_name / "frontend"
        
        if not (project_path / "src" / "tests").exists():
            return {
                "status": "skipped",
                "message": "No test directory found"
            }
        
        try:
            # Run npm test
            result = subprocess.run(
                ["npm", "test", "--", "--watchAll=false"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "errors": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "message": "Tests exceeded 120 second timeout"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    async def _run_api_tests(self, project_name: str, architecture: Dict) -> Dict:
        """Generate and run API endpoint tests"""
        
        api_specs = architecture.get("api_specs", [])
        
        if not api_specs:
            return {
                "status": "skipped",
                "message": "No API endpoints to test"
            }
        
        # Generate API test script
        test_prompt = f"""Generate a Python script using httpx to test these API endpoints:

{json.dumps(api_specs, indent=2)}

Include:
- Test each endpoint with valid data
- Test error cases
- Print test results
- Return JSON summary

Script should be standalone and executable."""

        response = await self.llm_client.ainvoke([HumanMessage(content=test_prompt)])
        test_script = self._extract_code_from_response(response.content)
        
        # Save and run test script
        test_file_path = f"{project_name}/api_test_script.py"
        self.file_service.write_file(project_name, test_file_path, test_script)
        
        try:
            result = subprocess.run(
                ["python", "api_test_script.py"],
                cwd=str(self.file_service.base_projects_dir / project_name),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "status": "passed" if result.returncode == 0 else "failed",
                "output": result.stdout,
                "errors": result.stderr,
                "exit_code": result.returncode
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code from LLM response"""
        import re
        code_pattern = r'```(?:python|javascript|jsx|js)?\n(.*?)\n```'
        matches = re.findall(code_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        return response.strip()
    
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


def get_tester_agent(llm_client, db, manager, file_service) -> TesterAgent:
    """Get TesterAgent instance"""
    return TesterAgent(llm_client, db, manager, file_service)
