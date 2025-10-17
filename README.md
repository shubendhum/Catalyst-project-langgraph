# Catalyst - Multi-Agent AI Platform

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue)](https://kubernetes.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.1-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue)](https://reactjs.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Enabled-purple)](https://github.com/langchain-ai/langgraph)

A production-ready multi-agent AI platform featuring LangGraph orchestration, conversational chat interface, and multi-LLM support (Claude, Bedrock, Emergent LLM Key).

**Catalyst** is a full-featured multi-agent AI platform that replicates enterprise-grade development workflows. It orchestrates AI agents to plan, code, test, review, and deploy applications end-to-end.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Deployment Options](#deployment-options)
- [Documentation](#documentation)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Core Capabilities

- **Multi-Agent Orchestration**: 6 specialized AI agents (Planner, Architect, Coder, Tester, Reviewer, Deployer)
- **LangGraph Integration**: State-driven workflow with conditional edges and feedback loops
- **Conversational Interface**: Natural language chat with intent recognition
- **Multi-LLM Support**: 
  - ✅ Emergent LLM Key (Claude, GPT, Gemini)
  - ✅ Anthropic Claude Direct
  - ✅ **AWS Bedrock** (All Claude models) - [See AWS_BEDROCK_GUIDE.md](AWS_BEDROCK_GUIDE.md)
- **Real-time Updates**: WebSocket-based agent activity streaming
- **Session Management**: Persistent conversations with context
- **Enterprise Explorer**: Read-only integration with GitHub, Jira, ServiceNow

### Technical Stack

**Backend**:
- FastAPI (Python 3.11+)
- LangGraph for agent orchestration
- MongoDB for data persistence
- Emergentintegrations for unified LLM access
- WebSocket for real-time communication

**Frontend**:
- React 18
- Tailwind CSS + Shadcn UI
- Zustand for state management
- Real-time WebSocket integration

**Infrastructure**:
- Docker & Docker Compose
- Kubernetes manifests
- AWS ECS task definitions
- Nginx reverse proxy

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Chat UI     │  │ Agent Logs   │  │ Task Graph   │      │
│  └─────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API + WebSocket
┌──────────────────────────┴──────────────────────────────────┐
│                   Backend (FastAPI)                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         LangGraph Orchestrator                      │   │
│  │  ┌─────┐  ┌──────┐  ┌─────┐  ┌──────┐  ┌──────┐  │   │
│  │  │Plan │→ │Arch  │→ │Code │→ │Test  │→ │Review│  │   │
│  │  └─────┘  └──────┘  └─────┘  └──────┘  └──────┘  │   │
│  │                        ↓                            │   │
│  │                   ┌─────────┐                      │   │
│  │                   │ Deploy  │                      │   │
│  │                   └─────────┘                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────┐  ┌────────────────────────────┐      │
│  │ Chat Interface  │  │   Unified LLM Client       │      │
│  │ - Intent        │  │ - Emergent LLM Key         │      │
│  │ - Context       │  │ - Anthropic API            │      │
│  │ - Multi-turn    │  │ - AWS Bedrock              │      │
│  └─────────────────┘  └────────────────────────────┘      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────┴───────┐
                    │   MongoDB    │
                    └──────────────┘
```

---

## Quick Start

### 🐳 Using Makefile + Docker Desktop (Fastest!)

**Prerequisites**: Docker Desktop installed and running

```bash
# Complete setup (builds Docker images)
make setup

# Start all services in Docker
make start

# Access:
# Frontend: http://localhost:3000
# Backend:  http://localhost:8001/api
# API Docs: http://localhost:8001/docs
```

**For Organizations Using Artifactory Mirror**:
```bash
# Setup with Artifactory
make setup-artifactory

# Start with Artifactory
make start-artifactory
```

**See [ARTIFACTORY_SETUP.md](ARTIFACTORY_SETUP.md) for Artifactory configuration.**

**That's it! Everything runs in Docker containers.**

**See [DOCKER_MAKEFILE_GUIDE.md](DOCKER_MAKEFILE_GUIDE.md) for complete Docker setup guide.**

### Using Docker Compose Directly

```bash
# Clone repository
git clone <repository-url>
cd catalyst

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001/api
# API Docs: http://localhost:8001/docs
```

### Using Helper Script

```bash
# Make executable
chmod +x deploy.sh

# Start services
./deploy.sh docker

# Or for production
./deploy.sh docker-prod
```

**See [QUICKSTART.md](QUICKSTART.md) for detailed quick start guides.**

---

## Deployment Options

Catalyst supports multiple deployment methods:

### 1. Local Development
Perfect for development and testing
```bash
./deploy.sh local
```

### 2. Docker Compose
Recommended for quick deployment
```bash
docker-compose up -d
```

### 3. Kubernetes
Production-ready orchestration
```bash
kubectl apply -f k8s/ -n catalyst
```

### 4. AWS EC2
Direct cloud deployment
```bash
./aws/deploy-ec2.sh
```

### 5. AWS ECS/Fargate
Managed container service
```bash
aws ecs register-task-definition --cli-input-json file://aws/ecs-task-definition.json
```

**See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive deployment documentation.**

---

## Documentation

### Quick References
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[API Documentation](http://localhost:8001/docs)** - Interactive API docs (when running)

### Architecture Documentation
- **Backend**: FastAPI + LangGraph + MongoDB
- **Frontend**: React + Tailwind + Zustand
- **Agents**: Planner → Architect → Coder → Tester → Reviewer → Deployer
- **LLM Integration**: Unified client supporting multiple providers

---

## API Reference

### Chat Endpoints

**Configure LLM Provider**
```bash
POST /api/chat/config
{
  "provider": "emergent",
  "model": "claude-3-7-sonnet-20250219",
  "api_key": null,
  "aws_config": null
}
```

**Create Conversation**
```bash
POST /api/chat/conversations
```

**Send Message**
```bash
POST /api/chat/send
{
  "message": "Build me a todo app",
  "conversation_id": "conv-123"
}
```

**List Conversations**
```bash
GET /api/chat/conversations
```

### Project & Task Endpoints

```bash
POST /api/projects          # Create project
GET  /api/projects          # List projects
POST /api/tasks             # Create task
GET  /api/tasks/{id}        # Get task
GET  /api/logs/{task_id}    # Get agent logs
```

**See [http://localhost:8001/docs](http://localhost:8001/docs) for complete API documentation.**

---

## Configuration

### Environment Variables

**Backend (.env)**
```bash
# Database
MONGO_URL=mongodb://admin:password@mongodb:27017
DB_NAME=catalyst_db

# LLM Configuration
EMERGENT_LLM_KEY=sk-emergent-b14E29723DeDaF2A74
DEFAULT_LLM_PROVIDER=emergent
DEFAULT_LLM_MODEL=claude-3-7-sonnet-20250219

# Optional: Custom Provider Keys
ANTHROPIC_API_KEY=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1

# Performance
MAX_CONCURRENT_TASKS=10
AGENT_TIMEOUT=600
```

**Frontend (.env)**
```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

### LLM Provider Configuration

**Option 1: Emergent LLM Key (Default)**
- Pre-configured and ready to use
- Supports Claude, GPT, Gemini models
- No additional API keys needed

**Option 2: Custom Anthropic API Key**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key
DEFAULT_LLM_PROVIDER=anthropic
```

**Option 3: AWS Bedrock**
```bash
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
DEFAULT_LLM_PROVIDER=bedrock
```

**Dynamic Configuration via API**
```bash
curl -X POST http://localhost:8001/api/chat/config \
  -H "Content-Type: application/json" \
  -d '{"provider": "anthropic", "model": "claude-3-7-sonnet-20250219", "api_key": "sk-ant-..."}'
```

---

## Project Structure

```
catalyst/
├── backend/                    # FastAPI backend
│   ├── agents/                 # Individual agent implementations
│   ├── chat_interface/         # Conversational interface
│   ├── langgraph_orchestrator/ # LangGraph workflow
│   ├── orchestrator/           # Original orchestrator
│   ├── connectors/             # External integrations
│   ├── llm_client.py           # Unified LLM client
│   ├── server.py               # Main FastAPI app
│   └── requirements*.txt       # Python dependencies
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/              # Page components
│   │   ├── store/              # State management
│   │   └── hooks/              # Custom hooks
│   └── package.json
├── k8s/                        # Kubernetes manifests
│   ├── mongodb-deployment.yaml
│   ├── backend-deployment.yaml
│   ├── frontend-deployment.yaml
│   ├── ingress.yaml
│   └── hpa.yaml
├── aws/                        # AWS deployment configs
│   ├── ecs-task-definition.json
│   └── deploy-ec2.sh
├── docker-compose.yml          # Development compose
├── docker-compose.prod.yml     # Production compose
├── Dockerfile.backend          # Backend image
├── Dockerfile.frontend         # Frontend image
├── deploy.sh                   # Deployment helper script
├── DEPLOYMENT_GUIDE.md         # Complete deployment guide
├── QUICKSTART.md               # Quick start guide
└── README.md                   # This file
```

---

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
yarn test
```

### Integration Tests
```bash
# Backend API
curl http://localhost:8001/api/

# Create and test conversation
curl -X POST http://localhost:8001/api/chat/conversations
curl -X POST http://localhost:8001/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{"message": "hello", "conversation_id": "test-123"}'
```

---

## Monitoring and Maintenance

### Health Checks
```bash
# Backend
curl http://localhost:8001/api/

# MongoDB
docker exec catalyst-mongo mongo --eval "db.adminCommand('ping')"
```

### View Logs
```bash
# Docker Compose
docker-compose logs -f

# Kubernetes
kubectl logs -f deployment/catalyst-backend -n catalyst

# Specific container
docker logs catalyst-backend
```

### Backup MongoDB
```bash
# Backup
docker exec catalyst-mongo mongodump \
  --username admin \
  --password catalyst_admin_pass \
  --out /backup/$(date +%Y%m%d)

# Restore
docker exec catalyst-mongo mongorestore \
  --username admin \
  --password catalyst_admin_pass \
  /backup/20240101
```

---

## Troubleshooting

### Common Issues

**Backend won't start**
```bash
# Check logs
docker logs catalyst-backend

# Verify MongoDB
docker ps | grep mongo

# Test MongoDB connection
mongo mongodb://admin:catalyst_admin_pass@localhost:27017
```

**Frontend can't connect**
```bash
# Check backend URL
cat frontend/.env

# Test backend API
curl http://localhost:8001/api/

# Verify CORS settings
docker exec catalyst-backend env | grep CORS_ORIGINS
```

**Port conflicts**
```bash
# Change ports in docker-compose.yml
ports:
  - "3001:80"  # Frontend
  - "8002:8001"  # Backend
```

**See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive troubleshooting.**

---

## Production Recommendations

1. **HTTPS**: Setup SSL/TLS certificates (Let's Encrypt)
2. **Secrets Management**: Use AWS Secrets Manager or Kubernetes Secrets
3. **Monitoring**: Setup Prometheus + Grafana
4. **Logging**: Use ELK stack or CloudWatch
5. **Backups**: Automate MongoDB backups
6. **Scaling**: Configure HPA for Kubernetes or ECS Auto Scaling
7. **CDN**: Use CloudFront for frontend assets
8. **Security**: 
   - Strong MongoDB passwords
   - Network policies
   - API rate limiting
   - Input validation

---

## Performance Tuning

### Backend
```bash
# Increase concurrent tasks
MAX_CONCURRENT_TASKS=20

# Adjust agent timeout
AGENT_TIMEOUT=900

# Enable performance monitoring
ENABLE_PERFORMANCE_MONITORING=true
```

### MongoDB
```bash
# Create indexes for better query performance
db.conversations.createIndex({"updated_at": -1})
db.tasks.createIndex({"project_id": 1, "created_at": -1})
db.agent_logs.createIndex({"task_id": 1, "timestamp": 1})
```

### Kubernetes Scaling
```bash
# Adjust HPA settings in k8s/hpa.yaml
minReplicas: 3
maxReplicas: 20
targetCPUUtilizationPercentage: 60
```

---

## Security

### Best Practices

1. **Environment Variables**: Never commit sensitive data
2. **MongoDB**: Enable authentication, use strong passwords
3. **API Keys**: Rotate regularly, use different keys per environment
4. **Network**: Use private networks, firewall rules
5. **HTTPS**: Always use SSL/TLS in production
6. **Updates**: Keep dependencies updated

### Secrets Management

**Development**:
```bash
cp .env.example .env
# Edit .env with your secrets
```

**Production**:
```bash
# Use AWS Secrets Manager
aws secretsmanager create-secret \
  --name catalyst/emergent-llm-key \
  --secret-string "sk-emergent-..."

# Or Kubernetes Secrets
kubectl create secret generic catalyst-secrets \
  --from-literal=emergent-llm-key=sk-emergent-... \
  -n catalyst
```

---

## Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-langgraph.txt
pip install -r requirements-dev.txt  # Dev dependencies

# Frontend
cd frontend
yarn install
```

### Code Style
- Python: Follow PEP 8, use `black` for formatting
- JavaScript: Use ESLint + Prettier
- Commits: Follow [Conventional Commits](https://www.conventionalcommits.org/)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Support

- **Documentation**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md), [QUICKSTART.md](QUICKSTART.md)
- **Issues**: [GitHub Issues](<repository-url>/issues)
- **Email**: support@catalyst.ai
- **Community**: [Discord](<discord-url>)

---

## Acknowledgments

- **LangGraph**: For the agent orchestration framework
- **FastAPI**: For the high-performance backend framework
- **React**: For the powerful frontend library
- **Emergent**: For the unified LLM integration
- **MongoDB**: For the flexible database solution

---

## Roadmap

### Phase 1 - Current ✅
- [x] Multi-agent orchestration
- [x] LangGraph integration
- [x] Chat interface
- [x] Multi-LLM support
- [x] Docker deployment
- [x] Kubernetes manifests

### Phase 2 - In Progress 🚧
- [ ] Frontend chat UI
- [ ] Agent switching interface
- [ ] Enhanced error handling
- [ ] Comprehensive testing suite

### Phase 3 - Planned 📋
- [ ] Agent memory system
- [ ] Plugin architecture
- [ ] Multi-language support
- [ ] Advanced monitoring dashboard
- [ ] CI/CD pipeline
- [ ] Helm charts

---

**Built with ❤️ by the Catalyst Team**
