# Catalyst Hardening Implementation Plan

**Date:** January 9, 2025  
**Target:** Docker Desktop Deployment  
**Status:** In Progress

## Overview

Comprehensive hardening and capability improvements for production-ready deployment on Docker Desktop.

## Tasks

### ✅ 1. Strengthen Docker Compose Healthchecks
- [x] Review existing healthchecks
- [ ] Enhance backend healthcheck with proper intervals
- [ ] Enhance frontend healthcheck
- [ ] Enhance Redis healthcheck (already good)
- [ ] Enhance Qdrant healthcheck (already good)
- [ ] Add healthchecks for RabbitMQ, Langfuse, etc.

### 2. Backend Health Endpoint Improvements
- [ ] Enhance /api/health endpoint
- [ ] Add Redis connectivity check
- [ ] Add Qdrant connectivity check
- [ ] Add LLM provider check
- [ ] Return structured JSON with per-dependency status

### 3. Frontend Status Page
- [ ] Create /status route and page
- [ ] Poll /api/health periodically
- [ ] Display per-dependency status badges
- [ ] Add header status indicator (green/amber/red)

### 4. Structured JSON Logging
- [ ] Create logging utility (backend/utils/logging.py)
- [ ] Implement JSON logger
- [ ] Add request ID middleware
- [ ] Update agents to use structured logging
- [ ] Add LOG_LEVEL and LOG_FORMAT env vars

### 5. Explorer Ingestion CLI
- [ ] Create backend/tools/ingest.py
- [ ] Support Confluence, Jira, PDF, ServiceDesk
- [ ] Implement chunking (512-1024 tokens, 64 overlap)
- [ ] Upsert to Qdrant with metadata
- [ ] Implement hybrid search (BM25 + vector)
- [ ] Add POST /api/search endpoint

### ✅ 6. Sandbox Runner
- [x] Already implemented in previous task
- [x] Docker image exists
- [x] Sandbox service created
- [x] API endpoints added
- [x] Tester agent integrated

### ✅ 7. Evals System
- [x] Already implemented in previous task
- [x] Gold tasks created
- [x] Eval runner implemented
- [x] Makefile/npm integration
- [x] Report comparison tool

### 8. Tests
- [ ] Add Python unit tests
- [ ] Add E2E tests with Playwright
- [ ] Add infrastructure tests with testcontainers
- [ ] Ensure pytest discoverability

### 9. CI Workflow
- [ ] Create/enhance .github/workflows
- [ ] Add lint + unit tests job
- [ ] Add E2E tests job
- [ ] Add evals job
- [ ] Add Docker build job
- [ ] Add security scan (Trivy)

### 10. Frontend UX Components
- [ ] Create AgentRunCard component
- [ ] Create LLMConfigPanel component
- [ ] Add runs timeline/history panel
- [ ] Add /api/config endpoint
- [ ] Implement auth/session awareness

### 11. Security Features
- [ ] Create SECRETS_README.md
- [ ] Implement log redaction utility
- [ ] Harden CORS configuration
- [ ] Add security headers middleware
- [ ] Implement decision audit log

## Priority Order

1. Health endpoint improvements (critical for monitoring)
2. Frontend status page (visibility)
3. Structured logging (observability)
4. Tests (quality)
5. CI workflow (automation)
6. Security features (hardening)
7. Explorer ingestion CLI (feature)
8. Frontend UX components (polish)

## Files to Create/Modify

### New Files
- backend/utils/logging.py
- backend/tools/ingest.py
- frontend/src/pages/Status.tsx
- frontend/src/components/AgentRunCard.tsx
- frontend/src/components/LLMConfigPanel.tsx
- tests/unit/
- tests/e2e/
- .github/workflows/ci.yml
- SECRETS_README.md
- backend/utils/redaction.py
- backend/services/audit_log.py

### Modified Files
- docker-compose.artifactory.yml
- backend/server.py
- backend/routers/health.py
- frontend/src/App.js
- backend/.env.example
- frontend/.env.example

## Notes

- All changes target Docker Desktop only
- Do not break existing functionality
- Extend and harden existing code
- Add comprehensive documentation
