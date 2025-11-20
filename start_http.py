"""
Start Black-Litterman MCP Server in HTTP mode.

This mode is used for:
- Google ADK Agent integration
- Web-based testing
- HTTP-based MCP clients

Usage:
    python start_http.py
    
Server will be available at: http://localhost:5000/mcp

For ADK Web UI:
    1. Terminal 1: python start_http.py
    2. Terminal 2: adk web
    3. Open browser: http://localhost:8000
"""

from bl_mcp.server import mcp

if __name__ == "__main__":
    print("=" * 60)
    print("Black-Litterman MCP Server - HTTP Mode")
    print("=" * 60)
    print()
    print("🚀 Server starting at: http://localhost:5000/mcp")
    print()
    print("📝 To test with ADK Web UI:")
    print("   1. Keep this terminal running")
    print("   2. Open new terminal and run: adk web")
    print("   3. Open browser: http://localhost:8000")
    print()
    print("=" * 60)
    print()
    
    mcp.run(transport="http", host="localhost", port=5000)
