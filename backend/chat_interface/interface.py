"""Conversational chat interface for Catalyst"""

from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
import uuid
import json
import re


class ChatMessage(BaseModel):
    id: str
    conversation_id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime
    metadata: Optional[Dict] = {}


class Conversation(BaseModel):
    id: str
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    title: str
    messages: List[ChatMessage] = []
    context: Dict = {}
    created_at: datetime
    updated_at: datetime


class ChatInterface:
    """Conversational interface for natural language commands"""
    
    def __init__(self, db, llm, langgraph_orchestrator):
        self.db = db
        self.llm = llm
        self.orchestrator = langgraph_orchestrator
        self.command_patterns = self._init_command_patterns()
    
    def _init_command_patterns(self) -> Dict:
        """Initialize command patterns for intent recognition"""
        return {
            "create_project": [
                r"create (a |an )?(?:new )?project",
                r"start (a |an )?(?:new )?project",
                r"new project",
                r"build (a |an )?(?:new )?(?:app|application|project)"
            ],
            "build_app": [
                r"build (a |an |me )?.+?(?:app|application)",
                r"create (a |an |me )?.+?(?:app|application)",
                r"develop (a |an |me )?.+?(?:app|application)",
                r"make (a |an |me )?.+?(?:app|application)"
            ],
            "add_feature": [
                r"add (a |an )?(?:new )?feature",
                r"implement.+?feature",
                r"create (a |an )?(?:new )?feature"
            ],
            "fix_bug": [
                r"fix (the )?bug",
                r"resolve (the )?issue",
                r"debug",
                r"there(?:'s| is) (a )?bug"
            ],
            "deploy": [
                r"deploy",
                r"launch",
                r"go live",
                r"push to production"
            ],
            "explore_system": [
                r"analyze.+?(?:system|codebase|repo)",
                r"explore.+?(?:system|codebase|repo)",
                r"scan.+?(?:system|codebase|repo)",
                r"audit.+?(?:system|codebase)"
            ],
            "status": [
                r"what(?:'s| is) the status",
                r"show (?:me )?(?:the )?status",
                r"check status",
                r"how(?:'s| is) it going"
            ],
            "help": [
                r"help",
                r"what can you do",
                r"show (?:me )?commands",
                r"how do i"
            ]
        }
    
    async def process_message(self, conversation_id: str, user_message: str) -> ChatMessage:
        """Process a user message and generate response"""
        
        # Load or create conversation
        conversation = await self._get_or_create_conversation(conversation_id)
        
        # Add user message
        user_msg = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="user",
            content=user_message,
            timestamp=datetime.now(timezone.utc)
        )
        conversation.messages.append(user_msg)
        
        # Detect intent
        intent = self._detect_intent(user_message)
        
        # Generate response based on intent
        assistant_response = await self._generate_response(
            conversation, 
            user_message, 
            intent
        )
        
        # Add assistant message
        assistant_msg = ChatMessage(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_response["content"],
            timestamp=datetime.now(timezone.utc),
            metadata=assistant_response.get("metadata", {})
        )
        conversation.messages.append(assistant_msg)
        
        # Save conversation
        await self._save_conversation(conversation)
        
        return assistant_msg
    
    def _detect_intent(self, message: str) -> str:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        
        return "general"  # Default intent
    
    async def _generate_response(self, conversation: Conversation, message: str, intent: str) -> Dict:
        """Generate response based on intent"""
        
        if intent == "create_project":
            return await self._handle_create_project(conversation, message)
        
        elif intent == "build_app":
            return await self._handle_build_app(conversation, message)
        
        elif intent == "add_feature":
            return await self._handle_add_feature(conversation, message)
        
        elif intent == "fix_bug":
            return await self._handle_fix_bug(conversation, message)
        
        elif intent == "deploy":
            return await self._handle_deploy(conversation, message)
        
        elif intent == "explore_system":
            return await self._handle_explore_system(conversation, message)
        
        elif intent == "status":
            return await self._handle_status(conversation, message)
        
        elif intent == "help":
            return await self._handle_help(conversation, message)
        
        else:
            return await self._handle_general(conversation, message)
    
    async def _handle_create_project(self, conversation: Conversation, message: str) -> Dict:
        """Handle project creation request"""
        
        # Extract project details using LLM
        prompt = f"""Extract project details from this user message:

"{message}"

Return JSON with: name, description (if mentioned).
If not clear, suggest a name based on context."""
        
        response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
        
        try:
            project_details = json.loads(response.content)
        except:
            project_details = {
                "name": "New Project",
                "description": message
            }
        
        # Create project in database
        project = {
            "id": str(uuid.uuid4()),
            "name": project_details.get("name", "New Project"),
            "description": project_details.get("description", message),
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.projects.insert_one(project)
        
        project_id = project["id"]
        project_name = project["name"]
        
        # Update conversation context
        conversation.context["current_project_id"] = project_id
        conversation.project_id = project_id
        
        return {
            "content": f"Project '{project_name}' created! I'm ready to help you build it. What would you like to create?",
            "metadata": {
                "action": "project_created",
                "project_id": project_id,
                "project_name": project_name
            }
        }
    
    async def _handle_build_app(self, conversation: Conversation, message: str) -> Dict:
        """Handle app building request"""
        
        # Ensure we have a project
        project_id = conversation.context.get("current_project_id")
        
        if not project_id:
            # Create project first
            project_response = await self._handle_create_project(conversation, message)
            project_id = project_response["metadata"]["project_id"]
        
        # Create task
        task = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "prompt": message,
            "graph_state": {},
            "status": "pending",
            "cost": 0.0,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.tasks.insert_one(task)
        
        task_id = task["id"]
        
        # Start LangGraph orchestration in background
        import asyncio
        asyncio.create_task(
            self.orchestrator.execute_task(task_id, project_id, message)
        )
        
        return {
            "content": f"""Perfect! I'm starting to work on that for you.

Here's what my team will do:
1. Planner will analyze your requirements
2. Architect will design the system
3. Coder will write the implementation
4. Tester will validate everything works
5. Reviewer will check code quality
6. Deployer will launch your app

I'll keep you updated on progress. You can check the status anytime!""",
            "metadata": {
                "action": "task_started",
                "task_id": task_id,
                "project_id": project_id
            }
        }
    
    async def _handle_status(self, conversation: Conversation, message: str) -> Dict:
        """Handle status check request"""
        
        project_id = conversation.context.get("current_project_id")
        
        if not project_id:
            return {
                "content": "You don't have any active projects yet. Would you like to create one?",
                "metadata": {"action": "no_project"}
            }
        
        # Get latest task
        tasks = await self.db.tasks.find({"project_id": project_id}).sort("created_at", -1).limit(1).to_list(1)
        
        if not tasks:
            return {
                "content": "No tasks running yet. What would you like me to build?",
                "metadata": {"action": "no_tasks"}
            }
        
        task = tasks[0]
        status = task["status"]
        graph_state = task.get("graph_state", {})
        
        # Format status message
        status_emojis = {
            "planner": "[PLAN]",
            "architect": "[ARCH]",
            "coder": "[CODE]",
            "tester": "[TEST]",
            "reviewer": "[REV]",
            "deployer": "[DEPLOY]"
        }
        
        status_msg = f"**Current Status:** {status}\n\n**Agent Progress:**\n"
        
        for agent, prefix in status_emojis.items():
            agent_status = graph_state.get(agent, "pending")
            status_icon = "[OK]" if agent_status == "completed" else "[RUN]" if agent_status == "reworking" else "[WAIT]"
            status_msg += f"{status_icon} {prefix} {agent.capitalize()}: {agent_status}\n"
        
        if status == "completed" and task.get("deployment_url"):
            status_msg += f"\n**Your app is live!** {task['deployment_url']}"
        
        return {
            "content": status_msg,
            "metadata": {
                "action": "status_check",
                "task_id": task["id"],
                "status": status
            }
        }
    
    async def _handle_help(self, conversation: Conversation, message: str) -> Dict:
        """Handle help request"""
        
        help_text = """**Hi! I'm your AI development team.**

I can help you with:

**Project Management**
- "Create a new project called X"
- "Start a project for Y"

**Development**
- "Build me a todo app with React"
- "Create a REST API for user management"
- "Develop a dashboard with charts"

**Features & Fixes**
- "Add authentication to my app"
- "Fix the login bug"
- "Implement dark mode"

**System Analysis**
- "Analyze my GitHub repository"
- "Explore the codebase at [URL]"
- "Audit our existing system"

**Status & Info**
- "What's the status?"
- "Show me progress"
- "How's it going?"

Just talk to me naturally - like you would with your dev team!
"""
        
        return {
            "content": help_text,
            "metadata": {"action": "help"}
        }
    
    async def _handle_general(self, conversation: Conversation, message: str) -> Dict:
        """Handle general conversation"""
        
        # Use LLM for general conversation with context
        context_messages = []
        
        # Add conversation history (last 5 messages)
        for msg in conversation.messages[-5:]:
            context_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Add current message
        context_messages.append({
            "role": "user",
            "content": message
        })
        
        # System prompt
        system_prompt = """You are Catalyst, an AI development team assistant. 
You help users build applications through natural conversation.
Be friendly, helpful, and proactive in suggesting what you can do.
If a user's request is unclear, ask clarifying questions."""
        
        response = await self.llm.ainvoke([
            {"role": "system", "content": system_prompt},
            *context_messages
        ])
        
        return {
            "content": response.content,
            "metadata": {"action": "general_conversation"}
        }
    
    # Placeholder handlers for other intents
    async def _handle_add_feature(self, conversation, message):
        return await self._handle_build_app(conversation, message)
    
    async def _handle_fix_bug(self, conversation, message):
        return await self._handle_build_app(conversation, message)
    
    async def _handle_deploy(self, conversation, message):
        return await self._handle_status(conversation, message)
    
    async def _handle_explore_system(self, conversation, message):
        # Similar to Explorer agent
        return {
            "content": "I'll analyze that system for you. Please provide the repository URL or system details.",
            "metadata": {"action": "explore_prompt"}
        }
    
    # Conversation management
    async def _get_or_create_conversation(self, conversation_id: str) -> Conversation:
        """Get or create a conversation"""
        
        conv = await self.db.conversations.find_one({"id": conversation_id})
        
        if conv:
            # Parse datetime strings if needed
            if isinstance(conv.get('created_at'), str):
                conv['created_at'] = datetime.fromisoformat(conv['created_at'])
            if isinstance(conv.get('updated_at'), str):
                conv['updated_at'] = datetime.fromisoformat(conv['updated_at'])
            return Conversation(**conv)
        
        # Create new conversation
        conversation = Conversation(
            id=conversation_id,
            title="New Conversation",
            messages=[],
            context={},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        doc = conversation.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        doc['updated_at'] = doc['updated_at'].isoformat()
        
        await self.db.conversations.insert_one(doc)
        
        return conversation
    
    async def _save_conversation(self, conversation: Conversation):
        """Save conversation to database"""
        
        conversation.updated_at = datetime.now(timezone.utc)
        
        # Update title if it's still "New Conversation" and we have messages
        if conversation.title == "New Conversation" and len(conversation.messages) > 0:
            first_msg = conversation.messages[0].content[:50]
            conversation.title = first_msg
        
        doc = conversation.model_dump()
        doc['created_at'] = doc['created_at'].isoformat() if isinstance(doc['created_at'], datetime) else doc['created_at']
        doc['updated_at'] = doc['updated_at'].isoformat() if isinstance(doc['updated_at'], datetime) else doc['updated_at']
        
        await self.db.conversations.update_one(
            {"id": conversation.id},
            {"$set": doc},
            upsert=True
        )