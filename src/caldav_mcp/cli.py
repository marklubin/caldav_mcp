"""CLI client for the CalDAV MCP server."""
import argparse
import json
import asyncio
import os
from fastmcp import Client
from fastmcp.client.transports.stdio import StdioServerParameters, stdio_client
from fastmcp.client.transports.sse import SseTransport

async def run_client(args):
    """Run the CLI client."""
    # Choose the transport based on the environment
    transport = None
    if os.environ.get("CALDAV_MCP_TRANSPORT", "sse") == "stdio":
        # Use stdio transport
        server_path = os.environ.get("CALDAV_MCP_PATH", "caldav-mcp")
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "caldav_mcp.main"],
        )
        async with stdio_client(server_params) as (read, write):
            async with Client(transport=(read, write)) as client:
                await process_commands(args, client)
    else:
        # Use SSE transport
        base_url = os.environ.get("CALDAV_MCP_URL", "http://localhost:8000")
        async with Client(transport=SseTransport(f"{base_url}/sse")) as client:
            await process_commands(args, client)

async def process_commands(args, client):
    """Process the commands using the client."""
    if args.command == "connect":
        result = await client.call_tool(
            "connect",
            {
                "url": args.url,
                "username": args.username,
                "password": args.password
            }
        )
        print(json.dumps(result, indent=2))
    
    elif args.command == "calendars":
        result = await client.call_tool("get_calendars")
        print(json.dumps(result, indent=2))
    
    elif args.command == "events":
        result = await client.call_tool(
            "get_events",
            {"calendar_id": args.calendar_id}
        )
        print(json.dumps(result, indent=2))

def main():
    """Main entry point for the CLI client."""
    parser = argparse.ArgumentParser(description="CalDAV MCP CLI Client")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Connect command
    connect_parser = subparsers.add_parser("connect", help="Connect to a CalDAV server")
    connect_parser.add_argument("--url", required=True, help="CalDAV server URL")
    connect_parser.add_argument("--username", required=True, help="Username")
    connect_parser.add_argument("--password", required=True, help="Password")
    
    # List calendars command
    subparsers.add_parser("calendars", help="List calendars")
    
    # List events command
    events_parser = subparsers.add_parser("events", help="List events")
    events_parser.add_argument("--calendar-id", required=True, help="Calendar ID")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    asyncio.run(run_client(args))

if __name__ == "__main__":
    main()
