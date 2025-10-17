# AWS Bedrock Integration Guide

## ✅ Yes, Catalyst Fully Supports AWS Bedrock!

Catalyst includes built-in support for **Amazon Bedrock** with Claude models. You can use Bedrock alongside or instead of the Emergent LLM Key.

---

## 🎯 Supported LLM Providers

Catalyst's `UnifiedLLMClient` supports three providers:

| Provider | Models | Configuration |
|----------|--------|---------------|
| **Emergent LLM Key** | Claude, GPT, Gemini | Default - Pre-configured |
| **Anthropic Direct** | Claude 3.x | Custom API key |
| **AWS Bedrock** ✅ | Claude via Bedrock | AWS credentials |

---

## 🚀 Quick Start with AWS Bedrock

### Option 1: Via Environment Variables (Recommended)

**1. Configure AWS Credentials**

Edit `backend/.env`:
```bash
# AWS Bedrock Configuration
DEFAULT_LLM_PROVIDER=bedrock
DEFAULT_LLM_MODEL=anthropic.claude-3-sonnet-20240229-v1:0

# AWS Credentials
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# Optional: Specific model ID
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

**2. Restart Backend**

```bash
# Using Makefile
make restart

# Or Docker Compose
docker-compose restart backend
```

**3. Verify Configuration**

```bash
curl http://localhost:8001/api/chat/config
```

---

### Option 2: Via API (Dynamic Configuration)

Change provider at runtime without restart:

```bash
curl -X POST http://localhost:8001/api/chat/config \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "bedrock",
    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "api_key": null,
    "aws_config": {
      "access_key_id": "your-access-key",
      "secret_access_key": "your-secret-key",
      "region": "us-east-1"
    }
  }'
```

---

## 🔧 Detailed Configuration

### Available Bedrock Models

| Model ID | Description | Context | Cost |
|----------|-------------|---------|------|
| `anthropic.claude-3-sonnet-20240229-v1:0` | Claude 3 Sonnet | 200K | $$ |
| `anthropic.claude-3-haiku-20240307-v1:0` | Claude 3 Haiku | 200K | $ |
| `anthropic.claude-3-opus-20240229-v1:0` | Claude 3 Opus | 200K | $$$ |
| `anthropic.claude-v2:1` | Claude 2.1 | 100K | $ |

**Recommended**: `anthropic.claude-3-sonnet-20240229-v1:0` for best balance

### AWS Regions Supporting Bedrock

- `us-east-1` (N. Virginia) ✅ Recommended
- `us-west-2` (Oregon)
- `ap-southeast-1` (Singapore)
- `eu-central-1` (Frankfurt)
- `eu-west-1` (Ireland)

Check [AWS Bedrock Regions](https://docs.aws.amazon.com/bedrock/latest/userguide/bedrock-regions.html) for updates.

---

## 🔐 AWS Credentials Setup

### Method 1: IAM User (Recommended for Development)

**1. Create IAM User**

In AWS Console:
1. Go to IAM → Users → Create User
2. Name: `catalyst-bedrock-user`
3. Enable: Programmatic access

**2. Attach Bedrock Policy**

Attach the following inline policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*"
      ]
    }
  ]
}
```

**3. Get Access Keys**

Save the Access Key ID and Secret Access Key.

---

### Method 2: IAM Role (Production)

**For EC2/ECS Deployment**:

1. Create IAM Role with Bedrock permissions
2. Attach role to EC2 instance or ECS task
3. No need to set AWS credentials in .env

The application will use the instance role automatically.

---

### Method 3: AWS CLI Profile

**1. Configure AWS CLI**

```bash
aws configure --profile catalyst
# Enter your Access Key ID
# Enter your Secret Access Key
# Default region: us-east-1
# Default output: json
```

**2. Use Profile**

```bash
export AWS_PROFILE=catalyst
```

Or in backend/.env:
```bash
AWS_PROFILE=catalyst
```

---

## 💻 Implementation Details

### UnifiedLLMClient with Bedrock

The client automatically handles Bedrock:

```python
from llm_client import get_llm_client

# Using environment variables
llm = get_llm_client()

# Or explicit configuration
llm = get_llm_client({
    "provider": "bedrock",
    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "aws_config": {
        "access_key_id": "...",
        "secret_access_key": "...",
        "region": "us-east-1"
    }
})

# Async invoke
response = await llm.ainvoke([
    HumanMessage(content="Hello, how are you?")
])
```

### LangGraph Integration

Bedrock works seamlessly with LangGraph orchestrator:

```python
from langgraph_orchestrator.orchestrator import LangGraphOrchestrator

# Initialize with Bedrock config
orchestrator = LangGraphOrchestrator(
    db=db,
    ws_manager=manager,
    config={
        "provider": "bedrock",
        "model": "anthropic.claude-3-sonnet-20240229-v1:0"
    }
)

# Execute task
await orchestrator.execute_task(task_id, project_id, prompt)
```

---

## 🧪 Testing Bedrock Connection

### Test via API

```bash
# 1. Set Bedrock as provider
curl -X POST http://localhost:8001/api/chat/config \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "bedrock",
    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "aws_config": {
      "access_key_id": "YOUR_KEY",
      "secret_access_key": "YOUR_SECRET",
      "region": "us-east-1"
    }
  }'

# 2. Send test message
curl -X POST http://localhost:8001/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from Bedrock!",
    "conversation_id": "test-bedrock-123"
  }'

# 3. Check response
# Should get AI response from Bedrock
```

### Test Locally

