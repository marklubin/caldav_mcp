"""Tests for the MCP server."""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from caldav_mcp.mcp_server import CalDAVMCPServer
from caldav_mcp.caldav_client import CalendarEvent

@pytest.fixture
def mcp_server():
    return CalDAVMCPServer()

@pytest.fixture
def mock_caldav_client():
    with patch('caldav_mcp.caldav_client.CalDAVClient', autospec=True) as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_class

def test_connect(mcp_server, mock_caldav_client):
    # Create a patch for the CalDAVClient to ensure proper mocking
    with patch('caldav_mcp.mcp_server.CalDAVClient', mock_caldav_client):
        # Call the connect method
        result = mcp_server.connect(
            url="https://example.com/caldav",
            username="testuser",
            password="testpass"
        )
        
        # Verify the response
        assert result["success"] == True
        
        # Verify CalDAVClient was initialized correctly
        mock_caldav_client.assert_called_with(
            url="https://example.com/caldav", 
            username="testuser", 
            password="testpass"
        )

def test_get_calendars(mcp_server, mock_caldav_client):
    # Create a mock calendar with explicit properties
    mock_calendar = MagicMock()
    type(mock_calendar).name = PropertyMock(return_value="Test Calendar")
    type(mock_calendar).id = PropertyMock(return_value="test-calendar-id")
    
    with patch('caldav_mcp.mcp_server.CalDAVClient', mock_caldav_client):
        # Set up the mock instance
        mock_instance = mock_caldav_client.return_value
        mock_instance.get_calendars.return_value = [mock_calendar]
        
        # Set the caldav_client
        mcp_server.caldav_client = mock_instance
        
        # Call the get_calendars method
        result = mcp_server.get_calendars()
        
        # Verify the response
        assert "calendars" in result
        assert len(result["calendars"]) == 1
        assert result["calendars"][0]["name"] == "Test Calendar"
        assert result["calendars"][0]["id"] == "test-calendar-id"
        
        # Verify CalDAVClient method was called
        mock_instance.get_calendars.assert_called_once()

def test_get_events(mcp_server, mock_caldav_client):
    # Create a mock calendar with an explicit ID attribute
    mock_calendar = MagicMock()
    type(mock_calendar).id = PropertyMock(return_value="test-calendar-id")
    
    mock_calendar_event = CalendarEvent(
        uid="test-event-uid",
        summary="Test Event",
        start="20230101T100000Z",
        end="20230101T110000Z",
        location="Test Location",
        description="Test Description"
    )
    
    with patch('caldav_mcp.mcp_server.CalDAVClient', mock_caldav_client):
        # Set up the mock instance
        mock_instance = mock_caldav_client.return_value
        mock_instance.get_calendars.return_value = [mock_calendar]
        mock_instance.get_events.return_value = [mock_calendar_event]
        
        # Set the caldav_client
        mcp_server.caldav_client = mock_instance
        
        # Call the get_events method
        result = mcp_server.get_events("test-calendar-id")
        
        # Debug print if the test fails
        if "events" not in result:
            print(f"Debug - Result: {result}")
            print(f"Debug - Calendar ID: {getattr(mock_calendar, 'id', None)}")
            calendars = mock_instance.get_calendars.return_value
            print(f"Debug - Calendar IDs in get_calendars: {[getattr(cal, 'id', str(hash(cal))) for cal in calendars]}")
        
        # Verify the response
        assert "events" in result
        assert len(result["events"]) == 1
        assert result["events"][0]["uid"] == "test-event-uid"
        assert result["events"][0]["summary"] == "Test Event"
        assert result["events"][0]["start"] == "20230101T100000Z"
        assert result["events"][0]["end"] == "20230101T110000Z"
        assert result["events"][0]["location"] == "Test Location"
        assert result["events"][0]["description"] == "Test Description"
        
        # Verify CalDAVClient method was called
        mock_instance.get_events.assert_called_once()
