"""Tests for the CalDAV MCP server."""
import pytest
from unittest.mock import patch, MagicMock, PropertyMock, ANY
from caldav_mcp.mcp_server import CalDAVMCPServer
import os
from datetime import datetime, timedelta
import icalendar
from caldav.objects import Calendar, Event
from caldav.lib.error import NotFoundError

@pytest.fixture(autouse=True)
def env_vars():
    """Set up test environment variables."""
    os.environ["MCP_CALDAV_URI"] = "https://example.com/caldav"
    os.environ["MCP_CALDAV_USERNAME"] = "testuser"
    os.environ["MCP_CALDAV_PASSWORD"] = "testpass"
    yield
    # Clean up after test
    del os.environ["MCP_CALDAV_URI"]
    del os.environ["MCP_CALDAV_USERNAME"]
    del os.environ["MCP_CALDAV_PASSWORD"]

@pytest.fixture
def mock_caldav():
    with patch('caldav_mcp.mcp_server.caldav') as mock:
        yield mock

@pytest.fixture
def mock_principal(mock_caldav):
    principal = MagicMock()
    mock_caldav.DAVClient.return_value.principal.return_value = principal
    return principal

@pytest.fixture
def mock_calendar():
    cal = MagicMock(spec=Calendar)
    cal.id = "test-calendar-id"
    cal.name = "Test Calendar"
    cal.url = "/calendars/test"
    return cal

@pytest.fixture
def mock_event():
    event = MagicMock(spec=Event)
    event.icalendar_component = icalendar.Event()
    event.icalendar_component.add('uid', 'test-event-1')
    event.icalendar_component.add('summary', 'Test Event')
    event.icalendar_component.add('dtstart', datetime.now())
    event.icalendar_component.add('dtend', datetime.now() + timedelta(hours=1))
    event.url = "/calendars/test/event1.ics"
    return event

@pytest.fixture
def mcp_server(mock_caldav, mock_principal):
    server = CalDAVMCPServer()
    server._principal = mock_principal  # Inject mock principal for testing
    return server

def test_get_calendars(mcp_server, mock_principal, mock_calendar):
    # Set up mock principal to return our test calendar
    mock_principal.calendars.return_value = [mock_calendar]
    
    # Call the method
    result = mcp_server.get_calendars()
    
    # Verify the response
    assert "calendars" in result
    assert len(result["calendars"]) == 1
    assert result["calendars"][0]["name"] == "Test Calendar"
    assert result["calendars"][0]["id"] == "test-calendar-id"
    mock_principal.calendars.assert_called_once()

def test_get_events(mcp_server, mock_principal, mock_calendar, mock_event):
    # Set up mock calendar to return our test event
    mock_principal.calendars.return_value = [mock_calendar]
    mock_calendar.events.return_value = [mock_event]
    
    # Call the method
    result = mcp_server.get_events("test-calendar-id")
    
    # Verify the response
    assert "events" in result
    assert len(result["events"]) == 1
    assert result["events"][0].icalendar_component["summary"] == "Test Event"
    mock_calendar.events.assert_called_once()

def test_get_event_by_id(mcp_server, mock_principal, mock_calendar, mock_event):
    # Set up mock calendar to find our test event
    mock_principal.calendars.return_value = [mock_calendar]
    mock_calendar.search.return_value = [mock_event]
    
    # Call the method
    result = mcp_server.get_event_by_id("test-calendar-id", "test-event-1")
    
    # Verify the response
    assert "event" in result
    assert result["event"].icalendar_component["uid"] == "test-event-1"
    mock_calendar.search.assert_called_once_with(event_id="test-event-1")

def test_get_events_in_range(mcp_server, mock_principal, mock_calendar, mock_event):
    # Set up mock calendar to return our test event
    mock_principal.calendars.return_value = [mock_calendar]
    mock_calendar.date_search.return_value = [mock_event]
    
    # Create timezone-aware datetime objects for the test
    from datetime import timezone
    now = datetime.now(timezone.utc)
    start_dt = now - timedelta(days=1)
    end_dt = now + timedelta(days=1)
    
    # Format as strings without timezone offset (since we'll mock the parsing)
    start = start_dt.strftime("%Y%m%dT%H%M%S")
    end = end_dt.strftime("%Y%m%dT%H%M%S")
    
    # Mock the datetime parsing in the method
    with patch('caldav_mcp.mcp_server.datetime') as mock_datetime:
        # Make sure now() returns our test time
        mock_datetime.now.return_value = now
        # Mock strptime to return our test datetimes
        mock_datetime.strptime.side_effect = [
            start_dt.replace(tzinfo=timezone.utc),
            end_dt.replace(tzinfo=timezone.utc)
        ]
        result = mcp_server.get_events_in_range("test-calendar-id", start, end)
    
    # Verify the response
    assert "events" in result
    assert len(result["events"]) == 1
    assert result["count"] == 1
    assert result["calendar_id"] == "test-calendar-id"
    mock_calendar.date_search.assert_called_once()

