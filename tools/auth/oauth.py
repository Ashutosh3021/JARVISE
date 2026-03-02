"""
Google OAuth2 Helper

Provides CLI-based OAuth2 flow for Google APIs.
Prints authorization URL, prompts for code, returns credentials.
"""

from pathlib import Path
from typing import Sequence

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

from loguru import logger


class GoogleOAuth:
    """Google OAuth2 authentication helper.
    
    Implements CLI-based OAuth2 flow:
    1. Prints authorization URL
    2. Prompts user to visit and enter code
    3. Returns credentials with refresh token support
    
    Uses access_type='offline' to get refresh tokens for automatic renewal.
    """
    
    # Default scopes for Google APIs
    CALENDAR_SCOPES = [
        "https://www.googleapis.com/auth/calendar.events",
        "https://www.googleapis.com/auth/calendar.readonly",
    ]
    
    GMAIL_SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.send",
    ]
    
    def __init__(self, client_secrets_path: str | Path | None = None):
        """Initialize GoogleOAuth helper.
        
        Args:
            client_secrets_path: Path to OAuth client secrets JSON file.
                                Can also be set via GOOGLE_CLIENT_SECRETS env var.
        """
        self.client_secrets_path = client_secrets_path
        self.logger = logger.bind(component="GoogleOAuth")
    
    def _get_client_secrets_path(self) -> Path:
        """Resolve client secrets path from args or environment.
        
        Returns:
            Path to client secrets file
            
        Raises:
            FileNotFoundError: If no client secrets file found
        """
        # Check explicit path first
        if self.client_secrets_path:
            path = Path(self.client_secrets_path)
            if path.exists():
                return path
        
        # Check environment variable
        import os
        env_path = os.environ.get("GOOGLE_CLIENT_SECRETS")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
        
        # Check common locations
        common_locations = [
            Path("data/google_client_secrets.json"),
            Path.home() / ".config" / "jarvis" / "google_client_secrets.json",
            Path("google_client_secrets.json"),
        ]
        
        for path in common_locations:
            if path.exists():
                return path
        
        raise FileNotFoundError(
            "Google OAuth client secrets not found. "
            "Please provide GOOGLE_CLIENT_SECRETS or place client secrets JSON at:\n"
            "- data/google_client_secrets.json\n"
            "- ~/.config/jarvis/google_client_secrets.json\n"
            "- google_client_secrets.json\n\n"
            "Get credentials from: https://console.cloud.google.com/apis/credentials"
        )
    
    def authenticate(
        self, 
        scopes: Sequence[str] | None = None,
        client_secrets_path: str | Path | None = None
    ) -> Credentials:
        """Authenticate using OAuth2 flow.
        
        Prints authorization URL, prompts for code, returns credentials.
        Uses access_type='offline' to get refresh tokens.
        
        Args:
            scopes: List of OAuth scopes to request
            client_secrets_path: Optional path to client secrets (overrides default)
            
        Returns:
            OAuth2 Credentials with refresh token
            
        Raises:
            FileNotFoundError: If client secrets not found
            Exception: If OAuth flow fails
        """
        # Resolve scopes
        if scopes is None:
            scopes = self.CALENDAR_SCOPES
        
        # Resolve client secrets path
        secrets_path = client_secrets_path or self._get_client_secrets_path()
        
        self.logger.info(f"Starting OAuth2 flow with scopes: {scopes}")
        
        # Create flow
        flow = InstalledAppFlow.from_client_secrets_file(
            str(secrets_path),
            scopes=scopes
        )
        
        # Use local server for token exchange (CLI mode)
        # This will prompt user to visit URL and enter code
        self.logger.info("Authorization URL generated. Opening in browser...")
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent'  # Force consent to get refresh token
        )
        
        print("\n" + "=" * 60)
        print("Google OAuth2 Authentication Required")
        print("=" * 60)
        print(f"\nPlease visit this URL in your browser:\n")
        print(f"  {auth_url}")
        print("\n" + "=" * 60)
        
        # Get authorization code from user
        code = input("\nEnter the authorization code: ").strip()
        
        if not code:
            raise ValueError("Authorization code cannot be empty")
        
        # Fetch token
        try:
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            self.logger.info("OAuth2 authentication successful")
            print("\nAuthentication successful! Credentials obtained.")
            
            return credentials
            
        except Exception as e:
            self.logger.error(f"OAuth2 flow failed: {e}")
            raise
    
    def authenticate_calendar(self, client_secrets_path: str | Path | None = None) -> Credentials:
        """Authenticate with Calendar API scopes.
        
        Args:
            client_secrets_path: Optional path to client secrets
            
        Returns:
            OAuth2 Credentials
        """
        return self.authenticate(self.CALENDAR_SCOPES, client_secrets_path)
    
    def authenticate_gmail(self, client_secrets_path: str | Path | None = None) -> Credentials:
        """Authenticate with Gmail API scopes.
        
        Args:
            client_secrets_path: Optional path to client secrets
            
        Returns:
            OAuth2 Credentials
        """
        return self.authenticate(self.GMAIL_SCOPES, client_secrets_path)
    
    @staticmethod
    def get_scopes_for_service(service: str) -> list[str]:
        """Get default scopes for a service.
        
        Args:
            service: Service name ('calendar' or 'gmail')
            
        Returns:
            List of OAuth scopes
        """
        if service.lower() == "calendar":
            return GoogleOAuth.CALENDAR_SCOPES
        elif service.lower() == "gmail":
            return GoogleOAuth.GMAIL_SCOPES
        else:
            raise ValueError(f"Unknown service: {service}. Use 'calendar' or 'gmail'")


__all__ = [
    "GoogleOAuth",
]
