"""CalDAV client module."""
import caldav
from pydantic import BaseModel
from typing import List, Optional
import re


    
class CalendarEvent(BaseModel):
    """Model for a calendar event."""
    uid: str
    summary: str
    start: str
    end: str
    location: Optional[str] = None
    description: Optional[str] = None
    
class CalDAVClient:
    """Client for connecting to a CalDAV server."""
    def __init__(self, url: str, username: str, password: str):
        """Initialize the CalDAV client.
        
        Args:
            url: The URL of the CalDAV server.
            username: The username for authentication.
            password: The password for authentication.
        """
        self.url = url
        self.username = username
        self.password = password
        self._client = None
    
    def connect(self):
        """Connect to the CalDAV server.
        
        Returns:
            The principal object from the CalDAV server.
        """
        self._client = caldav.DAVClient(
            url=self.url,
            username=self.username,
            password=self.password
        )
        return self._client.principal()
    
    def get_calendars(self):
        """Get all calendars from the CalDAV server.
        
        Returns:
            A list of calendar objects.
        """
        principal = self.connect()
        return principal.calendars()
    
    def get_events(self, calendar) -> List[CalendarEvent]:
        """Get all events from a calendar.
        
        Args:
            calendar: The calendar object.
            
        Returns:
            A list of CalendarEvent objects.
        """
        return [self.to_calendar_event(e) for e in calendar.events()]
        
       
       
    def to_calendar_event(self, caldav_event) -> CalendarEvent:
        """
        Convert a caldav Event resource to CalendarEvent.
        """
        ical = caldav_event.icalendar_component  # This retrieves the actual VEVENT

        uid = str(ical.get("UID"))
        summary = str(ical.get("SUMMARY", ""))
        start = ical.get("DTSTART").dt.strftime("%Y%m%dT%H%M%S%z") if ical.get("DTSTART") else ""
        end = ical.get("DTEND").dt.strftime("%Y%m%dT%H%M%S%z") if ical.get("DTEND") else ""
        location = str(ical.get("LOCATION", "")) if ical.get("LOCATION") else None
        description = str(ical.get("DESCRIPTION", "")) if ical.get("DESCRIPTION") else None

        return CalendarEvent(
            uid=uid,
            summary=summary,
            start=start,
            end=end,
            location=location,
            description=description)
        
    