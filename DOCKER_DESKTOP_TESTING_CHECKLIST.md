# Docker Desktop Testing Checklist
**For Catalyst Enterprise Migration (Phases 1-4)**

Use this checklist when testing on your local Docker Desktop machine.

---

## Prerequisites

- [ ] Docker Desktop installed and running
- [ ] Minimum 4GB RAM allocated to Docker
- [ ] Ports available: 5432, 27017, 6379, 6333, 5672, 15672, 80, 8080, 8001, 3000
- [ ] (Optional) GitHub Personal Access Token for Git push testing

---

## Phase 1 Testing: Infrastructure

### Setup

- [ ] Clone/download the Catalyst project
- [ ] Navigate to project directory: `cd /path/to/catalyst`
- [ ] Run testing script: `./test-docker-desktop.sh`

### Automated Tests (Via Script)

- [ ] Docker Desktop running ✅
- [ ] docker-compose available ✅
- [ ] make available ✅
- [ ] All 9 services started ✅
- [ ] Service count ≥ 8 ✅
- [ ] catalyst-postgres running ✅
- [ ] catalyst-mongodb running ✅
- [ ] catalyst-redis running ✅
- [ ] catalyst-rabbitmq running ✅
- [ ] catalyst-backend running ✅
- [ ] catalyst-frontend running ✅

### Manual Infrastructure Checks

- [ ] **Postgres Database:**
  ```bash
  docker exec -it catalyst-postgres psql -U catalyst -d catalyst_state
  ```
  - [ ] Run: `\dt` - Should show 6 tables
  - [ ] Tables present: tasks, projects, agent_events, preview_deployments, explorer_scans, llm_usage
  - [ ] Run: `\q` to exit

- [ ] **MongoDB:**
  ```bash
  docker exec -it catalyst-mongodb mongosh
  ```
  - [ ] Run: `show dbs` - Should show catalyst_db
  - [ ] Run: `exit`

- [ ] **Redis:**
  ```bash
  docker exec catalyst-redis redis-cli ping
  ```
  - [ ] Response: PONG ✅

- [ ] **RabbitMQ Management UI:**
  - [ ] Open: http://localhost:15672
  - [ ] Login: catalyst / catalyst_queue_2025
  - [ ] Click "Queues" tab
  - [ ] Verify 9 queues exist:
    - [ ] planner-queue
    - [ ] architect-queue
    - [ ] coder-queue
    - [ ] tester-queue
    - [ ] reviewer-queue
    - [ ] deployer-queue
    - [ ] explorer-queue
    - [ ] orchestrator-queue
    - [ ] failed-events (DLQ)
  - [ ] Click "Exchanges" tab
  - [ ] Verify: catalyst.events exchange exists (type: topic)

- [ ] **Traefik Dashboard:**
  - [ ] Open: http://localhost:8080
  - [ ] Dashboard loads successfully
  - [ ] Click "HTTP" → "Routers" (may be empty initially)

---

## Phase 2 Testing: Event-Driven Agents

### Environment Detection

- [ ] **Check Environment API:**
  ```bash
  curl http://localhost:8001/api/environment/info | jq
  ```
  - [ ] `"environment": "docker_desktop"` ✅
  - [ ] `"orchestration_mode": "event_driven"` ✅
  - [ ] `"features.postgres": true` ✅
  - [ ] `"features.event_streaming": true` ✅
  - [ ] `"features.git_integration": true` ✅
  - [ ] `"features.preview_deployments": true` ✅

### Backend Startup Logs

- [ ] **Check Backend Logs:**
  ```bash
  docker logs catalyst-backend | head -50
  ```
  - [ ] Should see: "🚀 Catalyst Backend Starting..."
  - [ ] Should see: "📍 Environment: docker_desktop"
  - [ ] Should see: "🎯 Orchestration Mode: event_driven"
  - [ ] Should see: "✅ Agent workers started in background"
  - [ ] Should see: "✅ Background scheduler started"
  - [ ] No errors about missing services

### Agent Workers

- [ ] **Verify Agent Workers Started:**
  ```bash
  docker logs catalyst-backend 2>&1 | grep -i "worker\|listening"
  ```
  - [ ] Should see: "Started {agent} worker" for each agent
  - [ ] Should see: "6 agent workers listening"

