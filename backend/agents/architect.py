import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from datetime import datetime, timezone

class ArchitectAgent:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
        self.llm = LlmChat(
            api_key=os.environ['EMERGENT_LLM_KEY'],
            session_id="architect",
            system_message="You are a software architect. Design system architecture including data models, API endpoints, file structure, and technology choices. Be specific and detailed."
        ).with_model("anthropic", "claude-3-7-sonnet-20250219")

    async def design(self, task_id: str, plan: str):
        await self._log(task_id, "Architect", "🏗️ Designing system architecture...")
        
        user_message = UserMessage(
            text=f"Based on this plan: {plan}\n\nCreate a detailed architecture design including: data models, API endpoints, file structure, component hierarchy."
        )
        
        try:
            response = await self.llm.send_message(user_message)
            await self._log(task_id, "Architect", f"✅ Architecture designed: {len(response)} chars")
            return {"architecture": response, "status": "success"}
        except Exception as e:
            await self._log(task_id, "Architect", f"❌ Architecture design failed: {str(e)}")
            return {"architecture": "", "status": "failed", "error": str(e)}

    async def _log(self, task_id: str, agent_name: str, message: str):
        log_doc = {
            "task_id": task_id,
            "agent_name": agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)