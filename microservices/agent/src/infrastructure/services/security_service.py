"""Interface for security service."""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from abc import ABC, abstractmethod


class ISecurityService(ABC):
    """Interface for security service."""
    
    @abstractmethod
    async def generate_token(
        self,
        user_id: str,
        scopes: Optional[List[str]] = None,
        expires_in: Optional[timedelta] = None
    ) -> str:
        """
        Generate a JWT token.
        
        Args:
            user_id: ID of the user
            scopes: Optional list of token scopes
            expires_in: Optional token expiration time
            
        Returns:
            Generated JWT token
        """
        pass
    
    @abstractmethod
    async def validate_token(
        self,
        token: str
    ) -> Dict[str, Any]:
        """
        Validate a JWT token.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Decoded token payload
            
        Raises:
            InvalidTokenError: If token is invalid
            TokenExpiredError: If token has expired
        """
        pass
    
    @abstractmethod
    async def revoke_token(
        self,
        token: str
    ) -> None:
        """
        Revoke a JWT token.
        
        Args:
            token: JWT token to revoke
        """
        pass
    
    @abstractmethod
    async def hash_password(
        self,
        password: str
    ) -> str:
        """
        Hash a password.
        
        Args:
            password: Password to hash
            
        Returns:
            Hashed password
        """
        pass
    
    @abstractmethod
    async def verify_password(
        self,
        password: str,
        hashed_password: str
    ) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Password to verify
            hashed_password: Hashed password to check against
            
        Returns:
            True if password matches, False otherwise
        """
        pass
    
    @abstractmethod
    async def encrypt_data(
        self,
        data: str,
        key_id: Optional[str] = None
    ) -> str:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            key_id: Optional key ID to use
            
        Returns:
            Encrypted data
        """
        pass
    
    @abstractmethod
    async def decrypt_data(
        self,
        encrypted_data: str,
        key_id: Optional[str] = None
    ) -> str:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Data to decrypt
            key_id: Optional key ID to use
            
        Returns:
            Decrypted data
        """
        pass
    
    @abstractmethod
    async def generate_api_key(
        self,
        user_id: str,
        name: str,
        scopes: Optional[List[str]] = None,
        expires_at: Optional[datetime] = None
    ) -> str:
        """
        Generate an API key.
        
        Args:
            user_id: ID of the user
            name: Name for the API key
            scopes: Optional list of key scopes
            expires_at: Optional expiration time
            
        Returns:
            Generated API key
        """
        pass
    
    @abstractmethod
    async def validate_api_key(
        self,
        api_key: str
    ) -> Dict[str, Any]:
        """
        Validate an API key.
        
        Args:
            api_key: API key to validate
            
        Returns:
            Key metadata
            
        Raises:
            InvalidApiKeyError: If key is invalid
            ApiKeyExpiredError: If key has expired
        """
        pass
    
    @abstractmethod
    async def revoke_api_key(
        self,
        api_key: str
    ) -> None:
        """
        Revoke an API key.
        
        Args:
            api_key: API key to revoke
        """
        pass
    
    @abstractmethod
    async def check_permission(
        self,
        user_id: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if a user has permission for an action.
        
        Args:
            user_id: ID of the user
            resource: Resource to check permission for
            action: Action to check permission for
            
        Returns:
            True if user has permission, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_user_permissions(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all permissions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of user permissions
        """
        pass
    
    @abstractmethod
    async def audit_log(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an audit event.
        
        Args:
            user_id: ID of the user
            action: Action performed
            resource: Resource acted upon
            details: Optional additional details
        """
        pass 