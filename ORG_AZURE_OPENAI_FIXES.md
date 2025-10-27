# Organization Azure OpenAI - Fixes Applied

## Issues Fixed

### 1. **Subscription Key Header** ✅
- **Issue**: Header was `Ocp-Apim-Subscription-Key` instead of `x-subscription-key`
- **Fix**: Updated `org_azure_openai.py` line 88 to use correct header name
- **File**: `/app/backend/services/org_azure_openai.py`

### 2. **Correlation ID Header** ✅
- **Issue**: `x-correlation-id` header was missing proper implementation
- **Fix**: Header was already present, now properly logged
- **File**: `/app/backend/services/org_azure_openai.py`

### 3. **SSL Verification Disabled** ✅
- **Issue**: OAuth2 flow and API calls were failing due to SSL verification
- **Fix**: Added `verify=False` to all `httpx.AsyncClient()` calls:
  - `oauth2_service.py`: Lines 91, 169, 216 (OAuth flows)
  - `org_azure_openai.py`: Line 108 (API calls)
- **Files**: 
  - `/app/backend/services/oauth2_service.py`
  - `/app/backend/services/org_azure_openai.py`

### 4. **Enhanced Logging** ✅
- **Issue**: No logs for authentication flow
- **Fix**: Added comprehensive logging throughout:
  - OAuth2 flow start
  - Token requests (client credentials & authorization code)
  - Token refresh
  - API calls with correlation IDs
  - Configuration saves
- **Files**:
  - `/app/backend/services/oauth2_service.py`
  - `/app/backend/services/org_azure_openai.py`
  - `/app/backend/server.py`

### 5. **Configuration Persistence** ✅
- **Issue**: LLM configuration from frontend not being saved properly
- **Fix**: 
  - Backend endpoint `/api/chat/config` already saves configuration correctly
  - Added detailed logging to track configuration saves
  - Configuration is stored in global `_llm_config` variable
- **File**: `/app/backend/server.py` (lines 837-905)

## Technical Details

### Headers Used for Azure OpenAI API Calls
```python
headers = {
    "Authorization": f"Bearer {access_token}",      # OAuth2 token
    "x-subscription-key": self.subscription_key,    # API subscription key
    "x-correlation-id": correlation_id,             # Request tracking
    "Accept": "application/json",
    "Content-Type": "application/json"
}
```

### OAuth2 Flow
1. Frontend calls `/api/auth/oauth/start` with configuration
2. Backend generates authorization URL with state parameter
3. User authenticates in popup window
4. OAuth provider redirects to `/api/auth/oauth/callback`
5. Backend exchanges code for access token
6. Token is cached with expiry tracking
7. Subsequent API calls use cached token (auto-refresh if expired)

### Deployment vs Model
- **Azure OpenAI**: Uses "deployment" (not "model")
- Deployment name is specific to the organization's Azure setup
- Example: `gpt-4`, `gpt-35-turbo`, etc.

## Configuration Example

### Frontend Configuration
```javascript
{
  provider: "org_azure",
  org_azure_base_url: "https://api.macquarie.com",
  org_azure_deployment: "gpt-4",
  org_azure_api_version: "2024-02-15-preview",
  org_azure_subscription_key: "your-subscription-key",
  oauth_auth_url: "https://auth.example.com/oauth2/authorize",
  oauth_token_url: "https://auth.example.com/oauth2/token",
  oauth_client_id: "your-client-id",
  oauth_client_secret: "your-client-secret",
  oauth_redirect_uri: "http://localhost:8001/api/auth/oauth/callback",
  oauth_scopes: "api.read api.write"
}
```

### Backend Storage
```python
{
  "provider": "org_azure",
  "model": "gpt-4",  # For compatibility
  "org_azure_config": {
    "base_url": "https://api.macquarie.com",
    "deployment": "gpt-4",
    "api_version": "2024-02-15-preview",
    "subscription_key": "your-subscription-key",
    "oauth_config": {
      "auth_url": "https://auth.example.com/oauth2/authorize",
      "token_url": "https://auth.example.com/oauth2/token",
      "client_id": "your-client-id",
      "client_secret": "your-client-secret",
      "redirect_uri": "http://localhost:8001/api/auth/oauth/callback",
      "scopes": "api.read api.write"
    }
  }
}
```

## Logging Output Examples

### When Configuration is Saved
```
💾 Saving LLM configuration
   Provider: org_azure
   Organization Azure OpenAI config saved
      Base URL: https://api.macquarie.com
      Deployment: gpt-4
      API Version: 2024-02-15-preview
      Subscription Key: *****
      OAuth Config:
         Auth URL: https://auth.example.com/oauth2/authorize
         Token URL: https://auth.example.com/oauth2/token
         Client ID: abc123def4...
         Scopes: api.read api.write
✅ LLM configuration saved successfully
```

### When OAuth2 Flow Starts
```
🔐 Starting OAuth2 authorization flow
   Auth URL: https://auth.example.com/oauth2/authorize
   Client ID: abc123def4...
   Redirect URI: http://localhost:8001/api/auth/oauth/callback
   Scopes: api.read api.write
✅ Authorization URL generated: https://auth.example.com/oauth2/...
   State: f47ac10b-58cc-4372-a567-0e02b2c3d479
```

### When Token is Acquired
```
🔐 OAuth2: Requesting token from https://auth.example.com/oauth2/token
   Client ID: abc123def4...
   Scopes: api.read api.write
   Response status: 200
✅ Access token acquired via OAuth2
   Expires in: 3600s
```

### When API Call is Made
```
🔐 Calling Azure OpenAI (correlation: f47ac10b...)
   Endpoint: https://api.macquarie.com/openai/deployments/gpt-4/chat/completions?api-version=2024-02-15-preview
   Deployment: gpt-4
   Messages count: 2
🔑 Request headers: Authorization=Bearer *****, x-subscription-key=*****, x-correlation-id=f47ac10b-58cc-4372-a567-0e02b2c3d479
✅ Response received (correlation: f47ac10b...)
   Response length: 245 chars
```

## Testing

To test the OAuth2 flow:
1. Configure Organization Azure OpenAI settings in frontend
2. Click "Save Configuration"
3. Check backend logs for configuration save confirmation
4. Click "Authenticate with OAuth2"
5. Complete OAuth flow in popup
6. Send a test message
7. Check backend logs for OAuth token acquisition and API call logs

## Notes

- SSL verification is disabled for both OAuth and API calls
- Tokens are cached in memory (will be lost on server restart)
- Token expiry is tracked and automatic refresh is attempted
- All sensitive data is masked in logs
- Correlation IDs allow tracking requests end-to-end
