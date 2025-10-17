# AWS VPC Endpoint URL Support

## Feature Overview

Added support for custom AWS Bedrock endpoint URLs to enable organizations to connect through:
- **VPC Endpoints** (PrivateLink)
- **Organization-specific AWS URLs**
- **Custom proxy endpoints**

This is particularly useful for enterprises that require private connectivity to AWS services without traversing the public internet.

## Implementation

### Architecture Flow

```
Frontend (LLM Settings)
    ↓ (sends AWS config including endpoint_url)
Backend (server.py)
    ↓ (transforms to aws_config dict)
LLM Client (llm_client.py)
    ↓ (passes endpoint_url to boto3)
AWS Bedrock (via custom endpoint)
```

### Files Modified

1. **`/app/frontend/src/pages/ChatInterface.js`**
   - Added `aws_endpoint_url` to llmConfig state
   - Added UI field "AWS Endpoint URL (Optional)" with helper text
   - Placeholder: `https://bedrock.vpce-xxxxx.region.vpce.amazonaws.com`

2. **`/app/backend/server.py`**
   - Updated `/api/chat/config` POST endpoint to transform frontend format to backend format
   - Added logic to extract `aws_endpoint_url` from frontend and add to `aws_config` dict
   - Updated `/api/chat/config` GET endpoint to transform backend format back to frontend format
   - Properly masks sensitive credentials (access keys, secret keys)

3. **`/app/backend/llm_client.py`**
   - Updated `ChatBedrock` initialization to accept `endpoint_url` parameter
   - Added conditional logic to include `endpoint_url` in bedrock_kwargs if provided

## Usage

### For Standard AWS Connection (Public Internet)
Simply provide:
- AWS Access Key ID
- AWS Secret Access Key
- AWS Region (e.g., `us-east-1`)
- Bedrock Model ID

Leave **AWS Endpoint URL** empty.

### For VPC Endpoint Connection
Provide all standard fields PLUS:
- **AWS Endpoint URL**: Your VPC endpoint URL
  - Format: `https://bedrock.vpce-{id}.{region}.vpce.amazonaws.com`
  - Example: `https://bedrock.vpce-0a1b2c3d.us-east-1.vpce.amazonaws.com`

### For Organization-Specific URLs
If your organization uses custom AWS endpoints (e.g., through a proxy), enter that URL in the **AWS Endpoint URL** field.

## Configuration Example

### Frontend State
```javascript
{
  provider: 'bedrock',
  model: 'claude-3-7-sonnet-20250219',
  aws_access_key_id: 'AKIA...',
  aws_secret_access_key: '***',
  aws_region: 'us-east-1',
  aws_endpoint_url: 'https://bedrock.vpce-xxxxx.us-east-1.vpce.amazonaws.com',
  bedrock_model_id: 'anthropic.claude-3-sonnet-20240229-v1:0'
}
```

### Backend Transformation (Internal)
```python
{
  'provider': 'bedrock',
  'model': 'anthropic.claude-3-sonnet-20240229-v1:0',
  'aws_config': {
    'access_key_id': 'AKIA...',
    'secret_access_key': '***',
    'region': 'us-east-1',
    'endpoint_url': 'https://bedrock.vpce-xxxxx.us-east-1.vpce.amazonaws.com'
  }
}
```

### LLM Client Usage
```python
ChatBedrock(
    model_id='anthropic.claude-3-sonnet-20240229-v1:0',
    region_name='us-east-1',
    endpoint_url='https://bedrock.vpce-xxxxx.us-east-1.vpce.amazonaws.com',  # Custom endpoint
    credentials_profile_name=None,
    model_kwargs={'temperature': 0.7, 'max_tokens': 4096}
)
```

## Security Considerations

1. **Credential Masking**: Access keys and secret keys are masked (`***`) when retrieving configuration
2. **VPC Security**: VPC endpoints keep traffic within AWS network
3. **No Public Exposure**: Endpoint URLs are not logged or exposed in error messages

## Testing

To test with your VPC endpoint:

1. Open LLM Settings in the UI
2. Select "AWS Bedrock" provider
3. Enter your AWS credentials
4. Enter your VPC endpoint URL in the "AWS Endpoint URL" field
5. Enter Bedrock Model ID
6. Click "Save Configuration"
7. Send a message to test the connection

## Benefits

✅ **Private Connectivity**: Traffic stays within AWS private network
✅ **Enhanced Security**: Meets enterprise security requirements
✅ **Reduced Latency**: Direct VPC connectivity can improve performance
✅ **Compliance**: Satisfies regulatory requirements for data transit
✅ **Flexible**: Works with standard public endpoints too (leave field empty)

## Troubleshooting

### Connection Fails with VPC Endpoint
- Verify the VPC endpoint is active and accessible from your network
- Check security groups allow traffic to the endpoint
- Ensure the endpoint URL format is correct
- Verify IAM permissions include necessary Bedrock actions

### "Endpoint URL not working"
- Double-check the URL format (should start with `https://`)
- Ensure the region in the URL matches the selected AWS Region
- Test with standard endpoint first (leave URL empty) to verify credentials

## Future Enhancements

Potential improvements:
- Add "Test Connection" button to validate endpoint before saving
- Support for AWS STS temporary credentials
- AWS SSO integration
- Endpoint URL validation with regex
