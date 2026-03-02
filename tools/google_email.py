"""
Google Email Tool

Provides email operations using Gmail API with OAuth2 authentication.
Supports reading and sending emails.
"""

from base64 import urlsafe_b64encode
from pathlib import Path
from typing import Any, Callable

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from tools.base import BaseTool, ToolError
from tools.auth.token_manager import TokenManager
from tools.auth.oauth import GoogleOAuth


class GoogleEmailTool(BaseTool):
    """Google Gmail API operations.
    
    Provides:
    - list_messages: List email messages
    - get_message: Get full message content
    - send_message: Send new emails
    - get_attachment: Download email attachments
    
    Requires OAuth2 authentication with Gmail API.
    """
    
    PROVIDER = "google_gmail"  # Separate provider for Gmail-specific tokens
    SERVICE_NAME = "gmail"
    SERVICE_VERSION = "v1"
    
    def __init__(
        self, 
        client_secrets_path: str | Path | None = None,
        token_manager: TokenManager | None = None
    ):
        """Initialize Google Email tool.
        
        Args:
            client_secrets_path: Path to OAuth client secrets JSON
            token_manager: TokenManager instance (creates default if None)
        """
        super().__init__(name="google_email")
        self.client_secrets_path = client_secrets_path
        self.token_manager = token_manager or TokenManager()
        self._oauth = GoogleOAuth(client_secrets_path)
        self._service = None
    
    @property
    def service(self):
        """Lazy-load the Gmail API service."""
        if self._service is None:
            self._service = build(
                self.SERVICE_NAME, 
                self.SERVICE_VERSION,
                credentials=self.authenticate()
            )
        return self._service
    
    def authenticate(self, force_reauth: bool = False) -> Credentials:
        """Authenticate with Gmail API.
        
        Args:
            force_reauth: If True, delete existing tokens and re-authenticate
            
        Returns:
            Valid OAuth2 credentials
        """
        if force_reauth:
            self.token_manager.delete_credentials(self.PROVIDER)
            self.logger.info("Forced re-authentication")
        
        # Try to load existing valid credentials
        credentials = self.token_manager.get_valid_credentials(self.PROVIDER)
        
        if credentials is None:
            self.logger.info("No valid credentials found, initiating OAuth flow")
            credentials = self._oauth.authenticate_gmail(self.client_secrets_path)
            self.token_manager.save_credentials(self.PROVIDER, credentials)
        
        return credentials
    
    def execute(self, action: str, **kwargs) -> dict[str, Any]:
        """Execute an email action.
        
        Args:
            action: Action to perform ('list', 'get', 'send')
            **kwargs: Arguments for the action
            
        Returns:
            Action result dictionary
        """
        actions = {
            "list": self.list_messages,
            "get": self.get_message,
            "send": self.send_message,
            "attachment": self.get_attachment,
        }
        
        if action not in actions:
            raise ToolError(
                self.name,
                f"Unknown action: {action}",
                "Use 'list', 'get', 'send', or 'attachment'"
            )
        
        return actions[action](**kwargs)
    
    def list_messages(
        self,
        max_results: int = 10,
        query: str | None = None,
        label_ids: list[str] | None = None,
        callback: Callable[[dict], None] | None = None
    ) -> dict[str, Any]:
        """List email messages.
        
        Args:
            max_results: Maximum messages to return (default 10)
            query: Gmail search query (e.g., "is:unread", "from:example.com")
            label_ids: Filter by label IDs (e.g., ['INBOX', 'UNREAD'])
            callback: Optional callback for streaming results
            
        Returns:
            Dictionary with messages list and metadata
        """
        try:
            # Build request
            request = self.service.users().messages().list(
                userId="me",
                maxResults=max_results,
                q=query,
                labelIds=label_ids
            )
            
            # Execute and process results
            messages = []
            while request is not None:
                response = request.execute()
                items = response.get("messages", [])
                
                # Get full details for each message
                for item in items:
                    msg = self.service.users().messages().get(
                        userId="me",
                        id=item["id"],
                        format="metadata",
                        metadataHeaders=["From", "Subject", "Date", "Snippet"]
                    ).execute()
                    
                    message_data = self._parse_message_header(msg)
                    messages.append(message_data)
                    
                    if callback:
                        callback(message_data)
                
                request = self.service.users().messages().list_next(request, response)
            
            self.logger.info(f"Listed {len(messages)} messages")
            return {
                "success": True,
                "count": len(messages),
                "messages": messages,
            }
            
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to list messages: {e}",
                "Check your internet connection and OAuth credentials"
            ) from e
    
    def get_message(
        self,
        message_id: str,
        format: str = "full"
    ) -> dict[str, Any]:
        """Get a specific message by ID.
        
        Args:
            message_id: The message ID to retrieve
            format: Message format ('full', 'metadata', 'raw', 'minimal')
            
        Returns:
            Full message data
        """
        try:
            message = self.service.users().messages().get(
                userId="me",
                id=message_id,
                format=format
            ).execute()
            
            message_data = self._parse_message(message)
            
            self.logger.info(f"Retrieved message: {message_id}")
            return {
                "success": True,
                "message": message_data
            }
            
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to get message {message_id}: {e}",
                "Verify the message ID is correct"
            ) from e
    
    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        from_name: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None,
        thread_id: str | None = None,
        callback: Callable[[dict], None] | None = None
    ) -> dict[str, Any]:
        """Send an email message.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            from_name: Optional sender display name
            cc: Optional CC recipients
            bcc: Optional BCC recipients
            reply_to: Optional reply-to address
            thread_id: Optional thread ID to reply to
            callback: Optional callback for streaming
            
        Returns:
            Sent message data
        """
        try:
            # Build email message
            message = self._build_message(
                to=to,
                subject=subject,
                body=body,
                from_name=from_name,
                cc=cc,
                bcc=bcc,
                reply_to=reply_to
            )
            
            # Send message
            if thread_id:
                # Reply to thread
                sent = self.service.users().messages().send(
                    userId="me",
                    body=message,
                    threadId=thread_id
                ).execute()
            else:
                # New message
                sent = self.service.users().messages().send(
                    userId="me",
                    body=message
                ).execute()
            
            message_data = {
                "id": sent.get("id"),
                "thread_id": sent.get("threadId"),
                "label_ids": sent.get("labelIds", []),
            }
            
            if callback:
                callback(message_data)
            
            self.logger.info(f"Sent message: {sent.get('id')}")
            return {
                "success": True,
                "message": message_data,
                "message_id": sent.get("id"),
                "thread_id": sent.get("threadId"),
            }
            
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to send message: {e}",
                "Check the recipient address and your permissions"
            ) from e
    
    def get_attachment(self, message_id: str, attachment_id: str) -> dict[str, Any]:
        """Download an email attachment.
        
        Args:
            message_id: ID of the message containing the attachment
            attachment_id: ID of the attachment to download
            
        Returns:
            Attachment data (base64 encoded)
        """
        try:
            attachment = self.service.users().messages().attachments().get(
                userId="me",
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            # Data is already base64url encoded
            data = attachment.get("data", "")
            
            return {
                "success": True,
                "attachment_id": attachment_id,
                "size": attachment.get("size", 0),
                "data": data,  # Base64url encoded
            }
            
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to get attachment: {e}",
                "Verify the message and attachment IDs"
            ) from e
    
    def _build_message(
        self,
        to: str,
        subject: str,
        body: str,
        from_name: str | None = None,
        cc: list[str] | None = None,
        bcc: list[str] | None = None,
        reply_to: str | None = None
    ) -> dict[str, Any]:
        """Build a MIME email message.
        
        Args:
            to: Recipient
            subject: Subject
            body: Body content
            from_name: Optional sender name
            cc: CC recipients
            bcc: BCC recipients
            reply_to: Reply-to address
            
        Returns:
            Gmail API message object
        """
        import email
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["To"] = to
        msg["Subject"] = subject
        
        if from_name:
            msg["From"] = f"{from_name} <me>"
        else:
            msg["From"] = "me"
        
        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            msg["Bcc"] = ", ".join(bcc)
        if reply_to:
            msg["Reply-To"] = reply_to
        
        # Attach body
        text_part = MIMEText(body, "plain")
        msg.attach(text_part)
        
        # Encode to base64url
        raw = urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        
        return {"raw": raw}
    
    def _parse_message_header(self, message: dict) -> dict[str, Any]:
        """Parse message headers into clean dict.
        
        Args:
            message: Raw message from API
            
        Returns:
            Parsed message dictionary
        """
        headers = {}
        for header in message.get("payload", {}).get("headers", []):
            headers[header["name"].lower()] = header["value"]
        
        return {
            "id": message.get("id"),
            "thread_id": message.get("threadId"),
            "from": headers.get("from"),
            "to": headers.get("to"),
            "subject": headers.get("subject"),
            "date": headers.get("date"),
            "snippet": message.get("snippet"),
            "label_ids": message.get("labelIds", []),
        }
    
    def _parse_message(self, message: dict) -> dict[str, Any]:
        """Parse full message into clean dict.
        
        Args:
            message: Raw message from API
            
        Returns:
            Parsed message dictionary with body
        """
        # Get headers
        headers = {}
        payload = message.get("payload", {})
        for header in payload.get("headers", []):
            headers[header["name"].lower()] = header["value"]
        
        # Get body
        body = ""
        if "data" in payload.get("body", {}):
            import base64
            body = base64.urlsafe_b64decode(
                payload["body"]["data"].encode("utf-8")
            ).decode("utf-8", errors="replace")
        elif "parts" in payload:
            # Multi-part message - find text/plain
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                    import base64
                    body = base64.urlsafe_b64decode(
                        part["body"]["data"].encode("utf-8")
                    ).decode("utf-8", errors="replace")
                    break
        
        return {
            "id": message.get("id"),
            "thread_id": message.get("threadId"),
            "from": headers.get("from"),
            "to": headers.get("to"),
            "cc": headers.get("cc"),
            "bcc": headers.get("bcc"),
            "subject": headers.get("subject"),
            "date": headers.get("date"),
            "reply_to": headers.get("reply-to"),
            "body": body,
            "snippet": message.get("snippet"),
            "label_ids": message.get("labelIds", []),
            "raw": message.get("raw"),  # Raw MIME message if requested
        }


__all__ = [
    "GoogleEmailTool",
]
