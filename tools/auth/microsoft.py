"""
JARVIS Auth - Microsoft OAuth2 Authentication

Provides Microsoft OAuth2 authentication using Azure AD (Entra ID).
Uses DeviceCodeCredential for CLI-based authentication with token caching.
"""

import os
import json
from pathlib import Path
from typing import Optional, Callable

from loguru import logger

# Microsoft Graph SDK imports
try:
    from azure.identity import DeviceCodeCredential, TokenCacheObsoleteError
    from msgraph import GraphServiceClient
except ImportError:
    logger.warning("msgraph-sdk or azure-identity not installed. Install with: pip install msgraph-sdk azure-identity")
    DeviceCodeCredential = None
    GraphServiceClient = None


class MicrosoftAuth:
    """Microsoft OAuth2 authentication handler using Device Code flow.
    
    Uses Azure AD (Entra ID) for authentication with Microsoft Graph API.
    Supports token caching for persistence across sessions.
    
    Attributes:
        client_id: Azure AD application client ID
        scopes: OAuth2 scopes to request
        tenant_id: Azure AD tenant ID (default: common)
        token_cache_path: Path to store cached tokens
    """
    
    # Default scopes for Microsoft Graph API
    DEFAULT_SCOPES = [
        "User.Read",
        "Mail.Read",
        "Mail.Send",
        "Calendars.Read",
        "Calendars.ReadWrite",
        "offline_access",  # Required for refresh tokens
    ]
    
    def __init__(
        self,
        client_id: str,
        scopes: Optional[list[str]] = None,
        tenant_id: str = "common",
        token_cache_path: Optional[Path] = None,
    ):
        """Initialize Microsoft OAuth2 authentication.
        
        Args:
            client_id: Azure AD application client ID
            scopes: OAuth2 scopes (defaults to DEFAULT_SCOPES)
            tenant_id: Azure AD tenant ID (use 'common' for multi-tenant)
            token_cache_path: Path to store cached tokens
        """
        self.client_id = client_id
        self.tenant_id = tenant_id
        self.scopes = scopes or self.DEFAULT_SCOPES
        
        # Token cache path
        if token_cache_path is None:
            data_dir = Path("data")
            data_dir.mkdir(exist_ok=True)
            token_cache_path = data_dir / "microsoft_token_cache.json"
        self.token_cache_path = Path(token_cache_path)
        
        self._credential: Optional[DeviceCodeCredential] = None
        self._client: Optional[GraphServiceClient] = None
        
        logger.info(f"MicrosoftAuth initialized for client_id={client_id[:8]}...")
    
    @property
    def credential(self) -> DeviceCodeCredential:
        """Get or create the DeviceCodeCredential."""
        if self._credential is None:
            # Check for cached token
            cache = self._load_token_cache()
            
            self._credential = DeviceCodeCredential(
                client_id=self.client_id,
                tenant_id=self.tenant_id,
                token_cache=cache,
                # Device code callback for CLI authentication
                _device_code_callback=self._device_code_callback,
            )
            
            logger.debug("Created new DeviceCodeCredential")
        
        return self._credential
    
    def _device_code_callback(self, instruction: str, code: str, expires_at: str) -> None:
        """Callback for device code authentication.
        
        Prints instructions for user to complete authentication.
        
        Args:
            instruction: Instructions for the user
            code: The device code to enter
            expires_at: When the code expires
        """
        print("\n" + "=" * 60)
        print("MICROSOFT AUTHENTICATION REQUIRED")
        print("=" * 60)
        print(f"\n{instruction}")
        print(f"\nDevice code: {code}")
        print(f"Expires at: {expires_at}")
        print("\n" + "=" * 60)
        print("\nWaiting for authentication... (press Ctrl+C to cancel)")
    
    def _load_token_cache(self):
        """Load token cache from disk if it exists."""
        if not self.token_cache_path.exists():
            return None
        
        try:
            import json
            cache_data = json.loads(self.token_cache_path.read_text(encoding="utf-8"))
            logger.debug(f"Loaded token cache from {self.token_cache_path}")
            
            # Return a simple dict-based cache
            return cache_data
        except Exception as e:
            logger.warning(f"Failed to load token cache: {e}")
            return None
    
    def _save_token_cache(self, cache) -> None:
        """Save token cache to disk."""
        try:
            # Serialize cache to JSON
            if hasattr(cache, 'serialize'):
                cache_data = json.loads(cache.serialize())
            elif isinstance(cache, dict):
                cache_data = cache
            else:
                cache_data = {}
            
            self.token_cache_path.write_text(
                json.dumps(cache_data, indent=2),
                encoding="utf-8"
            )
            logger.debug(f"Saved token cache to {self.token_cache_path}")
        except Exception as e:
            logger.warning(f"Failed to save token cache: {e}")
    
    def authenticate(self, callback: Optional[Callable[[str], None]] = None) -> bool:
        """Authenticate with Microsoft using device code flow.
        
        If tokens are cached and valid, this will succeed immediately.
        Otherwise, triggers the device code flow for user authentication.
        
        Args:
            callback: Optional callback to receive status messages
            
        Returns:
            True if authentication successful
            
        Raises:
            ToolError: If authentication fails
        """
        from tools.base import ToolError
        
        try:
            if callback:
                callback("Starting Microsoft authentication...")
            
            # Try to get a token - this will trigger device code flow if needed
            token = self.credential.get_token(*self.scopes)
            
            if token:
                logger.info("Microsoft authentication successful")
                if callback:
                    callback("Authentication successful!")
                return True
            
            return False
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Microsoft authentication failed: {error_msg}")
            
            if "AADSTS" in error_msg:
                # Azure AD error codes
                if "AADSTS700016" in error_msg:
                    suggestion = "Application not found. Verify client_id in Azure Portal -> App Registrations"
                elif "AADSTS50011" in error_msg:
                    suggestion = "Redirect URI not configured. Add redirect URI in Azure Portal -> App Registrations"
                elif "AADSTS7000215" in error_msg:
                    suggestion = "Invalid client secret. Generate new client secret in Azure Portal"
                elif "AADSTS90002" in error_msg:
                    suggestion = "Tenant not found. Check tenant_id parameter"
                elif "AADSTS90015" in error_msg:
                    suggestion = "Token cache is empty or expired. Delete cached token and re-authenticate"
                elif "AADSTS700027" in error_msg:
                    suggestion = "Client assertion contains invalid signature. Check certificate/thumbprint"
                else:
                    suggestion = f"Check Azure AD application configuration. Error code: {error_msg[:50]}"
            else:
                suggestion = "Ensure Azure AD application has Microsoft Graph permissions configured"
            
            raise ToolError(
                "microsoft_auth",
                f"Authentication failed: {error_msg}",
                suggestion
            )
    
    def get_client(self) -> Optional[GraphServiceClient]:
        """Get or create the GraphServiceClient.
        
        Returns:
            GraphServiceClient for Microsoft Graph API calls
            
        Raises:
            ToolError: If client creation fails
        """
        from tools.base import ToolError
        
        if GraphServiceClient is None:
            raise ToolError(
                "microsoft_graph",
                "msgraph-sdk not installed",
                "Install with: pip install msgraph-sdk"
            )
        
        if self._client is None:
            try:
                self._client = GraphServiceClient(
                    credential=self.credential,
                    scopes=self.scopes,
                )
                logger.debug("Created new GraphServiceClient")
            except Exception as e:
                raise ToolError(
                    "microsoft_graph",
                    f"Failed to create Graph client: {str(e)}",
                    "Check Azure AD application configuration"
                )
        
        return self._client
    
    def is_authenticated(self) -> bool:
        """Check if already authenticated (cached tokens valid).
        
        Returns:
            True if valid cached tokens exist
        """
        try:
            token = self.credential.get_token(*self.scopes)
            return token is not None
        except:
            return False
    
    def logout(self) -> None:
        """Clear cached tokens and logout."""
        if self.token_cache_path.exists():
            self.token_cache_path.unlink()
            logger.info("Microsoft tokens cleared")
        
        self._credential = None
        self._client = None
    
    def get_user_info(self) -> Optional[dict]:
        """Get current user information from Microsoft Graph.
        
        Returns:
            Dict with user info or None if not authenticated
        """
        try:
            client = self.get_client()
            if client is None:
                return None
            
            # Call Microsoft Graph /me endpoint
            # Note: This is async in the SDK
            import asyncio
            
            async def get_user():
                return await client.me.get()
            
            user = asyncio.run(get_user())
            
            if user:
                return {
                    "id": user.id,
                    "display_name": user.display_name,
                    "email": user.mail or user.user_principal_name,
                }
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get user info: {e}")
            return None


__all__ = ["MicrosoftAuth"]
