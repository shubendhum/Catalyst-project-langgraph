# LLM Cost Optimization Strategy for Catalyst Platform

## Executive Summary

**Current State**: All agents use LLM calls without cost optimization  
**Estimated Cost**: $8-10 per project (based on current usage)  
**Target Cost**: $3-5 per project (50-60% reduction)  
**Implementation**: Integrate Cost Optimizer into all agent LLM calls

---

## Current LLM Usage Analysis

### Agents Using LLM

| Agent | LLM Calls per Task | Avg Tokens | Current Cost | Use Case |
|-------|-------------------|------------|--------------|----------|
| **Planner** | 1-2 | 2,000-4,000 | $0.20-0.40 | Architecture planning |
| **Architect** | 1-2 | 3,000-5,000 | $0.30-0.50 | System design |
| **Coder** | 3-5 | 5,000-10,000 | $1.50-3.00 | Code generation |
| **Tester** | 2-4 | 3,000-6,000 | $0.60-1.20 | Test generation |
| **Reviewer** | 1-2 | 2,000-4,000 | $0.20-0.40 | Code review |
| **Deployer** | 1-2 | 1,500-3,000 | $0.15-0.30 | Deployment config |
| **Explorer** | 1-3 | 2,000-5,000 | $0.20-0.50 | Repo analysis |
| **Chat Interface** | Variable | 1,000-5,000 | $0.10-0.50 | User interaction |

**Total per Project**: 12-21 LLM calls, ~25,000-50,000 tokens, **$3.25-6.70**

### Cost Breakdown by Model

**Current Default**: Claude 3.7 Sonnet ($3/1M tokens)
- Small task (5K tokens): $0.015
- Medium task (10K tokens): $0.030
- Large task (50K tokens): $0.150

**Potential with Optimization**:
- GPT-4o-mini ($0.15/1M tokens): **95% cheaper**
- GPT-4o ($5/1M tokens): 40% cheaper for complex tasks
- Selective model use: **50-60% overall savings**

---

## Cost Optimization Opportunities

### 1. **Smart Caching** (30-40% savings)

**Current**: No caching between agents
**Optimized**: Cache similar prompts

**High-Value Caching Scenarios**:
```python
# Planner Agent
"Create a plan for building a [React + FastAPI] app"
# Similar requests within 1 hour → Cache hit

# Coder Agent  
"Generate authentication code for FastAPI with JWT"
# Common patterns → Cache hit rate: 25-30%

# Tester Agent
"Generate test cases for CRUD API"
# Standard tests → Cache hit rate: 40-50%
```

**Estimated Savings**: 
- Cache hit rate: 25% average
- Cost reduction: **30-40%**

### 2. **Intelligent Model Selection** (40-50% savings)

**Current**: All agents use Claude 3.7 Sonnet
**Optimized**: Match model to task complexity

| Task Type | Current Model | Optimal Model | Savings |
|-----------|--------------|---------------|---------|
| Simple bug fix | Claude Sonnet ($3/1M) | GPT-4o-mini ($0.15/1M) | **95%** |
| Boilerplate code | Claude Sonnet | GPT-4o-mini | **95%** |
| Standard tests | Claude Sonnet | GPT-4o-mini | **95%** |
| Config generation | Claude Sonnet | GPT-4o-mini | **95%** |
| Complex architecture | Claude Sonnet | Claude Sonnet | 0% |
| Security review | Claude Sonnet | GPT-4o ($5/1M) | -40% |

**Task Complexity Distribution**:
- Simple (30%): Use GPT-4o-mini → 95% savings
- Medium (50%): Use GPT-4o → 40% savings  
- Complex (20%): Use Claude Sonnet → No change

**Weighted Average Savings**: **40-50%**

### 3. **Prompt Optimization** (10-15% savings)

**Current**: Verbose prompts with examples
**Optimized**: Concise, structured prompts

