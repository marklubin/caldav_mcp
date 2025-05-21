"""Integration tests for the CalDAV MCP server."""
import pytest
from unittest.mock import patch, MagicMock
import icalendar
from datetime import datetime, timedelta
from caldav_mcp.mcp_server import CalDAVMCPServer
from caldav.objects import Calendar, Event

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

def test_tool_registration(mcp_server):
    """Test that the MCP server methods are callable."""
    # Verify that the main methods are callable
    assert callable(mcp_server.get_calendars)
    assert callable(mcp_server.get_events)
    assert callable(mcp_server.get_event_by_id)
    assert callable(mcp_server.get_events_in_range)
    assert callable(mcp_server.search_events)
    assert callable(mcp_server.create_event)

def test_integration_workflow(mcp_server, mock_principal, mock_calendar, mock_event):
    """Test a complete workflow from getting calendars to deleting events."""
    # Set up mock principal to return our test calendar
    mock_principal.calendars.return_value = [mock_calendar]
    
    # 1. Test getting calendars
    calendars = mcp_server.get_calendars()
    assert "calendars" in calendars
    assert len(calendars["calendars"]) == 1
    assert calendars["calendars"][0]["name"] == "Test Calendar"
    
    # 2. Test getting events
    mock_calendar.events.return_value = [mock_event]
    events = mcp_server.get_events("test-calendar-id")
    assert "events" in events
    assert len(events["events"]) == 1
    assert events["events"][0].icalendar_component["summary"] == "Test Event"
    
    # 3. Test creating an event
    event_data = {
        "uid": "new-test-event",
        "summary": "New Test Event",
        "start": "20250101T120000Z",
        "end": "20250101T130000Z"
    }
    created = mcp_server.create_event("test-calendar-id", event_data)
    assert "event" in created
    assert created["event"]["uid"] == "new-test-event"
    
    # 4. Test getting event by ID
    mock_calendar.search.return_value = [mock_event]
    event = mcp_server.get_event_by_id("test-calendar-id", "test-event-1")
    assert "event" in event
    assert event["event"].icalendar_component["summary"] == "Test Event"
    
    # 5. First test deleting an event
    # Create a separate mock for the event to be deleted
    event_to_delete = MagicMock()
    event_to_delete.icalendar_component = icalendar.Event()
    event_to_delete.icalendar_component.add('uid', 'event-to-delete')
    event_to_delete.url = "/calendars/test/event-to-delete.ics"
    
    mock_calendar.search.return_value = [event_to_delete]
    result = mcp_server.delete_event("test-calendar-id", "event-to-delete")
    assert "message" in result
    assert "deleted successfully" in result["message"]
    event_to_delete.delete.assert_called_once()
    
    # 6. Now test updating an event
    # Create a fresh mock for the event to be updated
    event_to_update = MagicMock()
    event_to_update.icalendar_component = icalendar.Event()
    event_to_update.icalendar_component.add('uid', 'event-to-update')
    event_to_update.icalendar_component.add('summary', 'Original Event')
    event_to_update.url = "/calendars/test/event-to-update.ics"
    
    mock_calendar.search.return_value = [event_to_update]
    
    # Mock create_event to return a success response
    with patch.object(mcp_server, 'create_event') as mock_create:
        mock_create.return_value = {
            "message": "Event updated",
            "event": {
                "uid": "event-to-update",
                "summary": "Updated Test Event",
                "description": "This is an updated description"
            }
        }
        
        # Create complete event data for the update
        event_data = {
            "uid": "event-to-update",  # Will be overridden by the event_id in the URL
            "summary": "Updated Test Event",
            "description": "This is an updated description",
            "start": "20250101T130000Z",
            "end": "20250101T140000Z"
        }
        
        # Call update_event
        updated = mcp_server.update_event("test-calendar-id", "event-to-update", event_data)
        
        # Verify the response
        assert "message" in updated
        assert "event" in updated
        assert updated["event"]["summary"] == "Updated Test Event"
        
        # Verify the old event was deleted
        event_to_update.delete.assert_called_once()
        
        # Verify create_event was called with the right data
        args, kwargs = mock_create.call_args
        assert args[0] == "test-calendar-id"
        assert args[1]["uid"] == "event-to-update"  # Should use the ID from the URL, not the body
    
    # 7. Verify event was deleted
    # Create a new mock for the delete verification
    event_to_verify_delete = MagicMock()
    event_to_verify_delete.icalendar_component = icalendar.Event()
    event_to_verify_delete.icalendar_component.add('uid', 'event-to-verify-delete')
    event_to_verify_delete.url = "/calendars/test/event-to-verify-delete.ics"
    
    # First verify it exists
    mock_calendar.search.return_value = [event_to_verify_delete]
    result = mcp_server.get_event_by_id("test-calendar-id", "event-to-verify-delete")
    assert "event" in result
    
    # Now delete it
    mock_calendar.search.return_value = [event_to_verify_delete]
    result = mcp_server.delete_event("test-calendar-id", "event-to-verify-delete")
    assert "message" in result
    assert "deleted successfully" in result["message"]
    
    # Finally verify it's gone
    mock_calendar.search.return_value = []
    result = mcp_server.get_event_by_id("test-calendar-id", "event-to-verify-delete")
    assert "error" in result
    assert "not found" in result["error"].lower()