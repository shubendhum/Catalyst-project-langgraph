import os
from emergentintegrations.llm.chat import LlmChat, UserMessage
from datetime import datetime, timezone
import json

class PlannerAgent:
    def __init__(self, db, manager):
        self.db = db
        self.manager = manager
        self.llm = LlmChat(
            api_key=os.environ['EMERGENT_LLM_KEY'],
            session_id="planner",
            system_message="You are a planning agent. Analyze user requirements and create a structured development plan with phases and tasks. Output JSON format with: {phases: [{name, tasks: []}], tech_stack: {}, requirements: []}"
        ).with_model("anthropic", "claude-3-7-sonnet-20250219")

    async def plan(self, task_id: str, prompt: str):
        await self._log(task_id, "Planner", "🧠 Analyzing requirements and creating development plan...")
        
        user_message = UserMessage(
            text=f"Create a detailed development plan for: {prompt}\n\nProvide a structured JSON plan."
        )
        
        try:
            response = await self.llm.send_message(user_message)
            await self._log(task_id, "Planner", f"✅ Plan created: {response[:200]}...")
            return {"plan": response, "status": "success"}
        except Exception as e:
            await self._log(task_id, "Planner", f"❌ Planning failed: {str(e)}")
            return {"plan": "", "status": "failed", "error": str(e)}

    async def _log(self, task_id: str, agent_name: str, message: str):
        log_doc = {
            "task_id": task_id,
            "agent_name": agent_name,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.db.agent_logs.insert_one(log_doc)
        await self.manager.send_log(task_id, log_doc)