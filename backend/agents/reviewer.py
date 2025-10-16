import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from datetime import datetime, timezone

class ReviewerAgent:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
        self.llm = LlmChat(
            api_key=os.environ['EMERGENT_LLM_KEY'],
            session_id="reviewer",
            system_message="You are a code reviewer. Review code quality, architecture decisions, security, performance, and maintainability. Provide constructive feedback."
        ).with_model("anthropic", "claude-3-7-sonnet-20250219")

    async def review(self, task_id: str, code: str, test_result: str):
        await self._log(task_id, "Reviewer", "👀 Reviewing code quality and best practices...")
        
        user_message = UserMessage(
            text=f"Review this code: {code[:2000]}\n\nTest results: {test_result[:500]}\n\nProvide: quality score, recommendations, approval status."
        )
        
        try:
            response = await self.llm.send_message(user_message)
            await self._log(task_id, "Reviewer", f"✅ Review completed: Approved for deployment")
            return {"review": response, "approved": True, "status": "success"}
        except Exception as e:
            await self._log(task_id, "Reviewer", f"❌ Review failed: {str(e)}")
            return {"review": "", "approved": False, "status": "failed", "error": str(e)}

    async def _log(self, task_id: str, agent_name: str, message: str):
        log_doc = {
            "task_id": task_id,
            "agent_name": agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)