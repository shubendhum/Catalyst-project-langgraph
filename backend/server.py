from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone
import json
import asyncio

from agents.planner import PlannerAgent
from agents.architect import ArchitectAgent
from agents.coder import CoderAgent
from agents.tester import TesterAgent
from agents.reviewer import ReviewerAgent
from agents.deployer import DeployerAgent
from agents.explorer import ExplorerAgent
from orchestrator.executor import TaskExecutor
from chat_interface.interface import ChatInterface, ChatMessage, Conversation
from orchestrator.phase2_orchestrator import get_phase2_orchestrator
from llm_client import get_llm_client

# Phase 4 Services
from services.context_manager import get_context_manager
from services.cost_optimizer import get_cost_optimizer
from services.learning_service import get_learning_service
from services.workspace_service import get_workspace_service
from services.analytics_service import get_analytics_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# WebSocket manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        self.active_connections[task_id] = websocket

    def disconnect(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]

    async def send_log(self, task_id: str, log_data: dict):
        if task_id in self.active_connections:
            try:
                await self.active_connections[task_id].send_text(json.dumps(log_data))
            except:
                pass

manager = ConnectionManager()

# Models
class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    status: str = "active"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectCreate(BaseModel):
    name: str
    description: str

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    prompt: str
    graph_state: Dict[str, Any] = {}
    status: str = "pending"
    cost: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskCreate(BaseModel):
    project_id: str
    prompt: str

class AgentLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    agent_name: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Deployment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    url: str
    commit_sha: str
    cost: float
    report: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExplorerScan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    system_name: str
    brief: str
    risks: List[str] = []
    proposals: List[str] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ExplorerScanCreate(BaseModel):
    system_name: str
    repo_url: Optional[str] = None
    jira_project: Optional[str] = None

# Routes
@api_router.get("/")
async def root():
    return {"message": "Catalyst AI Platform API", "version": "1.0.0"}

# Projects
@api_router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    project_obj = Project(**project.model_dump())
    doc = project_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.projects.insert_one(doc)
    return project_obj

