"""Start Black-Litterman MCP server in stdio mode (for Windsurf/Claude Desktop)."""

from bl_mcp.server import mcp


def main():
    """Main entry point for stdio mode."""
    # Run in stdio mode for IDE integration (Windsurf, Claude Desktop)
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
