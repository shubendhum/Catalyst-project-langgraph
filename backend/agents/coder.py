import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from datetime import datetime, timezone

class CoderAgent:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
        self.llm = LlmChat(
            api_key=os.environ['EMERGENT_LLM_KEY'],
            session_id="coder",
            system_message="You are a coding agent. Write clean, production-ready code based on architecture specifications. Include error handling, comments, and follow best practices."
        ).with_model("anthropic", "claude-3-7-sonnet-20250219")

    async def code(self, task_id: str, architecture: str, feedback: str = ""):
        context = f"Architecture: {architecture}"
        if feedback:
            context += f"\n\nFeedback from tests/review: {feedback}"
            await self._log(task_id, "Coder", "🔄 Fixing code based on feedback...")
        else:
            await self._log(task_id, "Coder", "💻 Writing code implementation...")
        
        user_message = UserMessage(
            text=f"{context}\n\nGenerate complete code implementation. Provide file paths and code content."
        )
        
        try:
            response = await self.llm.send_message(user_message)
            await self._log(task_id, "Coder", f"✅ Code generated: {len(response)} chars")
            return {"code": response, "status": "success"}
        except Exception as e:
            await self._log(task_id, "Coder", f"❌ Coding failed: {str(e)}")
            return {"code": "", "status": "failed", "error": str(e)}

    async def _log(self, task_id: str, agent_name: str, message: str):
        log_doc = {
            "task_id": task_id,
            "agent_name": agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)