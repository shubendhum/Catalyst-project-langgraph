"""
File System Service
Handles all file operations for code generation and project management
"""
import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class FileSystemService:
    """Service for managing project files and directories"""
    
    def __init__(self, base_projects_dir: str = "/app/generated_projects"):
        """
        Initialize FileSystemService
        
        Args:
            base_projects_dir: Base directory for all generated projects
        """
        self.base_projects_dir = Path(base_projects_dir)
        self.base_projects_dir.mkdir(parents=True, exist_ok=True)
    
    def create_project(self, project_name: str) -> str:
        """
        Create a new project directory structure
        
        Args:
            project_name: Name of the project
            
        Returns:
            Path to the project directory
        """
        project_path = self.base_projects_dir / project_name
        
        if project_path.exists():
            logger.warning(f"Project {project_name} already exists, using existing directory")
            return str(project_path)
        
        # Create main project structure
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for full-stack app
        (project_path / "backend").mkdir(exist_ok=True)
        (project_path / "frontend").mkdir(exist_ok=True)
        (project_path / "frontend" / "src").mkdir(exist_ok=True)
        (project_path / "frontend" / "public").mkdir(exist_ok=True)
        (project_path / "tests").mkdir(exist_ok=True)
        (project_path / "docs").mkdir(exist_ok=True)
        
        logger.info(f"Created project structure at {project_path}")
        return str(project_path)
    
    def write_file(self, project_name: str, file_path: str, content: str) -> bool:
        """
        Write content to a file in the project
        
        Args:
            project_name: Name of the project
            file_path: Relative path from project root (e.g., "backend/main.py")
            content: File content to write
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self.base_projects_dir / project_name / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Wrote file: {full_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {str(e)}")
            return False
    
    def read_file(self, project_name: str, file_path: str) -> Optional[str]:
        """
        Read content from a file in the project
        
        Args:
            project_name: Name of the project
            file_path: Relative path from project root
            
        Returns:
            File content if exists, None otherwise
        """
        try:
            full_path = self.base_projects_dir / project_name / file_path
            
            if not full_path.exists():
                logger.warning(f"File not found: {full_path}")
                return None
            
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return None
    
    def list_files(self, project_name: str, directory: str = "") -> List[str]:
        """
        List all files in a project directory
        
        Args:
            project_name: Name of the project
            directory: Subdirectory to list (empty for root)
            
        Returns:
            List of file paths relative to project root
        """
        try:
            project_path = self.base_projects_dir / project_name / directory
            
            if not project_path.exists():
                logger.warning(f"Directory not found: {project_path}")
                return []
            
            files = []
            for root, _, filenames in os.walk(project_path):
                for filename in filenames:
                    file_path = Path(root) / filename
                    relative_path = file_path.relative_to(self.base_projects_dir / project_name)
                    files.append(str(relative_path))
            
            return files
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {str(e)}")
            return []
    
    def delete_file(self, project_name: str, file_path: str) -> bool:
        """
        Delete a file from the project
        
        Args:
            project_name: Name of the project
            file_path: Relative path from project root
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self.base_projects_dir / project_name / file_path
            
            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted file: {full_path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {full_path}")
                return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
    
    def get_project_structure(self, project_name: str) -> Dict:
        """
        Get the entire project structure as a tree
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dictionary representing the project tree
        """
        project_path = self.base_projects_dir / project_name
        
        if not project_path.exists():
            return {"error": "Project not found"}
        
        def build_tree(path: Path) -> Dict:
            tree = {"name": path.name, "type": "directory", "children": []}
            
            try:
                for item in sorted(path.iterdir()):
                    if item.is_dir():
                        tree["children"].append(build_tree(item))
                    else:
                        tree["children"].append({
                            "name": item.name,
                            "type": "file",
                            "size": item.stat().st_size
                        })
            except PermissionError:
                tree["error"] = "Permission denied"
            
            return tree
        
        return build_tree(project_path)
    
    def save_metadata(self, project_name: str, metadata: Dict) -> bool:
        """
        Save project metadata
        
        Args:
            project_name: Name of the project
            metadata: Dictionary containing project metadata
            
        Returns:
            True if successful, False otherwise
        """
        metadata_path = self.base_projects_dir / project_name / "catalyst_metadata.json"
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Saved metadata for project {project_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
            return False
    
    def load_metadata(self, project_name: str) -> Optional[Dict]:
        """
        Load project metadata
        
        Args:
            project_name: Name of the project
            
        Returns:
            Metadata dictionary if exists, None otherwise
        """
        metadata_path = self.base_projects_dir / project_name / "catalyst_metadata.json"
        
        try:
            if not metadata_path.exists():
                return None
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return None
    
    def delete_project(self, project_name: str) -> bool:
        """
        Delete an entire project
        
        Args:
            project_name: Name of the project
            
        Returns:
            True if successful, False otherwise
        """
        project_path = self.base_projects_dir / project_name
        
        try:
            if project_path.exists():
                shutil.rmtree(project_path)
                logger.info(f"Deleted project: {project_name}")
                return True
            else:
                logger.warning(f"Project not found for deletion: {project_name}")
                return False
        except Exception as e:
            logger.error(f"Error deleting project {project_name}: {str(e)}")
            return False


# Singleton instance
_fs_service = None

def get_file_system_service() -> FileSystemService:
    """Get the singleton FileSystemService instance"""
    global _fs_service
    if _fs_service is None:
        _fs_service = FileSystemService()
    return _fs_service