def test_search_events(mcp_server, mock_principal, mock_calendar, mock_event):
    # Set up mock calendar to return our test event
    mock_principal.calendars.return_value = [mock_calendar]
    mock_calendar.events.return_value = [mock_event]
    
    # Call the search method
    result = mcp_server.search_events("test-calendar-id", "Test")
    
    # Verify the response
    assert "events" in result
    assert len(result["events"]) > 0
    assert result["query"] == "Test"
    assert result["calendar_id"] == "test-calendar-id"

def test_create_event(mcp_server, mock_principal, mock_calendar):
    # Set up mock calendar
    mock_principal.calendars.return_value = [mock_calendar]
    
    # Test event data
    event_data = {
        "uid": "test-event-1",
        "summary": "Test Event",
        "start": "20250101T120000Z",
        "end": "20250101T130000Z"
    }
    
    # Call the method
    result = mcp_server.create_event("test-calendar-id", event_data)
    
    # Verify the response
    assert "event" in result
    assert result["event"]["uid"] == "test-event-1"
    mock_calendar.add_event.assert_called_once()

def test_delete_event(mcp_server, mock_principal, mock_calendar, mock_event):
    # Set up mock calendar and event
    mock_principal.calendars.return_value = [mock_calendar]
    mock_calendar.search.return_value = [mock_event]
    
    # Test successful deletion
    result = mcp_server.delete_event("test-calendar-id", "test-event-1")
    assert "message" in result
    assert "deleted successfully" in result["message"]
    mock_event.delete.assert_called_once()

def test_update_event(mcp_server, mock_principal, mock_calendar, mock_event):
    # Set up mock calendar and event
    mock_principal.calendars.return_value = [mock_calendar]
    mock_calendar.search.return_value = [mock_event]
    
    # Mock create_event to return success
    with patch.object(mcp_server, 'create_event') as mock_create:
        mock_create.return_value = {"message": "Event created", "event": {"uid": "test-event-1"}}
        
        # Test updating event
        event_data = {
            "uid": "test-event-1",
            "summary": "Updated Event",
            "start": "20250101T120000Z",
            "end": "20250101T130000Z"
        }
        result = mcp_server.update_event("test-calendar-id", "test-event-1", event_data)
        
        # Verify the old event was deleted
        mock_event.delete.assert_called_once()
        
        # Verify create_event was called with the right data
        args, kwargs = mock_create.call_args
        assert args[0] == "test-calendar-id"
        assert args[1]["uid"] == "test-event-1"  # Should use the ID from the URL, not the body
        
        # Verify the response
        assert "message" in result
        assert result["event"]["uid"] == "test-event-1"

def test_update_event_not_found(mcp_server, mock_principal, mock_calendar):
    # Set up mock calendar with no events
    mock_principal.calendars.return_value = [mock_calendar]
    mock_calendar.search.return_value = []
    
    # Test event not found
    event_data = {
        "summary": "Updated Event",
        "start": "20250101T120000Z",
        "end": "20250101T130000Z"
    }
    result = mcp_server.update_event("test-calendar-id", "nonexistent-event", event_data)
    assert "error" in result
    assert "not found" in result["error"].lower()
    
    # Test calendar not found
    mock_principal.calendars.return_value = []
    result = mcp_server.update_event("nonexistent-calendar", "test-event-1", event_data)
    assert "error" in result
    assert "not found" in result["error"].lower()

def test_delete_event_not_found(mcp_server, mock_principal, mock_calendar):
    # Set up mock calendar with no events
    mock_principal.calendars.return_value = [mock_calendar]
    mock_calendar.search.return_value = []
    
    # Test event not found
    result = mcp_server.delete_event("test-calendar-id", "nonexistent-event")
    assert "error" in result
    assert "not found" in result["error"].lower()
    
    # Test calendar not found
    mock_principal.calendars.return_value = []
    result = mcp_server.delete_event("nonexistent-calendar", "test-event-1")
    assert "error" in result
    assert "not found" in result["error"].lower()

def test_error_handling(mcp_server, mock_principal, mock_calendar):
    # Test non-existent calendar
    mock_principal.calendars.return_value = [mock_calendar]
    result = mcp_server.get_events("nonexistent-calendar")
    assert "error" in result
    assert "not found" in result["error"].lower()
    
    # Test event not found
    mock_principal.calendars.return_value = [mock_calendar]
    mock_calendar.search.return_value = []
    result = mcp_server.get_event_by_id("test-calendar-id", "nonexistent-event")
    assert "error" in result
    assert "not found" in result["error"].lower()
    
    # Test delete event error
    mock_calendar.search.return_value = [MagicMock()]
    mock_calendar.search.return_value[0].delete.side_effect = Exception("Deletion failed")
    result = mcp_server.delete_event("test-calendar-id", "test-event-1")
    assert "error" in result
    assert "deleting event" in result["error"].lower()
    
    # Test invalid time format
    with patch('caldav_mcp.mcp_server.datetime') as mock_datetime:
        mock_datetime.strptime.side_effect = ValueError("Invalid date format")
        result = mcp_server.get_events_in_range(
            "test-calendar-id", 
            "invalid-date", 
            "invalid-date"
        )
        assert "error" in result
        assert "invalid" in result["error"].lower()