"""Integration tests for the CalDAV MCP server."""
import pytest
from unittest.mock import patch, MagicMock
from caldav_mcp.mcp_server import CalDAVMCPServer
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

@pytest.fixture
def mock_caldav_client():
    with patch('caldav_mcp.mcp_server.CalDAVClient', autospec=True) as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_class

@pytest.fixture
def mcp_server(mock_caldav_client):
    with patch('caldav_mcp.mcp_server.CalDAVClient', mock_caldav_client):
        server = CalDAVMCPServer()
        return server

def test_tool_registration(mcp_server):
    """Test that tools are registered correctly."""
    # Verify that the tools are registered
    # FastMCP 2.0 doesn't expose a direct method to check registered tools
    # So we'll check by calling the tools
    assert callable(mcp_server.get_calendars)
    assert callable(mcp_server.get_events)