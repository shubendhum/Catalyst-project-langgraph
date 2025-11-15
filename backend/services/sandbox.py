"""
Sandboxed Code Execution Service

Provides isolated code execution in ephemeral Docker containers.
Used by Coder and Tester agents to run generated code safely.
"""
import asyncio
import docker
import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SandboxExecutionError(Exception):
    """Raised when sandbox execution fails"""
    pass


class SandboxService:
    """
    Manages sandboxed code execution in Docker containers
    
    Features:
    - Ephemeral containers (created and destroyed per execution)
    - Isolated workspace with temporary file mounting
    - Resource limits (memory, CPU)
    - Timeout protection
    - Output capture (stdout, stderr, exit_code)
    - Automatic cleanup
    """
    
    def __init__(
        self,
        image_name: str = "catalyst-sandbox-runner:latest",
        default_timeout: int = 300,
        memory_limit: str = "512m",
        cpu_quota: int = 50000,  # 0.5 CPU (50000/100000)
        network_mode: str = "catalyst-network"
    ):
        """
        Initialize Sandbox Service
        
        Args:
            image_name: Docker image to use for sandbox containers
            default_timeout: Default execution timeout in seconds
            memory_limit: Memory limit (e.g., "512m", "1g")
            cpu_quota: CPU quota (50000 = 0.5 CPU)
            network_mode: Docker network mode
        """
        self.image_name = image_name
        self.default_timeout = default_timeout
        self.memory_limit = memory_limit
        self.cpu_quota = cpu_quota
        self.network_mode = network_mode
        
        try:
            self.docker_client = docker.from_env()
            logger.info(f"✅ Sandbox service initialized with image: {image_name}")
            
            # Check if image exists
            try:
                self.docker_client.images.get(image_name)
                logger.info(f"✅ Sandbox image '{image_name}' found")
            except docker.errors.ImageNotFound:
                logger.warning(f"⚠️ Sandbox image '{image_name}' not found - will be built on first docker-compose up")
        
        except Exception as e:
            logger.error(f"❌ Failed to initialize Docker client: {e}")
            raise SandboxExecutionError(f"Docker initialization failed: {e}")
    
    async def run_command(
        self,
        command: str,
        files: Optional[Dict[str, str]] = None,
        working_dir: str = "/workspace",
        timeout: Optional[int] = None,
        env_vars: Optional[Dict[str, str]] = None,
        requirements: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute a command in an isolated sandbox container
        
        Args:
            command: Shell command to execute (e.g., "pytest -v", "python test.py")
            files: Dictionary of files to create in workspace {filename: content}
            working_dir: Working directory inside container
            timeout: Execution timeout in seconds (None = use default)
            env_vars: Environment variables to set
            requirements: Python packages to install before execution
        
        Returns:
            Dictionary with execution results:
            {
                "success": bool,
                "stdout": str,
                "stderr": str,
                "exit_code": int,
                "duration": float,
                "container_id": str,
                "error": str (if failed)
            }
        
        Raises:
            SandboxExecutionError: If execution fails critically
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()
        container = None
        temp_dir = None
        
        try:
            # Create temporary workspace directory
            temp_dir = tempfile.mkdtemp(prefix="sandbox_")
            workspace_path = Path(temp_dir)
            
            logger.info(f"📁 Created temporary workspace: {temp_dir}")
            
            # Write files to workspace
            if files:
                for filename, content in files.items():
                    file_path = workspace_path / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.write_text(content)
                    logger.debug(f"  ✍️ Wrote file: {filename}")
            
            # Prepare environment variables
            container_env = env_vars or {}
            
            # Build setup commands
            setup_commands = []
            
            # Install Python requirements if specified
            if requirements:
                req_file = workspace_path / "requirements.txt"
                req_file.write_text("\n".join(requirements))
                setup_commands.append("pip install --no-cache-dir -r requirements.txt")
            
            # Combine setup and main command
            if setup_commands:
                full_command = f"cd {working_dir} && " + " && ".join(setup_commands) + f" && {command}"
            else:
                full_command = f"cd {working_dir} && {command}"
            
            logger.info("🚀 Starting sandbox container...")
            logger.info(f"   Command: {command}")
            logger.info(f"   Timeout: {timeout}s")
            logger.info(f"   Memory: {self.memory_limit}")
            logger.info(f"   CPU: {self.cpu_quota/100000} cores")
            
            # Create and start container
            container = self.docker_client.containers.run(
                image=self.image_name,
                command=["/bin/bash", "-c", full_command],
                volumes={
                    temp_dir: {
                        "bind": working_dir,
                        "mode": "rw"
                    }
                },
                working_dir=working_dir,
                environment=container_env,
                network=self.network_mode,
                mem_limit=self.memory_limit,
                cpu_quota=self.cpu_quota,
                detach=True,
                remove=False,  # We'll remove manually after capturing logs
                stdout=True,
                stderr=True
            )
            
            logger.info(f"✅ Container started: {container.short_id}")
            
            # Wait for container to complete with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get("StatusCode", -1)
            except Exception:
                logger.error(f"⏱️ Container execution timeout after {timeout}s")
                container.kill()
                raise SandboxExecutionError(f"Execution timeout after {timeout}s")
            
            # Capture output
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
            
            duration = time.time() - start_time
            
            success = exit_code == 0
            
            result = {
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
                "duration": duration,
                "container_id": container.short_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if not success:
                result["error"] = f"Command exited with code {exit_code}"
                logger.warning(f"⚠️ Sandbox execution failed with exit code {exit_code}")
            else:
                logger.info(f"✅ Sandbox execution completed successfully in {duration:.2f}s")
            
            return result
        
        except docker.errors.ImageNotFound:
            error_msg = f"Sandbox image '{self.image_name}' not found. Run 'docker-compose build sandbox-runner' first."
            logger.error(f"❌ {error_msg}")
            raise SandboxExecutionError(error_msg)
        
        except docker.errors.ContainerError as e:
            error_msg = f"Container error: {e}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": e.exit_status,
                "duration": time.time() - start_time,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            error_msg = f"Sandbox execution failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "duration": time.time() - start_time,
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        finally:
            # Cleanup: Remove container
            if container:
                try:
                    container.remove(force=True)
                    logger.debug(f"🗑️ Removed container: {container.short_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to remove container: {e}")
            
            # Cleanup: Remove temporary directory
            if temp_dir:
                try:
                    import shutil
                    shutil.rmtree(temp_dir)
                    logger.debug(f"🗑️ Removed workspace: {temp_dir}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to remove workspace: {e}")
    
    async def run_python_tests(
        self,
        test_files: Dict[str, str],
        source_files: Optional[Dict[str, str]] = None,
        requirements: Optional[List[str]] = None,
        pytest_args: str = "-v --tb=short"
    ) -> Dict[str, Any]:
        """
        Run Python tests using pytest in sandbox
        
        Args:
            test_files: Dictionary of test files {filename: content}
            source_files: Dictionary of source files to test
            requirements: Python packages to install
            pytest_args: pytest command line arguments
        
        Returns:
            Test execution results
        """
        # Combine test and source files
        all_files = {}
        if source_files:
            all_files.update(source_files)
        all_files.update(test_files)
        
        command = f"pytest {pytest_args}"
        
        return await self.run_command(
            command=command,
            files=all_files,
            requirements=requirements
        )
    
    async def run_javascript_tests(
        self,
        test_files: Dict[str, str],
        source_files: Optional[Dict[str, str]] = None,
        package_json: Optional[str] = None,
        test_command: str = "npm test"
    ) -> Dict[str, Any]:
        """
        Run JavaScript tests using npm/jest in sandbox
        
        Args:
            test_files: Dictionary of test files
            source_files: Dictionary of source files
            package_json: package.json content
            test_command: Test command to run
        
        Returns:
            Test execution results
        """
        all_files = {}
        if source_files:
            all_files.update(source_files)
        all_files.update(test_files)
        
        if package_json:
            all_files["package.json"] = package_json
        
        # Install dependencies and run tests
        command = f"npm install --silent && {test_command}"
        
        return await self.run_command(
            command=command,
            files=all_files
        )
    
    async def run_linter(
        self,
        files: Dict[str, str],
        linter: str = "flake8",
        linter_args: str = ""
    ) -> Dict[str, Any]:
        """
        Run linter on code files in sandbox
        
        Args:
            files: Dictionary of files to lint
            linter: Linter to use (flake8, pylint, eslint, etc.)
            linter_args: Additional linter arguments
        
        Returns:
            Linter execution results
        """
        command = f"{linter} {linter_args} ."
        
        return await self.run_command(
            command=command,
            files=files
        )
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get sandbox service status
        
        Returns:
            Status information
        """
        try:
            # Check Docker connectivity
            self.docker_client.ping()
            
            # Check if image exists
            try:
                image = self.docker_client.images.get(self.image_name)
                image_status = "ready"
                image_size = image.attrs.get("Size", 0) / (1024 * 1024)  # MB
            except docker.errors.ImageNotFound:
                image_status = "not_built"
                image_size = 0
            
            return {
                "status": "healthy",
                "docker_connected": True,
                "image_name": self.image_name,
                "image_status": image_status,
                "image_size_mb": round(image_size, 2),
                "default_timeout": self.default_timeout,
                "memory_limit": self.memory_limit,
                "cpu_quota": self.cpu_quota,
                "network_mode": self.network_mode
            }
        
        except Exception as e:
            return {
                "status": "unhealthy",
                "docker_connected": False,
                "error": str(e)
            }


# Global sandbox service instance
_sandbox_service: Optional[SandboxService] = None


def get_sandbox_service() -> SandboxService:
    """
    Get or create global sandbox service instance
    
    Returns:
        SandboxService instance
    """
    global _sandbox_service
    
    if _sandbox_service is None:
        _sandbox_service = SandboxService()
    
    return _sandbox_service


# Convenience functions for direct usage
async def run_sandboxed_command(command: str, **kwargs) -> Dict[str, Any]:
    """Run command in sandbox (convenience function)"""
    service = get_sandbox_service()
    return await service.run_command(command, **kwargs)


async def run_sandboxed_tests(test_files: Dict[str, str], **kwargs) -> Dict[str, Any]:
    """Run Python tests in sandbox (convenience function)"""
    service = get_sandbox_service()
    return await service.run_python_tests(test_files, **kwargs)
