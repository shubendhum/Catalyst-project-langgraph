"""
Unified LLM client supporting Emergent LLM Key and custom provider keys
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from emergentintegrations.llm.chat import LlmChat, UserMessage
from langchain_anthropic import ChatAnthropic
from langchain_aws import ChatBedrock
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class UnifiedLLMClient:
    """
    Unified LLM client that supports:
    1. Emergent LLM Key (for OpenAI, Anthropic, Gemini)
    2. Custom Anthropic API keys
    3. Custom AWS Bedrock credentials
    """
    
    def __init__(
        self,
        provider: str = "emergent",
        model: str = "claude-3-7-sonnet-20250219",
        api_key: Optional[str] = None,
        aws_config: Optional[Dict[str, str]] = None,
        org_azure_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the LLM client
        
        Args:
            provider: "emergent", "anthropic", "bedrock", or "org_azure"
            model: Model name
            api_key: API key (for emergent or anthropic)
            aws_config: AWS configuration dict
            org_azure_config: Organization Azure OpenAI config (OAuth2 + API details)
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv("EMERGENT_LLM_KEY")
        self.aws_config = aws_config
        self.org_azure_config = org_azure_config
        
        # Initialize the appropriate client
        if provider == "emergent":
            self.client_type = "emergent"
            self.session_id = f"catalyst-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        elif provider == "anthropic":
            self.client_type = "langchain_anthropic"
            self.client = ChatAnthropic(
                api_key=api_key or os.getenv("ANTHROPIC_API_KEY"),
                model=model,
                temperature=0.7,
                max_tokens=4096
            )
        elif provider == "bedrock":
            self.client_type = "langchain_bedrock"
            # Set AWS credentials if provided
            if aws_config:
                os.environ["AWS_ACCESS_KEY_ID"] = aws_config.get("access_key_id", "")
                os.environ["AWS_SECRET_ACCESS_KEY"] = aws_config.get("secret_access_key", "")
                os.environ["AWS_REGION"] = aws_config.get("region", "us-east-1")
            
            # Prepare ChatBedrock kwargs
            bedrock_kwargs = {
                "model_id": model or os.getenv("BEDROCK_MODEL_ID"),
                "region_name": aws_config.get("region") if aws_config else os.getenv("AWS_REGION", "us-east-1"),
                "credentials_profile_name": None,
                "model_kwargs": {"temperature": 0.7, "max_tokens": 4096}
            }
            
            # Add custom endpoint URL if provided (for VPC endpoints or org-specific URLs)
            if aws_config and aws_config.get("endpoint_url"):
                bedrock_kwargs["endpoint_url"] = aws_config.get("endpoint_url")
            
            self.client = ChatBedrock(**bedrock_kwargs)
        elif provider == "org_azure":
            self.client_type = "org_azure"
            # Will be initialized lazily when needed
            self.org_azure_client = None
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    async def ainvoke(
        self,
        messages: List[BaseMessage],
        system_message: Optional[str] = None
    ) -> AIMessage:
        """
        Async invoke the LLM with messages
        
        Args:
            messages: List of langchain BaseMessage objects
            system_message: Optional system message
            
        Returns:
            AIMessage response
        """
        if self.client_type == "emergent":
            return await self._invoke_emergent(messages, system_message)
        elif self.client_type == "org_azure":
            return await self._invoke_org_azure(messages, system_message)
        else:
            # For langchain clients (anthropic, bedrock)
            if system_message:
                full_messages = [SystemMessage(content=system_message)] + messages
            else:
                full_messages = messages
            
            response = await self.client.ainvoke(full_messages)
            return response
    
    async def _invoke_emergent(
        self,
        messages: List[BaseMessage],
        system_message: Optional[str] = None
    ) -> AIMessage:
        """Invoke using emergentintegrations"""
        
        # Determine provider for emergent
        # Map model to provider
        provider_map = {
            "claude": "anthropic",
            "gpt": "openai",
            "gemini": "gemini"
        }
        
        emergent_provider = "anthropic"  # default
        for key, val in provider_map.items():
            if key in self.model.lower():
                emergent_provider = val
                break
        
        # Create emergent chat client
        chat = LlmChat(
            api_key=self.api_key,
            session_id=self.session_id,
            system_message=system_message or "You are a helpful AI assistant."
        ).with_model(emergent_provider, self.model)
        
        # Convert last message to emergent format
        # For simplicity, we'll just use the last user message
        last_message = messages[-1] if messages else HumanMessage(content="Hello")
        
        user_msg = UserMessage(text=last_message.content)
        
        # Send message
        response_text = await chat.send_message(user_msg)
        
        # Convert response to AIMessage
        return AIMessage(content=response_text)
    
    async def _invoke_org_azure(
        self,
        messages: List[BaseMessage],
        system_message: Optional[str] = None
    ) -> AIMessage:
        """Invoke using organization's Azure OpenAI with OAuth2"""
        
        from services.org_azure_openai import create_org_azure_client
        
        logger.info("🔐 Invoking Organization Azure OpenAI")
        
        # Validate configuration
        if not self.org_azure_config:
            logger.error("❌ Organization Azure OpenAI configuration is missing")
            raise ValueError("Organization Azure OpenAI configuration is missing. Please configure it in LLM Settings.")
        
        logger.info(f"   Config keys present: {list(self.org_azure_config.keys())}")
        
        required_fields = ["base_url", "deployment", "api_version", "subscription_key", "oauth_config"]
        missing_fields = [field for field in required_fields if field not in self.org_azure_config]
        
        if missing_fields:
            logger.error(f"❌ Missing required fields: {missing_fields}")
            raise ValueError(f"Organization Azure OpenAI configuration is incomplete. Missing fields: {', '.join(missing_fields)}")
        
        # Initialize client if not already done
        if not self.org_azure_client:
            logger.info("   Creating Organization Azure OpenAI client...")
            self.org_azure_client = create_org_azure_client(self.org_azure_config)
            logger.info("   ✅ Client created")
        
        # Add system message if provided
        if system_message:
            messages = [SystemMessage(content=system_message)] + messages
        
        logger.info(f"   Sending {len(messages)} messages to Azure OpenAI")
        
        # Call organization's Azure OpenAI
        response = await self.org_azure_client.ainvoke(messages)
        
        logger.info("   ✅ Response received")
        
        return response
    
    def invoke(
        self,
        messages: List[BaseMessage],
        system_message: Optional[str] = None
    ) -> AIMessage:
        """
        Sync invoke (for compatibility)
        """
        import asyncio
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.ainvoke(messages, system_message))


def get_llm_client(config: Optional[Dict[str, Any]] = None) -> UnifiedLLMClient:
    """
    Factory function to get LLM client based on configuration
    
    Args:
        config: Configuration dict with provider, model, api_key, aws_config, org_azure_config
        
    Returns:
        UnifiedLLMClient instance
    """
    if config is None:
        config = {}
    
    provider = config.get("provider", os.getenv("DEFAULT_LLM_PROVIDER", "emergent"))
    model = config.get("model", os.getenv("DEFAULT_LLM_MODEL", "claude-3-7-sonnet-20250219"))
    api_key = config.get("api_key")
    aws_config = config.get("aws_config")
    org_azure_config = config.get("org_azure_config")
    
    return UnifiedLLMClient(
        provider=provider,
        model=model,
        api_key=api_key,
        aws_config=aws_config,
        org_azure_config=org_azure_config
    )
