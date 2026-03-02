"""
Token Manager - Encrypted Token Storage

Provides secure storage for OAuth2 tokens using Fernet encryption.
Handles automatic token refresh when tokens expire.
"""

import json
import os
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest

from loguru import logger


class TokenManager:
    """Manages encrypted OAuth2 token storage with automatic refresh.
    
    Uses cryptography.Fernet for symmetric encryption of stored tokens.
    Tokens are saved encrypted in the data/ directory and automatically
    refreshed when they expire.
    
    Attributes:
        token_dir: Directory where encrypted tokens are stored
        cipher: Fernet cipher for encryption/decryption
    """
    
    def __init__(self, token_dir: Path | str | None = None, encryption_key: bytes | None = None):
        """Initialize the TokenManager.
        
        Args:
            token_dir: Directory for storing encrypted tokens. 
                      Defaults to data/tokens in project root.
            encryption_key: Fernet encryption key. If None, generates a new key
                          and stores it in token_dir/.key
        """
        if token_dir is None:
            # Default to data/tokens in project root
            project_root = Path(__file__).parent.parent.parent
            token_dir = project_root / "data" / "tokens"
        
        self.token_dir = Path(token_dir)
        self.token_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup encryption key
        if encryption_key is None:
            key_file = self.token_dir / ".key"
            if key_file.exists():
                self.encryption_key = key_file.read_bytes()
            else:
                self.encryption_key = Fernet.generate_key()
                key_file.write_bytes(self.encryption_key)
                logger.info(f"Generated new encryption key at {key_file}")
        else:
            self.encryption_key = encryption_key
        
        self.cipher = Fernet(self.encryption_key)
        self.logger = logger.bind(component="TokenManager")
    
    def save_credentials(self, provider: str, credentials: Credentials) -> None:
        """Save credentials to encrypted storage.
        
        Args:
            provider: Provider name (e.g., 'google', 'microsoft')
            credentials: OAuth2 credentials to encrypt and save
        """
        # Convert credentials to dict
        token_data = credentials_to_dict(credentials)
        
        # Encrypt and save
        encrypted = self.cipher.encrypt(json.dumps(token_data).encode())
        token_file = self.token_dir / f"{provider}_token.enc"
        token_file.write_bytes(encrypted)
        
        self.logger.info(f"Saved encrypted credentials for provider: {provider}")
    
    def load_credentials(self, provider: str) -> Credentials | None:
        """Load credentials from encrypted storage.
        
        Args:
            provider: Provider name (e.g., 'google', 'microsoft')
            
        Returns:
            Credentials object if found and valid, None otherwise
        """
        token_file = self.token_dir / f"{provider}_token.enc"
        
        if not token_file.exists():
            self.logger.debug(f"No token file found for provider: {provider}")
            return None
        
        try:
            encrypted = token_file.read_bytes()
            token_data = json.loads(self.cipher.decrypt(encrypted).decode())
            credentials = Credentials.from_authorized_user_info(token_data)
            self.logger.info(f"Loaded credentials for provider: {provider}")
            return credentials
        except Exception as e:
            self.logger.error(f"Failed to load credentials for {provider}: {e}")
            return None
    
    def refresh_if_needed(self, credentials: Credentials) -> Credentials:
        """Refresh credentials if they are expired.
        
        Uses the refresh token to obtain new access tokens automatically.
        
        Args:
            credentials: The credentials to refresh if needed
            
        Returns:
            Refreshed credentials (or original if not expired or no refresh token)
        """
        if not credentials or not credentials.refresh_token:
            return credentials
        
        if credentials.expired:
            self.logger.info("Credentials expired, refreshing...")
            try:
                request = GoogleRequest()
                credentials.refresh(request)
                self.logger.info("Credentials refreshed successfully")
            except Exception as e:
                self.logger.error(f"Failed to refresh credentials: {e}")
                raise
        
        return credentials
    
    def get_valid_credentials(self, provider: str) -> Credentials | None:
        """Get valid credentials, refreshing if needed.
        
        This is the main entry point - loads credentials, checks if expired,
        refreshes if needed, and returns valid credentials.
        
        Args:
            provider: Provider name
            
        Returns:
            Valid Credentials object, or None if no credentials exist
        """
        credentials = self.load_credentials(provider)
        
        if credentials is None:
            return None
        
        return self.refresh_if_needed(credentials)
    
    def delete_credentials(self, provider: str) -> bool:
        """Delete stored credentials for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if deleted, False if file didn't exist
        """
        token_file = self.token_dir / f"{provider}_token.enc"
        
        if token_file.exists():
            token_file.unlink()
            self.logger.info(f"Deleted credentials for provider: {provider}")
            return True
        
        return False
    
    def has_credentials(self, provider: str) -> bool:
        """Check if credentials exist for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            True if credentials exist
        """
        token_file = self.token_dir / f"{provider}_token.enc"
        return token_file.exists()


def credentials_to_dict(credentials: Credentials) -> dict[str, Any]:
    """Convert Credentials object to dictionary for storage.
    
    Args:
        credentials: OAuth2 credentials
        
    Returns:
        Dictionary with token data
    """
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else [],
    }


__all__ = [
    "TokenManager",
    "credentials_to_dict",
]
