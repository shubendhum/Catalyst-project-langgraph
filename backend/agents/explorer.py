import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from datetime import datetime, timezone
import uuid
from connectors.github_connector import GitHubConnector
from connectors.jira_connector import JiraConnector

class ExplorerAgent:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
        self.llm = LlmChat(
            api_key=os.environ['EMERGENT_LLM_KEY'],
            session_id="explorer",
            system_message="You are an enterprise explorer agent. Analyze existing systems read-only and provide insights, risks, and enhancement proposals. Never modify production systems."
        ).with_model("anthropic", "claude-3-7-sonnet-20250219")
        self.github = GitHubConnector()
        self.jira = JiraConnector()

    async def scan_system(self, system_name: str, repo_url: str = None, jira_project: str = None):
        scan_id = str(uuid.uuid4())
        await self._log(scan_id, "Explorer", f"🔍 Scanning system: {system_name}")
        
        try:
            # Gather system context (mocked connectors)
            context = f"System: {system_name}\n"
            
            if repo_url:
                await self._log(scan_id, "Explorer", "📂 Analyzing repository...")
                repo_data = await self.github.analyze_repo(repo_url)
                context += f"Repository: {repo_data}\n"
            
            if jira_project:
                await self._log(scan_id, "Explorer", "📋 Analyzing Jira project...")
                jira_data = await self.jira.get_project_info(jira_project)
                context += f"Jira: {jira_data}\n"
            
            # AI analysis
            user_message = UserMessage(
                text=f"{context}\n\nProvide: 1) System brief, 2) Risk assessment, 3) Enhancement proposals. Be enterprise-safe."
            )
            
            response = await self.llm.send_message(user_message)
            
            # Create scan record
            scan_doc = {
                "id": scan_id,
                "system_name": system_name,
                "brief": response[:500],
                "risks": ["Data exposure risk", "Legacy dependencies"],
                "proposals": ["API modernization", "Add monitoring"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await self.db.explorer_scans.insert_one(scan_doc)
            
            await self._log(scan_id, "Explorer", "✅ System scan completed")
            
            return scan_doc
        except Exception as e:
            await self._log(scan_id, "Explorer", f"❌ Scan failed: {str(e)}")
            return None

    async def _log(self, scan_id: str, agent_name: str, message: str):
        log_doc = {
            "task_id": scan_id,
            "agent_name": agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(scan_id, log_doc)