---

## Phase 3 Testing: Git Integration

### Build an Application

- [ ] **Open Frontend:**
  - [ ] Navigate to: http://localhost:3000
  - [ ] Interface loads successfully
  - [ ] Chat is ready

- [ ] **Send Build Request:**
  - [ ] Type: "build a simple counter app"
  - [ ] Click Send (or press Enter)
  - [ ] Wait for response

### Watch Real-Time Updates

- [ ] **Verify Real-Time Updates Appear:**
  - [ ] See: "🤖 Orchestrator: Task initiated..."
  - [ ] See: "📋 Planner: Analyzing requirements..."
  - [ ] See: "✅ Planning complete..."
  - [ ] See: "🏗️ Architect: Designing architecture..."
  - [ ] See: "💻 Coder: Generating code..."
  - [ ] See file-level updates:
    - [ ] "🐍 Generated backend/models/..."
    - [ ] "⚛️ Generated frontend/src/..."
  - [ ] See: "🔀 Committed to branch: feature/task-..."
  - [ ] Chat UI is grayed out during processing
  - [ ] Green "Agent is running..." banner visible
  - [ ] Input field disabled

### Verify Git Repository Created

- [ ] **Check Local Repos:**
  ```bash
  ls -la /app/repos/
  ```
  - [ ] Project directory exists (counter-app or similar)
  - [ ] Navigate: `cd /app/repos/{project-name}/`
  - [ ] `.git` directory exists
  
- [ ] **Check Git Commits:**
  ```bash
  git log --oneline --all
  ```
  - [ ] Multiple commits visible
  - [ ] Commits from different agents:
    - [ ] "feat(planning): Add development plan"
    - [ ] "feat(architecture): Add system architecture"
    - [ ] "feat: Generate complete application code"

- [ ] **Check Git Branches:**
  ```bash
  git branch -a
  ```
  - [ ] main branch exists
  - [ ] feature/task-{id} branch exists

- [ ] **View Files:**
  ```bash
  ls -la
  tree -L 2  # If tree installed
  ```
  - [ ] planning/ directory with plan.yaml
  - [ ] architecture/ directory with design files
  - [ ] backend/ directory with Python code
  - [ ] frontend/ directory with React code
  - [ ] docker-compose.yml
  - [ ] README.md

### Test Git API

- [ ] **List Repositories:**
  ```bash
  curl http://localhost:8001/api/git/repos | jq
  ```
  - [ ] Returns list of repos
  - [ ] Shows commit count

- [ ] **Get Repo Details:**
  ```bash
  curl http://localhost:8001/api/git/repos/{project-name} | jq
  ```
  - [ ] Shows commits array
  - [ ] Shows lines_of_code
  - [ ] Shows current_commit

### GitHub Integration (If Token Set)

- [ ] **Set GitHub Token:**
  ```bash
  export GITHUB_TOKEN=ghp_your_token_here
  ```
  - [ ] Restart backend: `docker-compose -f docker-compose.artifactory.yml restart backend`

- [ ] **Build Another App:**
  - [ ] Chat: "create a todo list app"
  - [ ] Wait for completion
  - [ ] Should see: "📤 Pushed to GitHub: ..."
  - [ ] Should see: "📬 Pull Request created: ..."

- [ ] **Verify on GitHub:**
  - [ ] Visit: https://github.com/{your-org}/{project-name}
  - [ ] Repository exists
  - [ ] Code is present
  - [ ] PR exists (Pull Requests tab)
  - [ ] PR has description and link to Catalyst

---

## Phase 4 Testing: Preview Deployments

### Check Preview Configuration

- [ ] **Verify Preview Mode:**
  ```bash
  docker exec catalyst-backend printenv PREVIEW_MODE
  ```
  - [ ] Should be: `docker_in_docker` (default)

### Monitor Deployment Process