@api_router.get("/projects", response_model=List[Project])
async def get_projects():
    projects = await db.projects.find({}, {"_id": 0}).to_list(1000)
    for p in projects:
        if isinstance(p['created_at'], str):
            p['created_at'] = datetime.fromisoformat(p['created_at'])
    return projects

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if isinstance(project['created_at'], str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    return project

# Tasks
@api_router.post("/tasks", response_model=Task)
async def create_task(task: TaskCreate):
    task_obj = Task(**task.model_dump())
    doc = task_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.tasks.insert_one(doc)
    
    # Start task execution in background
    asyncio.create_task(execute_task(task_obj.id, task_obj.prompt, task_obj.project_id))
    
    return task_obj

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(project_id: Optional[str] = None):
    query = {"project_id": project_id} if project_id else {}
    tasks = await db.tasks.find(query, {"_id": 0}).to_list(1000)
    for t in tasks:
        if isinstance(t['created_at'], str):
            t['created_at'] = datetime.fromisoformat(t['created_at'])
    return tasks

@api_router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if isinstance(task['created_at'], str):
        task['created_at'] = datetime.fromisoformat(task['created_at'])
    return task

# Agent Logs
@api_router.get("/logs/{task_id}", response_model=List[AgentLog])
async def get_logs(task_id: str):
    logs = await db.agent_logs.find({"task_id": task_id}, {"_id": 0}).sort("timestamp", 1).to_list(1000)
    for log in logs:
        if isinstance(log['timestamp'], str):
            log['timestamp'] = datetime.fromisoformat(log['timestamp'])
    return logs

# Deployments
@api_router.get("/deployments/{task_id}", response_model=Deployment)
async def get_deployment(task_id: str):
    deployment = await db.deployments.find_one({"task_id": task_id}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    if isinstance(deployment['created_at'], str):
        deployment['created_at'] = datetime.fromisoformat(deployment['created_at'])
    return deployment

# Explorer
@api_router.post("/explorer/scan", response_model=ExplorerScan)
async def create_explorer_scan(scan: ExplorerScanCreate):
    explorer = ExplorerAgent(db, manager)
    scan_result = await explorer.scan_system(scan.system_name, scan.repo_url, scan.jira_project)
    return scan_result

@api_router.get("/explorer/scans", response_model=List[ExplorerScan])
async def get_explorer_scans():
    scans = await db.explorer_scans.find({}, {"_id": 0}).to_list(1000)
    for s in scans:
        if isinstance(s['created_at'], str):
            s['created_at'] = datetime.fromisoformat(s['created_at'])
    return scans

# ==================== CHAT INTERFACE ENDPOINTS ====================

# Chat configuration models
class LLMConfig(BaseModel):
    provider: str = "emergent"  # emergent, anthropic, bedrock
    model: str = "claude-3-7-sonnet-20250219"
    api_key: Optional[str] = None
    aws_config: Optional[Dict[str, str]] = None

class SendMessageRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ConversationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    messages: List[ChatMessage] = []
    context: Dict = {}
    created_at: datetime
    updated_at: datetime

# Initialize global chat interface and orchestrator
# These will be initialized on first use
_chat_interface = None
_langgraph_orchestrator = None
_llm_config = None

def get_chat_interface():
    """Get or create chat interface singleton"""
    global _chat_interface, _langgraph_orchestrator, _llm_config
    
    if _chat_interface is None:
        # Get LLM client
        llm = get_llm_client(_llm_config)
        
        # Initialize Phase2 orchestrator (complete agent suite)
        _langgraph_orchestrator = get_phase2_orchestrator(db, manager, _llm_config or {})
        
        # Initialize chat interface
        _chat_interface = ChatInterface(db, llm, _langgraph_orchestrator)
    
    return _chat_interface

# Chat configuration
@api_router.post("/chat/config")
async def set_llm_config(config: LLMConfig):
    """Set LLM provider configuration"""
    global _llm_config, _chat_interface, _langgraph_orchestrator
    
    config_dict = config.model_dump()
    
    # Transform frontend config to backend format
    # Frontend sends: aws_access_key_id, aws_secret_access_key, aws_region, aws_endpoint_url
    # Backend expects: aws_config dict
    if config_dict.get("provider") == "bedrock":
        aws_config = {}
        if "aws_access_key_id" in config_dict:
            aws_config["access_key_id"] = config_dict.pop("aws_access_key_id", "")
        if "aws_secret_access_key" in config_dict:
            aws_config["secret_access_key"] = config_dict.pop("aws_secret_access_key", "")
        if "aws_region" in config_dict:
            aws_config["region"] = config_dict.pop("aws_region", "us-east-1")
        if "aws_endpoint_url" in config_dict and config_dict["aws_endpoint_url"]:
            aws_config["endpoint_url"] = config_dict.pop("aws_endpoint_url", "")
        if "bedrock_model_id" in config_dict:
            config_dict["model"] = config_dict.pop("bedrock_model_id", config_dict["model"])
        
        config_dict["aws_config"] = aws_config
    elif config_dict.get("provider") == "anthropic":
        # Handle Anthropic API key
        if "anthropic_api_key" in config_dict:
            config_dict["api_key"] = config_dict.pop("anthropic_api_key", "")
    
    _llm_config = config_dict
    
    # Reset chat interface to use new config
    _chat_interface = None
    _langgraph_orchestrator = None
    
    return {"status": "success", "message": "LLM configuration updated", "config": _llm_config}

@api_router.get("/chat/config")
async def get_llm_config():
    """Get current LLM configuration"""
    global _llm_config
    
    # Auto-detect Emergent LLM key from environment
    emergent_key = os.getenv("EMERGENT_LLM_KEY")
    
    if _llm_config is None:
        # Initialize with Emergent LLM key if available
        if emergent_key:
            _llm_config = {
                "provider": "emergent",
                "model": "claude-3-7-sonnet-20250219",
                "api_key": None,
                "aws_config": None
            }
        else:
            _llm_config = {
                "provider": os.getenv("DEFAULT_LLM_PROVIDER", "emergent"),
                "model": os.getenv("DEFAULT_LLM_MODEL", "claude-3-7-sonnet-20250219"),
                "api_key": None,
                "aws_config": None
            }
    
    # Transform backend format to frontend format
    safe_config = _llm_config.copy()
    
    # Indicate if Emergent key is available
    safe_config["emergent_key_available"] = bool(emergent_key)
    
    # Handle AWS Bedrock config
    if safe_config.get("aws_config"):
        aws_config = safe_config.pop("aws_config")
        safe_config["aws_access_key_id"] = "***" if aws_config.get("access_key_id") else ""
        safe_config["aws_secret_access_key"] = "***" if aws_config.get("secret_access_key") else ""
        safe_config["aws_region"] = aws_config.get("region", "us-east-1")
        safe_config["aws_endpoint_url"] = aws_config.get("endpoint_url", "")
        safe_config["bedrock_model_id"] = safe_config.get("model", "")
    else:
        # Initialize empty AWS fields for frontend
        safe_config["aws_access_key_id"] = ""
        safe_config["aws_secret_access_key"] = ""
        safe_config["aws_region"] = "us-east-1"
        safe_config["aws_endpoint_url"] = ""
        safe_config["bedrock_model_id"] = ""
    
    # Handle Anthropic API key
    if safe_config.get("provider") == "anthropic" and safe_config.get("api_key"):
        safe_config["anthropic_api_key"] = "***"
    else:
        safe_config["anthropic_api_key"] = ""
    
    # Don't expose the internal api_key field
    if "api_key" in safe_config:
        safe_config.pop("api_key")
    
    return safe_config

# Conversations
@api_router.post("/chat/conversations", response_model=ConversationResponse)
async def create_conversation():
    """Create a new conversation"""
    conversation = Conversation(
        id=str(uuid.uuid4()),
        title="New Conversation",
        messages=[],
        context={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    
    doc = conversation.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.conversations.insert_one(doc)
    
    return conversation

@api_router.get("/chat/conversations", response_model=List[ConversationResponse])
async def list_conversations(limit: int = 50):
    """List all conversations"""
    conversations = await db.conversations.find({}, {"_id": 0}).sort("updated_at", -1).limit(limit).to_list(limit)
    
    for conv in conversations:
        if isinstance(conv['created_at'], str):
            conv['created_at'] = datetime.fromisoformat(conv['created_at'])
        if isinstance(conv['updated_at'], str):
            conv['updated_at'] = datetime.fromisoformat(conv['updated_at'])
    
    return conversations

@api_router.get("/chat/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """Get a specific conversation"""
    conversation = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if isinstance(conversation['created_at'], str):
        conversation['created_at'] = datetime.fromisoformat(conversation['created_at'])
    if isinstance(conversation['updated_at'], str):
        conversation['updated_at'] = datetime.fromisoformat(conversation['updated_at'])
    
    return conversation

@api_router.delete("/chat/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation"""
    result = await db.conversations.delete_one({"id": conversation_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"status": "success", "message": "Conversation deleted"}

# Messages
@api_router.post("/chat/send")
async def send_message(request: SendMessageRequest):
    """Send a message and get response"""
    chat_interface = get_chat_interface()
    
    # Create conversation if not provided
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    try:
        # Process message
        response_message = await chat_interface.process_message(conversation_id, request.message)
        
        return {
            "conversation_id": conversation_id,
            "message": response_message.model_dump(),
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@api_router.get("/chat/conversations/{conversation_id}/messages", response_model=List[ChatMessage])
async def get_conversation_messages(conversation_id: str):
    """Get all messages in a conversation"""
    conversation = await db.conversations.find_one({"id": conversation_id}, {"_id": 0})
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation.get("messages", [])

# ==================== END CHAT INTERFACE ENDPOINTS ====================

# WebSocket endpoint
@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await manager.connect(websocket, task_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(task_id)

# Task execution function
async def execute_task(task_id: str, prompt: str, project_id: str):
    try:
        executor = TaskExecutor(db, manager)
        await executor.execute(task_id, prompt, project_id)
    except Exception as e:
        logging.error(f"Task execution error: {str(e)}")
        await db.tasks.update_one(
            {"id": task_id},
            {"$set": {"status": "failed"}}
        )

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()