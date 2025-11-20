"""Start Black-Litterman MCP server in HTTP mode (for ADK Agent)."""

from bl_mcp.server import mcp

if __name__ == "__main__":
    # Run in HTTP mode for ADK Agent integration
    print("Starting Black-Litterman MCP server in HTTP mode...")
    print("Server will be available at http://localhost:5000/mcp")
    mcp.run(transport="http", host="localhost", port=5000)
