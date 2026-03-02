"""
JARVIS Tools - Microsoft Outlook Integration

Provides Microsoft Outlook/Exchange integration via Microsoft Graph API.
Supports reading emails, sending emails, and calendar operations.
"""

import os
import json
import asyncio
from typing import Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime

from loguru import logger

from tools.base import BaseTool, ToolError
from tools.auth.microsoft import MicrosoftAuth


# Microsoft Graph API default scopes
OUTLOOK_SCOPES = [
    "User.Read",
    "Mail.Read",
    "Mail.Send",
    "Calendars.Read",
    "Calendars.ReadWrite",
    "offline_access",
]


@dataclass
class EmailMessage:
    """Represents an email message from Microsoft Outlook."""
    id: str
    subject: str
    sender: str
    to_recipients: list[str]
    cc_recipients: Optional[list[str]] = None
    body_preview: Optional[str] = None
    body_content: Optional[str] = None
    received_date_time: Optional[str] = None
    is_read: bool = False
    has_attachments: bool = False


@dataclass
class CalendarEvent:
    """Represents a calendar event from Microsoft Outlook."""
    id: str
    subject: str
    start: str
    end: str
    location: Optional[str] = None
    organizer: Optional[str] = None
    attendees: Optional[list[str]] = None
    is_online_meeting: bool = False
    online_meeting_url: Optional[str] = None


