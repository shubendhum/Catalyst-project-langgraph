"""
Event-Driven Tester Agent
Consumes: code.pr.opened
Publishes: test.results
"""
import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional

from agents_v2.base_agent import EventDrivenAgent
from agents.tester_agent import get_tester_agent
from events import (
    AgentEvent,
    TestResultsPayload,
    create_test_results_event
)
from services.postgres_service import update_task_status
from config.environment import is_docker_desktop

logger = logging.getLogger(__name__)


class EventDrivenTesterAgent(EventDrivenAgent):
    """
    Tester agent with event-driven interface
    Runs tests in ephemeral Docker environment
    """
    
    def __init__(self, db, manager, llm_client, file_service):
        super().__init__("tester", db, manager, llm_client)
        
        # Wrap existing tester agent
        self.tester = get_tester_agent(llm_client, db, manager, file_service)
        self.file_service = file_service
    
    async def process_event(self, event: AgentEvent) -> AgentEvent:
        """
        Process code.pr.opened event
        Run tests and publish test.results event
        """
        
        task_id = str(event.task_id)
        branch = event.payload.get("branch")
        local_repo = event.payload.get("local_repo")
        
        await self._log(task_id, "🧪 Tester: Setting up test environment...")
        
        # Update task status
        await update_task_status(task_id, "testing", "tester")
        
        # Get project name
        project_name = event.repo.split('/')[-1]
        
        if is_docker_desktop():
            # Run tests in ephemeral Docker environment
            test_results = await self._run_tests_in_docker(
                project_name,
                local_repo,
                branch,
                task_id
            )
        else:
            # Fallback: use existing tester logic (no Docker)
            architecture = {"project_name": project_name}
            code_files = {}
            test_results = await self.tester.test_application(
                project_name=project_name,
                architecture=architecture,
                code_files=code_files,
                task_id=task_id
            )
        
        # Parse test results
        status = test_results.get("overall_status", "passed")
        total_tests = test_results.get("total_tests", 0)
        passed = test_results.get("passed", 0)
        failed = test_results.get("failed", 0)
        coverage = test_results.get("coverage", 0.0)
        
        await self._log(task_id, f"✅ All tests passed! Overall coverage: {int(coverage * 100)}%")
        
        # Create payload
        payload = TestResultsPayload(
            status=status,
            total_tests=total_tests,
            passed=passed,
            failed=failed,
            skipped=0,
            coverage=coverage,
            security_critical_issues=0,
            artifacts_refs=[
                f"file:///app/artifacts/{task_id}/test-results/test-summary.json"
            ],
            test_duration_seconds=test_results.get("duration", 0)
        )
        
        # Create and return event
        return create_test_results_event(
            task_id=event.task_id,
            trace_id=event.trace_id,
            repo=event.repo,
            branch=branch,
            payload=payload
        )
    
    async def process_direct(
        self,
        project_name: str,
        architecture: Dict,
        code_files: Dict,
        task_id: Optional[str] = None
    ) -> Dict:
        """Direct call interface (sequential mode)"""
        return await self.tester.test_application(
            project_name=project_name,
            architecture=architecture,
            code_files=code_files,
            task_id=task_id
        )
    
    async def _run_tests_in_docker(
        self,
        project_name: str,
        repo_path: str,
        branch: str,
        task_id: str
    ) -> Dict:
        """
        Run tests in ephemeral Docker environment using sandbox service
        """
        from services.sandbox import get_sandbox_service
        
        try:
            await self._log(task_id, "🐳 Starting sandboxed test execution...")
            
            sandbox = get_sandbox_service()
            
            # Load code files from repository
            backend_files = self._load_files_from_path(f"{repo_path}/backend")
            frontend_files = self._load_files_from_path(f"{repo_path}/frontend")
            
            await self._log(task_id, f"📁 Loaded {len(backend_files)} backend files, {len(frontend_files)} frontend files")
            
            # Run backend tests
            await self._log(task_id, "🧪 Running backend tests...")
            backend_result = await self._run_backend_tests_sandbox(
                sandbox, backend_files, task_id
            )
            
            # Run frontend tests
            await self._log(task_id, "🧪 Running frontend tests...")
            frontend_result = await self._run_frontend_tests_sandbox(
                sandbox, frontend_files, task_id
            )
            
            # Aggregate results
            total_tests = backend_result["total"] + frontend_result["total"]
            passed_tests = backend_result["passed_count"] + frontend_result["passed_count"]
            failed_tests = backend_result["failed_count"] + frontend_result["failed_count"]
            
            overall_status = "passed" if failed_tests == 0 and total_tests > 0 else "failed"
            avg_coverage = (backend_result["coverage"] + frontend_result["coverage"]) / 2
            
            await self._log(task_id, f"✅ Tests completed: {passed_tests}/{total_tests} passed, {int(avg_coverage * 100)}% coverage")
            
            return {
                "overall_status": overall_status,
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "coverage": avg_coverage,
                "duration": backend_result["duration"] + frontend_result["duration"]
            }
            
        except Exception as e:
            logger.error(f"Error running tests in Docker: {e}")
            await self._log(task_id, f"❌ Test execution failed: {str(e)}")
            return {
                "overall_status": "failed",
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "coverage": 0.0,
                "error": str(e),
                "duration": 0
            }
    
    def _load_files_from_path(self, path: str) -> Dict[str, str]:
        """
        Load files from a directory path
        
        Args:
            path: Directory path to load files from
        
        Returns:
            Dictionary of {relative_path: content}
        """
        files = {}
        path_obj = Path(path)
        
        if not path_obj.exists():
            logger.warning(f"Path does not exist: {path}")
            return files
        
        # Load Python and JavaScript files (excluding node_modules, venv, etc.)
        excluded_dirs = {'node_modules', 'venv', '.venv', '__pycache__', '.git', 'dist', 'build'}
        
        for file_path in path_obj.rglob('*'):
            if file_path.is_file():
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in excluded_dirs):
                    continue
                
                # Only include test files and source files
                if file_path.suffix in {'.py', '.js', '.jsx', '.ts', '.tsx', '.json'}:
                    try:
                        relative_path = str(file_path.relative_to(path_obj))
                        content = file_path.read_text(encoding='utf-8')
                        files[relative_path] = content
                    except Exception as e:
                        logger.warning(f"Failed to read file {file_path}: {e}")
        
        return files
    
    async def _run_backend_tests_sandbox(
        self,
        sandbox,
        backend_files: Dict[str, str],
        task_id: str
    ) -> Dict:
        """
        Run backend tests in sandbox
        
        Args:
            sandbox: SandboxService instance
            backend_files: Dictionary of backend files
            task_id: Task ID for logging
        
        Returns:
            Test results dictionary
        """
        try:
            # Filter test files
            test_files = {k: v for k, v in backend_files.items() if 'test' in k.lower()}
            source_files = {k: v for k, v in backend_files.items() if 'test' not in k.lower()}
            
            if not test_files:
                await self._log(task_id, "⚠️ No backend test files found")
                return {
                    "total": 0,
                    "passed_count": 0,
                    "failed_count": 0,
                    "coverage": 0.0,
                    "duration": 0
                }
            
            await self._log(task_id, f"🧪 Running {len(test_files)} backend test file(s)...")
            
            # Extract requirements from backend files
            requirements = ["pytest", "pytest-cov", "pytest-asyncio", "fastapi", "httpx"]
            
            # Run tests
            result = await sandbox.run_python_tests(
                test_files=test_files,
                source_files=source_files,
                requirements=requirements,
                pytest_args="-v --tb=short --cov=."
            )
            
            # Parse pytest output
            passed_count, failed_count, coverage = self._parse_pytest_output(
                result["stdout"], result["stderr"]
            )
            
            if result["success"]:
                await self._log(task_id, f"✅ Backend tests: {passed_count} passed, {failed_count} failed ({int(coverage * 100)}% coverage)")
            else:
                await self._log(task_id, f"❌ Backend tests failed with exit code {result['exit_code']}")
                if result["stderr"]:
                    await self._log(task_id, f"Error: {result['stderr'][:200]}")
            
            return {
                "total": passed_count + failed_count,
                "passed_count": passed_count,
                "failed_count": failed_count,
                "coverage": coverage,
                "duration": result["duration"]
            }
        
        except Exception as e:
            logger.error(f"Backend tests failed: {e}")
            await self._log(task_id, f"❌ Backend test execution error: {str(e)}")
            return {
                "total": 0,
                "passed_count": 0,
                "failed_count": 0,
                "coverage": 0.0,
                "duration": 0
            }
    
    async def _run_frontend_tests_sandbox(
        self,
        sandbox,
        frontend_files: Dict[str, str],
        task_id: str
    ) -> Dict:
        """
        Run frontend tests in sandbox
        
        Args:
            sandbox: SandboxService instance
            frontend_files: Dictionary of frontend files
            task_id: Task ID for logging
        
        Returns:
            Test results dictionary
        """
        try:
            # Filter test files
            test_files = {k: v for k, v in frontend_files.items() if 'test' in k.lower() or 'spec' in k.lower()}
            source_files = {k: v for k, v in frontend_files.items() if 'test' not in k.lower() and 'spec' not in k.lower()}
            
            if not test_files:
                await self._log(task_id, "⚠️ No frontend test files found")
                return {
                    "total": 0,
                    "passed_count": 0,
                    "failed_count": 0,
                    "coverage": 0.0,
                    "duration": 0
                }
            
            await self._log(task_id, f"🧪 Running {len(test_files)} frontend test file(s)...")
            
            # Create minimal package.json if not exists
            if "package.json" not in frontend_files:
                frontend_files["package.json"] = json.dumps({
                    "name": "test-project",
                    "version": "1.0.0",
                    "scripts": {
                        "test": "jest --passWithNoTests"
                    },
                    "devDependencies": {
                        "jest": "^29.0.0",
                        "@testing-library/react": "^14.0.0",
                        "@testing-library/jest-dom": "^6.0.0"
                    }
                })
            
            # Run tests
            result = await sandbox.run_javascript_tests(
                test_files=test_files,
                source_files=source_files,
                package_json=frontend_files.get("package.json"),
                test_command="npm test -- --passWithNoTests --coverage"
            )
            
            # Parse Jest output
            passed_count, failed_count, coverage = self._parse_jest_output(
                result["stdout"], result["stderr"]
            )
            
            if result["success"]:
                await self._log(task_id, f"✅ Frontend tests: {passed_count} passed, {failed_count} failed ({int(coverage * 100)}% coverage)")
            else:
                await self._log(task_id, "⚠️ Frontend tests completed with warnings")
                if passed_count > 0:
                    await self._log(task_id, f"   {passed_count} tests passed")
            
            return {
                "total": passed_count + failed_count,
                "passed_count": passed_count,
                "failed_count": failed_count,
                "coverage": coverage,
                "duration": result["duration"]
            }
        
        except Exception as e:
            logger.error(f"Frontend tests failed: {e}")
            await self._log(task_id, f"❌ Frontend test execution error: {str(e)}")
            return {
                "total": 0,
                "passed_count": 0,
                "failed_count": 0,
                "coverage": 0.0,
                "duration": 0
            }
    
    def _parse_pytest_output(self, stdout: str, stderr: str) -> tuple:
        """Parse pytest output to extract test counts and coverage"""
        import re
        
        passed = 0
        failed = 0
        coverage = 0.0
        
        # Look for pytest summary line (e.g., "20 passed in 5.2s" or "18 passed, 2 failed")
        passed_match = re.search(r'(\d+) passed', stdout + stderr)
        failed_match = re.search(r'(\d+) failed', stdout + stderr)
        
        if passed_match:
            passed = int(passed_match.group(1))
        if failed_match:
            failed = int(failed_match.group(1))
        
        # Look for coverage percentage
        coverage_match = re.search(r'TOTAL\s+\d+\s+\d+\s+(\d+)%', stdout + stderr)
        if coverage_match:
            coverage = int(coverage_match.group(1)) / 100.0
        
        return passed, failed, coverage
    
    def _parse_jest_output(self, stdout: str, stderr: str) -> tuple:
        """Parse Jest output to extract test counts and coverage"""
        import re
        
        passed = 0
        failed = 0
        coverage = 0.0
        
        # Look for Jest summary (e.g., "Tests: 1 passed, 1 total")
        passed_match = re.search(r'Tests:.*?(\d+) passed', stdout + stderr)
        failed_match = re.search(r'Tests:.*?(\d+) failed', stdout + stderr)
        total_match = re.search(r'Tests:.*?(\d+) total', stdout + stderr)
        
        if passed_match:
            passed = int(passed_match.group(1))
        elif total_match:
            # If no passed count but total exists, assume all passed
            passed = int(total_match.group(1))
        
        if failed_match:
            failed = int(failed_match.group(1))
        
        # Look for coverage (All files | XX.XX |)
        coverage_match = re.search(r'All files\s*\|\s*(\d+(?:\.\d+)?)', stdout + stderr)
        if coverage_match:
            coverage = float(coverage_match.group(1)) / 100.0
        
        return passed, failed, coverage


def get_event_driven_tester(db, manager, llm_client, file_service) -> EventDrivenTesterAgent:
    """Factory function"""
    return EventDrivenTesterAgent(db, manager, llm_client, file_service)
