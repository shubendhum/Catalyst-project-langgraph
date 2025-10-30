# Docker Desktop Architecture Review
## Comprehensive Analysis of Catalyst Event-Driven Architecture

**Review Date:** Current Session  
**Environment:** Docker Desktop (Local Development)  
**Focus:** Agent task pickup and event-driven orchestration

---

## Executive Summary

**Status:** 🔴 **CRITICAL ISSUES FOUND** - Agents not picking up tasks due to RabbitMQ infrastructure not being initialized

### Critical Issues Identified:
1. **RabbitMQ Initialization Script Not Executing** - Queues, exchanges, and bindings never created
2. **Startup Timing Issues** - Backend may start before RabbitMQ is fully ready
3. **Postgres Event Logging Failures** - May cause event publishing to fail silently

### Components Reviewed:
- ✅ Environment Detection Logic
- ✅ Orchestration Mode Selection
- ✅ Agent Worker Manager
- ✅ Event Publisher & Consumer
- ✅ RabbitMQ Configuration
- ⚠️ **RabbitMQ Infrastructure Initialization** (BROKEN)
- ✅ Docker Compose Dependencies

---

## Detailed Findings

### 1. Environment Detection ✅ CORRECT

**File:** `/app/backend/config/environment.py`

**Analysis:**
- Environment detection uses multiple fallback methods:
  1. `ENVIRONMENT` env var (explicitly set to "docker_desktop" in docker-compose.artifactory.yml:85)
  2. Kubernetes secret files check
  3. `COMPOSE_PROJECT_NAME` detection
  4. Docker socket presence
  5. `.dockerenv` file

**Verdict:** ✅ **Working correctly** - Docker Desktop should be detected properly

**Configuration:**
```yaml
# docker-compose.artifactory.yml:85
- ENVIRONMENT=docker_desktop
- ORCHESTRATION_MODE=event_driven
```

**Evidence:**
```python
def detect_environment() -> EnvironmentType:
    # Priority 1: Check for explicit environment variable
    explicit_env = os.getenv("ENVIRONMENT")
    if explicit_env == "docker_desktop":
        return "docker_desktop"
    # ... additional fallbacks
```

---

### 2. Orchestration Mode ✅ CORRECT

**Configuration:**
- Docker Desktop → `event_driven` mode
- Kubernetes → `sequential` mode

**Startup Logic (server.py:1752-1776):**
```python
@app.on_event("startup")
async def startup_event():
    # Log environment
    env_config = get_config()
    logger.info(f"📍 Environment: {env_config['environment']}")
    logger.info(f"🎯 Orchestration Mode: {env_config['orchestration_mode']}")
    
    # Start agent workers in event-driven mode
    if is_docker_desktop():
        logger.info("🐳 Docker Desktop detected - starting agent workers...")
        worker_manager = get_worker_manager(db, manager)
        asyncio.create_task(worker_manager.start_all_workers())
```

**Verdict:** ✅ **Logic is correct** - Should start agent workers in Docker Desktop mode

---

### 3. Agent Worker Manager ✅ CORRECT

**File:** `/app/backend/workers/agent_worker_manager.py`

**Worker Startup Process:**
1. Creates all event-driven agents (planner, architect, coder, tester, reviewer, deployer)
2. Starts each agent in its own asyncio task
3. Each task runs `agent.start_listening()` in a thread pool (to avoid blocking HTTP server)

**Code:**
```python
async def start_all_workers(self):
    agents = [
        get_event_driven_planner(self.db, self.manager, llm_client),
        get_event_driven_architect(self.db, self.manager, llm_client),
        # ... other agents
    ]
    
    for agent in agents:
        worker_task = asyncio.create_task(self._run_agent_worker(agent))
        self.workers.append(worker_task)

async def _run_agent_worker(self, agent):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, agent.start_listening)
```

**Verdict:** ✅ **Implementation is correct** - Uses thread pool to prevent blocking

---

### 4. Event Flow ✅ CORRECT DESIGN

