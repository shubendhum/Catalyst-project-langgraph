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