class JiraConnector:
    """Mock Jira connector - read-only integration"""
    
    async def get_project_info(self, project_key: str) -> str:
        # Mocked - would integrate with Jira API
        return f"Jira project analyzed (mocked): {project_key}. Found 24 open tickets, 12 in progress, 45 completed."