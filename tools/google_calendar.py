"""
Google Calendar Tool

Provides CRUD operations for Google Calendar events using OAuth2 authentication.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from tools.base import BaseTool, ToolError
from tools.auth.token_manager import TokenManager
from tools.auth.oauth import GoogleOAuth


class GoogleCalendarTool(BaseTool):
    """Google Calendar CRUD operations.
    
    Provides:
    - list_events: List upcoming calendar events
    - create_event: Create new calendar events
    - update_event: Modify existing events
    - delete_event: Remove events
    
    Requires OAuth2 authentication with Google Calendar API.
    """
    
    PROVIDER = "google"
    SERVICE_NAME = "calendar"
    SERVICE_VERSION = "v3"
    
    def __init__(
        self, 
        client_secrets_path: str | Path | None = None,
        token_manager: TokenManager | None = None
    ):
        """Initialize Google Calendar tool.
        
        Args:
            client_secrets_path: Path to OAuth client secrets JSON
            token_manager: TokenManager instance (creates default if None)
        """
        super().__init__(name="google_calendar")
        self.client_secrets_path = client_secrets_path
        self.token_manager = token_manager or TokenManager()
        self._oauth = GoogleOAuth(client_secrets_path)
        self._service = None
    
    @property
    def service(self):
        """Lazy-load the Calendar API service."""
        if self._service is None:
            self._service = build(
                self.SERVICE_NAME, 
                self.SERVICE_VERSION,
                credentials=self.authenticate()
            )
        return self._service
    
    def authenticate(self, force_reauth: bool = False) -> Credentials:
        """Authenticate with Google Calendar API.
        
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
            credentials = self._oauth.authenticate_calendar(self.client_secrets_path)
            self.token_manager.save_credentials(self.PROVIDER, credentials)
        
        return credentials
    
    def execute(self, action: str, **kwargs) -> dict[str, Any]:
        """Execute a calendar action.
        
        Args:
            action: Action to perform ('list', 'create', 'update', 'delete')
            **kwargs: Arguments for the action
            
        Returns:
            Action result dictionary
        """
        actions = {
            "list": self.list_events,
            "create": self.create_event,
            "update": self.update_event,
            "delete": self.delete_event,
            "get": self.get_event,
        }
        
        if action not in actions:
            raise ToolError(
                self.name,
                f"Unknown action: {action}",
                "Use 'list', 'create', 'update', 'delete', or 'get'"
            )
        
        return actions[action](**kwargs)
    
    def list_events(
        self, 
        max_results: int = 10,
        time_min: datetime | str | None = None,
        time_max: datetime | str | None = None,
        query: str | None = None,
        callback: Callable[[dict], None] | None = None
    ) -> dict[str, Any]:
        """List calendar events.
        
        Args:
            max_results: Maximum number of events to return (default 10)
            time_min: Start time for events (default: now)
            time_max: End time for events
            query: Search query for event summary/description
            callback: Optional callback for streaming results
            
        Returns:
            Dictionary with events list and metadata
        """
        try:
            # Prepare time bounds
            if time_min is None:
                time_min = datetime.utcnow()
            
            if isinstance(time_min, datetime):
                time_min = time_min.isoformat() + "Z"
            if isinstance(time_max, datetime):
                time_max = time_max.isoformat() + "Z"
            
            # Build request
            request = self.service.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
                q=query
            )
            
            # Execute and process results
            events = []
            while request is not None:
                response = request.execute()
                items = response.get("items", [])
                
                for item in items:
                    event_data = self._parse_event(item)
                    events.append(event_data)
                    
                    if callback:
                        callback(event_data)
                
                request = self.service.events().list_next(request, response)
            
            self.logger.info(f"Listed {len(events)} events")
            return {
                "success": True,
                "count": len(events),
                "events": events,
            }
            
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to list events: {e}",
                "Check your internet connection and OAuth credentials"
            ) from e
    
    def get_event(self, event_id: str) -> dict[str, Any]:
        """Get a specific event by ID.
        
        Args:
            event_id: The event ID to retrieve
            
        Returns:
            Event data dictionary
        """
        try:
            event = self.service.events().get(
                calendarId="primary",
                eventId=event_id
            ).execute()
            
            return {
                "success": True,
                "event": self._parse_event(event)
            }
            
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to get event {event_id}: {e}",
                "Verify the event ID is correct"
            ) from e
    
    def create_event(
        self,
        title: str,
        start_time: datetime | str,
        end_time: datetime | str,
        description: str | None = None,
        location: str | None = None,
        attendees: list[str] | None = None,
        callback: Callable[[dict], None] | None = None
    ) -> dict[str, Any]:
        """Create a new calendar event.
        
        Args:
            title: Event title/summary
            start_time: Start time (ISO format or datetime)
            end_time: End time (ISO format or datetime)
            description: Optional event description
            location: Optional event location
            attendees: Optional list of attendee email addresses
            callback: Optional callback for streaming
            
        Returns:
            Created event data
        """
        try:
            # Convert times to RFC3339 format
            if isinstance(start_time, datetime):
                start_time = start_time.isoformat() + "Z"
            if isinstance(end_time, datetime):
                end_time = end_time.isoformat() + "Z"
            
            # Build event body
            event = {
                "summary": title,
                "start": {"dateTime": start_time, "timeZone": "UTC"},
                "end": {"dateTime": end_time, "timeZone": "UTC"},
            }
            
            if description:
                event["description"] = description
            if location:
                event["location"] = location
            if attendees:
                event["attendees"] = [{"email": email} for email in attendees]
            
            # Create event
            created_event = self.service.events().insert(
                calendarId="primary",
                body=event,
                sendUpdates="none"
            ).execute()
            
            event_data = self._parse_event(created_event)
            
            if callback:
                callback(event_data)
            
            self.logger.info(f"Created event: {created_event.get('id')}")
            return {
                "success": True,
                "event": event_data,
                "message": f"Event '{title}' created successfully"
            }
            
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to create event: {e}",
                "Check the event details and your permissions"
            ) from e
    
    def update_event(
        self,
        event_id: str,
        title: str | None = None,
        description: str | None = None,
        location: str | None = None,
        start_time: datetime | str | None = None,
        end_time: datetime | str | None = None,
        callback: Callable[[dict], None] | None = None
    ) -> dict[str, Any]:
        """Update an existing calendar event.
        
        Args:
            event_id: ID of the event to update
            title: New title (or None to keep existing)
            description: New description (or None to keep existing)
            location: New location (or None to keep existing)
            start_time: New start time (or None to keep existing)
            end_time: New end time (or None to keep existing)
            callback: Optional callback for streaming
            
        Returns:
            Updated event data
        """
        try:
            # Get existing event
            existing = self.service.events().get(
                calendarId="primary",
                eventId=event_id
            ).execute()
            
            # Build update body with only provided fields
            updates = {}
            
            if title is not None:
                updates["summary"] = title
            if description is not None:
                updates["description"] = description
            if location is not None:
                updates["location"] = location
            if start_time is not None:
                if isinstance(start_time, datetime):
                    start_time = start_time.isoformat() + "Z"
                updates["start"] = {"dateTime": start_time, "timeZone": "UTC"}
            if end_time is not None:
                if isinstance(end_time, datetime):
                    end_time = end_time.isoformat() + "Z"
                updates["end"] = {"dateTime": end_time, "timeZone": "UTC"}
            
            if not updates:
                raise ToolError(
                    self.name,
                    "No updates provided",
                    "Provide at least one field to update"
                )
            
            # Patch the event
            updated_event = self.service.events().patch(
                calendarId="primary",
                eventId=event_id,
                body=updates
            ).execute()
            
            event_data = self._parse_event(updated_event)
            
            if callback:
                callback(event_data)
            
            self.logger.info(f"Updated event: {event_id}")
            return {
                "success": True,
                "event": event_data,
                "message": f"Event {event_id} updated successfully"
            }
            
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to update event {event_id}: {e}",
                "Verify the event ID and your permissions"
            ) from e
    
    def delete_event(self, event_id: str) -> dict[str, Any]:
        """Delete a calendar event.
        
        Args:
            event_id: ID of the event to delete
            
        Returns:
            Success confirmation
        """
        try:
            self.service.events().delete(
                calendarId="primary",
                eventId=event_id
            ).execute()
            
            self.logger.info(f"Deleted event: {event_id}")
            return {
                "success": True,
                "message": f"Event {event_id} deleted successfully"
            }
            
        except Exception as e:
            raise ToolError(
                self.name,
                f"Failed to delete event {event_id}: {e}",
                "Verify the event ID and your permissions"
            ) from e
    
    def _parse_event(self, event: dict) -> dict[str, Any]:
        """Parse Google Calendar event into clean dict.
        
        Args:
            event: Raw event from API
            
        Returns:
            Parsed event dictionary
        """
        start = event.get("start", {})
        end = event.get("end", {})
        
        return {
            "id": event.get("id"),
            "summary": event.get("summary"),
            "description": event.get("description"),
            "location": event.get("location"),
            "start": start.get("dateTime", start.get("date")),
            "end": end.get("dateTime", end.get("date")),
            "status": event.get("status"),
            "htmlLink": event.get("htmlLink"),
            "created": event.get("created"),
            "updated": event.get("updated"),
        }


__all__ = [
    "GoogleCalendarTool",
]
