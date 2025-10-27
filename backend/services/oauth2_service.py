"""
Organization OAuth2 Service
Handles OAuth2 authorization code flow for organization's Azure OpenAI
"""
import os
import logging
import httpx
import uuid
from typing import Optional, Dict
from datetime import datetime, timedelta
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class OrganizationOAuth2Service:
    """
    Handles OAuth2 flow for organization's API access
    Manages token lifecycle (acquire, refresh, expiry)
    """
    
    def __init__(self):
        self.token_cache: Dict[str, Dict] = {}
        logger.info("✅ OrganizationOAuth2Service initialized")
    
    async def get_access_token(
        self,
        auth_url: str,
        token_url: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        scopes: str,
        user_id: str = "default"
    ) -> Optional[str]:
        """
        Get valid access token (from cache or new OAuth2 flow)
        
        Args:
            auth_url: OAuth2 authorization endpoint
            token_url: OAuth2 token endpoint
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            redirect_uri: Redirect URI for callback
            scopes: Space-separated scopes
            user_id: User identifier for token caching
            
        Returns:
            Access token or None if failed
        """
        
        # Check cache first
        cached_token = self._get_cached_token(user_id)
        if cached_token:
            logger.info(f"✅ Using cached access token for {user_id}")
            return cached_token
        
        # Need to get new token via OAuth2 flow
        logger.info(f"🔐 Starting OAuth2 flow for {user_id}")
        
        # For server-to-server, use client credentials flow
        # If you need user interaction, we'll need to implement authorization code flow
        token_data = await self._get_token_client_credentials(
            token_url=token_url,
            client_id=client_id,
            client_secret=client_secret,
            scopes=scopes
        )
        
        if token_data:
            # Cache token
            self._cache_token(user_id, token_data)
            return token_data["access_token"]
        
        return None
    
    async def _get_token_client_credentials(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        scopes: str
    ) -> Optional[Dict]:
        """
        Get token using client credentials flow (server-to-server)
        """
        try:
            logger.info(f"🔐 OAuth2: Requesting token from {token_url}")
            logger.info(f"   Client ID: {client_id[:10]}...")
            logger.info(f"   Scopes: {scopes}")
            
            async with httpx.AsyncClient(verify=False) as client:  # Disable SSL verification
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "scope": scopes
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                logger.info(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info("✅ Access token acquired via OAuth2")
                    logger.info(f"   Expires in: {token_data.get('expires_in', 'unknown')}s")
                    return token_data
                else:
                    logger.error(f"❌ OAuth2 token request failed: {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ OAuth2 flow failed: {e}", exc_info=True)
            return None
    
    async def get_authorization_url(
        self,
        auth_url: str,
        client_id: str,
        redirect_uri: str,
        scopes: str,
        state: Optional[str] = None
    ) -> str:
        """
        Generate authorization URL for user-interactive flow
        
        Returns:
            URL to redirect user to for authorization
        """
        state = state or str(uuid.uuid4())
        
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "state": state
        }
        
        auth_url_with_params = f"{auth_url}?{urlencode(params)}"
        
        logger.info(f"Generated authorization URL with state: {state}")
        
        return auth_url_with_params
    
    async def exchange_code_for_token(
        self,
        token_url: str,
        code: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        user_id: str = "default"
    ) -> Optional[str]:
        """
        Exchange authorization code for access token
        
        Args:
            token_url: OAuth2 token endpoint
            code: Authorization code from callback
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            redirect_uri: Redirect URI (must match)
            user_id: User identifier
            
        Returns:
            Access token or None
        """
        try:
            logger.info(f"🔐 OAuth2: Exchanging authorization code for token")
            logger.info(f"   Token URL: {token_url}")
            logger.info(f"   Client ID: {client_id[:10]}...")
            logger.info(f"   Redirect URI: {redirect_uri}")
            
            async with httpx.AsyncClient(verify=False) as client:  # Disable SSL verification
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                logger.info(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # Cache token
                    self._cache_token(user_id, token_data)
                    
                    logger.info(f"✅ Access token acquired for {user_id}")
                    logger.info(f"   Expires in: {token_data.get('expires_in', 'unknown')}s")
                    return token_data["access_token"]
                else:
                    logger.error(f"❌ Token exchange failed: {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Token exchange error: {e}", exc_info=True)
            return None
    
    async def get_device_code(
        self,
        device_code_url: str,
        client_id: str,
        scopes: str
    ) -> Optional[Dict]:
        """
        Start device code flow - get device code and verification URL
        
        Returns:
            {
                "device_code": "...",
                "user_code": "ABC123",
                "verification_uri": "https://microsoft.com/devicelogin",
                "expires_in": 900,
                "interval": 5
            }
        """
        try:
            logger.info(f"🔐 OAuth2: Requesting device code")
            logger.info(f"   Device Code URL: {device_code_url}")
            logger.info(f"   Client ID: {client_id[:10]}...")
            logger.info(f"   Scopes: {scopes}")
            
            async with httpx.AsyncClient(verify=False) as client:  # Disable SSL verification
                response = await client.post(
                    device_code_url,
                    data={
                        "client_id": client_id,
                        "scope": scopes
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                logger.info(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    device_data = response.json()
                    logger.info("✅ Device code acquired")
                    logger.info(f"   User Code: {device_data.get('user_code')}")
                    logger.info(f"   Verification URI: {device_data.get('verification_uri')}")
                    logger.info(f"   Expires in: {device_data.get('expires_in')}s")
                    return device_data
                else:
                    logger.error(f"❌ Device code request failed: {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Device code flow failed: {e}", exc_info=True)
            return None
    
    async def poll_device_token(
        self,
        token_url: str,
        client_id: str,
        client_secret: str,
        device_code: str,
        user_id: str = "default"
    ) -> Optional[Dict]:
        """
        Poll for device token (checks if user has completed authentication)
        
        Returns:
            {
                "status": "pending|authorized|error",
                "access_token": "..." (if authorized),
                "error": "..." (if error)
            }
        """
        try:
            async with httpx.AsyncClient(verify=False) as client:  # Disable SSL verification
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "device_code": device_code
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # Cache token
                    self._cache_token(user_id, token_data)
                    
                    logger.info(f"✅ Device authentication complete for {user_id}")
                    logger.info(f"   Expires in: {token_data.get('expires_in', 'unknown')}s")
                    
                    return {
                        "status": "authorized",
                        "access_token": token_data["access_token"]
                    }
                elif response.status_code == 400:
                    error_data = response.json()
                    error_code = error_data.get("error", "")
                    
                    if error_code == "authorization_pending":
                        # User hasn't completed authentication yet
                        return {"status": "pending"}
                    elif error_code == "slow_down":
                        # Polling too fast
                        logger.warning("⚠️ Polling too fast, slowing down")
                        return {"status": "pending", "slow_down": True}
                    elif error_code == "expired_token":
                        # Device code expired
                        logger.error("❌ Device code expired")
                        return {"status": "error", "error": "Device code expired"}
                    elif error_code == "access_denied":
                        # User denied access
                        logger.error("❌ User denied access")
                        return {"status": "error", "error": "User denied access"}
                    else:
                        logger.error(f"❌ Device token error: {error_code}")
                        return {"status": "error", "error": error_code}
                else:
                    logger.error(f"❌ Device token request failed: {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                    return {"status": "error", "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"❌ Device token polling error: {e}", exc_info=True)
            return {"status": "error", "error": str(e)}
    
    async def refresh_token(
        self,
        token_url: str,
        refresh_token: str,
        client_id: str,
        client_secret: str,
        user_id: str = "default"
    ) -> Optional[str]:
        """
        Refresh access token using refresh token
        """
        try:
            logger.info(f"🔄 OAuth2: Refreshing token for {user_id}")
            
            async with httpx.AsyncClient(verify=False) as client:  # Disable SSL verification
                response = await client.post(
                    token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": client_id,
                        "client_secret": client_secret
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                logger.info(f"   Response status: {response.status_code}")
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    # Update cache
                    self._cache_token(user_id, token_data)
                    
                    logger.info(f"✅ Access token refreshed for {user_id}")
                    return token_data["access_token"]
                else:
                    logger.error(f"❌ Token refresh failed: {response.status_code}")
                    logger.error(f"   Response: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Token refresh error: {e}", exc_info=True)
            return None
    
    def _cache_token(self, user_id: str, token_data: Dict):
        """Cache token with expiry"""
        expires_in = token_data.get("expires_in", 3600)
        
        self.token_cache[user_id] = {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in - 60),  # 60s buffer
            "token_type": token_data.get("token_type", "Bearer")
        }
        
        logger.info(f"Token cached for {user_id}, expires in {expires_in}s")
    
    def _get_cached_token(self, user_id: str) -> Optional[str]:
        """Get cached token if still valid"""
        if user_id not in self.token_cache:
            return None
        
        token_info = self.token_cache[user_id]
        
        # Check if expired
        if datetime.utcnow() >= token_info["expires_at"]:
            logger.info(f"Cached token for {user_id} expired")
            del self.token_cache[user_id]
            return None
        
        return token_info["access_token"]
    
    def clear_cache(self, user_id: Optional[str] = None):
        """Clear token cache"""
        if user_id:
            self.token_cache.pop(user_id, None)
        else:
            self.token_cache.clear()
        
        logger.info(f"Token cache cleared for {user_id or 'all users'}")


# Singleton instance
_oauth2_service = None


def get_oauth2_service() -> OrganizationOAuth2Service:
    """Get or create OAuth2Service singleton"""
    global _oauth2_service
    if _oauth2_service is None:
        _oauth2_service = OrganizationOAuth2Service()
    return _oauth2_service