```python
# Before (3,000 tokens)
"""
You are a helpful coding assistant. I need you to help me create...
Here are some examples of what I mean:
Example 1: ...
Example 2: ...
Please follow these guidelines:
1. ...
2. ...
...
"""

# After (2,000 tokens) - 33% reduction
"""
Generate FastAPI endpoint:
- Function: user_login
- Input: email, password
- Output: JWT token
- Include: validation, error handling
"""
```

**Estimated Savings**: 10-15% token reduction

### 4. **Context Window Management** (15-20% savings)

**Current**: Include full conversation history
**Optimized**: Truncate old messages, keep essentials

```python
# Already implemented in Phase 4
# - Warning at 75% context usage
# - Auto-truncate at 85%
# - Smart truncation strategies
```

**Estimated Savings**: 15-20% on multi-turn conversations

### 5. **Streaming & Early Termination** (5-10% savings)

**Current**: Wait for full response
**Optimized**: Stream and stop when sufficient

```python
# Stop after getting enough code
if code_complete(streamed_response):
    stop_generation()
    # Save tokens on remaining response
```

**Estimated Savings**: 5-10% on code generation

### 6. **Template-Based Generation** (20-30% savings)

**Current**: LLM generates everything from scratch
**Optimized**: Use templates for common patterns

```python
# No LLM call needed for:
- Standard CRUD endpoints (use templates)
- Common authentication patterns
- Standard test structures
- Deployment configs

# LLM only customizes specific parts
```

**Estimated Savings**: 20-30% on boilerplate

---

## Implementation Plan

### Phase 1: Integrate Cost Optimizer (Week 1-2)

**Create Optimized LLM Client Wrapper**:

```python
# /app/backend/services/optimized_llm_client.py

from services.cost_optimizer import get_cost_optimizer
from services.context_manager import get_context_manager
from llm_client import UnifiedLLMClient
import logging

logger = logging.getLogger(__name__)

class OptimizedLLMClient:
    """Wrapper around LLM client with cost optimization"""
    
    def __init__(self, db=None, project_id=None):
        self.db = db
        self.project_id = project_id
        self.cost_optimizer = get_cost_optimizer(db)
        self.context_manager = get_context_manager()
        self.base_client = None
        
    async def ainvoke(
        self,
        messages,
        task_description="",
        complexity=None,
        use_cache=True,
        temperature=0.7
    ):
        """
        Optimized LLM invocation with:
        - Smart caching
        - Model selection
        - Token tracking
        - Budget checking
        """
        
        # 1. Check cache first
        if use_cache:
            prompt = self._messages_to_prompt(messages)
            cached = self.cost_optimizer.get_cached_response(
                prompt, 
                self.get_model(),
                temperature
            )
            if cached:
                logger.info(f"💰 Cache hit! Saved ${cached['cost_saved']:.4f}")
                return cached["response"]
        
        # 2. Select optimal model based on complexity
        if complexity is None:
            complexity = self._estimate_complexity(task_description)
        
        model_recommendation = self.cost_optimizer.select_optimal_model(
            task_description,
            complexity,
            current_model=self.get_model()
        )
        
        optimal_model = model_recommendation["recommended_model"]
        
        # Log if using cheaper model
        if optimal_model != self.get_model():
            savings_pct = model_recommendation["estimated_savings_percent"]
            logger.info(f"💡 Using {optimal_model} (saves {savings_pct:.1f}%)")
        
        # 3. Check budget
        if self.project_id:
            budget_status = await self.cost_optimizer.get_project_budget_status(
                self.project_id
            )
            if budget_status.get("status") == "exceeded":
                raise Exception("Project budget exceeded!")
        
        # 4. Check context limit
        tokens = self.context_manager.count_messages_tokens(messages)
        status = self.context_manager.check_limit(tokens)
        
        if status["status"] == "critical":
            # Truncate messages
            messages, metadata = self.context_manager.truncate_messages(messages)
            logger.warning(f"⚠️ Truncated {metadata['messages_removed']} messages")
        
        # 5. Initialize client with optimal model
        self.base_client = UnifiedLLMClient(
            provider=self._get_provider(optimal_model),
            model=optimal_model
        )
        
        # 6. Make LLM call
        try:
            response = await self.base_client.ainvoke(messages)
            
            # 7. Track usage and cost
            tokens_used = self._estimate_tokens(messages, response)
            cost = self.cost_optimizer.calculate_cost(tokens_used, optimal_model)
            
            if self.project_id:
                await self.cost_optimizer.track_usage(
                    self.project_id,
                    "task_id_here",
                    optimal_model,
                    tokens_used,
                    cost
                )
            
            # 8. Cache response
            if use_cache:
                self.cost_optimizer.cache_response(
                    self._messages_to_prompt(messages),
                    optimal_model,
                    response.content if hasattr(response, 'content') else str(response),
                    tokens_used,
                    temperature
                )
            
            logger.info(f"📊 Cost: ${cost:.4f}, Tokens: {tokens_used}, Model: {optimal_model}")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _estimate_complexity(self, task_description):
        """Estimate task complexity from description"""
        # Use cost_optimizer's complexity estimation
        if "simple" in task_description.lower() or "fix" in task_description.lower():
            return 0.3
        elif "complex" in task_description.lower() or "architecture" in task_description.lower():
            return 0.9
        else:
            return 0.6
    
    def _messages_to_prompt(self, messages):
        """Convert messages to cache key"""
        return " ".join([m.content if hasattr(m, 'content') else str(m) for m in messages])
    
    def _get_provider(self, model):
        """Determine provider from model name"""
        if "gpt" in model.lower():
            return "emergent"  # Or "openai"
        elif "claude" in model.lower():
            return "emergent"  # Or "anthropic"
        else:
            return "emergent"
    
    def _estimate_tokens(self, messages, response):
        """Estimate token count"""
        prompt_tokens = self.context_manager.count_messages_tokens(messages)
        response_tokens = self.context_manager.count_tokens(
            response.content if hasattr(response, 'content') else str(response)
        )
        return prompt_tokens + response_tokens
    
    def get_model(self):
        """Get current model"""
        if self.base_client:
            return self.base_client.model
        return "claude-3-7-sonnet-20250219"  # Default
```

