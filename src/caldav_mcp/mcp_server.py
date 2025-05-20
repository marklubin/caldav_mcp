"""MCP server for CalDAV integration."""
import json
from typing import Dict, List, Optional, Union, Any

from fastmcp import FastMCP
from caldav_mcp.caldav_client import CalDAVClient, CalendarEvent
import os


class EnvironmentConfigurationProvider:
    def uri(self):
        return os.environ.get("MCP_CALDAV_URI")
    
    def username(self):
        return os.environ.get("MCP_CALDAV_USERNAME")
    
    def password(self):
        return os.environ.get("MCP_CALDAV_PASSWORD")
    
        
class CalDAVMCPServer:
    """MCP server for CalDAV integration."""
    def __init__(self, name="CalDAV MCP Server"):
        """Initialize the server.
        
        Args:
            name: The name of the server.
        """
        self.mcp = FastMCP(name=name)
        self.caldav_client = None
        config_provider = EnvironmentConfigurationProvider()
    
        self.caldav_client = CalDAVClient(
            url=config_provider.uri(),
            username=config_provider.username(),
            password=config_provider.password()
        )
        
        # Test the connection
        self.caldav_client.connect()
        
        # Register tools
        self.mcp.tool()(self.get_calendars)
        self.mcp.tool()(self.get_events)
        
    def get_calendars(self) -> Dict[str, Any]:
        """Get all calendars from the CalDAV server.
        
        Returns:
            A dictionary with a list of calendars.
        """
        if not self.caldav_client:
            return {"error": "Not connected to CalDAV server"}
        
        try:
            calendars = self.caldav_client.get_calendars()
            result = []
            
            for calendar in calendars:
                result.append({
                    "name": getattr(calendar, "name", "Unknown"),
                    "id": getattr(calendar, "id", str(hash(calendar)))
                })
            
            return {"calendars": result}
        except Exception as e:
            return {"error": str(e)}
    
    def get_events(self, calendar_id: str) -> Dict[str, Any]:
        """Get all events from a calendar.
        
        Args:
            calendar_id: The ID of the calendar.
            
        Returns:
            A dictionary with a list of events.
        """
        if not self.caldav_client:
            return {"error": "Not connected to CalDAV server"}
        
        try:
            # Find the calendar by ID
            calendars = self.caldav_client.get_calendars()
            calendar = None
            
            for cal in calendars:
                if getattr(cal, "id", str(hash(cal))) == calendar_id:
                    calendar = cal
                    break
            
            if not calendar:
                return {"error": f"Calendar with ID {calendar_id} not found"}
            
            # Get events from the calendar
            events = self.caldav_client.get_events(calendar)
            result = []
            
            for event in events:
                result.append(event.dict())
            
            return {"events": result}
        except Exception as e:
            return {"error": str(e)}
            
    def run(self, **kwargs):
        """Run the server.
        
        Args:
            **kwargs: Additional arguments to pass to the FastMCP run method.
        """
        self.mcp.run(**kwargs)