class MicrosoftOutlookTool(BaseTool):
    """Microsoft Outlook integration via Microsoft Graph API.
    
    Provides capabilities to:
    - Read emails from inbox
    - Send emails
    - List calendar events
    - Create calendar events
    
    Requires Azure AD application with Microsoft Graph API permissions.
    Set MICROSOFT_CLIENT_ID environment variable or pass client_id to constructor.
    
    Example:
        >>> tool = MicrosoftOutlookTool()
        >>> tool.authenticate()
        >>> emails = tool.list_emails(max_results=5)
        >>> for email in emails:
        ...     print(f"{email.subject} from {email.sender}")
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        callback: Optional[Callable[[str], None]] = None,
    ):
        """Initialize Microsoft Outlook tool.
        
        Args:
            client_id: Azure AD application client ID
            scopes: OAuth2 scopes (defaults to OUTLOOK_SCOPES)
            callback: Optional callback for streaming status updates
        """
        super().__init__(name="MicrosoftOutlook")
        
        # Get client_id from environment if not provided
        self.client_id = client_id or os.environ.get("MICROSOFT_CLIENT_ID")
        if not self.client_id:
            logger.warning(
                "MICROSOFT_CLIENT_ID not set. Authentication will fail. "
                "Set MICROSOFT_CLIENT_ID env var or pass client_id to constructor."
            )
        
        self.scopes = scopes or OUTLOOK_SCOPES
        self.callback = callback
        self._auth: Optional[MicrosoftAuth] = None
        
        self.logger.info("MicrosoftOutlookTool initialized")
    
    @property
    def auth(self) -> MicrosoftAuth:
        """Get or create the MicrosoftAuth instance."""
        if self._auth is None:
            if not self.client_id:
                raise ToolError(
                    "microsoft_outlook",
                    "No client_id provided",
                    "Set MICROSOFT_CLIENT_ID environment variable or pass client_id to constructor"
                )
            
            self._auth = MicrosoftAuth(
                client_id=self.client_id,
                scopes=self.scopes,
            )
        
        return self._auth
    
    def _log(self, message: str) -> None:
        """Log message and optionally send to callback."""
        self.logger.info(message)
        if self.callback:
            self.callback(message)
    
    def authenticate(self) -> bool:
        """Authenticate with Microsoft using device code flow.
        
        Returns:
            True if authentication successful
            
        Raises:
            ToolError: If authentication fails
        """
        if self.callback:
            self.callback("Starting Microsoft authentication...")
        
        result = self.auth.authenticate(callback=self.callback)
        
        if result:
            self._log("Microsoft authentication successful!")
            
            # Try to get user info
            user_info = self.auth.get_user_info()
            if user_info:
                self._log(f"Authenticated as: {user_info.get('display_name', user_info.get('email', 'Unknown'))}")
        
        return result
    
    def _parse_email(self, msg: Any) -> EmailMessage:
        """Parse Microsoft Graph email message to EmailMessage dataclass."""
        return EmailMessage(
            id=msg.id,
            subject=msg.subject or "(No subject)",
            sender=msg.sender.email_address.name if msg.sender else "Unknown",
            to_recipients=[
                r.email_address.address 
                for r in (msg.to_recipients or [])
            ],
            cc_recipients=[
                r.email_address.address 
                for r in (msg.cc_recipients or [])
            ] if msg.cc_recipients else None,
            body_preview=msg.body_preview,
            body_content=msg.body.content if msg.body else None,
            received_date_time=str(msg.received_date_time) if msg.received_date_time else None,
            is_read=msg.is_read or False,
            has_attachments=msg.has_attachments or False,
        )
    
    def _parse_event(self, event: Any) -> CalendarEvent:
        """Parse Microsoft Graph event to CalendarEvent dataclass."""
        return CalendarEvent(
            id=event.id,
            subject=event.subject or "(No subject)",
            start=str(event.start.date_time) if event.start else "",
            end=str(event.end.date_time) if event.end else "",
            location=event.location.display_name if event.location else None,
            organizer=event.organizer.email_address.name if event.organizer else None,
            attendees=[
                a.email_address.address 
                for a in (event.attendees or [])
            ] if event.attendees else None,
            is_online_meeting=event.is_online_meeting or False,
            online_meeting_url=event.online_meeting_url,
        )
    
    def list_emails(
        self,
        max_results: int = 10,
        folder: str = "inbox",
        unread_only: bool = False,
    ) -> list[EmailMessage]:
        """List emails from the specified folder.
        
        Args:
            max_results: Maximum number of emails to return
            folder: Folder name (default: "inbox")
            unread_only: Only return unread emails
            
        Returns:
            List of EmailMessage objects
            
        Raises:
            ToolError: If listing fails
        """
        self._log(f"Listing {max_results} emails from {folder}...")
        
        try:
            client = self.auth.get_client()
            
            # Build query options
            query_params = {
                "top": max_results,
                "select": "id,subject,sender,toRecipients,ccRecipients,bodyPreview,body,receivedDateTime,isRead,hasAttachments",
                "orderby": "receivedDateTime desc",
            }
            
            if unread_only:
                query_params["filter"] = "isRead eq false"
            
            # Get messages (async)
            async def get_messages():
                # For inbox, use me/messages; for other folders, use folder path
                if folder.lower() == "inbox":
                    result = await client.me.messages.get(**{"query_parameters": query_params})
                else:
                    # Try to get folder ID first
                    folders = await client.me.mail_folders.get()
                    target_folder = None
                    if folders and folders.value:
                        for f in folders.value:
                            if f.display_name.lower() == folder.lower():
                                target_folder = f
                                break
                    
                    if target_folder:
                        result = await client.me.mail_folders.by_mail_folder_id(target_folder.id).messages.get(
                            **{"query_parameters": query_params}
                        )
                    else:
                        result = await client.me.messages.get(**{"query_parameters": query_params})
                
                return result
            
            result = asyncio.run(get_messages())
            
            emails = []
            if result and result.value:
                for msg in result.value:
                    emails.append(self._parse_email(msg))
            
            self._log(f"Found {len(emails)} emails")
            return emails
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Failed to list emails: {error_msg}")
            
            if "authentication" in error_msg.lower():
                suggestion = "Run authenticate() first to authenticate with Microsoft"
            elif "permission" in error.lower() if hasattr(e, 'lower') else False:
                suggestion = "Check that the app has Mail.Read permission in Azure Portal"
            else:
                suggestion = "Verify Microsoft Graph API is accessible"
            
            raise ToolError(
                "microsoft_outlook",
                f"Failed to list emails: {error_msg}",
                suggestion
            )
    
    def get_email(self, email_id: str) -> EmailMessage:
        """Get a specific email by ID.
        
        Args:
            email_id: The Microsoft Graph message ID
            
        Returns:
            EmailMessage object with full content
            
        Raises:
            ToolError: If retrieval fails
        """
        self._log(f"Getting email {email_id}...")
        
        try:
            client = self.auth.get_client()
            
            async def get_message():
                return await client.me.messages.by_message_id(email_id).get()
            
            msg = asyncio.run(get_message())
            
            if not msg:
                raise ToolError(
                    "microsoft_outlook",
                    f"Email not found: {email_id}",
                    "Verify the email ID is correct"
                )
            
            return self._parse_email(msg)
            
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(
                "microsoft_outlook",
                f"Failed to get email: {str(e)}",
                "Verify email ID is correct"
            )
    
    def send_email(
        self,
        to: str | list[str],
        subject: str,
        body: str,
        cc: Optional[str | list[str]] = None,
        is_html: bool = False,
    ) -> dict:
        """Send an email.
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            body: Email body content
            cc: Optional CC recipient(s)
            is_html: Whether body is HTML
            
        Returns:
            Dict with success status and message ID
            
        Raises:
            ToolError: If sending fails
        """
        # Normalize recipients to list
        to_list = [to] if isinstance(to, str) else to
        cc_list = [cc] if isinstance(cc, str) else (cc or [])
        
        self._log(f"Sending email to {to_list}...")
        
        try:
            client = self.auth.get_client()
            
            # Build the message
            from msgraph.generated.models import Message, EmailAddress, Recipient
            
            # Parse recipients
            def parse_recipients(addrs: list[str]) -> list[Recipient]:
                return [
                    Recipient(
                        email_address=EmailAddress(address=addr)
                    )
                    for addr in addrs
                ]
            
            message = Message(
                subject=subject,
                body={
                    "contentType": "html" if is_html else "text",
                    "content": body,
                },
                to_recipients=parse_recipients(to_list),
                cc_recipients=parse_recipients(cc_list) if cc_list else None,
            )
            
            async def send_message():
                await client.me.send_mail.post(message)
            
            asyncio.run(send_message())
            
            self._log(f"Email sent successfully!")
            return {
                "success": True,
                "subject": subject,
                "to": to_list,
            }
            
        except Exception as e:
            raise ToolError(
                "microsoft_outlook",
                f"Failed to send email: {str(e)}",
                "Verify recipient email addresses are valid"
            )
    
    def list_calendar_events(
        self,
        max_results: int = 10,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> list[CalendarEvent]:
        """List calendar events.
        
        Args:
            max_results: Maximum number of events to return
            start_date: Start date (ISO format, e.g., "2024-01-01")
            end_date: End date (ISO format, e.g., "2024-01-31")
            
        Returns:
            List of CalendarEvent objects
            
        Raises:
            ToolError: If listing fails
        """
        self._log(f"Listing {max_results} calendar events...")
        
        try:
            client = self.auth.get_client()
            
            # Build query params
            query_params = {
                "top": max_results,
                "select": "id,subject,start,end,location,organizer,attendees,isOnlineMeeting,onlineMeetingUrl",
                "orderby": "start/dateTime",
            }
            
            # Add date filter if provided
            if start_date and end_date:
                query_params["filter"] = f"start/dateTime ge '{start_date}T00:00:00Z' and end/dateTime le '{end_date}T23:59:59Z'"
            
            async def get_events():
                return await client.me.calendar.events.get(**{"query_parameters": query_params})
            
            result = asyncio.run(get_events())
            
            events = []
            if result and result.value:
                for event in result.value:
                    events.append(self._parse_event(event))
            
            self._log(f"Found {len(events)} events")
            return events
            
        except Exception as e:
            raise ToolError(
                "microsoft_outlook",
                f"Failed to list calendar events: {str(e)}",
                "Verify Microsoft Graph API permissions for Calendars"
            )
    
    def create_calendar_event(
        self,
        subject: str,
        start: str,
        end: str,
        body: Optional[str] = None,
        location: Optional[str] = None,
        attendees: Optional[list[str]] = None,
        is_online_meeting: bool = False,
    ) -> CalendarEvent:
        """Create a calendar event.
        
        Args:
            subject: Event subject/title
            start: Start datetime (ISO format, e.g., "2024-01-15T14:00:00Z")
            end: End datetime (ISO format, e.g., "2024-01-15T15:00:00Z")
            body: Optional event body/description
            location: Optional physical location
            attendees: Optional list of attendee email addresses
            is_online_meeting: Whether to create as online meeting
            
        Returns:
            Created CalendarEvent object
            
        Raises:
            ToolError: If creation fails
        """
        self._log(f"Creating calendar event: {subject}...")
        
        try:
            client = self.auth.get_client()
            
            from msgraph.generated.models import Event, EmailAddress, Recipient, Location, DateTimeTimeZone, BodyType
            
            # Parse attendees
            def parse_attendees(addrs: list[str]) -> list[Recipient]:
                return [
                    Recipient(
                        email_address=EmailAddress(address=addr)
                    )
                    for addr in addrs
                ]
            
            # Parse datetime
            def parse_datetime(dt: str) -> DateTimeTimeZone:
                return DateTimeTimeZone(
                    date_time=dt,
                    time_zone="UTC"
                )
            # Build event
            event = Event(
                subject=subject,
                start=parse_datetime(start),
                end=parse_datetime(end),
                body=body,
                location=Location(display_name=location) if location else None,
                attendees=parse_attendees(attendees) if attendees else None,
                is_online_meeting=is_online_meeting,
            )
            
            async def create_event():
                return await client.me.calendar.events.post(event)
            
            created = asyncio.run(create_event())
            
            self._log(f"Calendar event created: {created.id}")
            return self._parse_event(created)
            
        except Exception as e:
            raise ToolError(
                "microsoft_outlook",
                f"Failed to create calendar event: {str(e)}",
                "Verify event details and permissions"
            )
    
    def execute(self, action: str, **kwargs) -> Any:
        """Execute an Outlook action.
        
        Args:
            action: Action to perform (list_emails, get_email, send_email, 
                   list_events, create_event)
            **kwargs: Arguments for the action
            
        Returns:
            Result of the action
        """
        actions = {
            "list_emails": lambda: self.list_emails(
                max_results=kwargs.get("max_results", 10),
                folder=kwargs.get("folder", "inbox"),
                unread_only=kwargs.get("unread_only", False),
            ),
            "get_email": lambda: self.get_email(kwargs["email_id"]),
            "send_email": lambda: self.send_email(
                to=kwargs["to"],
                subject=kwargs["subject"],
                body=kwargs["body"],
                cc=kwargs.get("cc"),
                is_html=kwargs.get("is_html", False),
            ),
            "list_events": lambda: self.list_calendar_events(
                max_results=kwargs.get("max_results", 10),
                start_date=kwargs.get("start_date"),
                end_date=kwargs.get("end_date"),
            ),
            "create_event": lambda: self.create_calendar_event(
                subject=kwargs["subject"],
                start=kwargs["start"],
                end=kwargs["end"],
                body=kwargs.get("body"),
                location=kwargs.get("location"),
                attendees=kwargs.get("attendees"),
                is_online_meeting=kwargs.get("is_online_meeting", False),
            ),
            "authenticate": lambda: self.authenticate(),
        }
        
        if action not in actions:
            raise ToolError(
                "microsoft_outlook",
                f"Unknown action: {action}",
                f"Valid actions: {', '.join(actions.keys())}"
            )
        
        return actions[action]()


__all__ = ["MicrosoftOutlookTool", "EmailMessage", "CalendarEvent"]
