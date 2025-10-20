"""
Event System for Catalyst
Handles event-driven communication between agents
"""
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
import json

# Agent types
AgentType = Literal[
    "orchestrator",
    "planner", 
    "architect",
    "coder",
    "tester",
    "reviewer",
    "deployer",
    "explorer"
]

# Event types
EventType = Literal[
    "task.initiated",
    "plan.created",
    "architecture.proposed",
    "code.pr.opened",
    "test.results",
    "review.decision",
    "deploy.status",
    "deploy.complete",
    "explorer.findings",
    "task.progress",
    "task.failed"
]


class AgentEvent(BaseModel):
    """
    Base event schema for all agent communications
    Version: v1
    """
    version: Literal["v1"] = "v1"
    trace_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    actor: AgentType
    event_type: str  # {actor}.{action} format
    repo: str  # Repository identifier
    branch: str = "main"
    commit: str = ""  # Git commit SHA
    timestamp: datetime = Field(default_factory=lambda: datetime.utcnow())
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
    
    def to_routing_key(self) -> str:
        """Convert event to RabbitMQ routing key"""
        return f"catalyst.{self.event_type}"
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return self.model_dump_json()
    
    @classmethod
    def from_json(cls, json_str: str) -> 'AgentEvent':
        """Deserialize from JSON"""
        return cls.model_validate_json(json_str)


# Specific event payload schemas

class PlanCreatedPayload(BaseModel):
    """Payload for plan.created event"""
    plan_ref: str  # Git reference to plan.yaml
    feature_count: int
    task_count: int
    api_endpoint_count: int
    estimated_hours: int
    risk_level: Literal["low", "medium", "high"]
    complexity_score: float  # 0-1


class ArchitectureProposedPayload(BaseModel):
    """Payload for architecture.proposed event"""
    architecture_ref: str  # Git reference to architecture/
    tech_stack: Dict[str, str]
    data_model_count: int
    api_endpoint_count: int
    adrs_created: int
    requires_review: bool = False


class CodePROpenedPayload(BaseModel):
    """Payload for code.pr.opened event"""
    branch: str
    commit: str
    files_created: int
    lines_of_code: int
    backend_files: int
    frontend_files: int
    test_files: int
    estimated_coverage: float
    pr_url: Optional[str] = None
    local_repo: str
    git_diff_summary: Dict[str, int]


class TestResultsPayload(BaseModel):
    """Payload for test.results event"""
    status: Literal["passed", "failed", "partial"]
    total_tests: int
    passed: int
    failed: int
    skipped: int = 0
    coverage: float
    security_critical_issues: int
    artifacts_refs: list[str]
    test_duration_seconds: float


class ReviewDecisionPayload(BaseModel):
    """Payload for review.decision event"""
    decision: Literal["approved", "rejected", "needs_changes"]
    overall_score: int  # 0-100
    breakdown: Dict[str, int]
    blocking_issues: int
    recommendations: list[str]
    artifacts: list[str]


class DeployStatusPayload(BaseModel):
    """Payload for deploy.status event"""
    status: Literal["deploying", "deployed", "failed", "rollback"]
    deployment_mode: Literal["docker_in_docker", "compose_only", "traefik"]
    preview_url: Optional[str] = None
    fallback_url: Optional[str] = None
    backend_url: Optional[str] = None
    container_ids: list[str] = Field(default_factory=list)
    health: Literal["healthy", "unhealthy", "unknown"] = "unknown"
    error: Optional[str] = None


class ExplorerFindingsPayload(BaseModel):
    """Payload for explorer.findings event"""
    scan_id: UUID
    scan_type: Literal["github", "deployment", "database"]
    target: str
    can_replicate: bool
    tech_stack: list[str]
    similarity_score: float  # 0-1
    suggested_tasks: list[str]
    findings_ref: str  # File reference to full findings


class TaskProgressPayload(BaseModel):
    """Payload for task.progress event"""
    phase: str
    progress: float  # 0-1
    message: str
    files_created: Optional[int] = None
    estimated_completion_seconds: Optional[int] = None


# Helper functions to create typed events

def create_plan_created_event(
    task_id: UUID,
    trace_id: UUID,
    repo: str,
    commit: str,
    payload: PlanCreatedPayload
) -> AgentEvent:
    """Create a plan.created event"""
    return AgentEvent(
        trace_id=trace_id,
        task_id=task_id,
        actor="planner",
        event_type="plan.created",
        repo=repo,
        branch="main",
        commit=commit,
        payload=payload.model_dump()
    )


def create_architecture_proposed_event(
    task_id: UUID,
    trace_id: UUID,
    repo: str,
    commit: str,
    payload: ArchitectureProposedPayload
) -> AgentEvent:
    """Create an architecture.proposed event"""
    return AgentEvent(
        trace_id=trace_id,
        task_id=task_id,
        actor="architect",
        event_type="architecture.proposed",
        repo=repo,
        branch="main",
        commit=commit,
        payload=payload.model_dump()
    )


def create_code_pr_opened_event(
    task_id: UUID,
    trace_id: UUID,
    repo: str,
    branch: str,
    commit: str,
    payload: CodePROpenedPayload
) -> AgentEvent:
    """Create a code.pr.opened event"""
    return AgentEvent(
        trace_id=trace_id,
        task_id=task_id,
        actor="coder",
        event_type="code.pr.opened",
        repo=repo,
        branch=branch,
        commit=commit,
        payload=payload.model_dump()
    )


def create_test_results_event(
    task_id: UUID,
    trace_id: UUID,
    repo: str,
    branch: str,
    payload: TestResultsPayload
) -> AgentEvent:
    """Create a test.results event"""
    return AgentEvent(
        trace_id=trace_id,
        task_id=task_id,
        actor="tester",
        event_type="test.results",
        repo=repo,
        branch=branch,
        payload=payload.model_dump()
    )


def create_review_decision_event(
    task_id: UUID,
    trace_id: UUID,
    repo: str,
    branch: str,
    payload: ReviewDecisionPayload
) -> AgentEvent:
    """Create a review.decision event"""
    return AgentEvent(
        trace_id=trace_id,
        task_id=task_id,
        actor="reviewer",
        event_type="review.decision",
        repo=repo,
        branch=branch,
        payload=payload.model_dump()
    )


def create_deploy_status_event(
    task_id: UUID,
    trace_id: UUID,
    repo: str,
    branch: str,
    payload: DeployStatusPayload
) -> AgentEvent:
    """Create a deploy.status event"""
    return AgentEvent(
        trace_id=trace_id,
        task_id=task_id,
        actor="deployer",
        event_type="deploy.status",
        repo=repo,
        branch=branch,
        payload=payload.model_dump()
    )
