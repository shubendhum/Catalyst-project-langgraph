"""
Git Service V2
Advanced Git repository management with local + remote support
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime

from config.environment import should_use_git, get_config

logger = logging.getLogger(__name__)


class GitService:
    """
    Manages local Git repositories and operations
    Falls back to file system only in K8s mode
    """
    
    def __init__(self):
        self.enabled = should_use_git()
        
        if self.enabled:
            self.config = get_config()["git"]
            self.repos_path = Path(self.config["local_path"])
            self.repos_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ GitService initialized: {self.repos_path}")
        else:
            logger.info("✅ GitService initialized (disabled for K8s)")
    
    def init_repo(self, project_name: str) -> Path:
        """
        Initialize a Git repository for a project
        
        Args:
            project_name: Name of the project
            
        Returns:
            Path to repository
        """
        if not self.enabled:
            return Path(f"/app/generated_projects/{project_name}")
        
        repo_path = self.repos_path / project_name
        repo_path.mkdir(parents=True, exist_ok=True)
        
        git_dir = repo_path / ".git"
        
        if not git_dir.exists():
            # Initialize Git repo
            subprocess.run(
                ["git", "init"],
                cwd=repo_path,
                capture_output=True,
                check=True
            )
            
            # Configure Git
            subprocess.run(
                ["git", "config", "user.name", "Catalyst AI"],
                cwd=repo_path,
                check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "ai@catalyst.dev"],
                cwd=repo_path,
                check=True
            )
            
            # Create initial commit
            gitignore_content = """# Catalyst Generated Project
__pycache__/
*.pyc
.env
.env.local
node_modules/
build/
dist/
.DS_Store
*.log
"""
            (repo_path / ".gitignore").write_text(gitignore_content)
            
            subprocess.run(
                ["git", "add", ".gitignore"],
                cwd=repo_path,
                check=True
            )
            subprocess.run(
                ["git", "commit", "-m", "chore: Initialize repository\n\n[catalyst-ai]"],
                cwd=repo_path,
                check=True
            )
            
            logger.info(f"✅ Initialized Git repo: {repo_path}")
        
        return repo_path
    
    def create_branch(self, project_name: str, branch_name: str) -> bool:
        """
        Create a new branch
        
        Args:
            project_name: Project name
            branch_name: Name of branch to create
            
        Returns:
            bool: Success status
        """
        if not self.enabled:
            return False
        
        try:
            repo_path = self.repos_path / project_name
            
            # Create and checkout branch
            result = subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Created branch: {branch_name}")
                return True
            else:
                # Branch might already exist, try to checkout
                result = subprocess.run(
                    ["git", "checkout", branch_name],
                    cwd=repo_path,
                    capture_output=True
                )
                return result.returncode == 0
                
        except Exception as e:
            logger.error(f"Failed to create branch: {e}")
            return False
    
    def commit(
        self,
        project_name: str,
        message: str,
        files: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Commit changes to repository
        
        Args:
            project_name: Project name
            message: Commit message
            files: Specific files to commit (None = all changes)
            
        Returns:
            Commit SHA or None if failed
        """
        if not self.enabled:
            return None
        
        try:
            repo_path = self.repos_path / project_name
            
            # Add files
            if files:
                for file_path in files:
                    subprocess.run(
                        ["git", "add", file_path],
                        cwd=repo_path,
                        check=True
                    )
            else:
                subprocess.run(
                    ["git", "add", "."],
                    cwd=repo_path,
                    check=True
                )
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                if "nothing to commit" in result.stdout:
                    logger.info("No changes to commit")
                    return self.get_current_commit(project_name)
                else:
                    logger.error(f"Git commit failed: {result.stderr}")
                    return None
            
            # Get commit SHA
            commit_sha = self.get_current_commit(project_name)
            logger.info(f"✅ Committed: {commit_sha[:7]} - {message[:50]}")
            
            return commit_sha
            
        except Exception as e:
            logger.error(f"Failed to commit: {e}")
            return None
    
    def get_current_commit(self, project_name: str) -> Optional[str]:
        """Get current commit SHA"""
        if not self.enabled:
            return None
        
        try:
            repo_path = self.repos_path / project_name
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Failed to get commit SHA: {e}")
            return None
    
    def get_diff_stats(self, project_name: str, from_ref: str = "HEAD~1", to_ref: str = "HEAD") -> Dict:
        """
        Get diff statistics between two refs
        
        Returns:
            Dict with additions, deletions, files_changed
        """
        if not self.enabled:
            return {"additions": 0, "deletions": 0, "files_changed": 0}
        
        try:
            repo_path = self.repos_path / project_name
            
            result = subprocess.run(
                ["git", "diff", "--shortstat", from_ref, to_ref],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            output = result.stdout.strip()
            
            # Parse: "5 files changed, 123 insertions(+), 45 deletions(-)"
            import re
            
            files_match = re.search(r'(\d+) files? changed', output)
            additions_match = re.search(r'(\d+) insertions?', output)
            deletions_match = re.search(r'(\d+) deletions?', output)
            
            return {
                "files_changed": int(files_match.group(1)) if files_match else 0,
                "additions": int(additions_match.group(1)) if additions_match else 0,
                "deletions": int(deletions_match.group(1)) if deletions_match else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get diff stats: {e}")
            return {"additions": 0, "deletions": 0, "files_changed": 0}
    
    def count_lines_of_code(self, project_name: str) -> int:
        """Count total lines of code in repository"""
        if not self.enabled:
            return 0
        
        try:
            repo_path = self.repos_path / project_name
            
            # Use cloc if available, otherwise simple count
            result = subprocess.run(
                ["find", ".", "-name", "*.py", "-o", "-name", "*.js", "-o", "-name", "*.jsx", 
                 "-o", "-name", "*.ts", "-o", "-name", "*.tsx", "|", "xargs", "wc", "-l"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                shell=True
            )
            
            # Parse last line for total
            lines = result.stdout.strip().split('\n')
            if lines:
                last_line = lines[-1].strip()
                if last_line:
                    return int(last_line.split()[0])
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to count LOC: {e}")
            return 0
    
    def get_commit_history(self, project_name: str, limit: int = 10) -> List[Dict]:
        """Get commit history"""
        if not self.enabled:
            return []
        
        try:
            repo_path = self.repos_path / project_name
            
            result = subprocess.run(
                ["git", "log", f"--max-count={limit}", "--format=%H|%an|%ae|%at|%s"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            
            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 4)
                if len(parts) == 5:
                    commits.append({
                        "sha": parts[0],
                        "author_name": parts[1],
                        "author_email": parts[2],
                        "timestamp": datetime.fromtimestamp(int(parts[3])).isoformat(),
                        "message": parts[4]
                    })
            
            return commits
            
        except Exception as e:
            logger.error(f"Failed to get commit history: {e}")
            return []


# Singleton instance
_git_service = None


def get_git_service() -> GitService:
    """Get or create GitService singleton"""
    global _git_service
    if _git_service is None:
        _git_service = GitService()
    return _git_service