**Update All Agents**:

```python
# Before (in each agent)
from llm_client import get_llm_client

class CoderAgent:
    def __init__(self, llm_client, ...):
        self.llm_client = llm_client
    
    async def generate_code(self, ...):
        response = await self.llm_client.ainvoke([HumanMessage(...)])

# After
from services.optimized_llm_client import OptimizedLLMClient

class CoderAgent:
    def __init__(self, db, project_id, ...):
        self.llm_client = OptimizedLLMClient(db, project_id)
    
    async def generate_code(self, ...):
        response = await self.llm_client.ainvoke(
            messages=[HumanMessage(...)],
            task_description="Generate authentication code",
            complexity=0.5,  # Medium complexity
            use_cache=True
        )
```

### Phase 2: Add Budget Controls (Week 3)

```python
# Set project budget when creating project
await cost_optimizer.set_project_budget(
    project_id="proj_123",
    budget_limit=10.00,  # $10 max
    alert_threshold=0.75  # Alert at $7.50
)

# Budget is automatically checked before each LLM call
# Raises exception if exceeded
```

### Phase 3: Implement Template Library (Week 4)

```python
# /app/backend/templates/code_templates.py

TEMPLATES = {
    "fastapi_crud": """
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

@router.get("/{resource_name}/")
async def get_all():
    # TODO: Implement
    pass

@router.post("/{resource_name}/")
async def create(item: {ItemModel}):
    # TODO: Implement
    pass
""",
    # More templates...
}

# Use in Coder Agent
if is_standard_pattern(task):
    # Use template (no LLM call)
    code = TEMPLATES[pattern_name].format(**params)
else:
    # Use LLM for custom code
    code = await llm.generate_code(task)
```

### Phase 4: Add Monitoring Dashboard (Week 5)