**Event Chain:**
1. User sends task → `DualModeOrchestrator.execute_task()`
2. Orchestrator creates `AgentEvent` with `event_type="task.initiated"`
3. Event converted to routing key: `"catalyst.task.initiated"`
4. Published to RabbitMQ exchange `"catalyst.events"`
5. Planner agent listens on queue bound to routing key `"catalyst.task.initiated"`
6. Planner processes and publishes `"catalyst.plan.created"`
7. Architect agent picks up and continues chain...

**Routing Key Mapping (consumer.py:193-209):**
```python
routing_keys_map = {
    "planner": ["catalyst.task.initiated"],
    "architect": ["catalyst.plan.created"],
    "coder": ["catalyst.architecture.proposed"],
    "tester": ["catalyst.code.pr.opened"],
    "reviewer": ["catalyst.test.results"],
    "deployer": ["catalyst.review.decision"],
}
```

**Event to Routing Key Conversion (schemas.py:62-64):**
```python
def to_routing_key(self) -> str:
    return f"catalyst.{self.event_type}"
```

**Verdict:** ✅ **Routing keys match correctly** - No mismatch issues

---

### 5. 🔴 CRITICAL ISSUE: RabbitMQ Infrastructure Not Initialized

**Problem:** The RabbitMQ initialization script is **NOT BEING EXECUTED**

#### Issue Details:

**Current Setup (docker-compose.artifactory.yml:186-188):**
```yaml
rabbitmq:
  volumes:
    - rabbitmq_data:/var/lib/rabbitmq
    - ./rabbitmq-init.sh:/docker-entrypoint-initdb.d/init.sh:ro
```

**Why This Fails:**
1. `/docker-entrypoint-initdb.d/` is a convention for **PostgreSQL and MongoDB**, NOT RabbitMQ
2. RabbitMQ does NOT automatically execute scripts from this directory
3. The `rabbitmq:3-management-alpine` image has no built-in script execution mechanism

