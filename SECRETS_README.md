# Secrets Management Guide

## Overview

This document explains how to properly configure secrets and API keys for the Catalyst platform when running on Docker Desktop.

## Important Security Notes

⚠️ **NEVER commit secrets to git**  
⚠️ **NEVER hardcode API keys in code**  
⚠️ **Use environment variables for all sensitive data**

## Configuration Files

### Backend Environment Variables

**File:** `backend/.env` (create from `backend/.env.example`)

```env
# Database Credentials
MONGO_URL=mongodb://admin:your_secure_password@mongodb:27017
POSTGRES_URL=postgresql://catalyst:your_secure_password@postgres:5432/catalyst_state

# Redis
REDIS_URL=redis://redis:6379

# RabbitMQ
RABBITMQ_URL=amqp://catalyst:your_secure_password@rabbitmq:5672/catalyst

# LLM Provider API Keys
EMERGENT_LLM_KEY=your_emergent_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# LLM Configuration
DEFAULT_LLM_PROVIDER=emergent
DEFAULT_LLM_MODEL=claude-3-7-sonnet-20250219

# CORS Configuration (adjust for your domain)
CORS_ORIGINS=http://localhost:3000,http://localhost:8001
CORS_ALLOW_CREDENTIALS=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Qdrant
QDRANT_URL=http://qdrant:6333

# Audit Logging
AUDIT_LOG_PATH=/app/data/audit

# Optional: External Integrations
CONFLUENCE_API_TOKEN=your_confluence_token_here
JIRA_API_TOKEN=your_jira_token_here
SLACK_WEBHOOK_URL=your_slack_webhook_here

# Optional: Observability
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=http://langfuse:3000
```

### Frontend Environment Variables

**File:** `frontend/.env` (create from `frontend/.env.example`)

```env
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# Optional: Analytics
REACT_APP_ANALYTICS_ID=your_analytics_id
```

## Setting Up Secrets (Local Development)

### 1. Create .env Files

```bash
# Backend
cp backend/.env.example backend/.env

# Frontend
cp frontend/.env.example frontend/.env
```

### 2. Edit .env Files

Open each `.env` file and replace placeholders with your actual values:

```bash
# Edit backend secrets
nano backend/.env

# Edit frontend secrets
nano frontend/.env
```

### 3. Secure .env Files

```bash
# Ensure .env files are not tracked by git
git status  # Should NOT show .env files

# Set restrictive permissions (Linux/Mac)
chmod 600 backend/.env
chmod 600 frontend/.env
```

## Docker Compose Integration

Secrets are automatically loaded from `.env` files and environment variables.

**Start with secrets:**
```bash
# Secrets will be loaded from backend/.env
docker-compose up -d
```

**Override specific secrets:**
```bash
# Override at runtime
EMERGENT_LLM_KEY=sk-your-key docker-compose up -d
```

## Obtaining API Keys

### Emergent LLM Key
1. Contact Emergent support or your platform administrator
2. Set in `backend/.env` as `EMERGENT_LLM_KEY`

### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Create new API key
3. Set in `backend/.env` as `OPENAI_API_KEY`

### Anthropic API Key
1. Go to https://console.anthropic.com/
2. Generate API key
3. Set in `backend/.env` as `ANTHROPIC_API_KEY`

### Confluence/Jira Tokens
1. Go to Atlassian account settings
2. Create API token
3. Set in `backend/.env`

## Verifying Configuration

### Check Secrets are Loaded

```bash
# Check if backend can access secrets
docker-compose exec backend env | grep API_KEY

# Should show: EMERGENT_LLM_KEY=sk-******* (masked)
```

### Test Health Endpoint

```bash
# Check LLM configuration
curl http://localhost:8001/api/health | jq '.checks.llm'

# Should show: {"status": "healthy", "detail": "Provider: emergent, API key configured"}
```

## Security Best Practices

### 1. Use Strong Passwords

Generate secure passwords:
```bash
# Generate random password
openssl rand -base64 32

# Or use a password manager
```

### 2. Rotate Secrets Regularly

- Change database passwords quarterly
- Rotate API keys every 6 months
- Update tokens when team members leave

### 3. Limit API Key Permissions

- Use read-only keys where possible
- Set spending limits on LLM API keys
- Enable IP restrictions if available

### 4. Monitor API Usage

- Set up billing alerts
- Review API usage logs regularly
- Monitor for unusual activity

### 5. Separate Secrets by Environment

```
development/.env   # Local development
staging/.env       # Staging environment
production/.env    # Production (never commit!)
```

## Log Redaction

The platform automatically redacts sensitive information from logs:

- Email addresses (partially masked)
- API keys and tokens (fully masked)
- Passwords (fully masked)
- Bearer tokens (fully masked)
- Credit card numbers (if present)

**Example:**
```json
{
  "message": "API call made",
  "api_key": "***REDACTED***",
  "user_email": "***@example.com"
}
```

## Troubleshooting

### Issue: "LLM API key not configured"

**Solution:**
1. Check `.env` file exists: `ls -la backend/.env`
2. Verify key is set: `docker-compose exec backend env | grep LLM_KEY`
3. Restart services: `docker-compose restart backend`

### Issue: "Database connection failed"

**Solution:**
1. Check database password in `.env`
2. Verify database is running: `docker-compose ps mongodb`
3. Check connection string format

### Issue: "CORS error in browser"

**Solution:**
1. Check `CORS_ORIGINS` in backend/.env
2. Ensure frontend URL is included: `http://localhost:3000`
3. Restart backend: `docker-compose restart backend`

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MONGO_URL` | MongoDB connection string | `mongodb://user:pass@host:27017` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379` |
| `EMERGENT_LLM_KEY` | Emergent API key | `sk-emergent-xxx...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (json/plain) | `json` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `AUDIT_LOG_PATH` | Audit log directory | `/app/data/audit` |

## Additional Resources

- [Docker Secrets Documentation](https://docs.docker.com/engine/swarm/secrets/)
- [Environment Variables Best Practices](https://12factor.net/config)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

## Support

For questions about secrets management:
1. Check this document first
2. Review `.env.example` files for reference
3. Consult your security team
4. Contact platform administrators

---

**Remember:** Secrets are sensitive. Treat them like passwords. Never share them publicly.
