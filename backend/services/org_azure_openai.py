"""
Organization Azure OpenAI Client
Handles authentication and API calls to organization's Azure OpenAI endpoint
"""
import logging
import httpx
import uuid
from typing import List, Dict, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from services.oauth2_service import get_oauth2_service

logger = logging.getLogger(__name__)


class OrganizationAzureOpenAIClient:
    """
    Custom OpenAI client for organization's Azure OpenAI endpoint
    Handles OAuth2 authentication and custom headers
    """
    
    def __init__(
        self,
        base_url: str,
        deployment: str,
        api_version: str,
        subscription_key: str,
        oauth_config: Dict
    ):
        """
        Initialize organization's Azure OpenAI client
        
        Args:
            base_url: Base path (e.g., https://api.macquarie.com)
            deployment: Deployment name (e.g., gpt-4, gpt-35-turbo)
                       This deployment is already configured with a model in Azure
            api_version: API version (e.g., 2024-02-15-preview)
            subscription_key: x-subscription-key header value
            oauth_config: OAuth2 configuration dict
        """
        self.base_url = base_url.rstrip('/')
        self.deployment = deployment
        self.api_version = api_version
        self.subscription_key = subscription_key
        self.oauth_config = oauth_config
        
        self.oauth_service = get_oauth2_service()
        
        # Build endpoint URL
        self.endpoint_url = (
            f"{self.base_url}/openai/deployments/{self.deployment}"
            f"/chat/completions?api-version={self.api_version}"
        )
        
        logger.info(f"✅ Organization Azure OpenAI client initialized")
        logger.info(f"   Endpoint: {self.endpoint_url}")
        logger.info(f"   Deployment: {self.deployment}")
    
    async def ainvoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """
        Invoke Azure OpenAI with OAuth2 authentication
        
        Args:
            messages: List of messages (LangChain format)
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            AIMessage with response
        """
        
        # Get access token (will handle OAuth2 flow automatically)
        access_token = await self._get_access_token()
        
        if not access_token:
            raise Exception("Failed to acquire OAuth2 access token")
        
        # Convert messages to OpenAI format
        openai_messages = self._convert_messages(messages)
        
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {access_token}",
            "x-subscription-key": self.subscription_key,  # Changed from Ocp-Apim-Subscription-Key
            "x-correlation-id": correlation_id,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        logger.info(f"🔑 Request headers: Authorization=Bearer *****, x-subscription-key=*****, x-correlation-id={correlation_id}")
        
        body = {
            "messages": openai_messages,
            "max_completion_tokens": kwargs.get("max_tokens", 2000),  # Updated for newer Azure OpenAI API
            "stream": False
        }
        
        logger.info(f"🔐 Calling Azure OpenAI (correlation: {correlation_id[:8]}...)")
        logger.info(f"   Endpoint: {self.endpoint_url}")
        logger.info(f"   Deployment: {self.deployment}")
        logger.info(f"   Messages count: {len(openai_messages)}")
        
        try:
            async with httpx.AsyncClient(timeout=60.0, verify=False) as client:  # Disable SSL verification
                response = await client.post(
                    self.endpoint_url,
                    headers=headers,
                    json=body
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract response
                    content = data["choices"][0]["message"]["content"]
                    
                    logger.info(f"✅ Response received (correlation: {correlation_id[:8]}...)")
                    logger.info(f"   Response length: {len(content)} chars")
                    
                    return AIMessage(content=content)
                
                elif response.status_code == 401:
                    # Token expired or invalid
                    logger.warning("⚠️ Access token expired or invalid (401), refreshing...")
                    logger.warning(f"   Response: {response.text}")
                    
                    # Clear cache and retry
                    self.oauth_service.clear_cache()
                    
                    # Retry once with new token
                    return await self.ainvoke(messages, **kwargs)
                
                else:
                    error_msg = f"Azure OpenAI API error: {response.status_code} - {response.text}"
                    logger.error(f"❌ {error_msg}")
                    raise Exception(error_msg)
                    
        except httpx.TimeoutException:
            logger.error("Azure OpenAI API timeout")
            raise Exception("API request timed out")
        except Exception as e:
            logger.error(f"Azure OpenAI API call failed: {e}")
            raise
    
    async def _get_access_token(self) -> Optional[str]:
        """
        Get valid access token (handles OAuth2 flow)
        Uses cached token from device code flow if available
        """
        
        # First check if we have a token from device code flow
        # Device code flow stores tokens in oauth_service with user_id
        # For device code flow, we use a consistent user_id
        user_id = "device_code_user"
        
        # Check cached token first
        cached_token = self.oauth_service._get_cached_token(user_id)
        if cached_token:
            logger.info(f"✅ Using cached device code token")
            return cached_token
        
        # If no cached token, try to get one via client credentials
        # (This is fallback for non-device-code scenarios)
        logger.warning("⚠️ No cached device code token found, attempting client credentials flow")
        
        return await self.oauth_service.get_access_token(
            auth_url=self.oauth_config["auth_url"],
            token_url=self.oauth_config["token_url"],
            client_id=self.oauth_config["client_id"],
            client_secret=self.oauth_config["client_secret"],
            redirect_uri=self.oauth_config["redirect_uri"],
            scopes=self.oauth_config["scopes"],
            user_id=user_id  # Use consistent user_id
        )
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict]:
        """Convert LangChain messages to OpenAI format"""
        openai_messages = []
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            else:
                role = "user"
            
            content = msg.content if hasattr(msg, 'content') else str(msg)
            
            openai_messages.append({
                "role": role,
                "content": content
            })
        
        return openai_messages


def create_org_azure_client(config: Dict) -> OrganizationAzureOpenAIClient:
    """
    Factory function to create Organization Azure OpenAI client
    
    Args:
        config: Configuration dict with required fields:
               - base_url: API base URL
               - deployment: Deployment name (already configured with model in Azure)
               - api_version: API version
               - subscription_key: Subscription key for API
               - oauth_config: OAuth2 configuration
        
    Returns:
        OrganizationAzureOpenAIClient instance
    """
    return OrganizationAzureOpenAIClient(
        base_url=config["base_url"],
        deployment=config["deployment"],
        api_version=config["api_version"],
        subscription_key=config["subscription_key"],
        oauth_config=config["oauth_config"]
    )
