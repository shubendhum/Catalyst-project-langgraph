"""
Secret Management Service
Secure storage and retrieval of API keys, credentials, and sensitive data
Supports AWS Secrets Manager, environment variables, and encrypted database storage
"""
import logging
import os
from typing import Dict, Optional, Any
from datetime import datetime, timezone
import json
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)


class SecretManagementService:
    """
    Service for managing secrets and credentials securely
    """
    
    def __init__(self, db, config: Optional[Dict] = None):
        self.db = db
        self.config = config or {}
        
        # Initialize encryption
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        
        # AWS Secrets Manager client (if configured)
        self.aws_secrets_client = None
        if self.config.get("use_aws_secrets"):
            self._init_aws_secrets()
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key"""
        # Try to get from environment
        key_str = os.getenv("ENCRYPTION_KEY")
        
        if key_str:
            return base64.urlsafe_b64decode(key_str)
        
        # Generate new key (for development only!)
        logger.warning("No ENCRYPTION_KEY found, generating new one (NOT for production!)")
        key = Fernet.generate_key()
        logger.info(f"Generated encryption key. Set in environment: ENCRYPTION_KEY={base64.urlsafe_b64encode(key).decode()}")
        return key
    
    def _init_aws_secrets(self):
        """Initialize AWS Secrets Manager client"""
        try:
            import boto3
            
            session = boto3.Session(
                aws_access_key_id=self.config.get("aws_access_key_id"),
                aws_secret_access_key=self.config.get("aws_secret_access_key"),
                region_name=self.config.get("aws_region", "us-east-1")
            )
            
            self.aws_secrets_client = session.client('secretsmanager')
            logger.info("AWS Secrets Manager initialized")
        except Exception as e:
            logger.error(f"Error initializing AWS Secrets Manager: {str(e)}")
    
    def _encrypt(self, value: str) -> str:
        """Encrypt a value"""
        return self.cipher.encrypt(value.encode()).decode()
    
    def _decrypt(self, encrypted_value: str) -> str:
        """Decrypt a value"""
        return self.cipher.decrypt(encrypted_value.encode()).decode()
    
    async def store_secret(
        self,
        key: str,
        value: str,
        description: str = "",
        tags: Optional[Dict] = None,
        use_aws: bool = False
    ) -> bool:
        """
        Store a secret
        
        Args:
            key: Secret identifier
            value: Secret value
            description: Description of the secret
            tags: Optional tags for categorization
            use_aws: If True, store in AWS Secrets Manager instead of database
        """
        try:
            if use_aws and self.aws_secrets_client:
                # Store in AWS Secrets Manager
                self.aws_secrets_client.create_secret(
                    Name=key,
                    SecretString=value,
                    Description=description,
                    Tags=[{"Key": k, "Value": v} for k, v in (tags or {}).items()]
                )
                logger.info(f"Stored secret in AWS Secrets Manager: {key}")
            else:
                # Store in encrypted database
                encrypted_value = self._encrypt(value)
                
                secret_doc = {
                    "key": key,
                    "value": encrypted_value,
                    "description": description,
                    "tags": tags or {},
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "accessed_count": 0
                }
                
                await self.db.secrets.update_one(
                    {"key": key},
                    {"$set": secret_doc},
                    upsert=True
                )
                logger.info(f"Stored secret in database: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing secret: {str(e)}")
            return False
    
    async def get_secret(self, key: str, use_aws: bool = False) -> Optional[str]:
        """
        Retrieve a secret
        
        Args:
            key: Secret identifier
            use_aws: If True, retrieve from AWS Secrets Manager
            
        Returns:
            Decrypted secret value or None
        """
        try:
            if use_aws and self.aws_secrets_client:
                # Get from AWS Secrets Manager
                response = self.aws_secrets_client.get_secret_value(SecretId=key)
                logger.debug(f"Retrieved secret from AWS: {key}")
                return response['SecretString']
            else:
                # Get from database
                secret_doc = await self.db.secrets.find_one({"key": key})
                
                if secret_doc:
                    # Update access count
                    await self.db.secrets.update_one(
                        {"key": key},
                        {
                            "$inc": {"accessed_count": 1},
                            "$set": {"last_accessed_at": datetime.now(timezone.utc).isoformat()}
                        }
                    )
                    
                    decrypted_value = self._decrypt(secret_doc["value"])
                    logger.debug(f"Retrieved secret from database: {key}")
                    return decrypted_value
            
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving secret: {str(e)}")
            return None
    
    async def delete_secret(self, key: str, use_aws: bool = False) -> bool:
        """Delete a secret"""
        try:
            if use_aws and self.aws_secrets_client:
                self.aws_secrets_client.delete_secret(
                    SecretId=key,
                    ForceDeleteWithoutRecovery=True
                )
                logger.info(f"Deleted secret from AWS: {key}")
            else:
                await self.db.secrets.delete_one({"key": key})
                logger.info(f"Deleted secret from database: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting secret: {str(e)}")
            return False
    
    async def list_secrets(self, tags: Optional[Dict] = None) -> list:
        """List all secrets (metadata only, not values)"""
        try:
            query = {}
            if tags:
                query["tags"] = {"$all": [{"$elemMatch": {"$eq": [k, v]}} for k, v in tags.items()]}
            
            secrets = await self.db.secrets.find(
                query,
                {"value": 0}  # Exclude encrypted values
            ).to_list(length=None)
            
            return secrets
            
        except Exception as e:
            logger.error(f"Error listing secrets: {str(e)}")
            return []
    
    async def rotate_secret(self, key: str, new_value: str, use_aws: bool = False) -> bool:
        """Rotate a secret (update with new value)"""
        try:
            if use_aws and self.aws_secrets_client:
                self.aws_secrets_client.update_secret(
                    SecretId=key,
                    SecretString=new_value
                )
            else:
                encrypted_value = self._encrypt(new_value)
                await self.db.secrets.update_one(
                    {"key": key},
                    {
                        "$set": {
                            "value": encrypted_value,
                            "updated_at": datetime.now(timezone.utc).isoformat()
                        },
                        "$push": {
                            "rotation_history": {
                                "rotated_at": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    }
                )
            
            logger.info(f"Rotated secret: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Error rotating secret: {str(e)}")
            return False
    
    async def get_or_create_secret(
        self,
        key: str,
        default_value: str,
        description: str = ""
    ) -> str:
        """Get secret or create with default value if not exists"""
        secret = await self.get_secret(key)
        
        if secret is None:
            await self.store_secret(key, default_value, description)
            return default_value
        
        return secret
    
    def get_from_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from environment variable"""
        return os.getenv(key, default)
    
    async def import_from_env(self, prefix: str = "SECRET_"):
        """Import secrets from environment variables"""
        count = 0
        for key, value in os.environ.items():
            if key.startswith(prefix):
                secret_key = key[len(prefix):].lower()
                await self.store_secret(secret_key, value, description=f"Imported from env: {key}")
                count += 1
        
        logger.info(f"Imported {count} secrets from environment variables")
        return count


# Global secret management service instance
_secret_service = None


def get_secret_service(db, config: Optional[Dict] = None) -> SecretManagementService:
    """Get or create secret management service singleton"""
    global _secret_service
    if _secret_service is None:
        _secret_service = SecretManagementService(db, config)
    return _secret_service
