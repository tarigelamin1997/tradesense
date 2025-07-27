"""
Enhanced Secrets Management System for TradeSense
Supports multiple providers and encryption at rest
"""
import os
import json
import base64
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
# Cloud provider imports - commented out for local development
# import boto3
# from azure.keyvault.secrets import SecretClient
# from azure.identity import DefaultAzureCredential
# from google.cloud import secretmanager
# import hvac  # HashiCorp Vault client

from core.config import settings
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


class SecretProvider:
    """Supported secret providers"""
    LOCAL = "local"  # Development only
    ENV = "env"  # Environment variables
    AWS_SECRETS_MANAGER = "aws_secrets_manager"
    AZURE_KEY_VAULT = "azure_key_vault"
    GOOGLE_SECRET_MANAGER = "google_secret_manager"
    HASHICORP_VAULT = "hashicorp_vault"
    DATABASE = "database"  # Encrypted in database


class SecretType:
    """Types of secrets"""
    API_KEY = "api_key"
    DATABASE_CREDENTIAL = "database_credential"
    ENCRYPTION_KEY = "encryption_key"
    OAUTH_SECRET = "oauth_secret"
    WEBHOOK_SECRET = "webhook_secret"
    CERTIFICATE = "certificate"
    PRIVATE_KEY = "private_key"


