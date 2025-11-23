"""Entry point for Black-Litterman MCP server."""

import sys


def main_stdio():
    """Run MCP server in stdio mode (for Windsurf/Claude Desktop)."""
    from bl_mcp.server import mcp
    mcp.run(transport="stdio")


def main_http():
    """Run MCP server in HTTP mode (for Google ADK)."""
    from bl_mcp.server import mcp
    mcp.run(transport="sse", host="0.0.0.0", port=5000)


if __name__ == "__main__":
    main_stdio()
