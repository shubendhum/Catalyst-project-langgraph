"""
Event-Driven Agents Module (Version 2)
Agents with event streaming capabilities for Docker Desktop environment
"""

from agents_v2.base_agent import EventDrivenAgent
from agents_v2.planner_agent_v2 import EventDrivenPlannerAgent, get_event_driven_planner
from agents_v2.architect_agent_v2 import EventDrivenArchitectAgent, get_event_driven_architect
from agents_v2.coder_agent_v2 import EventDrivenCoderAgent, get_event_driven_coder
from agents_v2.tester_agent_v2 import EventDrivenTesterAgent, get_event_driven_tester
from agents_v2.reviewer_agent_v2 import EventDrivenReviewerAgent, get_event_driven_reviewer
from agents_v2.deployer_agent_v2 import EventDrivenDeployerAgent, get_event_driven_deployer

__all__ = [
    'EventDrivenAgent',
    'EventDrivenPlannerAgent',
    'EventDrivenArchitectAgent',
    'EventDrivenCoderAgent',
    'EventDrivenTesterAgent',
    'EventDrivenReviewerAgent',
    'EventDrivenDeployerAgent',
    'get_event_driven_planner',
    'get_event_driven_architect',
    'get_event_driven_coder',
    'get_event_driven_tester',
    'get_event_driven_reviewer',
    'get_event_driven_deployer'
]
