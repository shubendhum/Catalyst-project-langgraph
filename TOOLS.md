# Catalyst Platform - Tools & Technologies

Complete list of all tools, libraries, and technologies used in Catalyst AI Platform.

---

## 📦 Core Technologies

### Backend Stack

| Technology | Version | Purpose | Documentation |
|-----------|---------|---------|---------------|
| **Python** | 3.11+ | Backend runtime | [python.org](https://python.org) |
| **FastAPI** | 0.110.1 | Web framework | [fastapi.tiangolo.com](https://fastapi.tiangolo.com) |
| **Uvicorn** | 0.25.0 | ASGI server | [uvicorn.org](https://uvicorn.org) |
| **MongoDB** | 7.0 | NoSQL database | [mongodb.com](https://mongodb.com) |
| **Motor** | 3.3.1 | Async MongoDB driver | [motor.readthedocs.io](https://motor.readthedocs.io) |
| **Pydantic** | 2.6.4+ | Data validation | [docs.pydantic.dev](https://docs.pydantic.dev) |

### Frontend Stack

| Technology | Version | Purpose | Documentation |
|-----------|---------|---------|---------------|
| **React** | 19.0.0 | UI library | [react.dev](https://react.dev) |
| **Node.js** | 18+ | JavaScript runtime | [nodejs.org](https://nodejs.org) |
| **Yarn** | 1.22.22 | Package manager | [yarnpkg.com](https://yarnpkg.com) |
| **Webpack** | 5.x | Module bundler | [webpack.js.org](https://webpack.js.org) |
| **Tailwind CSS** | 3.4.17 | Utility CSS | [tailwindcss.com](https://tailwindcss.com) |

### Infrastructure

| Technology | Version | Purpose | Documentation |
|-----------|---------|---------|---------------|
| **Docker** | 24.0+ | Containerization | [docs.docker.com](https://docs.docker.com) |
| **Docker Compose** | 2.20+ | Multi-container orchestration | [docs.docker.com/compose](https://docs.docker.com/compose) |
| **Nginx** | Alpine | Web server / Reverse proxy | [nginx.org](https://nginx.org) |
| **Make** | 4.0+ | Build automation | [gnu.org/software/make](https://gnu.org/software/make) |

---

## 🔌 Backend Dependencies

### Web Framework & Server

```
fastapi==0.110.1          # Modern, fast web framework
uvicorn==0.25.0           # Lightning-fast ASGI server
starlette>=0.37.2         # ASGI framework (FastAPI dependency)
python-multipart>=0.0.9   # File upload support
```

### Database & ORM

```
motor==3.3.1              # Async MongoDB driver
pymongo==4.5.0            # MongoDB Python driver
```

### Data Validation & Serialization

```
pydantic>=2.6.4           # Data validation using Python type annotations
email-validator>=2.2.0    # Email validation for Pydantic
```

### LLM Integration

```
emergentintegrations      # Universal LLM library (OpenAI, Anthropic, Google)
                          # Source: https://d33sy5i8bnduwe.cloudfront.net/simple/
openai==1.99.9           # OpenAI API client
litellm>=1.0.0           # Multi-LLM proxy
aiohttp>=3.8.0           # Async HTTP client
google-generativeai>=0.3.0  # Google AI client
```

**LLM Integration Details:**
- **emergentintegrations**: Custom library for universal LLM access
  - Supports: OpenAI GPT-4.1, Anthropic Claude 3.7, Google Gemini 2.5
  - Features: Token counting, rate limiting, cost tracking
  - Installation: `pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/`

### Authentication & Security

```
pyjwt>=2.10.1            # JSON Web Token implementation
bcrypt==4.1.3            # Password hashing
passlib>=1.7.4           # Password hashing library
python-jose>=3.3.0       # JOSE implementation
cryptography>=42.0.8     # Cryptographic recipes
```

### Configuration & Environment

```
python-dotenv>=1.0.1     # Environment variable management
pyyaml>=6.0              # YAML parser (for config.yaml)
```

### HTTP & Networking

```
requests>=2.31.0         # HTTP library
httpx>=0.23.0           # Async HTTP client
websockets>=13.0        # WebSocket support
```

### Data Processing

```
pandas>=2.2.0            # Data analysis
numpy>=1.26.0            # Numerical computing
```

### Date & Time

```
tzdata>=2024.2           # Timezone data
```

### Development & Testing

```
pytest>=8.0.0            # Testing framework
black>=24.1.1            # Code formatter
isort>=5.13.2            # Import sorter
flake8>=7.0.0           # Linter
mypy>=1.8.0             # Type checker
```

### Utilities

```
typer>=0.9.0             # CLI framework
jq>=1.6.0               # JSON processor
boto3>=1.34.129         # AWS SDK (for S3, etc.)
requests-oauthlib>=2.0.0  # OAuth support
```

---

## 🎨 Frontend Dependencies

### Core React

```
react@19.0.0                    # React library
react-dom@19.0.0                # React DOM renderer
react-scripts@5.0.1             # Create React App scripts
```

### Routing

```
react-router-dom@7.5.1          # Declarative routing
```

### State Management

```
zustand@5.0.8                   # Lightweight state management
```

### HTTP & API

```
axios@1.8.4                     # Promise-based HTTP client
```

### UI Component Library

```
@radix-ui/react-accordion@1.2.12      # Accordion component
@radix-ui/react-alert-dialog@1.1.15   # Alert dialog
@radix-ui/react-avatar@1.1.10         # Avatar component
@radix-ui/react-checkbox@1.3.3        # Checkbox component
@radix-ui/react-dialog@1.1.15         # Dialog/Modal
@radix-ui/react-dropdown-menu@2.1.16  # Dropdown menu
@radix-ui/react-label@2.1.7           # Label component
@radix-ui/react-popover@1.1.15        # Popover component
@radix-ui/react-progress@1.1.7        # Progress bar
@radix-ui/react-scroll-area@1.2.10    # Scroll area
@radix-ui/react-select@2.2.6          # Select dropdown
@radix-ui/react-separator@1.1.7       # Separator line
@radix-ui/react-slider@1.3.6          # Slider input
@radix-ui/react-switch@1.2.6          # Toggle switch
@radix-ui/react-tabs@1.1.13           # Tabs component
@radix-ui/react-toast@1.2.15          # Toast notifications
@radix-ui/react-tooltip@1.2.8         # Tooltip component
```

### Styling

```
tailwindcss@3.4.17                    # Utility-first CSS
postcss@8.5.6                         # CSS post-processor
autoprefixer@10.4.21                  # CSS vendor prefixes
tailwindcss-animate@1.0.7             # Animation utilities
tailwind-merge@3.3.1                  # Merge Tailwind classes
class-variance-authority@0.7.1        # Component variants
clsx@2.1.1                            # Class name utility
```

### Icons

```
lucide-react@0.507.0                  # Modern icon library
```

### Code Editor

```
monaco-editor@0.54.0                  # VS Code editor
@monaco-editor/react@4.7.0            # React wrapper for Monaco
```

### Visualization

```
react-flow-renderer@10.3.17           # Flow diagrams (DAG)
embla-carousel-react@8.6.0            # Carousel component
```

### Markdown & Content

```
react-markdown@10.1.0                 # Markdown renderer
```

### Forms

```
react-hook-form@7.65.0                # Form management
@hookform/resolvers@5.2.2             # Form validators
zod@3.25.76                           # Schema validation
```

### Date Handling

```
date-fns@4.1.0                        # Date utility library
react-day-picker@8.10.1               # Date picker
```

### Notifications

```
sonner@2.0.7                          # Toast notifications
```

### Utilities

```
cmdk@1.1.1                            # Command palette
next-themes@0.4.6                     # Theme management
vaul@1.1.2                            # Drawer component
input-otp@1.4.2                       # OTP input
react-resizable-panels@3.0.6          # Resizable panels
```

### Build Tools

```
@craco/craco@7.1.0                    # Create React App Configuration
webpack@5.x                           # Module bundler
```

### Development Tools

```
eslint@9.23.0                         # JavaScript linter
eslint-plugin-react@7.37.4            # React-specific linting
eslint-plugin-import@2.31.0           # Import/export linting
eslint-plugin-jsx-a11y@6.10.2         # Accessibility linting
```

---

## 🐳 Docker Images

### Official Images Used

```yaml
# Backend
python:3.11-slim              # Lightweight Python image (Debian-based)

# Frontend Build
node:18-alpine                # Lightweight Node.js image (Alpine Linux)

# Frontend Production
nginx:alpine                  # Lightweight Nginx image

# Database
mongo:7.0                     # Official MongoDB image
```

**Image Selection Rationale:**
- **slim/alpine**: Smaller image size, faster deployment
- **Specific versions**: Reproducible builds
- **Official images**: Security updates, community support

---

## 🔧 System Tools & Utilities

### Build Tools

```
gcc                    # C compiler (for Python C extensions)
g++                    # C++ compiler
make                   # Build automation
cmake                  # Cross-platform build system
```

### System Libraries

```
curl                   # HTTP client
wget                   # File downloader
git                    # Version control
openssh-client        # SSH client
```

### Python Tools

```
pip                    # Python package installer
setuptools             # Python package development
wheel                  # Python package format
virtualenv             # Virtual environment manager
```

### Node.js Tools

```
npm                    # Node package manager (base)
yarn                   # Preferred package manager
npx                    # Package runner
```

---

## 📊 Monitoring & Observability (Optional)

### Logging

```
python-json-logger     # Structured logging
winston (Node.js)      # Logging for Node
```

### Metrics

```
prometheus-client      # Prometheus metrics
statsd                 # StatsD client
```

### Error Tracking

```
sentry-sdk            # Error tracking (if configured)
```

### APM

```
opentelemetry         # Distributed tracing (optional)
```

---

## 🔐 Security Tools

### Static Analysis

```
bandit                # Python security linter
safety                # Python dependency scanner
npm audit             # Node.js security audit
```

### Secrets Management

```
python-dotenv         # Environment variables
docker-secrets        # Docker secrets (production)
```

---

## 🧪 Testing Tools

### Backend Testing

```
pytest                # Testing framework
pytest-asyncio        # Async test support
pytest-cov            # Coverage plugin
httpx                 # HTTP testing
faker                 # Test data generation
```

### Frontend Testing

```
@testing-library/react       # React testing utilities
@testing-library/jest-dom    # Jest matchers
jest                         # JavaScript testing
playwright                   # E2E testing (if needed)
```

---

## 📦 Package Management

### Backend

**Tool**: pip + requirements.txt  
**Lock File**: requirements.txt (with ==versions)  
**Registry**: PyPI + custom index (emergentintegrations)

**Commands:**
```bash
pip install -r requirements.txt
pip freeze > requirements.txt
```

### Frontend

**Tool**: Yarn (v1 Classic)  
**Lock File**: yarn.lock  
**Registry**: npm registry

**Commands:**
```bash
yarn install          # Install dependencies
yarn add <package>    # Add package
yarn upgrade          # Update packages
```

---

## 🔄 Version Control

### Git

**Configuration:**
```
.gitignore            # Ignore patterns
.gitattributes        # File attributes
```

**Branches:**
- `main` - Production
- `develop` - Development
- `feature/*` - Features
- `hotfix/*` - Hotfixes

---

## 📚 Documentation Tools

### Markdown

```
README.md                    # Main documentation
DEPLOYMENT.md               # This file
REQUIREMENTS_VALIDATION.md  # Requirements doc
API_DOCS.md                 # API documentation
```

### API Documentation

```
FastAPI Swagger UI          # Auto-generated API docs
Redoc                       # Alternative API docs
```

**Access:**
- Swagger: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## 🌐 Network & Communication

### Protocols

```
HTTP/1.1              # Standard HTTP
HTTP/2                # Modern HTTP (nginx)
WebSocket             # Real-time communication
```

### Ports

```
3000                  # Frontend (React dev server)
8001                  # Backend (FastAPI)
27017                 # MongoDB
80                    # HTTP (production)
443                   # HTTPS (production)
```

---

## 💾 Data Storage

### Databases

```
MongoDB 7.0           # Primary database
  - motor (async)     # Python driver
  - mongosh           # Shell client
```

### File Storage (Optional)

```
Local filesystem      # Development
AWS S3               # Production (optional)
Cloudflare R2        # Alternative (optional)
```

### Backup Tools

```
mongodump            # MongoDB backup
mongorestore         # MongoDB restore
```

---

## 🚀 Deployment Tools

### Container Orchestration

```
docker-compose       # Local/single-host
docker-swarm         # Multi-host (optional)
kubernetes          # Production clusters (optional)
```

### CI/CD (Recommended)

```
GitHub Actions       # CI/CD pipelines
GitLab CI           # Alternative
Jenkins             # Self-hosted
```

### Cloud Platforms

```
AWS ECS             # Container service
Google Cloud Run    # Serverless containers
Azure ACI           # Container instances
Vercel              # Frontend hosting
Railway             # Full-stack hosting
```

---

## 📈 Performance Tools

### Profiling

```
cProfile            # Python profiling
py-spy              # Sampling profiler
React DevTools      # React profiling
```

### Load Testing

```
locust              # Python load testing
k6                  # Modern load testing
ab (Apache Bench)   # Simple benchmarking
```

---

## 🔍 Debugging Tools

### Backend

```
pdb                 # Python debugger
ipdb                # Interactive debugger
logging             # Standard logging
```

### Frontend

```
React DevTools      # React debugging
Redux DevTools      # State debugging
Chrome DevTools     # Browser debugging
```

---

## 📋 Installation Summary

### Quick Install All Tools

**Ubuntu/Debian:**
```bash
# System packages
sudo apt-get update
sudo apt-get install -y docker.io docker-compose make python3.11 nodejs yarn git curl

# Python packages
pip install -r backend/requirements.txt
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Node packages
cd frontend && yarn install
```

**macOS:**
```bash
# Using Homebrew
brew install docker docker-compose make python@3.11 node yarn git

# Python packages
pip3 install -r backend/requirements.txt
pip3 install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# Node packages
cd frontend && yarn install
```

**Windows (WSL2):**
```bash
# Enable WSL2 and install Ubuntu
wsl --install

# Then follow Ubuntu instructions above
```

---

## 📊 Tool Categories Summary

| Category | Count | Key Tools |
|----------|-------|-----------|
| **Backend Libraries** | 30+ | FastAPI, Motor, Pydantic, emergentintegrations |
| **Frontend Libraries** | 60+ | React, Zustand, Radix UI, Tailwind |
| **DevOps Tools** | 10+ | Docker, Compose, Make, Git |
| **Database Tools** | 3 | MongoDB, Motor, mongosh |
| **Testing Tools** | 8+ | pytest, Jest, httpx |
| **Build Tools** | 5+ | Webpack, Babel, PostCSS |
| **Security Tools** | 5+ | bcrypt, JWT, python-jose |
| **Monitoring Tools** | 4+ | logging, metrics, Sentry (optional) |

**Total Dependencies**: ~100+ packages across all categories

---

## 🔗 Official Links

- **Catalyst Repository**: https://github.com/your-org/catalyst
- **Docker Hub**: https://hub.docker.com
- **PyPI**: https://pypi.org
- **npm Registry**: https://npmjs.com
- **Emergent Platform**: https://emergent.sh
- **FastAPI**: https://fastapi.tiangolo.com
- **React**: https://react.dev
- **MongoDB**: https://mongodb.com

---

**Tools Documentation Version**: 1.0.0  
**Last Updated**: October 2025  
**Platform Version**: 1.0.0