```python
import asyncio
from llm_client import get_llm_client
from langchain_core.messages import HumanMessage

async def test_bedrock():
    # Configure Bedrock
    llm = get_llm_client({
        "provider": "bedrock",
        "model": "anthropic.claude-3-sonnet-20240229-v1:0",
        "aws_config": {
            "access_key_id": "YOUR_KEY",
            "secret_access_key": "YOUR_SECRET",
            "region": "us-east-1"
        }
    })
    
    # Test message
    response = await llm.ainvoke([
        HumanMessage(content="Say hello from AWS Bedrock!")
    ])
    
    print(f"Response: {response.content}")

# Run test
asyncio.run(test_bedrock())
```

---

## 🔄 Switching Between Providers

### Runtime Switching

Switch providers without restarting:

```bash
# Switch to Bedrock
curl -X POST http://localhost:8001/api/chat/config \
  -H "Content-Type: application/json" \
  -d '{"provider": "bedrock", "model": "anthropic.claude-3-sonnet-20240229-v1:0"}'

# Switch to Emergent LLM Key
curl -X POST http://localhost:8001/api/chat/config \
  -H "Content-Type: application/json" \
  -d '{"provider": "emergent", "model": "claude-3-7-sonnet-20250219"}'

# Switch to Direct Anthropic
curl -X POST http://localhost:8001/api/chat/config \
  -H "Content-Type: application/json" \
  -d '{"provider": "anthropic", "model": "claude-3-7-sonnet-20250219", "api_key": "sk-ant-..."}'
```

### Environment-Based

**Development** (`backend/.env`):
```bash
DEFAULT_LLM_PROVIDER=bedrock
```

**Production** (Docker Compose):
```yaml
environment:
  - DEFAULT_LLM_PROVIDER=bedrock
  - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
  - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
```

---

## 📊 Cost Comparison

### AWS Bedrock Pricing (Approximate)

**Claude 3 Sonnet**:
- Input: $3 per 1M tokens
- Output: $15 per 1M tokens

**Claude 3 Haiku**:
- Input: $0.25 per 1M tokens
- Output: $1.25 per 1M tokens

**Claude 3 Opus**:
- Input: $15 per 1M tokens
- Output: $75 per 1M tokens

### vs Emergent LLM Key

| Provider | Cost Model | Best For |
|----------|-----------|----------|
| **Emergent LLM Key** | Fixed budget | Development, Testing |
| **AWS Bedrock** | Pay per use | Production, Scale |
| **Direct Anthropic** | Pay per use | Flexibility |

---

## 🛡️ Security Best Practices

### 1. Never Hardcode Credentials

❌ **Bad**:
```python
aws_config = {
    "access_key_id": "AKIAIOSFODNN7EXAMPLE",
    "secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
```

✅ **Good**:
```python
aws_config = {
    "access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
    "secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY")
}
```

### 2. Use IAM Roles in Production

```yaml
# ECS Task Definition
executionRoleArn: arn:aws:iam::123456789:role/catalyst-bedrock-role
```

### 3. Rotate Credentials Regularly

```bash
# AWS CLI
aws iam create-access-key --user-name catalyst-bedrock-user
aws iam delete-access-key --access-key-id OLD_KEY --user-name catalyst-bedrock-user
```

### 4. Use AWS Secrets Manager

```python
import boto3

def get_bedrock_credentials():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    secret = client.get_secret_value(SecretId='catalyst/bedrock')
    return json.loads(secret['SecretString'])
```

---

## 🐛 Troubleshooting

### Error: "The security token included in the request is invalid"

**Cause**: Invalid or expired AWS credentials

**Solution**:
```bash
# Verify credentials
aws sts get-caller-identity

# Reconfigure if needed
aws configure
```

### Error: "AccessDeniedException"

**Cause**: IAM user/role lacks Bedrock permissions

**Solution**:
1. Add `bedrock:InvokeModel` permission
2. Ensure model ARN is allowed
3. Check region availability

### Error: "ThrottlingException"

**Cause**: Rate limit exceeded

**Solution**:
1. Implement exponential backoff
2. Request quota increase
3. Use multiple regions

### Model Not Available

**Cause**: Model not available in selected region

**Solution**:
```bash
# Check available models
aws bedrock list-foundation-models --region us-east-1

# Switch to supported region
AWS_REGION=us-west-2
```

---

## 📝 Complete Example

### Backend Configuration

**1. Update `.env`**:
```bash
# AWS Bedrock
DEFAULT_LLM_PROVIDER=bedrock
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

**2. Start Services**:
```bash
make restart
```

**3. Test**:
```bash
# Send message
curl -X POST http://localhost:8001/api/chat/send \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello from AWS Bedrock!",
    "conversation_id": "test-123"
  }'
```

---

## 🎯 Summary

✅ **Catalyst fully supports AWS Bedrock**
✅ **Works with all Claude models on Bedrock**
✅ **Easy configuration via .env or API**
✅ **Seamless integration with LangGraph**
✅ **Production-ready with IAM roles**
✅ **Runtime provider switching**

**Default Setup**: Emergent LLM Key
**Production Option**: AWS Bedrock
**Flexibility**: Switch anytime!

---

## 📚 Additional Resources

- **AWS Bedrock Docs**: https://docs.aws.amazon.com/bedrock/
- **Claude on Bedrock**: https://aws.amazon.com/bedrock/claude/
- **IAM Best Practices**: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- **Catalyst Docs**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

**Need help with Bedrock setup? Check the troubleshooting section or contact support!** 🚀