class SecretsManager:
    """
    Centralized secrets management with support for multiple providers
    and encryption at rest
    """
    
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("SECRETS_PROVIDER", SecretProvider.ENV)
        self._encryption_key = self._get_master_key()
        self._fernet = Fernet(self._encryption_key)
        self._cache = {}  # In-memory cache with TTL
        self._cache_ttl = timedelta(minutes=5)
        
        # Initialize provider clients
        self._init_providers()
    
    def _get_master_key(self) -> bytes:
        """Get or generate master encryption key"""
        master_key = os.getenv("MASTER_ENCRYPTION_KEY")
        
        if not master_key:
            # Generate key from SECRET_KEY using PBKDF2
            secret_key = settings.SECRET_KEY.encode()
            salt = b'tradesense-secrets-v1'  # Static salt for deterministic key
            
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000  # OWASP recommended
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret_key))
            return key
        
        return master_key.encode()
    
    def _init_providers(self):
        """Initialize provider-specific clients"""
        self._aws_client = None
        self._azure_client = None
        self._gcp_client = None
        self._vault_client = None
        
        if self.provider == SecretProvider.AWS_SECRETS_MANAGER:
            self._aws_client = boto3.client(
                'secretsmanager',
                region_name=os.getenv('AWS_REGION', 'us-east-1')
            )
        
        elif self.provider == SecretProvider.AZURE_KEY_VAULT:
            vault_url = os.getenv('AZURE_KEY_VAULT_URL')
            if vault_url:
                credential = DefaultAzureCredential()
                self._azure_client = SecretClient(
                    vault_url=vault_url,
                    credential=credential
                )
        
        elif self.provider == SecretProvider.GOOGLE_SECRET_MANAGER:
            project_id = os.getenv('GCP_PROJECT_ID')
            if project_id:
                self._gcp_client = secretmanager.SecretManagerServiceClient()
                self._gcp_project = project_id
        
        elif self.provider == SecretProvider.HASHICORP_VAULT:
            vault_url = os.getenv('VAULT_URL', 'http://localhost:8200')
            vault_token = os.getenv('VAULT_TOKEN')
            if vault_token:
                self._vault_client = hvac.Client(
                    url=vault_url,
                    token=vault_token
                )
    
    def get_secret(
        self, 
        secret_name: str, 
        secret_type: Optional[str] = None,
        version: Optional[str] = None,
        default: Optional[str] = None
    ) -> Optional[str]:
        """
        Get a secret value by name
        
        Args:
            secret_name: Name/key of the secret
            secret_type: Type of secret (for validation)
            version: Specific version (if supported by provider)
            default: Default value if secret not found
            
        Returns:
            Secret value or default
        """
        # Check cache first
        cache_key = f"{secret_name}:{version or 'latest'}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if cached['expires'] > datetime.utcnow():
                return cached['value']
        
        try:
            value = None
            
            if self.provider == SecretProvider.ENV:
                value = os.getenv(secret_name, default)
            
            elif self.provider == SecretProvider.LOCAL:
                value = self._get_local_secret(secret_name, default)
            
            elif self.provider == SecretProvider.AWS_SECRETS_MANAGER:
                value = self._get_aws_secret(secret_name, version)
            
            elif self.provider == SecretProvider.AZURE_KEY_VAULT:
                value = self._get_azure_secret(secret_name, version)
            
            elif self.provider == SecretProvider.GOOGLE_SECRET_MANAGER:
                value = self._get_gcp_secret(secret_name, version)
            
            elif self.provider == SecretProvider.HASHICORP_VAULT:
                value = self._get_vault_secret(secret_name, version)
            
            elif self.provider == SecretProvider.DATABASE:
                value = self._get_database_secret(secret_name)
            
            # Cache the result
            if value is not None:
                self._cache[cache_key] = {
                    'value': value,
                    'expires': datetime.utcnow() + self._cache_ttl
                }
            
            return value or default
            
        except Exception as e:
            logger.error(f"Error retrieving secret {secret_name}: {str(e)}")
            return default
    
    def set_secret(
        self,
        secret_name: str,
        secret_value: str,
        secret_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Set or update a secret
        
        Args:
            secret_name: Name/key of the secret
            secret_value: Secret value to store
            secret_type: Type of secret
            metadata: Additional metadata
            db: Database session (for database provider)
            
        Returns:
            Success status
        """
        try:
            # Validate secret type if provided
            if secret_type:
                self._validate_secret_type(secret_type, secret_value)
            
            if self.provider == SecretProvider.LOCAL:
                return self._set_local_secret(secret_name, secret_value)
            
            elif self.provider == SecretProvider.AWS_SECRETS_MANAGER:
                return self._set_aws_secret(secret_name, secret_value, metadata)
            
            elif self.provider == SecretProvider.AZURE_KEY_VAULT:
                return self._set_azure_secret(secret_name, secret_value, metadata)
            
            elif self.provider == SecretProvider.GOOGLE_SECRET_MANAGER:
                return self._set_gcp_secret(secret_name, secret_value, metadata)
            
            elif self.provider == SecretProvider.HASHICORP_VAULT:
                return self._set_vault_secret(secret_name, secret_value, metadata)
            
            elif self.provider == SecretProvider.DATABASE:
                return self._set_database_secret(secret_name, secret_value, secret_type, metadata, db)
            
            else:
                logger.warning(f"Cannot set secret for provider {self.provider}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting secret {secret_name}: {str(e)}")
            return False
    
    def delete_secret(self, secret_name: str, db: Optional[Session] = None) -> bool:
        """Delete a secret"""
        try:
            # Clear from cache
            cache_keys = [k for k in self._cache.keys() if k.startswith(f"{secret_name}:")]
            for key in cache_keys:
                del self._cache[key]
            
            if self.provider == SecretProvider.LOCAL:
                return self._delete_local_secret(secret_name)
            
            elif self.provider == SecretProvider.DATABASE:
                return self._delete_database_secret(secret_name, db)
            
            # Other providers would implement delete methods
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting secret {secret_name}: {str(e)}")
            return False
    
    def list_secrets(self, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all secrets (metadata only, not values)"""
        try:
            if self.provider == SecretProvider.DATABASE:
                return self._list_database_secrets(prefix)
            
            # Other providers would implement list methods
            
            return []
            
        except Exception as e:
            logger.error(f"Error listing secrets: {str(e)}")
            return []
    
    def rotate_secret(
        self,
        secret_name: str,
        rotation_lambda: Optional[callable] = None,
        db: Optional[Session] = None
    ) -> bool:
        """
        Rotate a secret
        
        Args:
            secret_name: Name of secret to rotate
            rotation_lambda: Custom rotation function
            db: Database session
            
        Returns:
            Success status
        """
        try:
            # Get current secret
            current_value = self.get_secret(secret_name)
            if not current_value:
                logger.error(f"Secret {secret_name} not found for rotation")
                return False
            
            # Generate new value
            if rotation_lambda:
                new_value = rotation_lambda(current_value)
            else:
                # Default rotation for different types
                import secrets as py_secrets
                if "key" in secret_name.lower():
                    new_value = py_secrets.token_urlsafe(32)
                elif "password" in secret_name.lower():
                    new_value = py_secrets.token_urlsafe(16)
                else:
                    new_value = py_secrets.token_hex(32)
            
            # Store new value
            success = self.set_secret(
                secret_name,
                new_value,
                metadata={"rotated_at": datetime.utcnow().isoformat()}
            )
            
            if success:
                logger.info(f"Successfully rotated secret {secret_name}")
                
                # Audit log
                if db:
                    db.execute(
                        text("""
                            INSERT INTO secret_rotation_log 
                            (secret_name, rotated_at, rotated_by)
                            VALUES (:name, NOW(), :user)
                        """),
                        {
                            "name": secret_name,
                            "user": "system"
                        }
                    )
                    db.commit()
            
            return success
            
        except Exception as e:
            logger.error(f"Error rotating secret {secret_name}: {str(e)}")
            return False
    
    # Provider-specific methods
    
    def _get_local_secret(self, name: str, default: str) -> Optional[str]:
        """Get secret from local file (dev only)"""
        secrets_file = "secrets.json"
        if os.path.exists(secrets_file):
            with open(secrets_file, 'r') as f:
                secrets = json.load(f)
                encrypted = secrets.get(name)
                if encrypted:
                    return self._fernet.decrypt(encrypted.encode()).decode()
        return default
    
    def _set_local_secret(self, name: str, value: str) -> bool:
        """Set secret in local file (dev only)"""
        secrets_file = "secrets.json"
        secrets = {}
        
        if os.path.exists(secrets_file):
            with open(secrets_file, 'r') as f:
                secrets = json.load(f)
        
        # Encrypt value
        encrypted = self._fernet.encrypt(value.encode()).decode()
        secrets[name] = encrypted
        
        with open(secrets_file, 'w') as f:
            json.dump(secrets, f, indent=2)
        
        return True
    
    def _delete_local_secret(self, name: str) -> bool:
        """Delete secret from local file"""
        secrets_file = "secrets.json"
        if os.path.exists(secrets_file):
            with open(secrets_file, 'r') as f:
                secrets = json.load(f)
            
            if name in secrets:
                del secrets[name]
                
                with open(secrets_file, 'w') as f:
                    json.dump(secrets, f, indent=2)
        
        return True
    
    def _get_aws_secret(self, name: str, version: Optional[str]) -> Optional[str]:
        """Get secret from AWS Secrets Manager"""
        if not self._aws_client:
            return None
        
        try:
            kwargs = {'SecretId': name}
            if version:
                kwargs['VersionId'] = version
            
            response = self._aws_client.get_secret_value(**kwargs)
            
            if 'SecretString' in response:
                return response['SecretString']
            else:
                # Binary secret
                return base64.b64decode(response['SecretBinary']).decode()
                
        except self._aws_client.exceptions.ResourceNotFoundException:
            return None
    
    def _set_aws_secret(self, name: str, value: str, metadata: Dict) -> bool:
        """Set secret in AWS Secrets Manager"""
        if not self._aws_client:
            return False
        
        try:
            # Try to update existing secret
            try:
                self._aws_client.update_secret(
                    SecretId=name,
                    SecretString=value
                )
            except self._aws_client.exceptions.ResourceNotFoundException:
                # Create new secret
                self._aws_client.create_secret(
                    Name=name,
                    SecretString=value,
                    Tags=[
                        {'Key': k, 'Value': str(v)}
                        for k, v in (metadata or {}).items()
                    ]
                )
            
            return True
            
        except Exception as e:
            logger.error(f"AWS Secrets Manager error: {str(e)}")
            return False
    
    def _get_azure_secret(self, name: str, version: Optional[str]) -> Optional[str]:
        """Get secret from Azure Key Vault"""
        if not self._azure_client:
            return None
        
        try:
            secret = self._azure_client.get_secret(name, version=version)
            return secret.value
        except:
            return None
    
    def _set_azure_secret(self, name: str, value: str, metadata: Dict) -> bool:
        """Set secret in Azure Key Vault"""
        if not self._azure_client:
            return False
        
        try:
            self._azure_client.set_secret(
                name,
                value,
                tags=metadata
            )
            return True
        except Exception as e:
            logger.error(f"Azure Key Vault error: {str(e)}")
            return False
    
    def _get_gcp_secret(self, name: str, version: Optional[str]) -> Optional[str]:
        """Get secret from Google Secret Manager"""
        if not self._gcp_client:
            return None
        
        try:
            # Build the secret version name
            if not version:
                version = "latest"
            
            secret_version = f"projects/{self._gcp_project}/secrets/{name}/versions/{version}"
            
            # Access the secret
            response = self._gcp_client.access_secret_version(
                request={"name": secret_version}
            )
            
            return response.payload.data.decode("UTF-8")
            
        except Exception:
            return None
    
    def _set_gcp_secret(self, name: str, value: str, metadata: Dict) -> bool:
        """Set secret in Google Secret Manager"""
        if not self._gcp_client:
            return False
        
        try:
            parent = f"projects/{self._gcp_project}"
            
            # Try to create the secret
            try:
                secret = self._gcp_client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": name,
                        "secret": {
                            "replication": {
                                "automatic": {}
                            }
                        }
                    }
                )
            except:
                # Secret might already exist
                pass
            
            # Add the secret version
            parent = f"projects/{self._gcp_project}/secrets/{name}"
            
            self._gcp_client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {
                        "data": value.encode("UTF-8")
                    }
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Google Secret Manager error: {str(e)}")
            return False
    
    def _get_vault_secret(self, name: str, version: Optional[str]) -> Optional[str]:
        """Get secret from HashiCorp Vault"""
        if not self._vault_client:
            return None
        
        try:
            path = f"secret/data/{name}"
            if version:
                path += f"?version={version}"
            
            response = self._vault_client.read(path)
            if response and 'data' in response:
                return response['data'].get('data', {}).get('value')
                
            return None
            
        except Exception:
            return None
    
    def _set_vault_secret(self, name: str, value: str, metadata: Dict) -> bool:
        """Set secret in HashiCorp Vault"""
        if not self._vault_client:
            return False
        
        try:
            path = f"secret/data/{name}"
            
            self._vault_client.write(
                path,
                data={
                    "value": value,
                    "metadata": metadata or {}
                }
            )
            
            return True
            
        except Exception as e:
            logger.error(f"HashiCorp Vault error: {str(e)}")
            return False
    
    def _get_database_secret(self, name: str) -> Optional[str]:
        """Get secret from database (requires separate DB connection)"""
        # This would need a separate DB connection to avoid circular dependency
        # For now, return None
        return None
    
    def _set_database_secret(
        self,
        name: str,
        value: str,
        secret_type: str,
        metadata: Dict,
        db: Session
    ) -> bool:
        """Set secret in database"""
        if not db:
            logger.error("Database session required for database provider")
            return False
        
        try:
            # Encrypt value
            encrypted_value = self._fernet.encrypt(value.encode()).decode()
            
            # Store in database
            db.execute(
                text("""
                    INSERT INTO application_secrets 
                    (name, encrypted_value, secret_type, metadata, created_at, updated_at)
                    VALUES (:name, :value, :type, :metadata, NOW(), NOW())
                    ON CONFLICT (name) DO UPDATE SET
                        encrypted_value = :value,
                        secret_type = :type,
                        metadata = :metadata,
                        updated_at = NOW(),
                        version = application_secrets.version + 1
                """),
                {
                    "name": name,
                    "value": encrypted_value,
                    "type": secret_type or SecretType.API_KEY,
                    "metadata": json.dumps(metadata or {})
                }
            )
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Database secret error: {str(e)}")
            db.rollback()
            return False
    
    def _delete_database_secret(self, name: str, db: Session) -> bool:
        """Delete secret from database"""
        if not db:
            return False
        
        try:
            db.execute(
                text("DELETE FROM application_secrets WHERE name = :name"),
                {"name": name}
            )
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Database secret deletion error: {str(e)}")
            db.rollback()
            return False
    
    def _list_database_secrets(self, prefix: Optional[str]) -> List[Dict[str, Any]]:
        """List secrets from database"""
        # Would need separate DB connection
        return []
    
    def _validate_secret_type(self, secret_type: str, value: str):
        """Validate secret based on type"""
        if secret_type == SecretType.API_KEY:
            if len(value) < 16:
                raise ValueError("API key too short")
        
        elif secret_type == SecretType.DATABASE_CREDENTIAL:
            # Could validate connection string format
            pass
        
        elif secret_type == SecretType.PRIVATE_KEY:
            if not value.startswith("-----BEGIN"):
                raise ValueError("Invalid private key format")


# Create singleton instance
secrets_manager = SecretsManager()