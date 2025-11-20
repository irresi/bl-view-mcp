"""Start Black-Litterman MCP server in stdio mode (for Windsurf/Claude Desktop)."""

from bl_mcp.server import mcp

if __name__ == "__main__":
    # Run in stdio mode for IDE integration (Windsurf, Claude Desktop)
    mcp.run(transport="stdio")
