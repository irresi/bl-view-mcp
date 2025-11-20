from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from .prompt import INSTRUCTION, DESCRIPTION

root_agent = Agent(
  model = "gemini-2.5-flash",
  name = "image_editor",
  description = DESCRIPTION,
  instruction = INSTRUCTION,
  tools = [
    MCPToolset(
      connection_params = StreamableHTTPConnectionParams(
        url = "http://localhost:5000/mcp"
      )
    )
  ]
)