- [ ] **Watch Build Progress:**
  - [ ] In chat, after code generation
  - [ ] Should see: "🤖 Deployer: Building Docker images..."
  - [ ] Should see: "🐳 Building backend image..."
  - [ ] Should see: "✅ Backend image built"
  - [ ] Should see: "🐳 Building frontend image..."
  - [ ] Should see: "✅ Frontend image built"
  - [ ] Should see: "🚀 Started containers..."
  - [ ] Should see: "✅ Health checks passed"
  - [ ] Should see: "🎉 Your app is live!"
  - [ ] Preview URLs displayed

### Verify Preview Containers

- [ ] **List Preview Containers:**
  ```bash
  docker ps | grep preview
  ```
  - [ ] See: preview-{task-id}-db
  - [ ] See: preview-{task-id}-backend
  - [ ] See: preview-{task-id}-frontend
  - [ ] All showing "Up" status

- [ ] **Check Preview Networks:**
  ```bash
  docker network ls | grep preview
  ```
  - [ ] Network: preview-{task-id} exists

### Access Preview Deployment

- [ ] **Get Preview Details:**
  ```bash
  curl http://localhost:8001/api/preview | jq
  ```
  - [ ] Returns preview array
  - [ ] Has preview_url
  - [ ] Has fallback_url
  - [ ] Has backend_url
  - [ ] status = "deployed"
  - [ ] health_status = "healthy"

- [ ] **Access Preview Frontend:**
  - [ ] Get fallback_url from API response
  - [ ] Open in browser: `http://localhost:{port}`
  - [ ] React app loads successfully
  - [ ] App is functional (can interact with UI)

- [ ] **Test Preview Backend:**
  - [ ] Get backend_url from API response
  - [ ] Test: `curl http://localhost:{backend-port}/api/`
  - [ ] Should return API info

- [ ] **Test with /etc/hosts (Optional):**
  - [ ] Add to /etc/hosts: `127.0.0.1 {project}-{task-id}.localhost`
  - [ ] Open: `http://{project}-{task-id}.localhost`
  - [ ] Should route to preview

### Verify Postgres Tracking

- [ ] **Check Preview Deployments Table:**
  ```bash
  docker exec catalyst-postgres psql -U catalyst -d catalyst_state \
    -c "SELECT task_id, preview_url, status, health_status, deployed_at FROM preview_deployments;"
  ```
  - [ ] Record exists for your task
  - [ ] preview_url matches what was shown in chat
  - [ ] status = 'deployed'
  - [ ] health_status = 'healthy'

### Test Health Monitoring

- [ ] **Wait 5 Minutes (for health check job)**

- [ ] **Check Health Updated:**
  ```bash
  docker exec catalyst-postgres psql -U catalyst -d catalyst_state \
    -c "SELECT task_id, health_status, last_health_check FROM preview_deployments;"
  ```
  - [ ] last_health_check timestamp updated
  - [ ] health_status reflects actual state

### Test Manual Cleanup

- [ ] **Get Task ID:**
  ```bash
  TASK_ID=$(curl -s http://localhost:8001/api/preview | jq -r '.previews[0].task_id')
  echo $TASK_ID
  ```

- [ ] **Cleanup Preview:**
  ```bash
  curl -X DELETE http://localhost:8001/api/preview/${TASK_ID}
  ```
  - [ ] Response: "success": true

- [ ] **Verify Containers Stopped:**
  ```bash
  docker ps | grep preview
  ```
  - [ ] Should be empty (containers removed)

- [ ] **Check Database Updated:**
  ```bash
  docker exec catalyst-postgres psql -U catalyst -d catalyst_state \
    -c "SELECT status FROM preview_deployments WHERE task_id = '${TASK_ID}';"
  ```
  - [ ] status = 'cleaned_up'

### Test Auto-Cleanup (Optional)

- [ ] **Force Expire a Preview:**
  ```bash
  docker exec catalyst-postgres psql -U catalyst -d catalyst_state \
    -c "UPDATE preview_deployments SET expires_at = NOW() - INTERVAL '1 hour' WHERE status = 'deployed';"
  ```

- [ ] **Trigger Cleanup:**
  ```bash
  curl -X POST http://localhost:8001/api/preview/cleanup-expired
  ```
  - [ ] Response shows count of cleaned up previews

- [ ] **Verify Cleanup Happened:**
  ```bash
  docker ps | grep preview
  ```
  - [ ] No preview containers running

