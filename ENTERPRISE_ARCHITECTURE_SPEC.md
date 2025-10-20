# Catalyst Enterprise Architecture - Technical Specification
**Version:** 2.0.0  
**Date:** October 2025  
**Status:** Design Phase  
**Migration:** Sequential → Event-Driven Architecture

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Infrastructure Components](#infrastructure-components)
4. [Agent Contracts & Data Flow](#agent-contracts--data-flow)
5. [Event Streaming Design](#event-streaming-design)
6. [Storage Strategy](#storage-strategy)
7. [Preview Deployment System](#preview-deployment-system)
8. [Explorer Agent Capabilities](#explorer-agent-capabilities)
9. [Configuration & Dual-Mode Operation](#configuration--dual-mode-operation)
10. [Implementation Phases](#implementation-phases)
11. [API Specifications](#api-specifications)
12. [Deployment Guide](#deployment-guide)

---

## 1. Executive Summary

### Current State (v1.0)
- Sequential agent execution
- MongoDB-only storage
- Direct function calls between agents
- No preview deployments
- Basic file system artifacts

### Target State (v2.0)
- **Event-driven architecture** with RabbitMQ
- **Multi-tier storage:** Postgres (state) + MongoDB (docs) + Git (code) + Redis (cache)
- **Asynchronous agent communication** via message queues
- **Preview deployments** with auto-generated URLs
- **Explorer agent** for system analysis
- **Dual-mode operation:** Fallback to sequential for K8s environment

### Key Benefits
- ✅ Parallel agent execution where possible
- ✅ Better fault tolerance (retry, dead letter queues)
- ✅ Audit trail via events
- ✅ Preview URLs for generated apps
- ✅ Gradual migration path

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface (React)                    │
│  - Chat Interface  - Cost Dashboard  - Backend Logs  - Preview  │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST + WebSocket
┌────────────────────────▼────────────────────────────────────────┐
│                     API Gateway (FastAPI)                        │
│  - Chat API  - Task API  - Preview API  - Explorer API          │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌────────────────┐ ┌──────────┐ ┌──────────────┐
│  Orchestrator  │ │ RabbitMQ │ │ State Store  │
│   (Dual-Mode)  │ │  Events  │ │  Postgres    │
└───────┬────────┘ └────┬─────┘ └──────────────┘
        │               │
        │    ┌──────────┴──────────┐
        │    │                     │
        ▼    ▼                     ▼
┌──────────────────────────────────────────────┐
│            Multi-Agent System                 │
│                                               │
│  Planner → Architect → Coder → Tester →      │
│       Reviewer → Deployer                     │
│                                               │
│  Explorer (parallel/on-demand)                │
└───────┬───────────────────────────────────┬──┘
        │                                   │
        ▼                                   ▼
┌───────────────┐                  ┌────────────────┐
│  Storage Layer│                  │ Preview Engine │
│  - Git repos  │                  │ - Docker spawn │
│  - Artifacts  │                  │ - Traefik      │
│  - MongoDB    │                  │ - URL routing  │
└───────────────┘                  └────────────────┘
```

### 2.2 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI (Python 3.11) | API Server |
| **Frontend** | React 19 | User Interface |
| **Event Bus** | RabbitMQ 3 | Agent communication |
| **State DB** | PostgreSQL 15 | Durable state, task tracking |
| **Document DB** | MongoDB 5 | Conversations, logs |
| **Cache** | Redis 7 | Cost optimization, sessions |
| **Vector DB** | Qdrant | Learning service |
| **Code Storage** | Git (local + GitHub) | Source control |
| **Artifact Storage** | File System | Test reports, builds |
| **Preview Routing** | Traefik v2.10 | Dynamic URL routing |
| **Container Runtime** | Docker | Preview deployments |

---

## 3. Infrastructure Components

### 3.1 Docker Compose Services (Complete Stack)

```yaml
version: '3.8'

services:
  # ============================================
  # Core Data Layer
  # ============================================
  
  postgres:
    image: postgres:15-alpine
    container_name: catalyst-postgres
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: catalyst_state
      POSTGRES_USER: catalyst
      POSTGRES_PASSWORD: catalyst_state_2025
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U catalyst"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - catalyst-network

  mongodb:
    image: mongo:5.0
    container_name: catalyst-mongodb
    restart: unless-stopped
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: catalyst_admin_pass
      MONGO_INITDB_DATABASE: catalyst_db
    volumes:
      - mongodb_data:/data/db
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongo localhost:27017/test --quiet
      interval: 10s
    networks:
      - catalyst-network

  redis:
    image: redis:7-alpine
    container_name: catalyst-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
    networks:
      - catalyst-network

  qdrant:
    image: qdrant/qdrant:latest
    container_name: catalyst-qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage
    networks:
      - catalyst-network

  # ============================================
  # Event Streaming & Messaging
  # ============================================
  
  rabbitmq:
    image: rabbitmq:3-management-alpine
    container_name: catalyst-rabbitmq
    restart: unless-stopped
    ports:
      - "5672:5672"   # AMQP
      - "15672:15672" # Management UI
    environment:
      RABBITMQ_DEFAULT_USER: catalyst
      RABBITMQ_DEFAULT_PASS: catalyst_queue_2025
      RABBITMQ_DEFAULT_VHOST: catalyst
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
      - ./rabbitmq-init.sh:/docker-entrypoint-initdb.d/init.sh
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 10s
    networks:
      - catalyst-network

  # ============================================
  # Application Services
  # ============================================
  
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: catalyst-backend
    restart: unless-stopped
    ports:
      - "8001:8001"
    environment:
      # Database connections
      - MONGO_URL=mongodb://admin:catalyst_admin_pass@mongodb:27017
      - POSTGRES_URL=postgresql://catalyst:catalyst_state_2025@postgres:5432/catalyst_state
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
      - RABBITMQ_URL=amqp://catalyst:catalyst_queue_2025@rabbitmq:5672/catalyst
      
      # LLM Configuration
      - EMERGENT_LLM_KEY=${EMERGENT_LLM_KEY}
      - DEFAULT_LLM_PROVIDER=emergent
      - DEFAULT_LLM_MODEL=claude-3-7-sonnet-20250219
      
      # Orchestration Mode
      - ORCHESTRATION_MODE=event_driven  # or sequential
      
      # Preview Configuration
      - PREVIEW_MODE=docker_in_docker    # or compose_only or traefik
      - PREVIEW_BASE_URL=http://localhost
      
      # Git Configuration
      - GIT_STORAGE_MODE=both            # local, github, or both
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - GIT_REPOS_PATH=/app/repos
      
      # Artifact Storage
      - ARTIFACTS_PATH=/app/artifacts
      
      # Feature Flags
      - ENABLE_PREVIEW_DEPLOYMENTS=true
      - ENABLE_GIT_INTEGRATION=true
      - ENABLE_EXPLORER_AGENT=true
      
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock  # Docker-in-Docker
      - ./repos:/app/repos                          # Git repositories
      - ./artifacts:/app/artifacts                  # Build/test artifacts
      - ./generated_projects:/app/generated_projects
    depends_on:
      - postgres
      - mongodb
      - redis
      - qdrant
      - rabbitmq
    networks:
      - catalyst-network

  frontend:
    build:
      context: ./frontend
      dockerfile: ../Dockerfile.frontend
      args:
        REACT_APP_BACKEND_URL: http://localhost:8001
    container_name: catalyst-frontend
    restart: unless-stopped
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - catalyst-network

  # ============================================
  # Preview & Routing
  # ============================================
  
  traefik:
    image: traefik:v2.10
    container_name: catalyst-traefik
    restart: unless-stopped
    ports:
      - "80:80"      # HTTP
      - "8080:8080"  # Dashboard
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - catalyst-network

volumes:
  postgres_data:
  mongodb_data:
  redis_data:
  qdrant_data:
  rabbitmq_data:

networks:
  catalyst-network:
    driver: bridge
```

### 3.2 Database Schemas

**Postgres Tables (State Management):**

```sql
-- Task execution state
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    project_id UUID NOT NULL,
    trace_id UUID NOT NULL,
    user_prompt TEXT NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_phase VARCHAR(50),
    branch_name VARCHAR(255),
    commit_sha VARCHAR(40),
    preview_url VARCHAR(512),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    cost_total DECIMAL(10, 6),
    metadata JSONB
);

-- Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    repo_url VARCHAR(512),
    repo_path VARCHAR(512),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent events (audit trail)
CREATE TABLE agent_events (
    id SERIAL PRIMARY KEY,
    trace_id UUID NOT NULL,
    task_id UUID,
    actor VARCHAR(50) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_trace (trace_id),
    INDEX idx_task (task_id),
    INDEX idx_actor (actor)
);

-- Preview deployments
CREATE TABLE preview_deployments (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id),
    url VARCHAR(512) NOT NULL,
    container_id VARCHAR(128),
    status VARCHAR(50),
    health_check_url VARCHAR(512),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    last_health_check TIMESTAMP
);

-- Explorer scans
CREATE TABLE explorer_scans (
    id UUID PRIMARY KEY,
    scan_type VARCHAR(50) NOT NULL, -- github, deployment, database
    target VARCHAR(512) NOT NULL,
    findings JSONB,
    tech_stack JSONB,
    security_score DECIMAL(5, 2),
    tech_debt_score DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

**MongoDB Collections (Documents):**

```javascript
// Conversations (chat history)
db.conversations = {
  id: UUID,
  user_id: String,
  project_id: UUID,
  title: String,
  messages: [ChatMessage],
  context: {
    current_task_id: UUID,
    current_project_id: UUID,
    ...
  },
  created_at: DateTime,
  updated_at: DateTime
}

// Generated project metadata
db.generated_projects = {
  id: UUID,
  name: String,
  description: String,
  architecture: Object,
  files: [FileMetadata],
  git_repo_path: String,
  git_commit: String,
  created_at: DateTime
}

// Agent logs (detailed execution logs)
db.agent_logs = {
  id: UUID,
  task_id: UUID,
  trace_id: UUID,
  agent_name: String,
  message: String,
  level: String, // info, warning, error
  timestamp: DateTime
}
```

---

## 4. Agent Contracts & Data Flow

### 4.1 Planner Agent

**Responsibility:** Break down user requirements into actionable plan

**Input Schema:**
```json
{
  "trace_id": "uuid",
  "user_requirements": "Build a todo app with user auth",
  "project_name": "Todo App",
  "context": {
    "existing_codebase": null,
    "explorer_findings": null,
    "constraints": []
  }
}
```

**Processing Steps:**
1. Analyze requirements with LLM (OptimizedLLMClient)
2. Extract features, priorities, acceptance criteria
3. Generate task breakdown with dependencies
4. Create task graph
5. Estimate complexity and timeline
6. Assess risks

**Output Structure:**
```yaml
# planning/plan.yaml
project:
  name: "Todo App"
  description: "Task management application with user authentication"
  target_users: "General users, teams"
  
features:
  - id: "F1"
    name: "User Authentication"
    description: "Login/register with JWT"
    priority: "high"
    complexity: "medium"
    tasks: ["T1", "T2", "T3"]
    acceptance_criteria:
      - "User can register with email/password"
      - "User can login and receive JWT token"
      - "Token expires after 24 hours"
  
  - id: "F2"
    name: "Todo Management"
    description: "CRUD operations for todos"
    priority: "high"
    complexity: "medium"
    tasks: ["T4", "T5", "T6"]

tasks:
  - id: "T1"
    feature: "F1"
    description: "Implement user registration endpoint"
    type: "backend"
    estimated_hours: 2
    depends_on: []
    files_affected: ["backend/routes/auth.py", "backend/models/user.py"]
  
  - id: "T2"
    feature: "F1"
    description: "Implement login endpoint"
    type: "backend"
    estimated_hours: 2
    depends_on: ["T1"]

api_endpoints:
  - method: "POST"
    path: "/api/auth/register"
    description: "Register new user"
    input: {email: string, password: string}
    output: {id: string, token: string}
  
  - method: "POST"
    path: "/api/auth/login"
    description: "Login user"
    input: {email: string, password: string}
    output: {token: string}

risk_assessment:
  - risk: "Password security"
    severity: "high"
    mitigation: "Use bcrypt hashing, enforce strong passwords"
  
  - risk: "JWT token theft"
    severity: "medium"
    mitigation: "HTTPOnly cookies, short expiry, refresh tokens"
```

**Additional Output Files:**
- `planning/acceptance.md` - Detailed acceptance criteria
- `planning/risk.md` - Risk analysis
- `planning/task-graph.json` - Task dependencies for visualization

**Git Commit:**
```
feat(planning): Add comprehensive plan for Todo App

- 8 features defined with priorities
- 24 tasks with dependencies
- 15 API endpoints specified
- Risk assessment completed

[planner-agent]
```

**Event Published to RabbitMQ:**
```json
{
  "version": "v1",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "actor": "planner",
  "event_type": "plan.created",
  "repo": "catalyst-generated/todo-app",
  "branch": "main",
  "commit": "abc123def456",
  "timestamp": "2025-10-20T10:30:00Z",
  "payload": {
    "plan_ref": "git://main/planning/plan.yaml",
    "feature_count": 8,
    "task_count": 24,
    "api_endpoint_count": 15,
    "estimated_hours": 48,
    "risk_level": "medium",
    "complexity_score": 0.65
  }
}
```

**Queue:** `catalyst.plan.created` → Architect listens

**Database Updates:**
```sql
-- Postgres: Update task state
UPDATE tasks 
SET status = 'planning_complete',
    current_phase = 'architecture',
    metadata = '{"plan_ref": "git://...", "feature_count": 8}'::jsonb,
    updated_at = NOW()
WHERE id = '...';

-- Insert event
INSERT INTO agent_events (trace_id, task_id, actor, event_type, payload)
VALUES ('...', '...', 'planner', 'plan.created', '...'::jsonb);
```

**User Chat Updates (WebSocket):**
```
🤖 Planner: Analyzing your requirements...
🤖 Planner: Identified 8 core features
🤖 Planner: Breaking down into 24 development tasks
🤖 Planner: Defining 15 API endpoints
🤖 Planner: Assessing risks and dependencies
✅ Planning complete: 8 features, 24 tasks, medium risk
📄 Generated planning/plan.yaml
📄 Generated planning/risk.md
📄 Generated planning/task-graph.json
```

---

### 4.2 Architect Agent

**Responsibility:** Design technical architecture from plan

**Input:** Subscribes to `catalyst.plan.created`

**Input Event:**
```json
{
  "trace_id": "...",
  "actor": "planner",
  "payload": {
    "plan_ref": "git://main/planning/plan.yaml",
    "feature_count": 8
  }
}
```

**Processing Steps:**
1. Load `plan.yaml` from Git
2. Determine tech stack based on requirements
3. Design data models for each feature
4. Create API contracts (OpenAPI spec)
5. Design system components and their interactions
6. Create Architecture Decision Records (ADRs)
7. Generate architecture diagrams

**Output Structure:**
```
architecture/
  ├── design.md
  ├── tech-stack.md
  ├── data-models.json
  ├── api-contracts/
  │   ├── openapi.yaml
  │   └── api-guide.md
  ├── adr/
  │   ├── 001-why-fastapi.md
  │   ├── 002-mongodb-for-flexibility.md
  │   ├── 003-jwt-authentication.md
  │   └── 004-react-frontend.md
  ├── components.md
  └── architecture-diagram.svg
```

**data-models.json:**
```json
{
  "models": [
    {
      "name": "User",
      "collection": "users",
      "fields": [
        {"name": "id", "type": "UUID", "required": true, "primary_key": true},
        {"name": "email", "type": "String", "required": true, "unique": true},
        {"name": "password_hash", "type": "String", "required": true},
        {"name": "created_at", "type": "DateTime", "required": true}
      ],
      "indexes": [
        {"fields": ["email"], "unique": true}
      ]
    },
    {
      "name": "Todo",
      "collection": "todos",
      "fields": [
        {"name": "id", "type": "UUID", "primary_key": true},
        {"name": "user_id", "type": "UUID", "required": true, "foreign_key": "User.id"},
        {"name": "title", "type": "String", "required": true},
        {"name": "completed", "type": "Boolean", "default": false},
        {"name": "created_at", "type": "DateTime"}
      ]
    }
  ]
}
```

**api-contracts/openapi.yaml:**
```yaml
openapi: 3.0.0
info:
  title: Todo App API
  version: 1.0.0
paths:
  /api/auth/register:
    post:
      summary: Register new user
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                email: {type: string, format: email}
                password: {type: string, minLength: 8}
      responses:
        201:
          description: User created
          content:
            application/json:
              schema:
                type: object
                properties:
                  id: {type: string, format: uuid}
                  token: {type: string}
  # ... more endpoints
```

**Event Published:**
```json
{
  "actor": "architect",
  "event_type": "architecture.proposed",
  "payload": {
    "architecture_ref": "git://main/architecture/",
    "tech_stack": {
      "backend": "FastAPI 0.110+",
      "frontend": "React 19",
      "database": "MongoDB 5.0",
      "cache": "Redis 7",
      "auth": "JWT"
    },
    "data_model_count": 2,
    "api_endpoint_count": 15,
    "adrs_created": 4,
    "requires_review": false
  }
}
```

**Queue:** `catalyst.architecture.proposed` → Coder listens

**User Chat Updates:**
```
🤖 Architect: Analyzing plan requirements...
🤖 Architect: Selecting optimal tech stack...
✅ Tech Stack: FastAPI + React + MongoDB
🤖 Architect: Designing 2 data models...
📊 Data Model: User (4 fields, email index)
📊 Data Model: Todo (5 fields, user_id FK)
🤖 Architect: Creating API contracts...
✅ API Design: 15 REST endpoints defined
📝 Generated architecture/design.md
📝 Generated architecture/adr/001-why-fastapi.md
📝 Generated architecture/openapi.yaml
✅ Architecture design complete
```

---

### 4.3 Coder Agent

**Responsibility:** Generate production-ready code from architecture

**Input:** Subscribes to `catalyst.architecture.proposed`

**Processing Steps:**
1. Load architecture specs from Git
2. Create feature branch: `feature/task-{id}`
3. Generate backend code:
   - Models based on `data-models.json`
   - Routes from `openapi.yaml`
   - Services, utils, tests
4. Generate frontend code:
   - Components, pages, API client
   - State management, routing
5. Generate configs:
   - `requirements.txt`, `package.json`
   - `.env.example`
   - `docker-compose.yml`
6. Commit with detailed messages
7. Create PR (if GitHub integration enabled)

**Output (Git Branch):**
```
feature/task-abc123/
  ├── backend/
  │   ├── main.py
  │   ├── models/
  │   │   ├── user.py
  │   │   └── todo.py
  │   ├── routes/
  │   │   ├── auth.py
  │   │   └── todos.py
  │   ├── services/
  │   │   ├── auth_service.py
  │   │   └── todo_service.py
  │   ├── utils/
  │   │   └── security.py
  │   ├── tests/
  │   │   ├── test_auth.py
  │   │   └── test_todos.py
  │   └── requirements.txt
  ├── frontend/
  │   ├── src/
  │   │   ├── App.js
  │   │   ├── components/
  │   │   │   ├── Login.js
  │   │   │   ├── Register.js
  │   │   │   └── TodoList.js
  │   │   ├── services/
  │   │   │   └── api.js
  │   │   └── store/
  │   │       └── authStore.js
  │   └── package.json
  ├── docker-compose.yml
  ├── Dockerfile.backend
  ├── Dockerfile.frontend
  └── README.md
```

**Git Commits (Atomic, Detailed):**
```bash
git log --oneline feature/task-abc123

def456 feat(frontend): Add TodoList component with CRUD operations
bcd345 feat(frontend): Implement auth UI (Login, Register)
abc234 feat(backend): Add todo routes with auth middleware
9ab123 feat(backend): Implement authentication service with JWT
8ab012 feat(backend): Add User and Todo models
7ab901 chore: Initialize project structure with dependencies
```

**Event Published:**
```json
{
  "actor": "coder",
  "event_type": "code.pr.opened",
  "payload": {
    "branch": "feature/task-abc123",
    "commit": "def456",
    "files_created": 47,
    "lines_of_code": 3842,
    "backend_files": 23,
    "frontend_files": 24,
    "test_files": 12,
    "estimated_coverage": 0.85,
    "pr_url": "https://github.com/org/repo/pull/456",  // if external Git
    "local_repo": "/app/repos/todo-app/.git",
    "git_diff_summary": {
      "additions": 3842,
      "deletions": 0,
      "files_changed": 47
    }
  }
}
```

**Queue:** `catalyst.code.pr.opened` → Tester listens

**User Chat Updates (Real-Time via WebSocket):**
```
🤖 Coder: Setting up project structure...
📁 Created backend/ directory
📁 Created frontend/ directory
🤖 Coder: Generating backend models...
🐍 Generated backend/models/user.py
🐍 Generated backend/models/todo.py
🤖 Coder: Implementing REST API endpoints...
🐍 Generated backend/routes/auth.py (3 endpoints)
🐍 Generated backend/routes/todos.py (5 endpoints)
🤖 Coder: Creating authentication service...
🐍 Generated backend/services/auth_service.py (JWT implementation)
🤖 Coder: Building React frontend...
⚛️ Generated frontend/src/App.js
⚛️ Generated frontend/src/components/Login.js
⚛️ Generated frontend/src/components/Register.js
⚛️ Generated frontend/src/components/TodoList.js
⚛️ Generated frontend/src/services/api.js (API client)
🤖 Coder: Generating tests...
🧪 Generated backend/tests/test_auth.py
🧪 Generated frontend/src/App.test.js
🤖 Coder: Creating deployment configuration...
🐳 Generated Dockerfile.backend
🐳 Generated Dockerfile.frontend
⚙️ Generated docker-compose.yml
📝 Generated README.md
✅ Code generation complete: 47 files created (3,842 lines)
🔀 Committed to branch: feature/task-abc123
📤 Pushed to GitHub: PR #456 opened
```

---

### 4.4 Tester Agent

**Responsibility:** Validate generated code with comprehensive testing

**Input:** Subscribes to `catalyst.code.pr.opened`

**Processing Steps:**
1. Clone/checkout the feature branch
2. Spin up ephemeral test environment (Docker containers)
3. Install dependencies
4. Run unit tests (pytest, jest)
5. Run integration tests
6. Run E2E tests (Playwright)
7. Measure code coverage
8. Security scan (dependencies, secrets)
9. Generate test reports
10. Cleanup ephemeral environment

**Ephemeral Test Environment:**
```yaml
# Auto-generated: test-env-{task-id}.yml
version: '3.8'
services:
  test-backend:
    build: ./backend
    environment:
      - MONGO_URL=mongodb://test-db:27017
      - REDIS_URL=redis://test-redis:6379
      - JWT_SECRET=test_secret_key
      - TESTING=true
    depends_on: [test-db, test-redis]
  
  test-frontend:
    build: ./frontend
    environment:
      - REACT_APP_BACKEND_URL=http://test-backend:8001
  
  test-db:
    image: mongo:5.0
    tmpfs: [/data/db]  # Ephemeral, no persistence
  
  test-redis:
    image: redis:7-alpine
    tmpfs: [/data]

  playwright:
    image: mcr.microsoft.com/playwright:latest
    environment:
      - BASE_URL=http://test-frontend:80
    volumes:
      - ./frontend:/app
    command: npx playwright test
```

**Test Execution:**
```bash
# Backend tests
docker-compose -f test-env-{task-id}.yml run test-backend pytest --cov --junitxml=junit.xml

# Frontend tests
docker-compose -f test-env-{task-id}.yml run test-frontend yarn test --coverage

# E2E tests
docker-compose -f test-env-{task-id}.yml run playwright
```

**Output Artifacts:**
```
artifacts/{task-id}/test-results/
  ├── backend/
  │   ├── junit.xml           # Test results
  │   ├── coverage.xml        # Coverage data
  │   ├── coverage.html       # Coverage report
  │   └── pytest.log
  ├── frontend/
  │   ├── jest-results.xml
  │   ├── coverage/
  │   │   ├── lcov.info
  │   │   └── index.html
  │   └── jest.log
  ├── e2e/
  │   ├── playwright-report/
  │   │   ├── index.html
  │   │   └── screenshots/
  │   └── playwright.log
  ├── security/
  │   ├── dependency-scan.json   # npm audit, safety check
  │   ├── secret-scan.json       # gitleaks
  │   └── sast-results.json      # bandit, eslint security
  └── test-summary.json
```

**test-summary.json:**
```json
{
  "overall_status": "passed",
  "backend": {
    "total": 87,
    "passed": 87,
    "failed": 0,
    "skipped": 0,
    "coverage": 0.89,
    "duration_seconds": 12.4
  },
  "frontend": {
    "total": 45,
    "passed": 45,
    "failed": 0,
    "coverage": 0.82,
    "duration_seconds": 8.2
  },
  "e2e": {
    "total": 12,
    "passed": 12,
    "failed": 0,
    "duration_seconds": 45.8
  },
  "security": {
    "critical": 0,
    "high": 0,
    "medium": 2,
    "low": 5,
    "info": 12
  },
  "total_duration_seconds": 66.4
}
```

**Event Published:**
```json
{
  "actor": "tester",
  "event_type": "test.results",
  "payload": {
    "status": "passed",
    "total_tests": 144,
    "passed": 144,
    "failed": 0,
    "coverage": 0.87,
    "security_critical_issues": 0,
    "artifacts_refs": [
      "file:///app/artifacts/task-123/test-results/test-summary.json",
      "file:///app/artifacts/task-123/test-results/backend/coverage.html"
    ],
    "test_duration_seconds": 66.4
  }
}
```

**Queue:** `catalyst.test.results` → Reviewer listens

**User Chat Updates:**
```
🤖 Tester: Setting up test environment...
🐳 Spinning up test containers...
✅ Test environment ready
🤖 Tester: Running backend unit tests...
🧪 Testing backend/tests/test_auth.py... ✅ 12 passed
🧪 Testing backend/tests/test_todos.py... ✅ 8 passed
✅ Backend tests: 87/87 passed (89% coverage)
🤖 Tester: Running frontend tests...
🧪 Testing App.test.js... ✅ 15 passed
🧪 Testing TodoList.test.js... ✅ 10 passed
✅ Frontend tests: 45/45 passed (82% coverage)
🤖 Tester: Running E2E tests with Playwright...
🎭 E2E: User registration flow... ✅ passed
🎭 E2E: Login and create todo... ✅ passed
🎭 E2E: Complete and delete todo... ✅ passed
✅ E2E tests: 12/12 passed
🤖 Tester: Running security scans...
🔒 Dependency scan: 0 critical, 2 medium vulnerabilities
🔒 Secret scan: No secrets detected
✅ All tests passed! Overall coverage: 87%
📊 Test report: artifacts/task-123/test-results/
```

---

### 4.5 Reviewer Agent

**Input:** Subscribes to `catalyst.test.results`

**Processing:**
1. Load test results
2. Static code analysis (complexity, duplication)
3. Security review (patterns, vulnerabilities)
4. Best practices check
5. AI-powered review (LLM analysis)
6. Generate review score and recommendations

**Output:**
```
artifacts/{task-id}/review/
  ├── review-summary.md
  ├── code-quality.json
  ├── security-review.json
  ├── recommendations.md
  └── review-decision.json
```

**review-decision.json:**
```json
{
  "decision": "approved",
  "overall_score": 92,
  "breakdown": {
    "code_quality": 90,
    "security": 95,
    "test_coverage": 87,
    "documentation": 88,
    "best_practices": 94
  },
  "issues": [
    {
      "severity": "medium",
      "file": "backend/routes/todos.py",
      "line": 45,
      "message": "Consider adding rate limiting to prevent abuse",
      "suggestion": "Use slowapi middleware"
    },
    {
      "severity": "low",
      "file": "frontend/src/components/TodoList.js",
      "line": 23,
      "message": "Missing PropTypes validation",
      "suggestion": "Add PropTypes for better type safety"
    }
  ],
  "recommendations": [
    "Add API rate limiting",
    "Implement request logging",
    "Add error boundary in React",
    "Consider adding Redux for complex state"
  ],
  "blocking_issues": 0,
  "approved_by": "reviewer-agent",
  "approved_at": "2025-10-20T11:15:00Z"
}
```

**Event Published:**
```json
{
  "actor": "reviewer",
  "event_type": "review.decision",
  "payload": {
    "decision": "approved",
    "score": 92,
    "blocking_issues": 0,
    "recommendations": 4,
    "artifacts": ["file:///app/artifacts/task-123/review/review-summary.md"]
  }
}
```

**Queue:** `catalyst.review.decision` → Deployer listens

**User Chat Updates:**
```
🤖 Reviewer: Analyzing code quality...
🔍 Checking backend code... (23 files)
📊 Code complexity: Low (cyclomatic < 10)
📊 Duplication: Minimal (2%)
✅ Backend code quality: 90/100
🔍 Checking frontend code... (24 files)
📊 Component structure: Well organized
📊 Prop validation: Needs improvement
✅ Frontend code quality: 88/100
🤖 Reviewer: Running security review...
🔒 No hardcoded secrets detected
🔒 Dependencies: 2 medium vulnerabilities (patchable)
🔒 Security patterns: JWT properly implemented
✅ Security score: 95/100
🤖 Reviewer: AI-powered review...
💡 Found 4 improvement suggestions
⚠️ 2 issues (0 blocking, 2 recommended)
✅ Code review complete: Score 92/100 - APPROVED
📋 Review report: artifacts/task-123/review/
```

---

### 4.6 Deployer Agent

**Responsibility:** Build, deploy, and provide preview URL

**Input:** Subscribes to `catalyst.review.decision` (approved only)

**Processing Steps:**

**Config-Driven Deployment:**
```python
deployment_config = {
    "mode": os.getenv("PREVIEW_MODE", "docker_in_docker"),
    # Modes: "docker_in_docker", "compose_only", "traefik"
    
    "docker_in_docker": {
        "enabled": True,
        "network": "catalyst_preview_network",
        "port_range": [9000, 9999],
        "auto_cleanup_hours": 24
    },
    
    "compose_only": {
        "enabled": True,
        "output_path": "/app/artifacts/{task_id}/deployment/"
    },
    
    "traefik": {
        "enabled": True,
        "base_domain": "localhost",
        "url_pattern": "{project-name}-{task-id}.localhost"
    }
}
```

**Mode A: Docker-in-Docker (Full Auto-Deploy)**
```python
1. Build images: 
   docker build -t catalyst-preview/{task-id}-backend ./backend
   docker build -t catalyst-preview/{task-id}-frontend ./frontend

2. Create preview network:
   docker network create preview-{task-id}

3. Start containers:
   docker run -d --name preview-{task-id}-db \
     --network preview-{task-id} \
     mongo:5.0

   docker run -d --name preview-{task-id}-backend \
     --network preview-{task-id} \
     -e MONGO_URL=mongodb://preview-{task-id}-db:27017 \
     -p {dynamic-port}:8001 \
     catalyst-preview/{task-id}-backend

   docker run -d --name preview-{task-id}-frontend \
     --network preview-{task-id} \
     -e REACT_APP_BACKEND_URL=http://localhost:{backend-port} \
     -p {dynamic-port}:80 \
     catalyst-preview/{task-id}-frontend

4. Health check:
   curl http://localhost:{frontend-port}/

5. Register with Traefik (if enabled):
   Label containers for auto-discovery
   URL: http://todo-app-{task-id}.localhost
```

**Mode B: Generate docker-compose Only**
```yaml
# Output: artifacts/{task-id}/deployment/docker-compose.preview.yml
version: '3.8'
services:
  backend:
    build: ../../repos/todo-app/backend
    ports: ["8001:8001"]
    environment:
      - MONGO_URL=mongodb://db:27017
    depends_on: [db]
  
  frontend:
    build: ../../repos/todo-app/frontend
    ports: ["3000:80"]
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001
  
  db:
    image: mongo:5.0
    volumes: [db_data:/data/db]

volumes:
  db_data:
```

**Mode C: Traefik Auto-Routing**
```yaml
# Add labels to containers
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.todo-app-{task-id}.rule=Host(`todo-app-{task-id}.localhost`)"
  - "traefik.http.services.todo-app-{task-id}.loadbalancer.server.port=80"
```

**Output:**
```
artifacts/{task-id}/deployment/
  ├── Dockerfile.backend
  ├── Dockerfile.frontend
  ├── docker-compose.preview.yml
  ├── k8s/                     # For production
  │   ├── deployment.yaml
  │   ├── service.yaml
  │   ├── ingress.yaml
  │   └── configmap.yaml
  ├── deployment-record.json
  └── DEPLOYMENT.md            # Instructions
```

**Preview Deployment Record:**
```json
{
  "task_id": "abc123",
  "deployment_mode": "docker_in_docker",
  "containers": [
    {
      "name": "preview-abc123-backend",
      "container_id": "docker://xyz789",
      "image": "catalyst-preview/abc123-backend:latest",
      "port": 9001,
      "status": "healthy"
    },
    {
      "name": "preview-abc123-frontend",
      "container_id": "docker://xyz790",
      "image": "catalyst-preview/abc123-frontend:latest",
      "port": 9002,
      "status": "healthy"
    }
  ],
  "urls": {
    "frontend": "http://localhost:9002",
    "backend": "http://localhost:9001/api",
    "traefik": "http://todo-app-abc123.localhost"
  },
  "deployed_at": "2025-10-20T11:20:00Z",
  "expires_at": "2025-10-21T11:20:00Z",
  "health_checks": {
    "last_check": "2025-10-20T11:21:00Z",
    "backend": "healthy",
    "frontend": "healthy"
  }
}
```

**Event Published:**
```json
{
  "actor": "deployer",
  "event_type": "deploy.status",
  "payload": {
    "status": "deployed",
    "preview_url": "http://todo-app-abc123.localhost",
    "fallback_url": "http://localhost:9002",
    "backend_url": "http://localhost:9001/api",
    "container_ids": ["xyz789", "xyz790"],
    "health": "healthy",
    "deployment_mode": "docker_in_docker"
  }
}
```

**Queue:** `catalyst.deploy.status` → UI/Chat listens for completion

**User Chat Updates:**
```
🤖 Deployer: Building Docker images...
🐳 Building backend image... ✅ (1.2 GB, 45s)
🐳 Building frontend image... ✅ (890 MB, 32s)
🤖 Deployer: Creating preview environment...
🌐 Creating isolated network: preview-abc123
🤖 Deployer: Starting containers...
🚀 Started MongoDB (preview-abc123-db)
🚀 Started Backend (preview-abc123-backend) on port 9001
🚀 Started Frontend (preview-abc123-frontend) on port 9002
🤖 Deployer: Running health checks...
✅ Backend health check: PASSED
✅ Frontend health check: PASSED
🤖 Deployer: Registering with Traefik...
✅ Preview deployment complete!

🎉 Your app is live!
   Frontend: http://todo-app-abc123.localhost
   Fallback: http://localhost:9002
   Backend:  http://localhost:9001/api
   
📋 Deployment details: artifacts/task-abc123/deployment/
⏰ Preview expires in 24 hours
```

---

### 4.7 Explorer Agent (Parallel/On-Demand)

**Trigger:** User command or scheduled scan

**Input Types:**

**A. GitHub Repository Analysis**
```json
{
  "type": "github",
  "target": "https://github.com/user/repo",
  "credentials": {"github_token": "..."},
  "analysis_depth": "full"  // quick, standard, full
}
```

**B. Running Deployment Scan**
```json
{
  "type": "deployment",
  "target": "http://app.example.com",
  "credentials": {"api_key": "..."},
  "checks": ["health", "performance", "security", "apis"]
}
```

**C. Database Analysis**
```json
{
  "type": "database",
  "target": "mongodb://host:27017",
  "credentials": {"username": "...", "password": "..."},
  "read_only": true
}
```

**Processing - GitHub:**
1. Clone repository
2. Analyze file structure
3. Parse package.json/requirements.txt (dependencies)
4. Identify tech stack
5. Measure code metrics (LOC, complexity, test coverage)
6. Security scan (CVEs, secrets)
7. Detect patterns, frameworks
8. Generate dependency graph

**Processing - Deployment:**
1. Probe endpoints (OpenAPI discovery)
2. Measure response times
3. Check SSL/security headers
4. Lighthouse audit (frontend)
5. Detect technologies (Wappalyzer-style)
6. Test auth mechanisms

**Processing - Database:**
1. Connect read-only
2. Get schema/collections
3. Analyze relationships
4. Check indexes
5. Identify slow query patterns
6. Suggest optimizations

**Output:**
```
explorer/{scan-id}/
  ├── report.md                  # Executive summary
  ├── findings.json              # Structured data
  ├── tech-stack.json            # Detected technologies
  ├── dependencies/
  │   ├── dependency-graph.svg
  │   ├── cves.json              # Security vulnerabilities
  │   └── outdated.json          # Package updates needed
  ├── architecture/
  │   ├── inferred-architecture.md
  │   └── component-map.svg
  ├── security/
  │   ├── security-score.json
  │   └── recommendations.md
  └── suggested-tasks.yaml       # Feed to Planner
```

**findings.json (GitHub example):**
```json
{
  "scan_id": "scan-xyz",
  "scan_type": "github",
  "target": "https://github.com/user/todo-app",
  "scanned_at": "2025-10-20T12:00:00Z",
  "summary": {
    "tech_stack": ["React", "Node.js", "Express", "MongoDB"],
    "languages": {"JavaScript": 78, "CSS": 15, "HTML": 7},
    "lines_of_code": 5432,
    "file_count": 87,
    "test_coverage": 0.65,
    "dependencies": 47,
    "vulnerabilities": {"critical": 0, "high": 1, "medium": 3}
  },
  "tech_stack_details": {
    "frontend": {
      "framework": "React 18.2.0",
      "state_mgmt": "Redux Toolkit",
      "routing": "React Router v6",
      "ui_library": "Material-UI"
    },
    "backend": {
      "framework": "Express 4.18.0",
      "orm": "Mongoose",
      "auth": "Passport.js + JWT"
    },
    "database": "MongoDB 5.0",
    "testing": ["Jest", "React Testing Library"]
  },
  "architecture_inferred": {
    "pattern": "REST API + SPA",
    "layers": ["frontend", "backend", "database"],
    "authentication": "JWT-based",
    "api_endpoints_detected": 12
  },
  "security_findings": [
    {
      "severity": "high",
      "package": "express",
      "version": "4.17.1",
      "vulnerability": "CVE-2022-24999",
      "fix": "Upgrade to 4.18.2"
    }
  ],
  "can_replicate": true,
  "similarity_to_catalyst_templates": 0.78,
  "suggested_improvements": [
    "Add TypeScript for type safety",
    "Increase test coverage to 80%+",
    "Implement proper error handling",
    "Add API documentation (Swagger)"
  ]
}
```

**Event Published:**
```json
{
  "actor": "explorer",
  "event_type": "explorer.findings",
  "payload": {
    "scan_id": "scan-xyz",
    "scan_type": "github",
    "target": "https://github.com/user/todo-app",
    "can_replicate": true,
    "tech_stack": ["React", "Express", "MongoDB"],
    "similarity_score": 0.78,
    "suggested_tasks": [
      "Upgrade Express to fix CVE",
      "Add TypeScript support",
      "Increase test coverage"
    ],
    "findings_ref": "file:///app/explorer/scan-xyz/findings.json"
  }
}
```

**Integration with Planner:**

User: **"analyze this repo and build something similar"**

Flow:
1. Explorer scans GitHub repo → outputs findings
2. Planner receives explorer.findings event
3. Planner uses findings as context:
   - Tech stack → same stack in plan
   - Architecture → similar structure
   - Features → enhanced version
4. Continue normal flow (Architect → Coder...)

**User Chat Updates:**
```
🔍 Explorer: Cloning repository...
✅ Repository cloned: 87 files, 5,432 LOC
🔍 Explorer: Analyzing tech stack...
✅ Detected: React 18 + Express + MongoDB
🔍 Explorer: Scanning dependencies...
📦 Found 47 dependencies
⚠️ Security: 1 high, 3 medium vulnerabilities
🔍 Explorer: Analyzing architecture...
✅ Pattern: REST API + SPA
✅ Detected 12 API endpoints
🔍 Explorer: Generating recommendations...
💡 4 improvement suggestions identified
✅ Exploration complete!
📊 Similarity to Catalyst templates: 78%
🚀 Can replicate this architecture? YES

Would you like me to:
1. Build a similar app with improvements?
2. Create a migration plan to Catalyst stack?
3. Just show me the findings?
```

---

## 5. Event Streaming Design

### 5.1 RabbitMQ Topic Configuration

**Exchange Type:** Topic Exchange
**Exchange Name:** `catalyst.events`

**Topics (Routing Keys):**
```
catalyst.plan.created             # Planner publishes
catalyst.architecture.proposed    # Architect publishes
catalyst.code.pr.opened          # Coder publishes
catalyst.test.results            # Tester publishes
catalyst.review.decision         # Reviewer publishes
catalyst.deploy.status           # Deployer publishes
catalyst.deploy.complete         # Final status
catalyst.explorer.findings       # Explorer publishes
catalyst.task.progress           # Generic progress updates
```

**Agent Subscriptions:**
```python
# Architect
queue: "architect-queue"
binds_to: ["catalyst.plan.created"]

# Coder
queue: "coder-queue"
binds_to: ["catalyst.architecture.proposed"]

# Tester
queue: "tester-queue"
binds_to: ["catalyst.code.pr.opened"]

# Reviewer
queue: "reviewer-queue"
binds_to: ["catalyst.test.results"]

# Deployer
queue: "deployer-queue"
binds_to: ["catalyst.review.decision"]
filters: ["payload.decision = 'approved'"]

# UI/WebSocket
queue: "ui-updates-{task-id}"
binds_to: ["catalyst.*.{task-id}"]  # All events for specific task
```

### 5.2 Event Schema (Versioned)

**Base Event Envelope (v1):**
```python
from pydantic import BaseModel
from typing import Literal, Dict, Any
from datetime import datetime
from uuid import UUID

class AgentEvent(BaseModel):
    version: Literal["v1"] = "v1"
    trace_id: UUID
    task_id: UUID
    actor: Literal["planner", "architect", "coder", "tester", "reviewer", "deployer", "explorer", "orchestrator"]
    event_type: str  # {actor}.{action} e.g., "planner.created", "code.pr.opened"
    repo: str        # "catalyst-generated/todo-app"
    branch: str      # "feature/task-abc123" or "main"
    commit: str      # Git commit SHA (if applicable)
    timestamp: datetime
    payload: Dict[str, Any]  # Agent-specific data
    metadata: Dict[str, Any] = {}  # Optional metadata
```

**Event Publishing (Python):**
```python
import pika
import json
from uuid import UUID

class EventPublisher:
    def __init__(self, rabbitmq_url: str):
        self.connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange='catalyst.events',
            exchange_type='topic',
            durable=True
        )
    
    def publish(self, event: AgentEvent):
        routing_key = f"catalyst.{event.event_type}"
        
        message = event.model_dump_json()
        
        self.channel.basic_publish(
            exchange='catalyst.events',
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent
                content_type='application/json',
                headers={
                    'trace_id': str(event.trace_id),
                    'task_id': str(event.task_id)
                }
            )
        )
        
        # Also save to Postgres for audit
        await save_event_to_postgres(event)
```

**Event Consumption (Python):**
```python
class AgentConsumer:
    def __init__(self, agent_name: str, rabbitmq_url: str):
        self.agent_name = agent_name
        self.connection = pika.BlockingConnection(
            pika.URLParameters(rabbitmq_url)
        )
        self.channel = self.connection.channel()
        
        # Declare queue
        queue_name = f"{agent_name}-queue"
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        # Bind to relevant topics
        bindings = self._get_bindings()
        for routing_key in bindings:
            self.channel.queue_bind(
                exchange='catalyst.events',
                queue=queue_name,
                routing_key=routing_key
            )
    
    def start_consuming(self, callback):
        self.channel.basic_qos(prefetch_count=1)  # Process one at a time
        self.channel.basic_consume(
            queue=f"{self.agent_name}-queue",
            on_message_callback=callback,
            auto_ack=False  # Manual ack after processing
        )
        self.channel.start_consuming()
```

### 5.3 Error Handling & Retries

**Dead Letter Queue:**
```python
# Failed messages go to DLQ after 3 retries
dlq_exchange = "catalyst.dlq"
dlq_queue = "failed-events"

# Queue arguments for auto-retry
arguments = {
    'x-dead-letter-exchange': 'catalyst.dlq',
    'x-message-ttl': 60000,  # 1 minute
    'x-max-retries': 3
}
```

**Retry Logic:**
```python
async def process_event_with_retry(event: AgentEvent, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await agent.process(event)
            return result
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                # Send to DLQ
                await send_to_dlq(event, error=str(e))
                raise
```

---

## 6. Storage Strategy

### 6.1 Storage Tier Design

| Data Type | Storage | Why | TTL/Retention |
|-----------|---------|-----|---------------|
| **Task State** | Postgres | ACID, queries | Infinite |
| **Events** | Postgres | Audit trail | 90 days |
| **Conversations** | MongoDB | Flexible schema | Infinite |
| **Agent Logs** | MongoDB | High volume, search | 30 days |
| **Source Code** | Git (local) | Version control | Infinite |
| **Source Code** | GitHub | Backup, collaboration | Infinite |
| **Test Artifacts** | File System | Large files | 7 days |
| **Build Images** | Docker Registry | Container images | 30 days |
| **Cache** | Redis | Performance | By TTL |
| **Embeddings** | Qdrant | Vector search | Infinite |

### 6.2 Git Storage Strategy

**Dual-Mode Git Storage:**

**Mode 1: Local Git Repos**
```
/app/repos/
  ├── {project-name-1}/
  │   ├── .git/
  │   ├── planning/
  │   ├── architecture/
  │   ├── backend/
  │   ├── frontend/
  │   └── README.md
  └── {project-name-2}/
      └── ...
```

**Mode 2: External GitHub Push**
```python
# After local commit
git remote add origin https://github.com/org/{project-name}
git push origin feature/task-{id}

# Create PR via GitHub API
POST /repos/{owner}/{repo}/pulls
{
  "title": "feat: Todo App - Task abc123",
  "head": "feature/task-abc123",
  "base": "main",
  "body": "Generated by Catalyst AI\n\n[Auto-generated code]"
}
```

**Configuration:**
```python
GIT_CONFIG = {
    "mode": "both",  # "local", "github", "both"
    "local": {
        "base_path": "/app/repos",
        "auto_commit": True,
        "commit_author": "Catalyst AI <ai@catalyst.dev>"
    },
    "github": {
        "enabled": True,
        "token": os.getenv("GITHUB_TOKEN"),
        "org": os.getenv("GITHUB_ORG", "catalyst-generated"),
        "create_repo": True,  # Auto-create if doesn't exist
        "create_pr": True,
        "pr_auto_merge": False  # Require human review
    }
}
```

### 6.3 Artifact Storage Structure

```
/app/artifacts/
  ├── {task-id}/
  │   ├── planning/
  │   │   └── plan.yaml
  │   ├── architecture/
  │   │   ├── design.md
  │   │   └── openapi.yaml
  │   ├── test-results/
  │   │   ├── backend/
  │   │   │   ├── junit.xml
  │   │   │   └── coverage.html
  │   │   ├── frontend/
  │   │   └── e2e/
  │   ├── review/
  │   │   └── review-summary.md
  │   └── deployment/
  │       ├── docker-compose.preview.yml
  │       └── deployment-record.json
  └── {task-id-2}/
      └── ...
```

---

## 7. Preview Deployment System

### 7.1 Three Deployment Modes

**Mode A: Docker-in-Docker (Full Auto-Deploy)**

**Use Case:** Developer wants instant preview
**Requirements:** Docker socket access

```python
class DockerInDockerDeployer:
    async def deploy(self, task_id: str, project_path: str) -> PreviewDeployment:
        # 1. Build images
        backend_image = await self._build_image(
            f"{project_path}/backend",
            f"catalyst-preview/{task_id}-backend"
        )
        
        frontend_image = await self._build_image(
            f"{project_path}/frontend",
            f"catalyst-preview/{task_id}-frontend"
        )
        
        # 2. Create network
        network = await self._create_network(f"preview-{task_id}")
        
        # 3. Start database
        db_container = await docker.containers.run(
            image="mongo:5.0",
            name=f"preview-{task_id}-db",
            network=network,
            detach=True,
            remove=True  # Auto-cleanup on stop
        )
        
        # 4. Start backend
        backend_port = await self._get_available_port(range(9000, 9999))
        backend_container = await docker.containers.run(
            image=backend_image,
            name=f"preview-{task_id}-backend",
            network=network,
            ports={'8001/tcp': backend_port},
            environment={
                'MONGO_URL': f'mongodb://preview-{task_id}-db:27017',
                'CORS_ORIGINS': '*'
            },
            detach=True,
            remove=True
        )
        
        # 5. Start frontend
        frontend_port = await self._get_available_port(range(10000, 10999))
        frontend_container = await docker.containers.run(
            image=frontend_image,
            name=f"preview-{task_id}-frontend",
            network=network,
            ports={'80/tcp': frontend_port},
            environment={
                'REACT_APP_BACKEND_URL': f'http://localhost:{backend_port}'
            },
            labels={
                'traefik.enable': 'true',
                'traefik.http.routers.{task_id}.rule': f'Host(`{project_name}-{task_id}.localhost`)'
            },
            detach=True,
            remove=True
        )
        
        # 6. Health check
        await self._wait_for_health(backend_container, frontend_container)
        
        # 7. Save to database
        preview = PreviewDeployment(
            task_id=task_id,
            url_traefik=f"http://{project_name}-{task_id}.localhost",
            url_direct=f"http://localhost:{frontend_port}",
            backend_url=f"http://localhost:{backend_port}",
            containers=[db_container.id, backend_container.id, frontend_container.id],
            status="healthy",
            expires_at=datetime.now() + timedelta(hours=24)
        )
        
        await save_preview_deployment(preview)
        
        return preview
```

**Mode B: Compose-Only (Generate Files)**

**Use Case:** User wants to manually review/test

```python
class ComposeOnlyDeployer:
    async def deploy(self, task_id: str, project_path: str) -> Dict:
        # Generate docker-compose.preview.yml
        compose_content = self._generate_compose_yaml(project_path)
        
        compose_path = f"/app/artifacts/{task_id}/deployment/docker-compose.preview.yml"
        with open(compose_path, 'w') as f:
            f.write(compose_content)
        
        # Generate instructions
        instructions = f"""
# Preview Deployment Instructions

## Quick Start
cd {project_path}
docker-compose -f ../../artifacts/{task_id}/deployment/docker-compose.preview.yml up -d

## Access
- Frontend: http://localhost:3000
- Backend: http://localhost:8001/api

## Stop
docker-compose -f ../../artifacts/{task_id}/deployment/docker-compose.preview.yml down
        """
        
        return {
            "mode": "compose_only",
            "compose_file": compose_path,
            "instructions": instructions
        }
```

**Mode C: Traefik Auto-Routing**

**Use Case:** Best UX with clean URLs

**Traefik Config:**
```yaml
# traefik.yml
entryPoints:
  web:
    address: ":80"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: catalyst-network

api:
  dashboard: true
  insecure: true
```

**Container Labels for Auto-Discovery:**
```python
labels = {
    'traefik.enable': 'true',
    'traefik.http.routers.{project}-{task}.rule': f'Host(`{project}-{task}.localhost`)',
    'traefik.http.routers.{project}-{task}.entrypoints': 'web',
    'traefik.http.services.{project}-{task}.loadbalancer.server.port': '80'
}
```

**Result:** 
- Access via: `http://todo-app-abc123.localhost`
- Traefik automatically routes to correct container
- Clean URLs, no port numbers

### 7.2 Preview Lifecycle Management

**Creation:**
```python
1. Build images
2. Start containers with labels
3. Run health checks (15s timeout)
4. Register in Postgres preview_deployments table
5. Return preview URL
```

**Health Monitoring:**
```python
# Background task runs every 60 seconds
async def monitor_preview_health():
    previews = await get_active_previews()
    
    for preview in previews:
        try:
            # Check health
            response = await httpx.get(f"{preview.health_check_url}/health", timeout=5)
            
            if response.status_code == 200:
                await update_preview_health(preview.id, "healthy")
            else:
                await update_preview_health(preview.id, "unhealthy")
        except:
            await update_preview_health(preview.id, "unreachable")
```

**Auto-Cleanup:**
```python
# Runs every hour
async def cleanup_expired_previews():
    expired = await get_expired_previews()
    
    for preview in expired:
        # Stop and remove containers
        for container_id in preview.containers:
            await docker.containers.get(container_id).stop()
            await docker.containers.get(container_id).remove()
        
        # Remove network
        await docker.networks.get(f"preview-{preview.task_id}").remove()
        
        # Mark as cleaned up
        await update_preview_status(preview.id, "expired")
```

**Manual Cleanup:**
```python
# API endpoint: DELETE /api/preview/{task_id}
async def delete_preview(task_id: str):
    preview = await get_preview_by_task(task_id)
    
    if preview:
        await cleanup_preview(preview)
        return {"status": "deleted"}
```

---

## 8. Explorer Agent Capabilities

### 8.1 GitHub Repository Analysis

**Supported Analysis:**
- File structure and organization
- Tech stack detection (package.json, requirements.txt, etc.)
- Dependency analysis with vulnerability scanning
- Code metrics (LOC, complexity, maintainability index)
- Git history analysis (commit patterns, contributors)
- License detection
- Documentation quality
- Test coverage estimation

**Example Implementation:**
```python
class GitHubExplorer:
    async def analyze_repo(self, repo_url: str, token: str) -> ExplorerFindings:
        # 1. Clone repo
        repo_path = await self._clone_repo(repo_url, token)
        
        # 2. Detect tech stack
        tech_stack = await self._detect_tech_stack(repo_path)
        
        # 3. Analyze dependencies
        deps = await self._analyze_dependencies(repo_path)
        
        # 4. Security scan
        security = await self._security_scan(repo_path)
        
        # 5. Code metrics
        metrics = await self._calculate_metrics(repo_path)
        
        # 6. Generate architecture inference
        architecture = await self._infer_architecture(repo_path, tech_stack)
        
        # 7. Create findings report
        findings = ExplorerFindings(
            tech_stack=tech_stack,
            dependencies=deps,
            security=security,
            metrics=metrics,
            architecture=architecture
        )
        
        # 8. Generate visual diagrams
        await self._generate_diagrams(findings, repo_path)
        
        return findings
    
    async def _detect_tech_stack(self, repo_path: str) -> TechStack:
        tech_stack = {"frontend": None, "backend": None, "database": None}
        
        # Check for package.json
        if os.path.exists(f"{repo_path}/package.json"):
            with open(f"{repo_path}/package.json") as f:
                pkg = json.load(f)
                deps = pkg.get("dependencies", {})
                
                if "react" in deps:
                    tech_stack["frontend"] = f"React {deps['react']}"
                elif "vue" in deps:
                    tech_stack["frontend"] = f"Vue {deps['vue']}"
                elif "angular" in deps:
                    tech_stack["frontend"] = f"Angular {deps['@angular/core']}"
                
                if "express" in deps:
                    tech_stack["backend"] = f"Express {deps['express']}"
        
        # Check for requirements.txt
        if os.path.exists(f"{repo_path}/requirements.txt"):
            with open(f"{repo_path}/requirements.txt") as f:
                for line in f:
                    if "fastapi" in line.lower():
                        tech_stack["backend"] = f"FastAPI {line.split('==')[1] if '==' in line else 'latest'}"
                    elif "django" in line.lower():
                        tech_stack["backend"] = f"Django {line.split('==')[1] if '==' in line else 'latest'}"
                    elif "flask" in line.lower():
                        tech_stack["backend"] = f"Flask {line.split('==')[1] if '==' in line else 'latest'}"
        
        return tech_stack
```

### 8.2 Explorer Integration with Planner

**Workflow:**

User: **"Analyze github.com/user/blog and build an improved version"**

```python
# 1. Chat detects "analyze" intent → triggers Explorer
explorer_result = await explorer.analyze_repo(
    "https://github.com/user/blog",
    github_token
)

# 2. Explorer publishes findings
event = AgentEvent(
    actor="explorer",
    event_type="explorer.findings",
    payload=explorer_result
)
await publish_event(event)

# 3. Planner subscribes to explorer.findings
# When building, Planner includes findings as context
plan = await planner.create_plan(
    user_requirements="Build an improved version",
    context={
        "explorer_findings": explorer_result,
        "base_architecture": explorer_result.architecture,
        "improvements": explorer_result.suggested_improvements
    }
)

# 4. Plan includes improvements
# "Build similar blog but with: TypeScript, better auth, 90% test coverage"
```

---

## 9. Configuration & Dual-Mode Operation

### 9.1 Orchestration Modes

**Sequential Mode (Current - Fallback):**
```python
# For K8s environment without Docker/RabbitMQ
ORCHESTRATION_MODE=sequential

# Flow: Direct function calls
async def execute_sequential(task_id, project_id, requirements):
    plan = await planner.create_plan(requirements)
    architecture = await architect.design_architecture(plan)
    code = await coder.generate_code(architecture)
    test_results = await tester.test_application(code)
    review = await reviewer.review_code(code, test_results)
    if review.approved:
        deployment = await deployer.deploy(code)
    return deployment
```

**Event-Driven Mode (New - Docker Desktop):**
```python
# For Docker Desktop with full infrastructure
ORCHESTRATION_MODE=event_driven

# Flow: Event-driven via RabbitMQ
async def execute_event_driven(task_id, project_id, requirements):
    # Orchestrator only triggers first agent
    event = create_planner_event(task_id, requirements)
    await publish_event(event)
    
    # Each agent listens to its queue and processes independently
    # Planner → publishes → Architect listens → processes → publishes → Coder listens...
    # Fully asynchronous, parallel where possible
```

### 9.2 Configuration File

**config.yaml:**
```yaml
orchestration:
  mode: event_driven  # or sequential
  
  sequential:
    enabled: true
    timeout_seconds: 600
    
  event_driven:
    enabled: true
    rabbitmq_url: ${RABBITMQ_URL}
    max_concurrent_tasks: 5
    retry_attempts: 3

storage:
  git:
    mode: both  # local, github, both
    local_path: /app/repos
    github_token: ${GITHUB_TOKEN}
    github_org: catalyst-generated
    auto_push: true
    create_pr: true
  
  artifacts:
    path: /app/artifacts
    retention_days: 30
  
  databases:
    postgres:
      url: ${POSTGRES_URL}
      pool_size: 20
    
    mongodb:
      url: ${MONGO_URL}
      database: catalyst_db

preview:
  mode: docker_in_docker  # docker_in_docker, compose_only, traefik
  
  docker_in_docker:
    enabled: true
    port_range: [9000, 9999]
    auto_cleanup_hours: 24
    health_check_interval: 60
  
  traefik:
    enabled: true
    base_domain: localhost
    dashboard_port: 8080
  
  compose_only:
    enabled: true
    output_path: /app/artifacts/{task_id}/deployment/

explorer:
  enabled: true
  max_concurrent_scans: 3
  
  github:
    enabled: true
    max_repo_size_mb: 500
    clone_depth: 100
  
  deployment:
    enabled: true
    timeout_seconds: 30
  
  database:
    enabled: true
    read_only: true

agents:
  planner:
    llm_model: gpt-4o-mini  # Cheaper for planning
    max_features: 20
  
  architect:
    llm_model: claude-3-7-sonnet-20250219  # Better for architecture
    generate_diagrams: true
  
  coder:
    llm_model: gpt-4o-mini  # Cheaper, still good for code
    max_files_per_batch: 10
  
  tester:
    run_unit_tests: true
    run_integration_tests: true
    run_e2e_tests: true
    min_coverage: 0.80
  
  reviewer:
    llm_model: claude-3-7-sonnet-20250219
    min_approval_score: 75
  
  deployer:
    default_mode: docker_in_docker
    auto_cleanup: true
```

### 9.3 Mode Switching Logic

```python
# backend/orchestrator/dual_mode_orchestrator.py

class DualModeOrchestrator:
    def __init__(self, config: Dict):
        self.mode = config.get("orchestration", {}).get("mode", "sequential")
        
        if self.mode == "event_driven":
            self.executor = EventDrivenExecutor(config)
        else:
            self.executor = SequentialExecutor(config)
    
    async def execute_task(self, task_id: str, project_id: str, requirements: str):
        logger.info(f"Executing task {task_id} in {self.mode} mode")
        
        if self.mode == "event_driven":
            return await self._execute_event_driven(task_id, project_id, requirements)
        else:
            return await self._execute_sequential(task_id, project_id, requirements)
    
    async def _execute_event_driven(self, task_id, project_id, requirements):
        # Publish initial event to trigger Planner
        event = AgentEvent(
            trace_id=uuid.uuid4(),
            task_id=task_id,
            actor="orchestrator",
            event_type="task.initiated",
            repo=f"catalyst-generated/{project_id}",
            branch="main",
            commit="",
            timestamp=datetime.now(),
            payload={
                "project_id": project_id,
                "requirements": requirements,
                "next_agent": "planner"
            }
        )
        
        await self.event_publisher.publish(event)
        
        # Orchestrator's job is done - agents handle the rest via events
        return {
            "status": "initiated",
            "mode": "event_driven",
            "trace_id": str(event.trace_id)
        }
    
    async def _execute_sequential(self, task_id, project_id, requirements):
        # Current implementation - Phase1/Phase2 orchestrator
        # Direct function calls
        return await self.phase2_orchestrator.execute_task(
            task_id, project_id, requirements
        )
```

---

## 10. Implementation Phases

### Phase 1: Infrastructure & Event Foundation (Week 1)

**Tasks:**
1. ✅ Add Postgres to docker-compose
2. ✅ Create init.sql with table schemas
3. ✅ Configure RabbitMQ topics
4. ✅ Create event schemas (Pydantic models)
5. ✅ Implement EventPublisher and EventConsumer base classes
6. ✅ Add Traefik to docker-compose
7. ✅ Create configuration system (config.yaml)
8. ✅ Implement DualModeOrchestrator

**Deliverables:**
- Updated docker-compose.yml with Postgres, Traefik
- Event system library (`backend/events/`)
- Config management (`backend/config/`)
- Database migrations

**Testing:**
- Can start all services with `make start`
- RabbitMQ topics exist
- Postgres tables created
- Events can be published/consumed

---

### Phase 2: Agent Refactoring (Week 1-2)

**Tasks:**
1. ✅ Refactor each agent to implement event-driven interface
2. ✅ Update Planner to output plan.yaml + publish event
3. ✅ Update Architect to consume plan event, output architecture/
4. ✅ Update Coder to consume architecture event, create Git branch
5. ✅ Update Tester to spin up ephemeral Docker environment
6. ✅ Update Reviewer to load test results, publish decision
7. ✅ Update Deployer with 3 deployment modes
8. ✅ Add detailed logging to each agent (file-level)

**Deliverables:**
- Event-driven agents in `backend/agents_v2/`
- Git integration service
- Docker deployment service
- Enhanced logging system

**Testing:**
- End-to-end event flow (Planner → Deployer)
- Verify events in RabbitMQ management UI
- Check Postgres event audit trail
- Verify Git commits created

---

### Phase 3: Git Integration (Week 2)

**Tasks:**
1. ✅ Implement local Git repository manager
2. ✅ Create GitHub API integration service
3. ✅ Auto-commit with detailed messages
4. ✅ Branch management (create, merge, delete)
5. ✅ PR creation on GitHub (optional)
6. ✅ Dual-mode: local + GitHub simultaneously

**Deliverables:**
- Git service (`backend/services/git_service_v2.py`)
- GitHub integration (`backend/integrations/github_integration.py`)
- Repo storage at `/app/repos/`

**Testing:**
- Create local Git repo
- Commit code
- Push to GitHub
- Create PR
- Verify both local and remote have same code

---

### Phase 4: Preview Deployments (Week 2-3)

**Tasks:**
1. ✅ Implement DockerInDockerDeployer
2. ✅ Implement ComposeOnlyDeployer
3. ✅ Implement TraefikDeployer
4. ✅ Port allocation system (9000-9999)
5. ✅ Health check monitoring
6. ✅ Auto-cleanup scheduler
7. ✅ Preview API endpoints (list, get, delete)

**Deliverables:**
- Deployment engine (`backend/services/preview_deployment.py`)
- Traefik configuration
- Preview management API
- Cleanup scheduler

**Testing:**
- Deploy generated app
- Access via preview URL
- Health checks working
- Auto-cleanup after TTL
- Manual cleanup works

---

### Phase 5: Explorer Agent (Week 3-4)

**Tasks:**
1. ✅ GitHub analysis implementation
2. ✅ Deployment scanning (live apps)
3. ✅ Database schema analysis
4. ✅ Tech stack detection
5. ✅ Security vulnerability scanning
6. ✅ Architecture inference
7. ✅ Integration with Planner (enrichment)

**Deliverables:**
- Explorer agent v2
- Analysis report generator
- Diagram generator (architecture, dependencies)
- Planner enrichment service

**Testing:**
- Analyze sample GitHub repo
- Scan running deployment
- Analyze MongoDB schema
- Feed results to Planner
- Build similar app

---

### Phase 6: Frontend Enhancements (Week 4)

**Tasks:**
1. ✅ Real-time WebSocket updates (already started)
2. ✅ Task progress visualization
3. ✅ Preview iframe integration
4. ✅ File tree viewer for generated code
5. ✅ Test results display
6. ✅ Architecture diagram viewer

**Deliverables:**
- Enhanced ChatInterface with real-time updates
- Preview viewer component
- Code browser component
- Analytics dashboard enhancements

---

## 11. API Specifications

### 11.1 New REST Endpoints

```python
# Preview Management
GET    /api/preview                        # List all active previews
GET    /api/preview/{task_id}              # Get preview details
DELETE /api/preview/{task_id}              # Cleanup preview
POST   /api/preview/{task_id}/restart      # Restart preview

# Git Management
GET    /api/git/repos                      # List local repos
GET    /api/git/repos/{project_id}         # Get repo details
GET    /api/git/repos/{project_id}/commits # Get commit history
POST   /api/git/repos/{project_id}/push    # Push to GitHub
POST   /api/git/repos/{project_id}/pr      # Create PR

# Explorer
POST   /api/explorer/scan                  # Trigger scan
GET    /api/explorer/scans                 # List scans
GET    /api/explorer/scans/{scan_id}       # Get scan results
GET    /api/explorer/scans/{scan_id}/graph # Get dependency graph

# Events & Monitoring
GET    /api/events/{task_id}               # Get events for task
GET    /api/events/{task_id}/stream        # SSE stream of events
GET    /api/tasks/{task_id}/progress       # Get current progress
```

### 11.2 WebSocket Protocol

**Connection:** `wss://{host}/ws/{task_id}`

**Messages from Backend:**
```json
{
  "type": "agent_log",
  "task_id": "abc123",
  "agent_name": "Coder",
  "message": "Generated backend/models/user.py",
  "level": "info",
  "timestamp": "2025-10-20T12:00:00Z"
}

{
  "type": "progress",
  "task_id": "abc123",
  "phase": "coding",
  "progress": 0.45,
  "files_created": 21,
  "total_estimated_files": 47
}

{
  "type": "preview_ready",
  "task_id": "abc123",
  "preview_url": "http://todo-app-abc123.localhost",
  "fallback_url": "http://localhost:9002"
}

{
  "type": "task_complete",
  "task_id": "abc123",
  "status": "completed",
  "artifacts": {
    "code": "git://repos/todo-app",
    "tests": "file://artifacts/abc123/test-results/",
    "preview": "http://todo-app-abc123.localhost"
  }
}
```

---

## 12. Deployment Guide

### 12.1 Docker Desktop Setup (Complete)

**Single Command:**
```bash
make setup-complete-stack
make start-all-services
```

**Services Started:**
1. PostgreSQL (state DB)
2. MongoDB (document DB)
3. Redis (caching)
4. Qdrant (vector DB)
5. RabbitMQ (event streaming)
6. Traefik (routing)
7. Backend (API + agents)
8. Frontend (UI)

**Total: 8 services**

### 12.2 Testing the System

**Test 1: Basic Build**
```bash
# 1. Open http://localhost:3000
# 2. Send: "build a hello world app"
# 3. Watch real-time updates
# 4. Preview URL appears: http://hello-world-abc123.localhost
```

**Test 2: Explorer Integration**
```bash
# 1. Send: "analyze https://github.com/user/sample-app"
# 2. Explorer scans repo
# 3. Send: "build something similar"
# 4. Planner uses findings as context
```

**Test 3: Multiple Concurrent Tasks**
```bash
# Send 3 build requests
# All process in parallel via event system
# Each gets own preview URL
```

---

## 13. Migration Checklist

### Prerequisites
- [ ] User confirms all phases approved
- [ ] Docker Desktop available for testing
- [ ] GitHub token available (optional)

### Implementation Order
1. [ ] Create event system foundation
2. [ ] Add Postgres + update docker-compose
3. [ ] Refactor agents for event-driven mode
4. [ ] Implement Git integration (local + GitHub)
5. [ ] Build preview deployment system
6. [ ] Enhance Explorer agent
7. [ ] Update frontend with real-time updates
8. [ ] Comprehensive testing
9. [ ] Documentation updates

### Testing Checkpoints
- [ ] All 8 services start successfully
- [ ] Events flow through RabbitMQ
- [ ] Code commits to local Git
- [ ] Code pushes to GitHub (if enabled)
- [ ] Preview URL accessible
- [ ] Real-time updates in chat
- [ ] Explorer can analyze repos
- [ ] Dual-mode switching works

---

## 14. Success Metrics

**System works if:**
1. ✅ User sends "build X" → sees real-time file creation updates
2. ✅ Preview URL accessible within 5 minutes
3. ✅ Code pushed to GitHub with PR
4. ✅ Test coverage ≥ 80%
5. ✅ Security scan shows 0 critical issues
6. ✅ Chat interface grayed out during agent work
7. ✅ All 8 services healthy in Docker Desktop
8. ✅ Explorer can analyze and feed to Planner

---

## Next Steps

1. **Review this spec** - User confirms architecture
2. **Create implementation tasks** - Break into PRs
3. **Start Phase 1** - Infrastructure + events
4. **Iterative development** - Test each phase before next
5. **User testing** - Continuous feedback loop

**This spec serves as the blueprint for the complete migration.**

Ready to proceed with implementation?
