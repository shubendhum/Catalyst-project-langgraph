"""
Jira MCP Server
Provides tools for interacting with Jira (issues, projects, sprints)
"""
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone
import requests
from mcp.mcp_framework import MCPServer, MCPTool

logger = logging.getLogger(__name__)


class JiraMCPServer(MCPServer):
    """
    MCP Server for Jira integration
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.jira_url = None
        self.jira_email = None
        self.jira_api_token = None
        self.session = None
        super().__init__("jira", config)
    
    def _register_tools(self):
        """Register Jira-specific tools"""
        
        # Issue Management
        self.register_tool(MCPTool(
            name="create_issue",
            description="Create a new Jira issue",
            parameters={
                "project_key": {"type": "string", "required": True},
                "summary": {"type": "string", "required": True},
                "description": {"type": "string", "required": False},
                "issue_type": {"type": "string", "required": True, "default": "Task"}
            },
            handler=self._create_issue,
            category="issues"
        ))
        
        self.register_tool(MCPTool(
            name="get_issue",
            description="Get details of a Jira issue",
            parameters={
                "issue_key": {"type": "string", "required": True}
            },
            handler=self._get_issue,
            category="issues"
        ))
        
        self.register_tool(MCPTool(
            name="update_issue",
            description="Update a Jira issue",
            parameters={
                "issue_key": {"type": "string", "required": True},
                "fields": {"type": "object", "required": True}
            },
            handler=self._update_issue,
            category="issues"
        ))
        
        self.register_tool(MCPTool(
            name="search_issues",
            description="Search for Jira issues using JQL",
            parameters={
                "jql": {"type": "string", "required": True},
                "max_results": {"type": "integer", "required": False, "default": 50}
            },
            handler=self._search_issues,
            category="issues"
        ))
        
        self.register_tool(MCPTool(
            name="add_comment",
            description="Add a comment to a Jira issue",
            parameters={
                "issue_key": {"type": "string", "required": True},
                "comment": {"type": "string", "required": True}
            },
            handler=self._add_comment,
            category="issues"
        ))
        
        # Project Management
        self.register_tool(MCPTool(
            name="list_projects",
            description="List all Jira projects",
            parameters={},
            handler=self._list_projects,
            category="projects"
        ))
        
        self.register_tool(MCPTool(
            name="get_project",
            description="Get details of a Jira project",
            parameters={
                "project_key": {"type": "string", "required": True}
            },
            handler=self._get_project,
            category="projects"
        ))
        
        # Sprint Management
        self.register_tool(MCPTool(
            name="get_active_sprint",
            description="Get active sprint for a board",
            parameters={
                "board_id": {"type": "integer", "required": True}
            },
            handler=self._get_active_sprint,
            category="sprints"
        ))
        
        self.register_tool(MCPTool(
            name="get_sprint_issues",
            description="Get issues in a sprint",
            parameters={
                "sprint_id": {"type": "integer", "required": True}
            },
            handler=self._get_sprint_issues,
            category="sprints"
        ))
    
    async def connect(self) -> bool:
        """Connect to Jira"""
        try:
            self.jira_url = self.config.get("jira_url")
            self.jira_email = self.config.get("jira_email")
            self.jira_api_token = self.config.get("jira_api_token")
            
            if not all([self.jira_url, self.jira_email, self.jira_api_token]):
                logger.error("Jira configuration incomplete")
                return False
            
            # Create session with authentication
            self.session = requests.Session()
            self.session.auth = (self.jira_email, self.jira_api_token)
            self.session.headers.update({
                "Accept": "application/json",
                "Content-Type": "application/json"
            })
            
            # Test connection
            response = self.session.get(f"{self.jira_url}/rest/api/3/myself")
            
            if response.status_code == 200:
                self.connected = True
                self.connection_time = datetime.now(timezone.utc)
                logger.info("Successfully connected to Jira")
                return True
            else:
                logger.error(f"Failed to connect to Jira: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to Jira: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from Jira"""
        if self.session:
            self.session.close()
        self.connected = False
        logger.info("Disconnected from Jira")
    
    async def _create_issue(self, project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> Dict:
        """Create a new Jira issue"""
        try:
            url = f"{self.jira_url}/rest/api/3/issue"
            
            payload = {
                "fields": {
                    "project": {"key": project_key},
                    "summary": summary,
                    "description": {
                        "type": "doc",
                        "version": 1,
                        "content": [
                            {
                                "type": "paragraph",
                                "content": [
                                    {"type": "text", "text": description}
                                ]
                            }
                        ]
                    },
                    "issuetype": {"name": issue_type}
                }
            }
            
            response = self.session.post(url, json=payload)
            
            if response.status_code == 201:
                issue_data = response.json()
                return {
                    "issue_key": issue_data["key"],
                    "issue_id": issue_data["id"],
                    "self": issue_data["self"]
                }
            else:
                raise Exception(f"Failed to create issue: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error creating Jira issue: {str(e)}")
    
    async def _get_issue(self, issue_key: str) -> Dict:
        """Get Jira issue details"""
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                issue = response.json()
                return {
                    "key": issue["key"],
                    "summary": issue["fields"]["summary"],
                    "status": issue["fields"]["status"]["name"],
                    "assignee": issue["fields"].get("assignee", {}).get("displayName", "Unassigned"),
                    "created": issue["fields"]["created"],
                    "updated": issue["fields"]["updated"]
                }
            else:
                raise Exception(f"Failed to get issue: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error getting Jira issue: {str(e)}")
    
    async def _update_issue(self, issue_key: str, fields: Dict) -> Dict:
        """Update a Jira issue"""
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}"
            
            payload = {"fields": fields}
            response = self.session.put(url, json=payload)
            
            if response.status_code == 204:
                return {"message": f"Issue {issue_key} updated successfully"}
            else:
                raise Exception(f"Failed to update issue: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error updating Jira issue: {str(e)}")
    
    async def _search_issues(self, jql: str, max_results: int = 50) -> Dict:
        """Search for issues using JQL"""
        try:
            url = f"{self.jira_url}/rest/api/3/search"
            
            params = {
                "jql": jql,
                "maxResults": max_results
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                issues = []
                for issue in data["issues"]:
                    issues.append({
                        "key": issue["key"],
                        "summary": issue["fields"]["summary"],
                        "status": issue["fields"]["status"]["name"]
                    })
                
                return {
                    "total": data["total"],
                    "issues": issues
                }
            else:
                raise Exception(f"Failed to search issues: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error searching Jira issues: {str(e)}")
    
    async def _add_comment(self, issue_key: str, comment: str) -> Dict:
        """Add comment to a Jira issue"""
        try:
            url = f"{self.jira_url}/rest/api/3/issue/{issue_key}/comment"
            
            payload = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": comment}
                            ]
                        }
                    ]
                }
            }
            
            response = self.session.post(url, json=payload)
            
            if response.status_code == 201:
                return {"message": f"Comment added to {issue_key}"}
            else:
                raise Exception(f"Failed to add comment: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error adding comment: {str(e)}")
    
    async def _list_projects(self) -> Dict:
        """List all Jira projects"""
        try:
            url = f"{self.jira_url}/rest/api/3/project"
            response = self.session.get(url)
            
            if response.status_code == 200:
                projects = response.json()
                return {
                    "projects": [
                        {
                            "key": p["key"],
                            "name": p["name"],
                            "type": p.get("projectTypeKey", "unknown")
                        }
                        for p in projects
                    ]
                }
            else:
                raise Exception(f"Failed to list projects: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error listing projects: {str(e)}")
    
    async def _get_project(self, project_key: str) -> Dict:
        """Get project details"""
        try:
            url = f"{self.jira_url}/rest/api/3/project/{project_key}"
            response = self.session.get(url)
            
            if response.status_code == 200:
                project = response.json()
                return {
                    "key": project["key"],
                    "name": project["name"],
                    "description": project.get("description", ""),
                    "lead": project.get("lead", {}).get("displayName", "Unknown")
                }
            else:
                raise Exception(f"Failed to get project: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error getting project: {str(e)}")
    
    async def _get_active_sprint(self, board_id: int) -> Dict:
        """Get active sprint for a board"""
        try:
            url = f"{self.jira_url}/rest/agile/1.0/board/{board_id}/sprint"
            
            params = {"state": "active"}
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data["values"]:
                    sprint = data["values"][0]
                    return {
                        "id": sprint["id"],
                        "name": sprint["name"],
                        "state": sprint["state"],
                        "startDate": sprint.get("startDate"),
                        "endDate": sprint.get("endDate")
                    }
                else:
                    return {"message": "No active sprint found"}
            else:
                raise Exception(f"Failed to get active sprint: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error getting active sprint: {str(e)}")
    
    async def _get_sprint_issues(self, sprint_id: int) -> Dict:
        """Get issues in a sprint"""
        try:
            url = f"{self.jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
            response = self.session.get(url)
            
            if response.status_code == 200:
                data = response.json()
                issues = []
                for issue in data["issues"]:
                    issues.append({
                        "key": issue["key"],
                        "summary": issue["fields"]["summary"],
                        "status": issue["fields"]["status"]["name"]
                    })
                
                return {
                    "total": data["total"],
                    "issues": issues
                }
            else:
                raise Exception(f"Failed to get sprint issues: {response.text}")
                
        except Exception as e:
            raise Exception(f"Error getting sprint issues: {str(e)}")


def get_jira_server(config: Optional[Dict] = None) -> JiraMCPServer:
    """Get Jira MCP server instance"""
    return JiraMCPServer(config)