---

## Event System Verification

### RabbitMQ Event Flow

- [ ] **Build App While Watching RabbitMQ:**
  - [ ] Open: http://localhost:15672
  - [ ] Go to "Queues" tab
  - [ ] In chat: "build a hello world app"
  - [ ] Watch queues:
    - [ ] planner-queue gets message
    - [ ] Message processed (count goes to 0)
    - [ ] architect-queue gets message
    - [ ] Each queue processes in sequence
  
- [ ] **Check Message Details:**
  - [ ] Click on any queue
  - [ ] Click "Get messages"
  - [ ] Should see event payloads with trace_id, task_id, actor

### Postgres Event Audit

- [ ] **View Event Trail:**
  ```bash
  docker exec catalyst-postgres psql -U catalyst -d catalyst_state
  ```
  
  - [ ] Run:
    ```sql
    SELECT actor, event_type, created_at 
    FROM agent_events 
    ORDER BY created_at DESC 
    LIMIT 20;
    ```
  - [ ] Should see events from all agents
  - [ ] Events in order: orchestrator → planner → architect → coder → tester → reviewer → deployer

- [ ] **View Task Progression:**
  ```sql
  SELECT id, status, current_phase, created_at, updated_at
  FROM tasks
  ORDER BY created_at DESC
  LIMIT 5;
  ```
  - [ ] Task transitions visible: pending → planning → architecting → coding → testing → reviewing → deploying → completed

---

## Integration Testing

### Test Multiple Concurrent Builds

- [ ] **Send 3 Build Requests Quickly:**
  1. "build a blog"
  2. "create a chat app"
  3. "make a calculator"

- [ ] **Verify Parallel Processing:**
  - [ ] Open RabbitMQ UI
  - [ ] Multiple messages in queues simultaneously
  - [ ] Each task gets own trace_id
  - [ ] All complete successfully

### Test Error Handling

- [ ] **Send Invalid Request:**
  - [ ] Chat: "build a [something complex/impossible]"
  - [ ] Should still complete (may have lower quality)
  - [ ] No crashes
  - [ ] Error logged properly

### Test Chat Features

- [ ] **Message Persistence:**
  - [ ] Send several messages
  - [ ] Refresh page (F5)
  - [ ] Messages reload from backend ✅
  - [ ] Conversation continues

- [ ] **New Chat Button:**
  - [ ] Click "New Chat" button
  - [ ] New conversation starts
  - [ ] Old messages cleared
  - [ ] Can start new build

- [ ] **Navigation:**
  - [ ] Click "Cost Dashboard"
  - [ ] Loads cost metrics
  - [ ] Click "Backend Logs"
  - [ ] Shows logs
  - [ ] Navigate back to chat

---

## Performance Testing

### Resource Usage

- [ ] **Check Docker Resource Usage:**
  ```bash
  docker stats --no-stream
  ```
  - [ ] Total memory usage acceptable (<4GB recommended)
  - [ ] CPU usage reasonable
  - [ ] No containers constantly restarting

### Build Time Measurement

- [ ] **Time a Complete Build:**
  - [ ] Start timer
  - [ ] Send: "build a simple app"
  - [ ] Note time when "Your app is live!" appears
  - [ ] **Expected:** 3-6 minutes total
    - Planning: 30s
    - Architecture: 30s
    - Coding: 60-90s
    - Testing: 30s
    - Review: 30s
    - Deploy: 60-120s (image builds)

### Preview Access Time

- [ ] **Measure Preview Access:**
  - [ ] Note URL provided in chat
  - [ ] Open URL immediately
  - [ ] **Expected:** Loads within 5 seconds

---

## Troubleshooting Checklist

### If Services Won't Start

- [ ] **Check Docker Desktop:**
  - [ ] Docker Desktop app is running
  - [ ] Adequate resources allocated (Settings → Resources)
  - [ ] No other conflicting services using same ports

- [ ] **Check Logs:**
  ```bash
  docker-compose -f docker-compose.artifactory.yml logs | grep -i error
  ```

