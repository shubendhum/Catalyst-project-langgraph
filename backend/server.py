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
import logging

# Initialize logger early
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
from orchestrator.dual_mode_orchestrator import get_dual_mode_orchestrator
from llm_client import get_llm_client
from config.environment import get_config, is_docker_desktop
from workers import get_worker_manager

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

class OAuthStartRequest(BaseModel):
    """OAuth2 authorization flow start request"""
    auth_url: str
    client_id: str
    redirect_uri: str
    scopes: str

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

# ============================================
# Backend Logs Endpoints (must come before /logs/{task_id})
# ============================================

# ============================================
# OAuth2 Authentication Endpoints
# ============================================

# OAuth2 state storage (in-memory for simplicity)
oauth_states = {}

@api_router.post("/auth/oauth/start")
async def start_oauth_flow(request: OAuthStartRequest):
    """
    Start OAuth2 authorization code flow
    Returns authorization URL for user to visit
    """
    from services.oauth2_service import get_oauth2_service
    import uuid
    
    try:
        logger.info("🔐 Starting OAuth2 authorization flow")
        logger.info(f"   Auth URL: {request.auth_url}")
        logger.info(f"   Client ID: {request.client_id[:10]}...")
        logger.info(f"   Redirect URI: {request.redirect_uri}")
        logger.info(f"   Scopes: {request.scopes}")
        
        oauth_service = get_oauth2_service()
        
        # Generate state for CSRF protection
        state = str(uuid.uuid4())
        
        # Store state
        oauth_states[state] = {
            "created_at": datetime.now(timezone.utc),
            "authenticated": False,
            "error": None,
            "access_token": None
        }
        
        # Generate authorization URL
        authorization_url = await oauth_service.get_authorization_url(
            auth_url=request.auth_url,
            client_id=request.client_id,
            redirect_uri=request.redirect_uri,
            scopes=request.scopes,
            state=state
        )
        
        logger.info(f"✅ Authorization URL generated: {authorization_url[:100]}...")
        logger.info(f"   State: {state}")
        
        return {
            "success": True,
            "authorization_url": authorization_url,
            "state": state
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting OAuth flow: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


@api_router.get("/auth/oauth/callback")
async def oauth_callback(code: str, state: str):
    """
    OAuth2 callback endpoint
    Exchanges authorization code for access token
    """
    from services.oauth2_service import get_oauth2_service
    
    try:
        logger.info("🔐 OAuth2 callback received")
        logger.info(f"   State: {state}")
        logger.info(f"   Code: {code[:20]}...")
        
        # Verify state
        if state not in oauth_states:
            logger.error(f"❌ Invalid state parameter: {state}")
            return {"error": "Invalid state parameter"}
        
        oauth_service = get_oauth2_service()
        
        # Get config from global state (you'll need to pass this)
        # For now, we'll store it in oauth_states
        # In production, store in session or database
        
        # Exchange code for token
        # Note: We need the full config here
        # This is a simplified version - you'll need to pass config properly
        
        oauth_states[state]["authenticated"] = True
        oauth_states[state]["code"] = code
        
        logger.info(f"✅ OAuth2 callback processed successfully")
        
        # Return success page
        return """
        <html>
        <head><title>Authentication Successful</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: #16a34a;">✅ Authentication Successful!</h1>
            <p>You can close this window and return to Catalyst.</p>
            <script>
                // Notify parent window
                if (window.opener) {
                    window.opener.postMessage({type: 'oauth_success'}, '*');
                }
                setTimeout(() => window.close(), 2000);
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        logger.error(f"❌ OAuth callback error: {e}", exc_info=True)
        oauth_states[state]["authenticated"] = False
        oauth_states[state]["error"] = str(e)
        
        return f"""
        <html>
        <head><title>Authentication Failed</title></head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1 style="color: #dc2626;">❌ Authentication Failed</h1>
            <p>{str(e)}</p>
            <p>Please close this window and try again.</p>
        </body>
        </html>
        """


@api_router.get("/auth/oauth/status")
async def get_oauth_status(state: str):
    """
    Check OAuth2 authentication status
    Used by frontend to poll for completion
    """
    if state not in oauth_states:
        return {"authenticated": False, "error": "Invalid state"}
    
    state_data = oauth_states[state]
    
    return {
        "authenticated": state_data.get("authenticated", False),
        "error": state_data.get("error")
    }


@api_router.get("/environment/info")
async def get_environment_info():
    """Get current environment information"""
    from config.environment import get_config
    from services.llm_observability import get_observability_service
    
    config = get_config()
    obs_service = get_observability_service()
    
    return {
        "success": True,
        "environment": config["environment"],
        "orchestration_mode": config["orchestration_mode"],
        "features": {
            "postgres": config["databases"]["postgres"]["enabled"],
            "event_streaming": config["event_streaming"]["enabled"],
            "git_integration": config["git"]["enabled"],
            "preview_deployments": config["preview"]["enabled"]
        },
        "infrastructure": {
            "mongodb": config["databases"]["mongodb"]["enabled"],
            "redis": config["databases"]["redis"].get("enabled", False),
            "qdrant": config["databases"]["qdrant"].get("enabled", False)
        },
        "observability": {
            "langfuse": obs_service.langfuse_enabled,
            "langfuse_url": "http://localhost:3001" if obs_service.langfuse_enabled else None,
            "langsmith": obs_service.langsmith_enabled,
            "langsmith_url": "https://smith.langchain.com" if obs_service.langsmith_enabled else None
        }
    }


# ============================================
# Git Management Endpoints
# ============================================

@api_router.get("/git/repos")
async def list_git_repos():
    """List all local Git repositories"""
    from services.git_service_v2 import get_git_service
    
    try:
        git_service = get_git_service()
        
        if not git_service.enabled:
            return {"success": True, "repos": [], "message": "Git not enabled in this environment"}
        
        repos = []
        repos_path = git_service.repos_path
        
        if repos_path.exists():
            for item in repos_path.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    # Get repo info
                    commits = git_service.get_commit_history(item.name, limit=1)
                    last_commit = commits[0] if commits else None
                    
                    repos.append({
                        "name": item.name,
                        "path": str(item),
                        "last_commit": last_commit,
                        "branches": []  # TODO: List branches
                    })
        
        return {"success": True, "repos": repos, "count": len(repos)}
        
    except Exception as e:
        logger.error(f"Error listing repos: {e}")
        return {"success": False, "error": str(e)}


@api_router.get("/git/repos/{project_name}")
async def get_git_repo_details(project_name: str):
    """Get details of a specific repository"""
    from services.git_service_v2 import get_git_service
    
    try:
        git_service = get_git_service()
        
        if not git_service.enabled:
            return {"success": False, "error": "Git not enabled"}
        
        repo_path = git_service.repos_path / project_name
        
        if not repo_path.exists():
            return {"success": False, "error": "Repository not found"}
        
        # Get commit history
        commits = git_service.get_commit_history(project_name, limit=20)
        
        # Get current commit
        current_commit = git_service.get_current_commit(project_name)
        
        # Get LOC
        loc = git_service.count_lines_of_code(project_name)
        
        return {
            "success": True,
            "repo": {
                "name": project_name,
                "path": str(repo_path),
                "current_commit": current_commit,
                "lines_of_code": loc,
                "commits": commits
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting repo details: {e}")
        return {"success": False, "error": str(e)}


@api_router.post("/git/repos/{project_name}/push")
async def push_repo_to_github(project_name: str, branch: str = "main"):
    """Push repository to GitHub"""
    from integrations.github_integration import get_github_service
    
    try:
        github_service = get_github_service()
        
        if not github_service.enabled:
            return {
                "success": False,
                "error": "GitHub integration not enabled. Set GITHUB_TOKEN environment variable."
            }
        
        success = await github_service.push_to_github(project_name, branch)
        
        if success:
            return {
                "success": True,
                "message": f"Pushed {branch} to GitHub",
                "repo_url": f"https://github.com/{github_service.org}/{project_name}"
            }
        else:
            return {"success": False, "error": "Push failed"}
            
    except Exception as e:
        logger.error(f"Error pushing to GitHub: {e}")
        return {"success": False, "error": str(e)}


@api_router.post("/git/repos/{project_name}/pr")
async def create_github_pr(
    project_name: str,
    branch: str,
    title: str,
    description: str = "",
    base: str = "main"
):
    """Create a pull request on GitHub"""
    from integrations.github_integration import get_github_service
    
    try:
        github_service = get_github_service()
        
        if not github_service.enabled:
            return {"success": False, "error": "GitHub integration not enabled"}
        
        pr_url = await github_service.create_pull_request(
            project_name=project_name,
            branch=branch,
            title=title,
            description=description,
            base=base
        )
        
        if pr_url:
            return {"success": True, "pr_url": pr_url}
        else:
            return {"success": False, "error": "Failed to create PR"}
            
    except Exception as e:
        logger.error(f"Error creating PR: {e}")
        return {"success": False, "error": str(e)}


# ============================================
# Preview Deployment Endpoints
# ============================================

@api_router.get("/preview")
async def list_preview_deployments():
    """List all active preview deployments"""
    from services.preview_deployment import get_preview_service
    
    try:
        preview_service = get_preview_service()
        
        if not preview_service.enabled:
            return {
                "success": True,
                "previews": [],
                "message": "Preview deployments not available in this environment"
            }
        
        previews = await preview_service.list_active_previews()
        
        return {"success": True, "previews": previews, "count": len(previews)}
        
    except Exception as e:
        logger.error(f"Error listing previews: {e}")
        return {"success": False, "error": str(e)}


@api_router.get("/preview/{task_id}")
async def get_preview_deployment(task_id: str):
    """Get preview deployment details"""
    from services.preview_deployment import get_preview_service
    
    try:
        preview_service = get_preview_service()
        
        if not preview_service.enabled:
            return {"success": False, "error": "Preview deployments not available"}
        
        preview = await preview_service.get_preview(task_id)
        
        if preview:
            return {"success": True, "preview": preview}
        else:
            return {"success": False, "error": "Preview not found"}
            
    except Exception as e:
        logger.error(f"Error getting preview: {e}")
        return {"success": False, "error": str(e)}


@api_router.delete("/preview/{task_id}")
async def delete_preview_deployment(task_id: str):
    """Cleanup preview deployment"""
    from services.preview_deployment import get_preview_service
    
    try:
        preview_service = get_preview_service()
        
        if not preview_service.enabled:
            return {"success": False, "error": "Preview deployments not available"}
        
        success = await preview_service.cleanup_preview(task_id)
        
        if success:
            return {"success": True, "message": "Preview cleaned up successfully"}
        else:
            return {"success": False, "error": "Failed to cleanup preview"}
            
    except Exception as e:
        logger.error(f"Error deleting preview: {e}")
        return {"success": False, "error": str(e)}


@api_router.post("/preview/cleanup-expired")
async def cleanup_expired_previews():
    """Cleanup all expired preview deployments"""
    from services.preview_deployment import get_preview_service
    
    try:
        preview_service = get_preview_service()
        
        if not preview_service.enabled:
            return {"success": False, "error": "Preview deployments not available"}
        
        count = await preview_service.cleanup_expired_previews()
        
        return {
            "success": True,
            "cleaned_up": count,
            "message": f"Cleaned up {count} expired previews"
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up expired previews: {e}")
        return {"success": False, "error": str(e)}


@api_router.get("/logs/backend")
async def get_backend_logs(minutes: int = 5, limit: int = 1000):
    """Get backend logs from the last N minutes"""
    import subprocess
    from datetime import timedelta
    
    logger.info(f"get_backend_logs called with minutes={minutes}, limit={limit}")
    
    try:
        # Calculate timestamp for N minutes ago
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        
        # Read supervisor logs for backend
        log_files = [
            "/var/log/supervisor/backend.out.log",
            "/var/log/supervisor/backend.err.log"
        ]
        
        all_logs = []
        
        for log_file in log_files:
            try:
                # Read log file
                result = subprocess.run(
                    ["tail", "-n", str(limit), log_file],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        if line.strip():
                            all_logs.append({
                                "source": log_file.split('/')[-1],
                                "message": line,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            })
                    logger.info(f"Read {len(lines)} lines from {log_file}")
                else:
                    logger.warning(f"Failed to read {log_file}: return code {result.returncode}")
            except Exception as e:
                logger.error(f"Error reading {log_file}: {str(e)}")
                continue
        
        # Also get agent logs from database (last N minutes)
        agent_logs = await db.agent_logs.find({
            "timestamp": {
                "$gte": cutoff_time.isoformat()
            }
        }).sort("timestamp", -1).limit(limit).to_list(limit)
        
        logger.info(f"Found {len(agent_logs)} agent logs from database")
        
        # Convert agent logs to same format
        for log in agent_logs:
            all_logs.append({
                "source": "agent",
                "agent_name": log.get("agent_name", "Unknown"),
                "task_id": log.get("task_id", ""),
                "message": log.get("message", ""),
                "timestamp": log.get("timestamp", "")
            })
        
        # Sort by timestamp (most recent first)
        all_logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        result = {
            "success": True,
            "logs": all_logs[:limit],
            "count": len(all_logs[:limit]),
            "timeframe_minutes": minutes
        }
        
        logger.info(f"Returning {len(all_logs[:limit])} logs")
        return result
    except Exception as e:
        logger.error(f"Error fetching backend logs: {str(e)}")
        return {"success": False, "error": str(e)}


@api_router.get("/logs/cost-stats")
async def get_global_cost_stats():
    """Get aggregated cost statistics from all tasks"""
    try:
        # Get all completed tasks with cost_stats
        tasks = await db.tasks.find(
            {"cost_stats": {"$exists": True}},
            {"_id": 0, "id": 1, "cost_stats": 1, "project_id": 1, "created_at": 1}
        ).to_list(1000)
        
        # Aggregate statistics
        total_calls = 0
        total_cache_hits = 0
        total_cost = 0.0
        task_count = len(tasks)
        
        for task in tasks:
            stats = task.get("cost_stats", {})
            total_calls += stats.get("calls_made", 0)
            total_cache_hits += stats.get("cache_hits", 0)
            total_cost += stats.get("total_cost", 0.0)
        
        cache_hit_rate = (total_cache_hits / total_calls * 100) if total_calls > 0 else 0
        avg_cost_per_task = total_cost / task_count if task_count > 0 else 0
        
        # Get cost optimizer stats
        optimizer_stats = cost_optimizer.get_cache_stats()
        
        return {
            "success": True,
            "global_stats": {
                "total_tasks": task_count,
                "total_llm_calls": total_calls,
                "total_cache_hits": total_cache_hits,
                "cache_hit_rate": cache_hit_rate,
                "total_cost": total_cost,
                "average_cost_per_task": avg_cost_per_task
            },
            "optimizer_stats": optimizer_stats
        }
    except Exception as e:
        logger.error(f"Error fetching cost stats: {str(e)}")
        return {"success": False, "error": str(e)}

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
    provider: str = "emergent"  # emergent, anthropic, bedrock, org_azure
    model: str = "claude-3-7-sonnet-20250219"
    api_key: Optional[str] = None
    aws_config: Optional[Dict[str, str]] = None
    # Organization Azure OpenAI OAuth2 Config
    org_azure_base_url: Optional[str] = None
    org_azure_deployment: Optional[str] = None
    org_azure_api_version: Optional[str] = None
    org_azure_subscription_key: Optional[str] = None
    oauth_auth_url: Optional[str] = None
    oauth_token_url: Optional[str] = None
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    oauth_redirect_uri: Optional[str] = None
    oauth_scopes: Optional[str] = None

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
        
        # Initialize orchestrator based on environment
        if is_docker_desktop():
            # Use dual-mode orchestrator (will use event-driven)
            _langgraph_orchestrator = get_dual_mode_orchestrator(db, manager, _llm_config or {})
            logger.info("🐳 Using DualModeOrchestrator for Docker Desktop")
        else:
            # Use Phase2 orchestrator (sequential)
            _langgraph_orchestrator = get_phase2_orchestrator(db, manager, _llm_config or {})
            logger.info("☸️ Using Phase2Orchestrator for Kubernetes")
        
        # Initialize chat interface
        _chat_interface = ChatInterface(db, llm, _langgraph_orchestrator)
    
    return _chat_interface

# Chat configuration
@api_router.post("/chat/config")
async def set_llm_config(config: LLMConfig):
    """Set LLM provider configuration"""
    global _llm_config, _chat_interface, _langgraph_orchestrator
    
    logger.info("💾 Saving LLM configuration")
    logger.info(f"   Provider: {config.provider}")
    
    config_dict = config.model_dump()
    
    # Transform frontend config to backend format
    if config_dict.get("provider") == "bedrock":
        # Handle Bedrock config
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
        logger.info(f"   Bedrock config saved with region: {aws_config.get('region')}")
    
    elif config_dict.get("provider") == "anthropic":
        # Handle Anthropic API key
        if "anthropic_api_key" in config_dict:
            config_dict["api_key"] = config_dict.pop("anthropic_api_key", "")
        logger.info(f"   Anthropic config saved")
    
    elif config_dict.get("provider") == "org_azure":
        # Handle Organization Azure OpenAI config
        # Note: Azure OpenAI uses deployments, not models
        # The deployment name is what matters, and it's already configured with a model in Azure
        org_azure_config = {
            "base_url": config_dict.pop("org_azure_base_url", ""),
            "deployment": config_dict.pop("org_azure_deployment", ""),
            "api_version": config_dict.pop("org_azure_api_version", ""),
            "subscription_key": config_dict.pop("org_azure_subscription_key", ""),
            "oauth_config": {
                "auth_url": config_dict.pop("oauth_auth_url", ""),
                "token_url": config_dict.pop("oauth_token_url", ""),
                "client_id": config_dict.pop("oauth_client_id", ""),
                "client_secret": config_dict.pop("oauth_client_secret", ""),
                "redirect_uri": config_dict.pop("oauth_redirect_uri", "http://localhost:8001/api/auth/oauth/callback"),
                "scopes": config_dict.pop("oauth_scopes", "")
            }
        }
        config_dict["org_azure_config"] = org_azure_config
        # Don't set config_dict["model"] - deployment handles this
        logger.info(f"   Organization Azure OpenAI config saved")
        logger.info(f"      Base URL: {org_azure_config['base_url']}")
        logger.info(f"      Deployment: {org_azure_config['deployment']}")
        logger.info(f"      API Version: {org_azure_config['api_version']}")
        logger.info(f"      Subscription Key: {'*****' if org_azure_config['subscription_key'] else 'NOT SET'}")
        logger.info(f"      OAuth Config:")
        logger.info(f"         Auth URL: {org_azure_config['oauth_config']['auth_url']}")
        logger.info(f"         Token URL: {org_azure_config['oauth_config']['token_url']}")
        client_id = org_azure_config['oauth_config']['client_id']
        logger.info(f"         Client ID: {client_id[:10] if client_id else 'NOT SET'}...")
        logger.info(f"         Scopes: {org_azure_config['oauth_config']['scopes']}")
    
    _llm_config = config_dict
    
    # Save to database for persistence
    try:
        config_dict["_id"] = "llm_config"  # Use fixed ID for upsert
        config_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.config.update_one(
            {"_id": "llm_config"},
            {"$set": config_dict},
            upsert=True
        )
        logger.info("✅ LLM configuration saved to database")
    except Exception as e:
        logger.error(f"❌ Failed to save config to database: {e}")
        # Continue anyway - at least it's in memory
    
    # Reset chat interface to use new config
    _chat_interface = None
    _langgraph_orchestrator = None
    
    logger.info("✅ LLM configuration saved successfully")
    logger.info(f"   Config keys: {list(_llm_config.keys())}")
    
    return {"status": "success", "message": "LLM configuration updated", "config": _llm_config}

@api_router.get("/chat/config")
async def get_llm_config():
    """Get current LLM configuration"""
    global _llm_config
    
    # Auto-detect Emergent LLM key from environment
    emergent_key = os.getenv("EMERGENT_LLM_KEY")
    
    if _llm_config is None:
        # Try to load from database first
        try:
            stored_config = await db.config.find_one({"_id": "llm_config"})
            if stored_config:
                stored_config.pop("_id", None)
                stored_config.pop("updated_at", None)
                _llm_config = stored_config
                logger.info("✅ Loaded LLM config from database")
                logger.info(f"   Provider: {_llm_config.get('provider')}")
        except Exception as e:
            logger.warning(f"⚠️ Could not load config from database: {e}")
        
        # If still None, initialize with defaults
        if _llm_config is None:
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
    
    # Handle Organization Azure OpenAI config
    if safe_config.get("org_azure_config"):
        org_config = safe_config.pop("org_azure_config")
        safe_config["org_azure_base_url"] = org_config.get("base_url", "")
        safe_config["org_azure_deployment"] = org_config.get("deployment", "")
        safe_config["org_azure_api_version"] = org_config.get("api_version", "2024-02-15-preview")
        safe_config["org_azure_subscription_key"] = "***" if org_config.get("subscription_key") else ""
        
        oauth_config = org_config.get("oauth_config", {})
        safe_config["oauth_auth_url"] = oauth_config.get("auth_url", "")
        safe_config["oauth_token_url"] = oauth_config.get("token_url", "")
        safe_config["oauth_client_id"] = oauth_config.get("client_id", "")
        safe_config["oauth_client_secret"] = "***" if oauth_config.get("client_secret") else ""
        safe_config["oauth_redirect_uri"] = oauth_config.get("redirect_uri", "http://localhost:8001/api/auth/oauth/callback")
        safe_config["oauth_scopes"] = oauth_config.get("scopes", "")
        safe_config["oauth_authenticated"] = False  # Will be updated by OAuth status
    else:
        # Initialize empty Organization Azure OpenAI fields
        safe_config["org_azure_base_url"] = ""
        safe_config["org_azure_deployment"] = ""
        safe_config["org_azure_api_version"] = "2024-02-15-preview"
        safe_config["org_azure_subscription_key"] = ""
        safe_config["oauth_auth_url"] = ""
        safe_config["oauth_token_url"] = ""
        safe_config["oauth_client_id"] = ""
        safe_config["oauth_client_secret"] = ""
        safe_config["oauth_redirect_uri"] = "http://localhost:8001/api/auth/oauth/callback"
        safe_config["oauth_scopes"] = ""
        safe_config["oauth_authenticated"] = False
    
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



# ============================================
# Phase 4: Intelligence & Optimization APIs
# ============================================

# Initialize Phase 4 services
context_manager = get_context_manager()
cost_optimizer = get_cost_optimizer(db)
learning_service = get_learning_service(db)
workspace_service = get_workspace_service(db)
analytics_service = get_analytics_service(db)


# Context Management Endpoints
@api_router.post("/context/check")
async def check_context_limit(messages: List[Dict], model: str = "claude-3-7-sonnet-20250219"):
    """Check context usage for conversation"""
    try:
        cm = get_context_manager(model)
        total_tokens = cm.count_messages_tokens(messages)
        status = cm.check_limit(total_tokens)
        
        return {
            "success": True,
            **status,
            "formatted_status": cm.format_context_status(status)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/context/truncate")
async def truncate_context(
    messages: List[Dict],
    model: str = "claude-3-7-sonnet-20250219",
    strategy: str = "sliding_window"
):
    """Truncate messages to fit within limits"""
    try:
        cm = get_context_manager(model)
        truncated, metadata = cm.truncate_messages(messages, strategy=strategy)
        
        return {
            "success": True,
            "messages": truncated,
            "metadata": metadata
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# Cost Optimizer Endpoints
@api_router.post("/optimizer/select-model")
async def select_optimal_model(
    task_description: str,
    complexity: Optional[float] = None,
    current_model: str = "claude-3-7-sonnet-20250219"
):
    """Get optimal model recommendation for task"""
    try:
        recommendation = cost_optimizer.select_optimal_model(
            task_description, complexity or 0.7, current_model=current_model
        )
        return {"success": True, **recommendation}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/optimizer/cache-stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = cost_optimizer.get_cache_stats()
        return {"success": True, **stats}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/optimizer/budget/{project_id}")
async def get_project_budget(project_id: str):
    """Get budget status for project"""
    try:
        status = await cost_optimizer.get_project_budget_status(project_id)
        return {"success": True, **status}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/optimizer/budget/{project_id}")
async def set_project_budget(
    project_id: str,
    budget_limit: float,
    alert_threshold: float = 0.75
):
    """Set budget for project"""
    try:
        result = await cost_optimizer.set_project_budget(
            project_id, budget_limit, alert_threshold
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/optimizer/analytics")
async def get_cost_analytics(
    project_id: Optional[str] = None,
    timeframe_days: int = 30
):
    """Get cost analytics"""
    try:
        analytics = await cost_optimizer.get_cost_analytics(project_id, timeframe_days)
        return {"success": True, **analytics}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Learning Service Endpoints
@api_router.post("/learning/learn")
async def learn_from_project(
    project_id: str,
    task_description: str,
    tech_stack: List[str],
    success: bool,
    metrics: Dict
):
    """Extract learnings from project"""
    try:
        result = await learning_service.learn_from_project(
            project_id, task_description, tech_stack, success, metrics
        )
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/learning/similar")
async def find_similar_projects(
    task_description: str,
    tech_stack: Optional[List[str]] = None,
    limit: int = 5
):
    """Find similar past projects"""
    try:
        similar = await learning_service.find_similar_projects(
            task_description, tech_stack, limit
        )
        return {"success": True, "similar_projects": similar}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/learning/predict")
async def predict_success(task_description: str, tech_stack: List[str]):
    """Predict success probability"""
    try:
        prediction = await learning_service.predict_success_probability(
            task_description, tech_stack
        )
        return {"success": True, **prediction}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/learning/suggest/{project_id}")
async def suggest_improvements(project_id: str, current_metrics: Dict):
    """Get improvement suggestions"""
    try:
        suggestions = await learning_service.suggest_improvements(
            project_id, current_metrics
        )
        return {"success": True, "suggestions": suggestions}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/learning/stats")
async def get_learning_stats():
    """Get learning system statistics"""
    try:
        stats = await learning_service.get_learning_stats()
        return {"success": True, **stats}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Workspace Endpoints
@api_router.post("/workspaces")
async def create_workspace(
    name: str,
    owner_id: str,
    owner_email: str,
    settings: Optional[Dict] = None
):
    """Create a new workspace"""
    try:
        result = await workspace_service.create_workspace(
            name, owner_id, owner_email, settings
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/workspaces/{workspace_id}")
async def get_workspace(workspace_id: str):
    """Get workspace details"""
    try:
        workspace = await workspace_service.get_workspace(workspace_id)
        if workspace:
            # Remove MongoDB _id field before returning
            if "_id" in workspace:
                del workspace["_id"]
            return {"success": True, "workspace": workspace}
        return {"success": False, "error": "Workspace not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/workspaces/user/{user_id}")
async def list_user_workspaces(user_id: str):
    """List user's workspaces"""
    try:
        workspaces = await workspace_service.list_user_workspaces(user_id)
        # Remove MongoDB _id field from each workspace
        for workspace in workspaces:
            if "_id" in workspace:
                del workspace["_id"]
        return {"success": True, "workspaces": workspaces}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.post("/workspaces/{workspace_id}/invite")
async def invite_member(
    workspace_id: str,
    email: str,
    role: str,
    invited_by: str
):
    """Invite member to workspace"""
    try:
        result = await workspace_service.invite_member(
            workspace_id, email, role, invited_by
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.put("/workspaces/{workspace_id}/members/{user_id}/role")
async def update_member_role(
    workspace_id: str,
    user_id: str,
    new_role: str,
    updated_by: str
):
    """Update member role"""
    try:
        result = await workspace_service.update_member_role(
            workspace_id, user_id, new_role, updated_by
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.delete("/workspaces/{workspace_id}/members/{user_id}")
async def remove_member(
    workspace_id: str,
    user_id: str,
    removed_by: str
):
    """Remove member from workspace"""
    try:
        result = await workspace_service.remove_member(
            workspace_id, user_id, removed_by
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/workspaces/{workspace_id}/analytics")
async def get_workspace_analytics(workspace_id: str):
    """Get workspace analytics"""
    try:
        analytics = await workspace_service.get_workspace_analytics(workspace_id)
        # Analytics already returns clean data
        return {"success": True, **analytics}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Analytics Endpoints
@api_router.post("/analytics/track")
async def track_metric(
    metric_name: str,
    value: float,
    unit: str,
    tags: Optional[Dict] = None
):
    """Track a metric"""
    try:
        await analytics_service.track_metric(metric_name, value, unit, tags)
        return {"success": True, "message": "Metric tracked"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/analytics/performance")
async def get_performance_dashboard(
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    timeframe_days: int = 30
):
    """Get performance dashboard"""
    try:
        data = await analytics_service.get_performance_dashboard(
            user_id, project_id, timeframe_days
        )
        return {"success": True, **data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/analytics/cost")
async def get_cost_dashboard(
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    timeframe_days: int = 30
):
    """Get cost dashboard"""
    try:
        data = await analytics_service.get_cost_dashboard(
            user_id, project_id, timeframe_days
        )
        return {"success": True, **data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/analytics/quality")
async def get_quality_dashboard(
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    timeframe_days: int = 30
):
    """Get quality dashboard"""
    try:
        data = await analytics_service.get_quality_dashboard(
            user_id, project_id, timeframe_days
        )
        return {"success": True, **data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/analytics/insights/{user_id}")
async def get_insights(user_id: str, timeframe_days: int = 30):
    """Get AI-powered insights"""
    try:
        insights = await analytics_service.generate_insights(user_id, timeframe_days)
        return {"success": True, "insights": insights}
    except Exception as e:
        return {"success": False, "error": str(e)}


@api_router.get("/analytics/export")
async def export_analytics(
    format: str = "json",
    user_id: Optional[str] = None,
    timeframe_days: int = 30
):
    """Export analytics data"""
    try:
        result = await analytics_service.export_analytics(format, user_id, timeframe_days)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Catalyst Backend Starting...")
    
    # Log environment
    env_config = get_config()
    logger.info(f"📍 Environment: {env_config['environment']}")
    logger.info(f"🎯 Orchestration Mode: {env_config['orchestration_mode']}")
    
    # Start agent workers in event-driven mode
    if is_docker_desktop():
        logger.info("🐳 Docker Desktop detected - starting agent workers...")
        worker_manager = get_worker_manager(db, manager)
        asyncio.create_task(worker_manager.start_all_workers())
        logger.info("✅ Agent workers started in background")
        
        # Start background scheduler
        from workers.background_scheduler import get_scheduler
        scheduler = get_scheduler()
        await scheduler.start()
        logger.info("✅ Background scheduler started")
    else:
        logger.info("☸️ Kubernetes detected - using sequential mode")

@app.on_event("shutdown")
async def shutdown_db_client():
    """Cleanup on shutdown"""
    # Stop agent workers if running
    if is_docker_desktop():
        worker_manager = get_worker_manager(db, manager)
        await worker_manager.stop_all_workers()
        
        # Stop background scheduler
        from workers.background_scheduler import get_scheduler
        scheduler = get_scheduler()
        await scheduler.stop()
    
    # Close database
    client.close()
    logger.info("✅ Catalyst Backend Shutdown Complete")