"""Installation script for the CalDAV MCP server."""
import os
import sys
import shutil
import subprocess
import platform
import json

def install():
    """Install the CalDAV MCP server for Claude desktop."""
    print("Installing CalDAV MCP server for Claude desktop...")
    
    # Determine the Claude desktop directory based on OS
    if platform.system() == "Windows":
        claude_dir = os.path.expanduser("~\\AppData\\Local\\Claude\\plugins")
    elif platform.system() == "Darwin":  # macOS
        claude_dir = os.path.expanduser("~/Library/Application Support/Claude/plugins")
    else:  # Linux
        claude_dir = os.path.expanduser("~/.config/Claude/plugins")
    
    # Create the plugins directory if it doesn't exist
    os.makedirs(claude_dir, exist_ok=True)
    
    # Create the caldav-mcp directory
    caldav_mcp_dir = os.path.join(claude_dir, "caldav-mcp")
    os.makedirs(caldav_mcp_dir, exist_ok=True)
    
    # Create the manifest.json file
    manifest = {
        "name": "caldav-mcp",
        "version": "0.1.0",
        "description": "CalDAV integration for Claude desktop",
        "main": "main.py",
        "author": "Your Name",
        "license": "MIT"
    }
    
    with open(os.path.join(caldav_mcp_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Create the main.py file that will start the server
    main_py = """
import subprocess
import sys
import os
import threading

def start_server():
    script_path = os.path.join(os.path.dirname(__file__), "caldav_mcp_server.py")
    subprocess.Popen([sys.executable, script_path])

# Start the server in a separate thread
threading.Thread(target=start_server, daemon=True).start()

# This function will be called by Claude desktop
def initialize():
    return {
        "status": "success",
        "message": "CalDAV MCP server started"
    }
"""
    
    with open(os.path.join(caldav_mcp_dir, "main.py"), "w") as f:
        f.write(main_py)
    
    # Create the caldav_mcp_server.py file
    server_py = """
from caldav_mcp.mcp_server import CalDAVMCPServer

def main():
    server = CalDAVMCPServer()
    server.run(transport="sse", host="localhost", port=8000)

if __name__ == "__main__":
    main()
"""
    
    with open(os.path.join(caldav_mcp_dir, "caldav_mcp_server.py"), "w") as f:
        f.write(server_py)
    
    print(f"CalDAV MCP server installed at {caldav_mcp_dir}")
    print("Please restart Claude desktop to activate the plugin.")

if __name__ == "__main__":
    install()
