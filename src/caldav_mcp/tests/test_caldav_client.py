"""Tests for the CalDAV client."""
import pytest
from unittest.mock import patch, MagicMock
from caldav_mcp.caldav_client import CalDAVClient, CalendarEvent

@pytest.fixture
def mock_caldav():
    with patch('caldav_mcp.caldav_client.caldav') as mock:
        yield mock

@pytest.fixture
def caldav_client():
    return CalDAVClient(
        url="https://example.com/caldav",
        username="testuser",
        password="testpass"
    )

def test_client_initialization(caldav_client):
    assert caldav_client.url == "https://example.com/caldav"
    assert caldav_client.username == "testuser"
    assert caldav_client.password == "testpass"

def test_connect(caldav_client, mock_caldav):
    mock_principal = MagicMock()
    mock_caldav.DAVClient.return_value.principal.return_value = mock_principal
    
    principal = caldav_client.connect()
    
    mock_caldav.DAVClient.assert_called_once_with(
        url="https://example.com/caldav", 
        username="testuser", 
        password="testpass"
    )
    assert principal == mock_principal

def test_get_calendars(caldav_client, mock_caldav):
    mock_calendar = MagicMock()
    mock_principal = MagicMock()
    mock_principal.calendars.return_value = [mock_calendar]
    mock_caldav.DAVClient.return_value.principal.return_value = mock_principal
    
    calendars = caldav_client.get_calendars()
    
    assert calendars == [mock_calendar]

def test_get_events(caldav_client, mock_caldav):
    mock_event = MagicMock()
    mock_event.data = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Example//Example Calendar//EN
BEGIN:VEVENT
SUMMARY:Test Event
DTSTART:20230101T100000Z
DTEND:20230101T110000Z
LOCATION:Test Location
DESCRIPTION:Test Description
UID:test-event-uid
END:VEVENT
END:VCALENDAR"""
    
    mock_calendar = MagicMock()
    mock_calendar.events.return_value = [mock_event]
    
    events = caldav_client.get_events(mock_calendar)
    
    assert len(events) == 1
    assert events[0].summary == "Test Event"
    assert events[0].start == "20230101T100000Z"
    assert events[0].end == "20230101T110000Z"
    assert events[0].location == "Test Location"
    assert events[0].description == "Test Description"
    assert events[0].uid == "test-event-uid"
