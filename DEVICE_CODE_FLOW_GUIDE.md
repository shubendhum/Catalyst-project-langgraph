# OAuth2 Device Code Flow - Complete Guide

## What is Device Code Flow?

Device Code Flow is an OAuth2 authentication method designed for devices or applications that:
- Cannot display a web browser for redirect-based login
- Cannot use a custom redirect URI
- Need to work with corporate security policies

Perfect for your use case where the Azure AD app is configured with `https://login.microsoft.com/common/oAuth2/nativeclient` as the redirect URI.

## How It Works

```
┌─────────┐                  ┌──────────┐                 ┌─────────────┐
│  User   │                  │ Catalyst │                 │   Azure AD  │
│         │                  │ Backend  │                 │             │
└────┬────┘                  └─────┬────┘                 └──────┬──────┘
     │                             │                              │
     │  1. Click "Authenticate"    │                              │
     ├────────────────────────────>│                              │
     │                             │                              │
     │                             │  2. Request Device Code      │
     │                             ├─────────────────────────────>│
     │                             │                              │
     │                             │  3. Return Device Code       │
     │                             │     + User Code + URL        │
     │                             │<─────────────────────────────┤
     │                             │                              │
     │  4. Show User Code & URL    │                              │
     │<────────────────────────────┤                              │
     │                             │                              │
     │  5. Visit URL in browser    │                              │
     │  6. Enter user code         │                              │
     │  7. Complete authentication │                              │
     ├──────────────────────────────────────────────────────────>│
     │                             │                              │
     │                             │  8. Poll for token           │
     │                             │     (every 5 seconds)        │
     │                             ├─────────────────────────────>│
     │                             │                              │
     │                             │  9. Return access token      │
     │                             │     (when user completes)    │
     │                             │<─────────────────────────────┤
     │                             │                              │
     │  10. Authentication Done!   │                              │
     │<────────────────────────────┤                              │
     │                             │                              │
```

## Configuration

### Required Fields

In the Organization Azure OpenAI settings:

1. **Base URL**: Your API endpoint
   ```
   https://api.macquarie.com
   ```

2. **Deployment Name**: Azure OpenAI deployment
   ```
   gpt-4
   ```

3. **API Version**: Azure OpenAI API version
   ```
   2024-02-15-preview
   ```

4. **Subscription Key**: Your x-subscription-key header value
   ```
   your-subscription-key-here
   ```

5. **Token URL**: OAuth2 token endpoint
   ```
   https://login.microsoftonline.com/{tenant-id}/oauth2/v2.0/token
   ```
   
   Replace `{tenant-id}` with:
   - Your actual tenant ID (e.g., `abc123-def456-...`)
   - OR use `common` for multi-tenant
   - OR use `organizations` for any organizational account

6. **Client ID**: Your Azure AD application client ID
   ```
   12345678-1234-1234-1234-123456789012
   ```

7. **Client Secret**: Your Azure AD application client secret
   ```
   your-client-secret-here
   ```

8. **Scopes**: Required OAuth scopes
   ```
   https://api.macquarie.com/.default
   ```
   
   Common Azure AD scopes:
   - `https://api.macquarie.com/.default` - For your custom API
   - `https://graph.microsoft.com/.default` - For Microsoft Graph
   - `openid profile email` - For user info

### Optional Fields (Not Used in Device Code Flow)

- **Authorization URL**: Disabled (not needed)
- **Redirect URI**: Disabled (not needed)

## How to Use

### Step 1: Configure Settings

1. Navigate to Chat Interface
2. Open "LLM Settings"
3. Select "Organization Azure OpenAI"
4. Fill in all required fields
5. Click "Save Configuration"

### Step 2: Authenticate

1. Click "Start Device Code Authentication" button
2. You'll see a message like:

```
🔑 Authentication Required:

1. Visit: https://microsoft.com/devicelogin
2. Enter code: ABC123XYZ
3. Return here - we'll detect when you're done!

This code expires in 15 minutes.
```

### Step 3: Complete Authentication

1. Click the link or copy the URL to your browser
2. Sign in with your organizational credentials
3. Enter the device code when prompted
4. Grant the requested permissions
5. Return to Catalyst - it will automatically detect completion!

### Step 4: Start Using!

Once authenticated, you can:
- Send messages to Organization Azure OpenAI
- Token is cached and auto-refreshed
- Works until token expires (typically 1 hour)

## API Endpoints

### Backend Endpoints

#### 1. Start Device Code Flow
```http
POST /api/auth/device/start
Content-Type: application/json

{
  "device_code_url": "https://login.microsoftonline.com/.../oauth2/v2.0/devicecode",
  "token_url": "https://login.microsoftonline.com/.../oauth2/v2.0/token",
  "client_id": "your-client-id",
  "client_secret": "your-client-secret",
  "scopes": "https://api.macquarie.com/.default"
}
```

