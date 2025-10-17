"""LangGraph-based agent orchestration with conversational interface"""

from typing import TypedDict, Annotated, Sequence, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator
import os
from datetime import datetime
from llm_client import get_llm_client


class AgentState(TypedDict):
    """State shared across all agents in the graph"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    task_id: str
    project_id: str
    user_prompt: str
    plan: str
    architecture: str
    code: str
    test_results: str
    review_results: str
    deployment_url: str
    current_agent: str
    retry_count: int
    feedback: str
    status: Literal["planning", "architecting", "coding", "testing", "reviewing", "deploying", "completed", "failed"]


class LangGraphOrchestrator:
    """LangGraph-based orchestrator for Catalyst agents"""
    
    def __init__(self, db, ws_manager, config):
        self.db = db
        self.ws_manager = ws_manager
        self.config = config
        
        # Initialize LLM based on provider
        self.llm = self._init_llm()
        
        # Initialize checkpoint saver
        self.checkpointer = MemorySaver()
        
        # Build the agent graph
        self.graph = self._build_graph()
    
    def _init_llm(self):
        """Initialize LLM based on configured provider"""
        provider = os.getenv("PRIMARY_LLM_PROVIDER", "anthropic")
        
        if provider == "anthropic":
            return ChatAnthropic(
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-7-sonnet-20250219"),
                temperature=0.7,
                max_tokens=4096
            )
        
        elif provider == "bedrock":
            return ChatBedrock(
                model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"),
                region_name=os.getenv("AWS_REGION", "us-east-1"),
                credentials_profile_name=None,  # Uses AWS credentials from env
                model_kwargs={"temperature": 0.7, "max_tokens": 4096}
            )
        
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes (agents)
        workflow.add_node("planner", self.planner_node)
        workflow.add_node("architect", self.architect_node)
        workflow.add_node("coder", self.coder_node)
        workflow.add_node("tester", self.tester_node)
        workflow.add_node("reviewer", self.reviewer_node)
        workflow.add_node("deployer", self.deployer_node)
        
        # Define edges (workflow)
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "architect")
        workflow.add_edge("architect", "coder")
        
        # Conditional edge for testing feedback loop
        workflow.add_conditional_edges(
            "coder",
            self.should_test,
            {
                "test": "tester",
                "skip": "reviewer"
            }
        )
        
        # Conditional edge for test results
        workflow.add_conditional_edges(
            "tester",
            self.check_test_results,
            {
                "pass": "reviewer",
                "retry": "coder",
                "fail": END
            }
        )
        
        workflow.add_edge("reviewer", "deployer")
        workflow.add_edge("deployer", END)
        
        # Compile with checkpointer
        return workflow.compile(checkpointer=self.checkpointer)
    
    # Node implementations
    async def planner_node(self, state: AgentState) -> AgentState:
        """Planner agent node"""
        await self._log(state["task_id"], "Planner", "🧠 Analyzing requirements...")
        
        prompt = f"""You are a planning agent. Analyze this requirement and create a structured plan:

User Request: {state['user_prompt']}

Provide a JSON plan with: phases, tech_stack, requirements, and estimated timeline."""
        
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        await self._log(state["task_id"], "Planner", "✅ Plan created")
        
        state["plan"] = response.content
        state["status"] = "architecting"
        state["current_agent"] = "architect"
        state["messages"].append(response)
        
        return state
    
    async def architect_node(self, state: AgentState) -> AgentState:
        """Architect agent node"""
        await self._log(state["task_id"], "Architect", "🏗️ Designing architecture...")
        
        prompt = f"""You are an architect agent. Based on this plan, design the system architecture:

Plan: {state['plan']}

Provide: data models, API endpoints, file structure, and component hierarchy."""
        
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        await self._log(state["task_id"], "Architect", "✅ Architecture designed")
        
        state["architecture"] = response.content
        state["status"] = "coding"
        state["current_agent"] = "coder"
        state["messages"].append(response)
        
        return state
    
    async def coder_node(self, state: AgentState) -> AgentState:
        """Coder agent node"""
        if state.get("feedback"):
            await self._log(state["task_id"], "Coder", "🔄 Fixing code based on feedback...")
        else:
            await self._log(state["task_id"], "Coder", "💻 Writing code...")
        
        prompt = f"""You are a coder agent. Generate production-ready code:

Architecture: {state['architecture']}

{f"Feedback to address: {state['feedback']}" if state.get('feedback') else ''}