**Impact:**
- ❌ Exchange `catalyst.events` is never created
- ❌ Agent queues (planner-queue, architect-queue, etc.) are never created
- ❌ Routing key bindings are never established
- ❌ Agents cannot consume messages (queues don't exist)
- ❌ Publisher may fail or messages go nowhere

#### What SHOULD Happen:

The `rabbitmq-init.sh` script contains:
```bash
# Create topic exchange
rabbitmqadmin declare exchange name=catalyst.events type=topic durable=true

# Create queues for each agent
for agent in planner architect coder tester reviewer deployer explorer orchestrator; do
  rabbitmqadmin declare queue name=${agent}-queue durable=true
done

# Create bindings
rabbitmqadmin declare binding source=catalyst.events destination=planner-queue routing_key="catalyst.task.initiated"
# ... etc
```

**But it's never executed!**

#### Partial Mitigation:

The **EventConsumer** (consumer.py:42-60) and **EventPublisher** (publisher.py:34-38) DO create some infrastructure:

**Consumer creates:**
- ✅ Its own queue (e.g., "planner-queue")
- ✅ Binds queue to exchange with routing keys

**Publisher creates:**
- ✅ The exchange "catalyst.events"

**However:**
- The consumer might fail if the exchange doesn't exist yet
- There's a race condition if publisher hasn't run before consumers start
- The initialization is scattered and not centralized

---

### 6. 🟡 ISSUE: Backend Startup Timing

**File:** `/app/docker-compose.artifactory.yml:98-108`

```yaml
backend:
  depends_on:
    postgres:
      condition: service_healthy
    mongodb:
      condition: service_healthy
    redis:
      condition: service_started
    qdrant:
      condition: service_started
    rabbitmq:
      condition: service_started  # ⚠️ NOT service_healthy!
```

**Problem:**
- Backend waits for RabbitMQ `service_started`, not `service_healthy`
- RabbitMQ has a healthcheck defined but it's not used
- Backend may start before RabbitMQ is ready to accept connections
- Agent worker initialization may fail silently

**RabbitMQ Healthcheck (lines 189-193):**
```yaml
healthcheck:
  test: ["CMD", "rabbitmq-diagnostics", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
```

**Recommendation:** Change to:
```yaml
rabbitmq:
  condition: service_healthy
```

---

### 7. 🟡 ISSUE: Postgres Event Logging May Fail

**File:** `/app/backend/events/publisher.py:84-122`

```python
async def publish(self, event: AgentEvent) -> bool:
    # Publish to RabbitMQ...
    
    # Also save to Postgres for audit (if enabled)
    if get_config()["databases"]["postgres"]["enabled"]:
        await self._save_to_postgres(event)  # May fail silently
    
    return True
```

**Problem:**
- Postgres saving happens AFTER RabbitMQ publish
- If Postgres save fails, it logs error but doesn't affect return value
- However, in Docker Desktop, Postgres IS enabled, so this may cause issues
- Error: `asyncio.run()` cannot be called from a running event loop

**Evidence from event publisher:**
- Uses `await` but might be in a sync context from pika
- pika is synchronous, calling async functions from sync code is problematic

**Potential Fix:**
- Wrap postgres save in try-except to ensure it doesn't break event publishing
- Or make postgres save optional/fire-and-forget

---

## Root Cause Analysis

### Why Agents Don't Pick Up Tasks:

**Primary Cause:**
1. RabbitMQ infrastructure (exchanges, queues, bindings) is **not initialized**
2. `rabbitmq-init.sh` is mounted but **never executed**
3. Agents try to bind to non-existent queues and fail silently

**Secondary Causes:**
1. Backend may start before RabbitMQ is fully ready (timing issue)
2. EventConsumer creates queues but there's a race condition with exchange creation
3. No centralized RabbitMQ setup verification

**Verification Path:**
1. Check backend logs for RabbitMQ connection errors
2. Exec into RabbitMQ container and list exchanges/queues:
   ```bash
   docker exec catalyst-rabbitmq rabbitmqctl list_exchanges
   docker exec catalyst-rabbitmq rabbitmqctl list_queues
   docker exec catalyst-rabbitmq rabbitmqctl list_bindings
   ```
3. Expected: Should see `catalyst.events` exchange and 8 agent queues
4. Actual: Likely only empty/default exchange

---

## Recommended Fixes

### Fix 1: 🔴 HIGH PRIORITY - Initialize RabbitMQ Infrastructure

**Option A: Use Separate Init Container**

Add to `docker-compose.artifactory.yml`:

```yaml
  rabbitmq-init:
    image: artifactory.devtools.syd.c1.macquarie.com:9996/rabbitmq:3-management-alpine
    container_name: catalyst-rabbitmq-init
    depends_on:
      rabbitmq:
        condition: service_healthy
    volumes:
      - ./rabbitmq-init.sh:/init.sh:ro
    entrypoint: ["/bin/bash", "/init.sh"]
    networks:
      - catalyst-network

  backend:
    depends_on:
      rabbitmq-init:
        condition: service_completed_successfully
      # ... other deps
```

**Option B: Add to Backend Startup**

Create `/app/backend/init_rabbitmq.py`:

```python
import pika
import logging
import time

logger = logging.getLogger(__name__)

def init_rabbitmq(rabbitmq_url: str, max_retries: int = 10):
    """
    Initialize RabbitMQ infrastructure on startup
    Creates exchange, queues, and bindings
    """
    for attempt in range(max_retries):
        try:
            connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            channel = connection.channel()
            
            # Declare exchange
            channel.exchange_declare(
                exchange='catalyst.events',
                exchange_type='topic',
                durable=True
            )
            logger.info("✅ Created exchange: catalyst.events")
            
            # Create queues and bindings
            agents = ["planner", "architect", "coder", "tester", "reviewer", "deployer", "explorer", "orchestrator"]
            routing_keys = {
                "planner": "catalyst.task.initiated",
                "architect": "catalyst.plan.created",
                "coder": "catalyst.architecture.proposed",
                "tester": "catalyst.code.pr.opened",
                "reviewer": "catalyst.test.results",
                "deployer": "catalyst.review.decision",
                "explorer": "catalyst.explorer.scan.request",
                "orchestrator": "catalyst.*.complete"
            }
            
            for agent in agents:
                queue_name = f"{agent}-queue"
                
                # Declare queue
                channel.queue_declare(
                    queue=queue_name,
                    durable=True,
                    arguments={
                        'x-message-ttl': 3600000,
                        'x-max-length': 10000
                    }
                )
                
                # Bind to routing key
                if agent in routing_keys:
                    channel.queue_bind(
                        exchange='catalyst.events',
                        queue=queue_name,
                        routing_key=routing_keys[agent]
                    )
                    logger.info(f"✅ Created and bound queue: {queue_name}")
            
            connection.close()
            logger.info("✅ RabbitMQ infrastructure initialized successfully")
            return True
            
        except Exception as e:
            logger.warning(f"RabbitMQ init attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                logger.error("Failed to initialize RabbitMQ after all retries")
                return False
```

Call from `server.py` startup:

```python
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Catalyst Backend Starting...")
    
    # Initialize RabbitMQ infrastructure FIRST
    if is_docker_desktop():
        from init_rabbitmq import init_rabbitmq
        rabbitmq_url = os.getenv("RABBITMQ_URL")
        if not init_rabbitmq(rabbitmq_url):
            logger.error("Failed to initialize RabbitMQ - event system may not work")
    
    # Then start agent workers
    if is_docker_desktop():
        worker_manager = get_worker_manager(db, manager)
        asyncio.create_task(worker_manager.start_all_workers())
```

**Recommendation:** Use **Option B** (Backend initialization) as it's simpler and ensures infrastructure is ready before workers start

---

### Fix 2: 🟡 MEDIUM PRIORITY - Fix Startup Dependencies

**Change in `docker-compose.artifactory.yml`:**

```yaml
backend:
  depends_on:
    postgres:
      condition: service_healthy
    mongodb:
      condition: service_healthy
    redis:
      condition: service_started
    qdrant:
      condition: service_started
    rabbitmq:
      condition: service_healthy  # Changed from service_started
```

---

### Fix 3: 🟡 MEDIUM PRIORITY - Fix Postgres Event Logging

**Option A: Make it truly optional**

```python
async def publish(self, event: AgentEvent) -> bool:
    try:
        # Publish to RabbitMQ
        routing_key = event.to_routing_key()
        message = event.to_json()
        
        self.channel.basic_publish(
            exchange='catalyst.events',
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        logger.info(f"📤 Published event: {routing_key}")
        
        # Try to save to Postgres (best effort)
        try:
            if get_config()["databases"]["postgres"]["enabled"]:
                asyncio.create_task(self._save_to_postgres(event))
        except Exception as e:
            logger.debug(f"Postgres event logging skipped: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to publish event {event.event_type}: {e}")
        return False
```

**Option B: Disable Postgres event logging in config**

```python
# In environment.py for Docker Desktop config
"databases": {
    "postgres": {
        "enabled": False,  # Disable Postgres event audit for now
        "url": os.getenv("POSTGRES_URL", "...")
    },
}
```

---

## Testing Checklist

After implementing fixes:

### 1. Verify RabbitMQ Infrastructure
```bash
# SSH into RabbitMQ container
docker exec -it catalyst-rabbitmq bash

# Check exchange exists
rabbitmqctl list_exchanges
# Should see: catalyst.events (topic)

# Check queues exist
rabbitmqctl list_queues
# Should see: planner-queue, architect-queue, coder-queue, etc.

# Check bindings
rabbitmqctl list_bindings
# Should see bindings between catalyst.events and agent queues
```

### 2. Verify Agent Workers Started
```bash
# Check backend logs
docker logs catalyst-backend | grep "Starting agent worker"
# Should see: "✅ Started planner worker", "✅ Started architect worker", etc.

# Check worker listening
docker logs catalyst-backend | grep "listening on"
# Should see: "🎧 planner listening on planner-queue", etc.
```

### 3. Test Task Execution
```bash
# Send a test task via API
curl -X POST http://localhost:8001/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Build a simple todo app", "conversation_id": "test-123"}'

# Monitor agent logs
docker logs -f catalyst-backend | grep "🎯"
# Should see: "🎯 planner processing event: task.initiated"
```

### 4. Verify Event Flow
```bash
# Check RabbitMQ message stats
docker exec catalyst-rabbitmq rabbitmqctl list_queues name messages_ready messages_unacknowledged
# Should see messages moving through queues

# Check WebSocket updates
# Open browser to frontend and watch real-time agent updates
```

---

## Summary

### Current State:
- ❌ Agents not picking up tasks
- ❌ RabbitMQ infrastructure not initialized
- ⚠️ Startup timing issues
- ⚠️ Postgres event logging may fail

### Root Cause:
**RabbitMQ initialization script (`rabbitmq-init.sh`) is mounted but never executed because `/docker-entrypoint-initdb.d/` is not a valid location for RabbitMQ**

### Solution:
1. **Implement RabbitMQ infrastructure initialization in backend startup** (Option B above)
2. **Change RabbitMQ dependency to `service_healthy`**
3. **Make Postgres event logging optional/best-effort**

### Priority:
1. 🔴 **Critical**: Fix RabbitMQ infrastructure initialization
2. 🟡 **Medium**: Fix startup dependencies
3. 🟡 **Medium**: Fix Postgres event logging

### Expected Outcome:
After implementing fixes:
- ✅ RabbitMQ exchange and queues created on startup
- ✅ All 6 agent workers listening to their queues
- ✅ Tasks published by orchestrator picked up by planner
- ✅ Event chain flows through all agents
- ✅ Real-time updates visible in frontend

---

## Architecture Diagrams

### Current Event Flow (Broken)
```
User Request
    ↓
DualModeOrchestrator.execute_task()
    ↓
Create AgentEvent(event_type="task.initiated")
    ↓
EventPublisher.publish() → RabbitMQ (Exchange doesn't exist!)
    ↓
[FAILS - Event lost or publisher fails]
    ↓
Planner Agent listening on planner-queue (Queue doesn't exist!)
    ↓
[NEVER RECEIVES EVENT]
```

### Fixed Event Flow
```
Backend Startup
    ↓
init_rabbitmq() - Create infrastructure
    ├─ Create exchange: catalyst.events
    ├─ Create queues: planner-queue, architect-queue, etc.
    └─ Create bindings: routing keys to queues
    ↓
Start Agent Workers
    ├─ Planner listens on planner-queue ✅
    ├─ Architect listens on architect-queue ✅
    └─ ... all agents ready ✅
    ↓
User Request
    ↓
DualModeOrchestrator.execute_task()
    ↓
Create AgentEvent(event_type="task.initiated")
    ↓
EventPublisher.publish()
    ├─ Routing key: "catalyst.task.initiated"
    └─ Exchange: catalyst.events ✅
    ↓
RabbitMQ Routes to planner-queue (binding exists!) ✅
    ↓
Planner Agent receives event ✅
    ↓
Planner processes and publishes "catalyst.plan.created"
    ↓
Architect Agent receives event ✅
    ↓
... workflow continues through all agents ✅
```

---

## Code References

### Key Files Reviewed:
1. `/app/backend/config/environment.py` - Environment detection ✅
2. `/app/backend/server.py` - Startup logic ✅
3. `/app/backend/workers/agent_worker_manager.py` - Agent workers ✅
4. `/app/backend/agents_v2/base_agent.py` - Agent listening ✅
5. `/app/backend/events/publisher.py` - Event publishing ✅
6. `/app/backend/events/consumer.py` - Event consumption ✅
7. `/app/backend/events/schemas.py` - Event schemas & routing keys ✅
8. `/app/backend/orchestrator/dual_mode_orchestrator.py` - Task orchestration ✅
9. `/app/docker-compose.artifactory.yml` - Docker configuration ⚠️
10. `/app/rabbitmq-init.sh` - RabbitMQ init (NOT EXECUTED) ❌

### Architecture Quality Assessment:

**Overall Design:** ⭐⭐⭐⭐⭐ Excellent
- Clean separation of concerns
- Dual-mode orchestration is elegant
- Event-driven architecture is well-designed
- Proper use of async/await patterns

**Implementation:** ⭐⭐⭐⚠️⚠️ Good but incomplete
- Core logic is correct
- Infrastructure initialization is missing
- Startup timing needs improvement
- Postgres integration needs refinement

**After Fixes:** Expected ⭐⭐⭐⭐⭐
- All critical issues resolved
- Clean event flow
- Robust error handling
- Production-ready

---

**End of Architecture Review**