```python
# Real-time cost monitoring
GET /api/optimizer/dashboard/{project_id}

{
  "total_cost": 3.45,
  "budget": 10.00,
  "usage_percent": 34.5,
  "breakdown": {
    "planner": 0.25,
    "coder": 2.10,
    "tester": 0.85,
    "reviewer": 0.25
  },
  "cache_savings": 1.20,
  "model_optimization_savings": 0.80
}
```

---

## Expected Results

### Cost Reduction Breakdown

| Optimization | Savings | Cumulative |
|--------------|---------|------------|
| **Baseline** | - | $8.00 |
| Smart Caching | 30% | $5.60 |
| Model Selection | 40% on remaining | $3.36 |
| Prompt Optimization | 10% on remaining | $3.02 |
| Context Management | 5% on remaining | $2.87 |
| Templates | 15% on remaining | $2.44 |
| **Total Savings** | **69.5%** | **$2.44** |

### ROI Analysis

**Current State**:
- Average project: 100 API calls, $8.00
- Monthly (1000 projects): $8,000

**After Optimization**:
- Average project: 100 API calls, $2.44
- Monthly (1000 projects): $2,440
- **Monthly Savings**: $5,560
- **Annual Savings**: $66,720

**Implementation Cost**:
- Development time: 5 weeks
- **Payback period**: Less than 1 week

---

## Quick Wins (Immediate Implementation)

### 1. Enable Caching (1 day)
```python
# Add to all agent calls
response = await llm.ainvoke(messages, use_cache=True)
```
**Savings**: 25-30%

### 2. Use Cheaper Models for Simple Tasks (2 days)
```python
# Update agents to specify complexity
if task_is_simple:
    response = await llm.ainvoke(
        messages,
        complexity=0.3  # Will use gpt-4o-mini
    )
```
**Savings**: 40-50% on simple tasks (30% of all tasks)

### 3. Add Budget Limits (1 day)
```python
# Prevent runaway costs
await cost_optimizer.set_project_budget(project_id, budget_limit=10.0)
```
**Protection**: Prevent cost overruns

---

## Monitoring & Alerts

### Cost Alerts

```python
# Alert when approaching budget
if budget_usage > 0.75:
    send_alert("Budget 75% used")

# Alert on expensive calls
if single_call_cost > 0.50:
    send_alert(f"Expensive call: ${single_call_cost}")

# Daily cost reports
async def generate_daily_report():
    return {
        "date": today,
        "total_cost": daily_total,
        "projects": project_costs,
        "savings": cache_savings + model_savings
    }
```

### Analytics

```python
# Track optimization effectiveness
GET /api/optimizer/effectiveness

{
  "cache_hit_rate": 28.5,
  "model_optimization_rate": 35.0,
  "average_savings_per_project": 5.56,
  "total_savings_this_month": 5560.00
}
```

---

## Best Practices

1. **Always specify task complexity** for optimal model selection
2. **Enable caching** for all non-unique requests
3. **Set project budgets** to prevent overruns
4. **Monitor cost per agent** to identify optimization opportunities
5. **Use templates** for common patterns
6. **Optimize prompts** to reduce token count
7. **Stream responses** and stop early when possible
8. **Review cost analytics** weekly

---

## Migration Path

### Week 1: Setup
- Create OptimizedLLMClient wrapper
- Add to one agent (Tester) as pilot
- Test and measure savings

### Week 2: Rollout
- Add to all agents
- Update orchestrators
- Enable monitoring

### Week 3: Optimize
- Fine-tune complexity thresholds
- Add templates for common patterns
- Optimize prompt engineering

### Week 4: Monitor
- Analyze results
- Adjust budgets
- Document best practices

---

## Success Metrics

**Target Metrics**:
- ✅ 50-70% cost reduction
- ✅ <$3 per project average
- ✅ 25%+ cache hit rate
- ✅ 90%+ budget compliance
- ✅ No quality degradation

**Quality Checks**:
- Code quality score maintained (>85)
- Task success rate maintained (>90%)
- User satisfaction maintained (>4.5/5)

---

*This strategy can save $66K+ annually while maintaining quality!*