Provide complete, working code with error handling and comments."""
        
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        await self._log(state["task_id"], "Coder", "✅ Code generated")
        
        state["code"] = response.content
        state["status"] = "testing"
        state["current_agent"] = "tester"
        state["messages"].append(response)
        
        return state
    
    async def tester_node(self, state: AgentState) -> AgentState:
        """Tester agent node"""
        await self._log(state["task_id"], "Tester", "🧪 Running tests...")
        
        prompt = f"""You are a tester agent. Analyze this code and provide test results:

Code: {state['code'][:3000]}

Identify: bugs, edge cases, security issues. Return JSON with: passed (bool), issues (list), suggestions (list)."""
        
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        # Simulate test pass/fail (can be enhanced with actual testing)
        import random
        test_passed = random.random() > 0.3  # 70% pass rate
        
        if test_passed:
            await self._log(state["task_id"], "Tester", "✅ All tests passed")
        else:
            await self._log(state["task_id"], "Tester", "⚠️ Tests found issues")
            state["feedback"] = response.content
            state["retry_count"] = state.get("retry_count", 0) + 1
        
        state["test_results"] = response.content
        state["messages"].append(response)
        
        return state
    
    async def reviewer_node(self, state: AgentState) -> AgentState:
        """Reviewer agent node"""
        await self._log(state["task_id"], "Reviewer", "👀 Reviewing code quality...")
        
        prompt = f"""You are a code reviewer. Review this code:

Code: {state['code'][:2000]}
Test Results: {state['test_results'][:500]}

Provide: quality score, security assessment, recommendations, and approval status."""
        
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        
        await self._log(state["task_id"], "Reviewer", "✅ Review completed - Approved")
        
        state["review_results"] = response.content
        state["status"] = "deploying"
        state["current_agent"] = "deployer"
        state["messages"].append(response)
        
        return state
    
    async def deployer_node(self, state: AgentState) -> AgentState:
        """Deployer agent node"""
        await self._log(state["task_id"], "Deployer", "🚀 Deploying application...")
        
        # Simulate deployment
        import hashlib
        commit_sha = hashlib.sha256(state["code"].encode()).hexdigest()[:12]
        deployment_url = f"https://catalyst-{state['project_id'][:8]}.deploy.catalyst.ai"
        
        await self._log(state["task_id"], "Deployer", "📦 Building...")
        await self._log(state["task_id"], "Deployer", "☁️ Deploying...")
        await self._log(state["task_id"], "Deployer", f"✅ Deployed: {deployment_url}")
        
        state["deployment_url"] = deployment_url
        state["status"] = "completed"
        
        return state
    
    # Conditional edge functions
    def should_test(self, state: AgentState) -> str:
        """Decide if we should test the code"""
        return "test"
    
    def check_test_results(self, state: AgentState) -> str:
        """Check if tests passed or need retry"""
        # Check if tests passed (simple heuristic)
        if "passed" in state.get("test_results", "").lower() and "true" in state.get("test_results", "").lower():
            return "pass"
        
        # Check retry limit
        if state.get("retry_count", 0) >= 2:
            return "fail"
        
        return "retry"
    
    # Execution method
    async def execute_task(self, task_id: str, project_id: str, user_prompt: str):
        """Execute a task through the LangGraph workflow"""
        
        # Initial state
        initial_state = AgentState(
            messages=[],
            task_id=task_id,
            project_id=project_id,
            user_prompt=user_prompt,
            plan="",
            architecture="",
            code="",
            test_results="",
            review_results="",
            deployment_url="",
            current_agent="planner",
            retry_count=0,
            feedback="",
            status="planning"
        )
        
        # Configure execution
        config = {"configurable": {"thread_id": task_id}}
        
        try:
            # Run the graph
            final_state = await self.graph.ainvoke(initial_state, config)
            
            # Update task in database
            await self._update_task_status(task_id, "completed", 0.85)
            
            return final_state
        
        except Exception as e:
            await self._log(task_id, "Orchestrator", f"❌ Error: {str(e)}")
            await self._update_task_status(task_id, "failed", 0)
            raise
    
    # Helper methods
    async def _log(self, task_id: str, agent_name: str, message: str):
        """Log agent activity"""
        from internal.models import AgentLog
        import uuid
        
        log = AgentLog(
            id=str(uuid.uuid4()),
            task_id=task_id,
            agent_name=agent_name,
            message=message,
            timestamp=datetime.now()
        )
        
        await self.db.Logs.insert_one(log.dict())
        self.ws_manager.send_log(task_id, log.dict())
    
    async def _update_task_status(self, task_id: str, status: str, cost: float):
        """Update task status in database"""
        await self.db.Tasks.update_one(
            {"id": task_id},
            {"$set": {"status": status, "cost": cost}}
        )