- [ ] **Common Issues:**
  - [ ] Port 5432 in use: `lsof -i :5432` (kill or change port)
  - [ ] Port 27017 in use: `lsof -i :27017`
  - [ ] Out of disk space: `docker system df`
  - [ ] Out of memory: Check Docker Desktop resources

### If Postgres Tables Missing

- [ ] **Check Init Script Ran:**
  ```bash
  docker logs catalyst-postgres | grep "Catalyst database initialized"
  ```

- [ ] **Manual Init:**
  ```bash
  docker exec -i catalyst-postgres psql -U catalyst -d catalyst_state < /app/init-db.sql
  ```

### If RabbitMQ Queues Missing

- [ ] **Check Init Script:**
  ```bash
  docker logs catalyst-rabbitmq | grep "initialization complete"
  ```

- [ ] **Manual Init:**
  ```bash
  docker exec catalyst-rabbitmq sh /docker-entrypoint-initdb.d/init.sh
  ```

### If Preview Deployment Fails

- [ ] **Check Docker Socket Access:**
  ```bash
  docker exec catalyst-backend ls -la /var/run/docker.sock
  ```
  - [ ] Should be accessible

- [ ] **Check Backend Logs:**
  ```bash
  docker logs catalyst-backend | grep -i "deploy\|preview"
  ```

- [ ] **Check Available Ports:**
  ```bash
  lsof -i :9000-9999
  ```
  - [ ] Should have free ports in range

### If GitHub Push Fails

- [ ] **Verify Token:**
  ```bash
  docker exec catalyst-backend printenv GITHUB_TOKEN
  ```
  - [ ] Token is set (not empty)

- [ ] **Test Token:**
  ```bash
  curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
  ```
  - [ ] Returns your user info

- [ ] **Check Logs:**
  ```bash
  docker logs catalyst-backend | grep -i github
  ```

---

## Success Criteria

### Minimum Success (Phase 1-2)

- [x] All 9 services running
- [x] Environment detected as docker_desktop
- [x] Can send chat messages
- [x] Real-time updates working
- [x] No critical errors

### Full Success (Phases 1-4)

- [ ] Event-driven mode active
- [ ] RabbitMQ events flowing
- [ ] Git repos created locally
- [ ] Code committed with proper messages
- [ ] Preview containers deployed
- [ ] Preview URL accessible
- [ ] Health monitoring working
- [ ] Auto-cleanup configured

### Bonus (With GitHub Token)

- [ ] Code pushed to GitHub
- [ ] Repository auto-created
- [ ] PR created automatically
- [ ] PR contains all generated code

---

## Final Verification Commands

Run these to verify everything:

```bash
# 1. Service count
docker ps --filter "name=catalyst" | wc -l
# Expected: 9

# 2. Environment check
curl -s http://localhost:8001/api/environment/info | jq '.environment'
# Expected: "docker_desktop"

# 3. Repos created
ls /app/repos/ | wc -l
# Expected: 1+ (number of apps you built)

# 4. Postgres records
docker exec catalyst-postgres psql -U catalyst -d catalyst_state \
  -c "SELECT COUNT(*) FROM tasks;"
# Expected: Number of build requests

# 5. Event count
docker exec catalyst-postgres psql -U catalyst -d catalyst_state \
  -c "SELECT COUNT(*) FROM agent_events;"
# Expected: Multiple (events from all agents)

# 6. Previews active
curl -s http://localhost:8001/api/preview | jq '.count'
# Expected: Number of active previews
```

---

## Report Results

After completing all tests, report:

### What Worked ✅
- List all successful tests
- Note any particularly impressive features

### What Failed ❌
- List failures with error messages
- Include relevant logs
- Note which phase failed

### Performance Notes
- Build time
- Resource usage
- Preview access speed

### Questions/Issues
- Any unexpected behavior
- Feature requests
- Bugs discovered

---

## Next Actions

### If All Tests Pass ✅
- Ready for Phase 5-6 implementation
- Ready for production hardening
- Can start using for real projects

### If Some Tests Fail ⚠️
- Report failures to AI
- Provide logs and error messages
- AI will fix issues before proceeding

### If Major Issues ❌
- May need to rollback
- Re-examine architecture
- Consider alternative approaches

---

**Save this checklist and tick off items as you test!**
