"""Main entry point for the CalDAV MCP server."""
import argparse
from caldav_mcp.mcp_server import CalDAVMCPServer

def run():
    """Run the server."""
    parser = argparse.ArgumentParser(description="CalDAV MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "sse"], help="Transport to use")
    
    args = parser.parse_args()
    
    server = CalDAVMCPServer()
    print(f"Starting CalDAV MCP server with {args.transport} transport")
    
    if args.transport == "sse":
        server.run(transport="sse", host=args.host, port=args.port)
    else:
        server.run(transport="stdio")

if __name__ == "__main__":
    run()