Response:
```json
{
  "success": true,
  "session_id": "uuid-here",
  "user_code": "ABC123XYZ",
  "verification_uri": "https://microsoft.com/devicelogin",
  "expires_in": 900,
  "interval": 5
}
```

#### 2. Poll for Authentication
```http
GET /api/auth/device/poll?session_id={session_id}
```

Responses:

**Pending (still waiting):**
```json
{
  "status": "pending"
}
```

**Authorized (success):**
```json
{
  "status": "authorized",
  "access_token": "eyJ0eXAi..."
}
```

**Error:**
```json
{
  "status": "error",
  "error": "Device code expired"
}
```

## Troubleshooting

### Issue: Device code expired
**Solution**: Code expires in 15 minutes. Click "Start Device Code Authentication" again to get a new code.

### Issue: User denied access
**Solution**: You declined the permission request. Try again and accept the permissions.

### Issue: Invalid client credentials
**Solution**: Check that your Client ID and Client Secret are correct in the configuration.

### Issue: Invalid scopes
**Solution**: Verify the scopes match what's configured in your Azure AD app registration. Use `.default` scope for API access.

### Issue: Polling timeout
**Solution**: Authentication took too long. Try again and complete within 15 minutes.

### Issue: SSL certificate errors
**Solution**: SSL verification is already disabled in the code for corporate environments. No action needed.

## Azure AD App Configuration

Your Azure AD app registration should have:

✅ **Application Type**: 
- Public client/native (allows device code flow)
- OR Confidential client with device code enabled

✅ **Redirect URIs**: 
- Can use `https://login.microsoft.com/common/oAuth2/nativeclient`
- Device code flow doesn't need custom redirect URI

✅ **API Permissions**:
- Grant appropriate API permissions
- Admin consent may be required

✅ **Supported Account Types**:
- Accounts in this organizational directory only (single tenant)
- OR Accounts in any organizational directory (multi-tenant)

## Advantages of Device Code Flow

✅ **No Redirect URI Issues**: Works with native client redirect URIs
✅ **User-Friendly**: Clear instructions, easy to follow
✅ **Secure**: Industry-standard OAuth2 flow
✅ **Corporate Compatible**: Works with SSL inspection, proxies, etc.
✅ **Browser Agnostic**: Works on any device with a browser
✅ **No Popup Blockers**: User opens link manually

## Security Notes

🔒 **Device Code**: Short-lived, single-use, random code
🔒 **Token Storage**: Cached in memory only (server-side)
🔒 **SSL Disabled**: For corporate proxy compatibility
🔒 **Client Secret**: Stored server-side, never exposed to frontend
🔒 **Polling**: Backend polls Azure AD, frontend polls backend

## Logging

All authentication steps are logged:

```
🔐 Starting OAuth2 Device Code Flow
   Device Code URL: https://login.microsoftonline.com/.../devicecode
   Token URL: https://login.microsoftonline.com/.../token
   Client ID: abc123def4...
   Scopes: https://api.macquarie.com/.default
✅ Device code acquired
   User Code: ABC123XYZ
   Verification URI: https://microsoft.com/devicelogin
   Expires in: 900s
✅ Device authentication complete for session 12345678...
   Expires in: 3600s
```

Check backend logs at `/api/logs/backend` for full authentication flow details.

## Example Configuration

**For Microsoft Commercial Cloud:**
```
Token URL: https://login.microsoftonline.com/common/oauth2/v2.0/token
Scopes: https://api.macquarie.com/.default
```

**For Azure Government:**
```
Token URL: https://login.microsoftonline.us/{tenant-id}/oauth2/v2.0/token
Scopes: https://api.macquarie.com/.default
```

**For Azure China:**
```
Token URL: https://login.chinacloudapi.cn/{tenant-id}/oauth2/v2.0/token
Scopes: https://api.macquarie.com/.default
```

## Testing

To test the device code flow:

1. **Save configuration** with all required fields
2. **Click authenticate** and note the user code
3. **Visit verification URI** in any browser
4. **Enter the code** and complete login
5. **Return to Catalyst** - should auto-detect completion within 5-10 seconds
6. **Send a test message** to verify API calls work

## Support

If you encounter issues:
1. Check backend logs for detailed error messages
2. Verify all configuration fields are correct
3. Ensure Azure AD app has appropriate permissions
4. Confirm scopes match Azure AD app configuration
5. Try generating a new device code if expired

---

**Status**: ✅ Fully Implemented and Working
**Last Updated**: 2025-10-27
