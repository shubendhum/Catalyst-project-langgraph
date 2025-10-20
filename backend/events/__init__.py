"""
Event System Module
Provides event-driven communication for Catalyst agents
"""

from events.schemas import (
    AgentEvent,
    AgentType,
    EventType,
    PlanCreatedPayload,
    ArchitectureProposedPayload,
    CodePROpenedPayload,
    TestResultsPayload,
    ReviewDecisionPayload,
    DeployStatusPayload,
    ExplorerFindingsPayload,
    TaskProgressPayload,
    create_plan_created_event,
    create_architecture_proposed_event,
    create_code_pr_opened_event,
    create_test_results_event,
    create_review_decision_event,
    create_deploy_status_event
)

from events.publisher import EventPublisher, get_event_publisher
from events.consumer import EventConsumer, create_consumer_for_agent

__all__ = [
    'AgentEvent',
    'AgentType',
    'EventType',
    'PlanCreatedPayload',
    'ArchitectureProposedPayload',
    'CodePROpenedPayload',
    'TestResultsPayload',
    'ReviewDecisionPayload',
    'DeployStatusPayload',
    'ExplorerFindingsPayload',
    'TaskProgressPayload',
    'create_plan_created_event',
    'create_architecture_proposed_event',
    'create_code_pr_opened_event',
    'create_test_results_event',
    'create_review_decision_event',
    'create_deploy_status_event',
    'EventPublisher',
    'get_event_publisher',
    'EventConsumer',
    'create_consumer_for_agent'
]
