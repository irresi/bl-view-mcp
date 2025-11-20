from image_mcp.server import mcp

mcp.run(transport="http", host="localhost", port=5000)