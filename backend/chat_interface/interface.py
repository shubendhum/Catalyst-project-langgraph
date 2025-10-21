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
                r"new project"
            ],
            "build_mvp": [
                r"(?:build|create|make) (?:a |an )?(?:quick|rapid|fast|simple|minimal|basic) (?:mvp|prototype|demo)",
                r"(?:build|create|make) (?:a |an )?mvp",
                r"rapid (?:prototype|mvp|build)",
                r"quick (?:prototype|mvp|build|demo)",
                r"(?:build|create|make) (?:me )?(?:a |an )?(?:simple|quick|fast) \w+",
                r"can you quickly (?:build|create|make)"
            ],
            "build_app": [
                r"build (a |an |me )?(?:simple |basic |new )?\w+",
                r"create (a |an |me )?(?:simple |basic |new )?\w+",
                r"develop (a |an |me )?(?:simple |basic |new )?\w+",
                r"make (a |an |me )?(?:simple |basic |new )?\w+",
                r"i want (a |an )?(?:simple |basic )?\w+ (?:app|application|website|site|tool|system)",
                r"can you (?:build|create|make|develop)",
                r"let's (?:build|create|make|develop)"
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
        
        # LOG INTENT DETECTION
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🎯 Intent detected: {intent} for message: '{user_message[:50]}...'")
        
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
        
        elif intent == "build_mvp":
            return await self._handle_build_mvp(conversation, message)
        
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
        
        from langchain_core.messages import HumanMessage
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        
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
        """Handle app building request using full workflow"""
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"🚀 _handle_build_app called for message: {message[:100]}")
        
        # Ensure we have a project
        project_id = conversation.context.get("current_project_id")
        
        if not project_id:
            # Create project first
            logger.info("Creating new project...")
            project_response = await self._handle_create_project(conversation, message)
            project_id = project_response["metadata"]["project_id"]
            logger.info(f"Project created: {project_id}")
        
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
        logger.info(f"Task created: {task_id}, triggering orchestrator...")
        
        # Update conversation context with active task
        conversation.context["current_task_id"] = task_id
        conversation.context["task_started_at"] = datetime.now(timezone.utc).isoformat()
        
        # Start orchestration in background (full workflow)
        import asyncio
        asyncio.create_task(
            self.orchestrator.execute_task(task_id, project_id, message)
        )
        
        logger.info(f"✅ Orchestrator triggered for task {task_id}")
        
        return {
            "content": f"""Perfect! I'm starting the **full development workflow** for you.

Here's what my team will do:
1. 📋 Planner will analyze your requirements
2. 🏗️ Architect will design the system
3. 💻 Coder will write the implementation
4. 🧪 Tester will validate everything works
5. 🔍 Reviewer will check code quality
6. 🚀 Deployer will launch your app

**Task ID:** `{task_id}`

This is the complete workflow with all best practices. Estimated time: 3-5 minutes.

💡 **Want it faster?** Say "build a quick MVP" instead!

I'm working on it in the background. I'll keep you updated!""",
            "metadata": {
                "action": "task_started",
                "task_id": task_id,
                "project_id": project_id,
                "workflow": "full"
            }
        }
    
    async def _handle_build_mvp(self, conversation: Conversation, message: str) -> Dict:
        """Handle rapid MVP building request (FAST workflow)"""
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"⚡ _handle_build_mvp called for message: {message[:100]}")
        
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
            "created_at": datetime.now(timezone.utc).isoformat(),
            "workflow": "rapid_mvp"
        }
        
        await self.db.tasks.insert_one(task)
        
        task_id = task["id"]
        logger.info(f"Task created: {task_id}, triggering RAPID MVP workflow...")
        
        # Update conversation context
        conversation.context["current_task_id"] = task_id
        conversation.context["task_started_at"] = datetime.now(timezone.utc).isoformat()
        conversation.context["workflow"] = "rapid_mvp"
        
        # Use Rapid MVP Orchestrator instead of full workflow
        from orchestrator.rapid_mvp_orchestrator import get_rapid_mvp_orchestrator
        
        rapid_orchestrator = get_rapid_mvp_orchestrator(self.db, self.orchestrator.manager, {})
        
        import asyncio
        asyncio.create_task(
            rapid_orchestrator.execute_task(task_id, project_id, message)
        )
        
        logger.info(f"✅ Rapid MVP Orchestrator triggered for task {task_id}")
        
        return {
            "content": f"""⚡ **RAPID MVP MODE** - Building your app super fast!

I'm focusing on the max value feature to give you that "aha moment" quickly.

**What I'm doing:**
💨 Skipping detailed planning
💨 No complex architecture
✅ Building beautiful, functional UI
✅ Core feature working end-to-end
✅ Modern design with advanced Tailwind

**Task ID:** `{task_id}`

**Estimated time:** 60-90 seconds

I'll create a working demo that showcases the main value. Let's ship fast! 🚀""",
            "metadata": {
                "action": "task_started",
                "task_id": task_id,
                "project_id": project_id,
                "workflow": "rapid_mvp"
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
        
        import logging
        logger = logging.getLogger(__name__)
        
        # Check if there's an active task in this conversation
        current_task_id = conversation.context.get("current_task_id")
        
        if current_task_id:
            # There's an active task - check its status
            logger.info(f"Active task found: {current_task_id}, checking status...")
            task = await self.db.tasks.find_one({"id": current_task_id})
            
            if task:
                task_status = task.get("status", "unknown")
                logger.info(f"Task {current_task_id} status: {task_status}")
                
                # If task is still running, provide status update
                if task_status in ["pending", "planning", "architecting", "coding", "testing_and_reviewing", "testing", "reviewing", "deploying"]:
                    status_messages = {
                        "pending": "⏳ Your task is queued and will start shortly...",
                        "planning": "📋 Planner is analyzing your requirements...",
                        "architecting": "🏗️ Architect is designing the system architecture...",
                        "coding": "💻 Coder is generating your application code...",
                        "testing_and_reviewing": "⚡ Tester and Reviewer are analyzing the code in parallel...",
                        "testing": "🧪 Tester is running tests...",
                        "reviewing": "🔍 Reviewer is checking code quality...",
                        "deploying": "🚀 Deployer is creating deployment configuration..."
                    }
                    
                    status_msg = status_messages.get(task_status, f"Working on it... Status: {task_status}")
                    
                    return {
                        "content": f"""{status_msg}

**Task ID:** `{current_task_id}`
**Status:** {task_status}

Your app is being built by my multi-agent team. This usually takes 2-5 minutes. I'll let you know when it's done! 

Want me to do something else in the meantime?""",
                        "metadata": {
                            "action": "task_status_update",
                            "task_id": current_task_id,
                            "status": task_status
                        }
                    }
                
                # Task completed - show results
                elif task_status == "completed":
                    project_path = task.get("project_path", "Unknown")
                    cost_stats = task.get("cost_stats", {})
                    
                    # Clear active task from context
                    conversation.context.pop("current_task_id", None)
                    
                    return {
                        "content": f"""✅ **Your app is ready!**

**Task ID:** `{current_task_id}`
**Status:** Completed
**Location:** `{project_path}`
**Cost:** ${cost_stats.get('total_cost', 0):.4f} ({cost_stats.get('calls_made', 0)} LLM calls)

The complete application has been generated and is ready to use. You can find it in the generated_projects directory.

What would you like to build next?""",
                        "metadata": {
                            "action": "task_completed",
                            "task_id": current_task_id,
                            "project_path": project_path
                        }
                    }
                
                # Task failed
                elif task_status == "failed":
                    error_msg = task.get("error", "Unknown error")
                    conversation.context.pop("current_task_id", None)
                    
                    return {
                        "content": f"""❌ **Task encountered an error**

**Task ID:** `{current_task_id}`
**Error:** {error_msg}

I can try again or we can approach this differently. What would you like to do?""",
                        "metadata": {
                            "action": "task_failed",
                            "task_id": current_task_id
                        }
                    }
        
        # No active task or general conversation - use LLM
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        context_messages = []
        
        # Add conversation history (last 5 messages)
        for msg in conversation.messages[-5:]:
            if msg.role == "user":
                context_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                context_messages.append(AIMessage(content=msg.content))
            elif msg.role == "system":
                context_messages.append(SystemMessage(content=msg.content))
        
        # Add current message
        context_messages.append(HumanMessage(content=message))
        
        # System prompt
        system_prompt = """You are Catalyst, an AI development team assistant. 
You help users build applications through natural conversation.
Be friendly, helpful, and proactive in suggesting what you can do.
If a user's request is unclear, ask clarifying questions."""
        
        response = await self.llm.ainvoke(
            context_messages,
            system_message=system_prompt
        )
        
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