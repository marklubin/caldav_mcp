"""Tests for the CalDAV client."""
import pytest
from unittest.mock import patch, MagicMock
from caldav_mcp.caldav_client import CalDAVClient, CalendarEvent
from datetime import datetime
from zoneinfo import ZoneInfo

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

def test_get_calendars(caldav_client, mock_caldav):
    mock_calendar = MagicMock()
    mock_principal = MagicMock()
    mock_principal.calendars.return_value = [mock_calendar]
    mock_caldav.DAVClient.return_value.principal.return_value = mock_principal
    
    calendars = caldav_client.get_calendars()
    
    assert calendars == [mock_calendar]

def test_get_events(caldav_client, mock_caldav):
    mock_event = MagicMock()
    mock_ical = MagicMock()
    
    # Set up the datetime mocks
    start_dt = MagicMock()
    start_dt.dt = datetime(2023, 1, 1, 10, 0, 0, tzinfo=ZoneInfo("UTC"))
    end_dt = MagicMock()
    end_dt.dt = datetime(2023, 1, 1, 11, 0, 0, tzinfo=ZoneInfo("UTC"))
    
    # Configure the mock to return appropriate values
    mock_ical.get.side_effect = lambda key, default="": {
        "SUMMARY": "Test Event",
        "DTSTART": start_dt,
        "DTEND": end_dt,
        "LOCATION": "Test Location",
        "DESCRIPTION": "Test Description",
        "UID": "test-event-uid"
    }.get(key, default)
    
    mock_event.icalendar_component = mock_ical
    mock_calendar = MagicMock()
    mock_calendar.events.return_value = [mock_event]
    
    events = caldav_client.get_events(mock_calendar)
    
    assert len(events) == 1
    assert events[0].summary == "Test Event"
    assert events[0].start == "20230101T100000+0000"
    assert events[0].end == "20230101T110000+0000"
    assert events[0].location == "Test Location"
    assert events[0].description == "Test Description"
    assert events[0].uid == "test-event-uid"
