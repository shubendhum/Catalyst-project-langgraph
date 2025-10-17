"""
GitHub Integration Service
Handles GitHub operations: cloning, analyzing, pushing code, creating PRs
"""
import logging
import subprocess
import os
from typing import Dict, List, Optional
from pathlib import Path
import tempfile
import shutil
import requests

logger = logging.getLogger(__name__)


class GitHubService:
    """
    Service for GitHub operations
    """
    
    def __init__(self):
        self.github_api_base = "https://api.github.com"
    
    def clone_repository(
        self,
        repo_url: str,
        destination: str,
        token: Optional[str] = None,
        branch: Optional[str] = None
    ) -> Dict:
        """
        Clone a GitHub repository
        
        Args:
            repo_url: GitHub repository URL
            destination: Local destination path
            token: Optional GitHub token for private repos
            branch: Optional specific branch to clone
            
        Returns:
            Dictionary with clone result
        """
        logger.info(f"Cloning repository: {repo_url}")
        
        try:
            # Prepare clone URL with token if provided
            clone_url = self._prepare_clone_url(repo_url, token)
            
            # Prepare clone command
            cmd = ["git", "clone"]
            
            if branch:
                cmd.extend(["-b", branch])
            
            cmd.extend([clone_url, destination])
            
            # Execute clone
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "path": destination,
                    "message": "Repository cloned successfully"
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr,
                    "message": "Failed to clone repository"
                }
                
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "error": "Clone operation timed out after 5 minutes"
            }
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def push_to_github(
        self,
        local_path: str,
        repo_url: str,
        token: str,
        branch: str = "main",
        commit_message: str = "Update from Catalyst"
    ) -> Dict:
        """
        Push local code to GitHub repository
        
        Args:
            local_path: Path to local repository
            repo_url: GitHub repository URL
            token: GitHub token for authentication
            branch: Branch to push to
            commit_message: Commit message
            
        Returns:
            Dictionary with push result
        """
        logger.info(f"Pushing to GitHub: {repo_url}")
        
        try:
            # Configure git user
            subprocess.run(
                ["git", "config", "user.name", "Catalyst AI"],
                cwd=local_path,
                check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "catalyst@example.com"],
                cwd=local_path,
                check=True
            )
            
            # Add all files
            subprocess.run(
                ["git", "add", "."],
                cwd=local_path,
                check=True
            )
            
            # Commit
            result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=local_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0 and "nothing to commit" in result.stdout:
                return {
                    "status": "success",
                    "message": "No changes to commit"
                }
            
            # Set remote with token
            remote_url = self._prepare_clone_url(repo_url, token)
            subprocess.run(
                ["git", "remote", "set-url", "origin", remote_url],
                cwd=local_path,
                check=True
            )
            
            # Push
            result = subprocess.run(
                ["git", "push", "origin", branch],
                cwd=local_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "message": "Code pushed to GitHub successfully",
                    "branch": branch
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr,
                    "message": "Failed to push to GitHub"
                }
                
        except Exception as e:
            logger.error(f"Error pushing to GitHub: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def create_pull_request(
        self,
        repo_owner: str,
        repo_name: str,
        token: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> Dict:
        """
        Create a pull request on GitHub
        
        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
            token: GitHub token
            title: PR title
            body: PR description
            head_branch: Source branch
            base_branch: Target branch
            
        Returns:
            Dictionary with PR creation result
        """
        logger.info(f"Creating PR: {repo_owner}/{repo_name}")
        
        try:
            url = f"{self.github_api_base}/repos/{repo_owner}/{repo_name}/pulls"
            
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            data = {
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 201:
                pr_data = response.json()
                return {
                    "status": "success",
                    "pr_number": pr_data["number"],
                    "pr_url": pr_data["html_url"],
                    "message": "Pull request created successfully"
                }
            else:
                return {
                    "status": "error",
                    "error": response.json(),
                    "message": f"Failed to create PR: {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error creating PR: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def create_branch(
        self,
        local_path: str,
        branch_name: str,
        from_branch: str = "main"
    ) -> Dict:
        """
        Create a new branch in local repository
        
        Args:
            local_path: Path to local repository
            branch_name: New branch name
            from_branch: Branch to create from
            
        Returns:
            Dictionary with branch creation result
        """
        try:
            # Checkout from branch
            subprocess.run(
                ["git", "checkout", from_branch],
                cwd=local_path,
                check=True
            )
            
            # Create and checkout new branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=local_path,
                check=True
            )
            
            return {
                "status": "success",
                "branch": branch_name,
                "message": f"Branch '{branch_name}' created successfully"
            }
            
        except Exception as e:
            logger.error(f"Error creating branch: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_repository_info(
        self,
        repo_owner: str,
        repo_name: str,
        token: Optional[str] = None
    ) -> Dict:
        """
        Get repository information from GitHub API
        
        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
            token: Optional GitHub token for private repos
            
        Returns:
            Dictionary with repository information
        """
        try:
            url = f"{self.github_api_base}/repos/{repo_owner}/{repo_name}"
            
            headers = {}
            if token:
                headers["Authorization"] = f"token {token}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                repo_data = response.json()
                return {
                    "status": "success",
                    "name": repo_data["name"],
                    "full_name": repo_data["full_name"],
                    "description": repo_data.get("description"),
                    "language": repo_data.get("language"),
                    "stars": repo_data["stargazers_count"],
                    "forks": repo_data["forks_count"],
                    "open_issues": repo_data["open_issues_count"],
                    "default_branch": repo_data["default_branch"],
                    "created_at": repo_data["created_at"],
                    "updated_at": repo_data["updated_at"],
                    "private": repo_data["private"],
                    "url": repo_data["html_url"]
                }
            else:
                return {
                    "status": "error",
                    "error": f"GitHub API returned {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error getting repository info: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def list_branches(
        self,
        repo_owner: str,
        repo_name: str,
        token: Optional[str] = None
    ) -> Dict:
        """
        List all branches in a repository
        
        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
            token: Optional GitHub token
            
        Returns:
            Dictionary with branch list
        """
        try:
            url = f"{self.github_api_base}/repos/{repo_owner}/{repo_name}/branches"
            
            headers = {}
            if token:
                headers["Authorization"] = f"token {token}"
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                branches = response.json()
                return {
                    "status": "success",
                    "branches": [branch["name"] for branch in branches],
                    "count": len(branches)
                }
            else:
                return {
                    "status": "error",
                    "error": f"GitHub API returned {response.status_code}"
                }
                
        except Exception as e:
            logger.error(f"Error listing branches: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def parse_github_url(self, github_url: str) -> Dict:
        """
        Parse GitHub URL to extract owner and repo name
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            Dictionary with owner and repo name
        """
        try:
            # Handle various GitHub URL formats
            # https://github.com/owner/repo
            # https://github.com/owner/repo.git
            # git@github.com:owner/repo.git
            
            if github_url.startswith("git@github.com:"):
                # SSH format
                parts = github_url.replace("git@github.com:", "").replace(".git", "").split("/")
            else:
                # HTTPS format
                parts = github_url.replace("https://github.com/", "").replace(".git", "").split("/")
            
            if len(parts) >= 2:
                return {
                    "owner": parts[0],
                    "repo": parts[1],
                    "full_name": f"{parts[0]}/{parts[1]}"
                }
            else:
                return {
                    "error": "Invalid GitHub URL format"
                }
                
        except Exception as e:
            return {
                "error": str(e)
            }
    
    def _prepare_clone_url(self, repo_url: str, token: Optional[str]) -> str:
        """Prepare clone URL with authentication token"""
        if token and "github.com" in repo_url:
            # Add token to HTTPS URL
            if repo_url.startswith("https://github.com/"):
                repo_url = repo_url.replace("https://github.com/", f"https://{token}@github.com/")
            elif repo_url.startswith("http://github.com/"):
                repo_url = repo_url.replace("http://github.com/", f"http://{token}@github.com/")
        
        return repo_url


# Singleton instance
_github_service = None

def get_github_service() -> GitHubService:
    """Get GitHubService singleton instance"""
    global _github_service
    if _github_service is None:
        _github_service = GitHubService()
    return _github_service
