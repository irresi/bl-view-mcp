"""
Test Black-Litterman MCP Server with Google ADK Agent.

This script creates an ADK agent that connects to the MCP server
and tests the portfolio optimization workflow.

Usage:
    1. Start MCP server: python start_http.py
    2. Run this test: python test_agent.py
"""

import asyncio
import os

from google.adk.agents.llm_agent import Agent
from google.genai.types import Tool
from mcp import MCPToolset
from mcp.client.stdio import StdioServerParameters
from mcp.client.sse import sse_client


AGENT_NAME = "portfolio-optimizer"
AGENT_DESCRIPTION = "Portfolio optimization expert using Black-Litterman model"

INSTRUCTION = """
You are a portfolio optimization expert that helps users create optimal portfolios
using the Black-Litterman model.

Available Tools:
1. calculate_expected_returns - Calculate historical expected returns
2. calculate_covariance_matrix - Calculate covariance matrix
3. create_investor_view - Create investor views
4. optimize_portfolio_bl - Run Black-Litterman optimization

Workflow:
1. User provides tickers and optional views
2. You call optimize_portfolio_bl with appropriate parameters
3. You explain the results clearly

Always explain:
- Portfolio weights (as percentages)
- Expected return (annualized)
- Volatility (annualized)
- Sharpe ratio
- How views affected the portfolio
"""


async def test_basic_optimization():
    """Test basic portfolio optimization without views."""
    
    print("=" * 60)
    print("TEST 1: Basic Optimization (No Views)")
    print("=" * 60)
    
    # Connect to MCP server via HTTP
    async with sse_client("http://localhost:5000/mcp") as (read, write):
        async with MCPToolset(read, write) as toolset:
            
            # Create agent
            agent = Agent(
                model="gemini-2.0-flash-exp",
                name=AGENT_NAME,
                description=AGENT_DESCRIPTION,
                instruction=INSTRUCTION,
                tools=[toolset]
            )
            
            # Test query
            query = """
            AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘.
            2023년 1월 1일부터 데이터를 사용해.
            견해는 없고, 시장 균형만 사용해.
            """
            
            print(f"\n📝 Query: {query}\n")
            
            response = agent.generate_response(query)
            print(f"🤖 Agent Response:\n{response.text}\n")
            
            # Check tool calls
            if hasattr(response, 'tool_calls'):
                print(f"🔧 Tool Calls: {len(response.tool_calls)}")
                for i, call in enumerate(response.tool_calls, 1):
                    print(f"  {i}. {call.name}")


async def test_with_views():
    """Test portfolio optimization with investor views."""
    
    print("\n" + "=" * 60)
    print("TEST 2: Optimization with Views")
    print("=" * 60)
    
    async with sse_client("http://localhost:5000/mcp") as (read, write):
        async with MCPToolset(read, write) as toolset:
            
            agent = Agent(
                model="gemini-2.0-flash-exp",
                name=AGENT_NAME,
                description=AGENT_DESCRIPTION,
                instruction=INSTRUCTION,
                tools=[toolset]
            )
            
            query = """
            AAPL, MSFT, GOOGL로 포트폴리오를 최적화해줘.
            2023년 1월 1일부터 데이터를 사용하고,
            AAPL이 10% 수익을 낼 것으로 예상해. 확신도는 70%야.
            """
            
            print(f"\n📝 Query: {query}\n")
            
            response = agent.generate_response(query)
            print(f"🤖 Agent Response:\n{response.text}\n")


async def test_direct_tool_call():
    """Test direct MCP tool call without agent."""
    
    print("\n" + "=" * 60)
    print("TEST 3: Direct Tool Call")
    print("=" * 60)
    
    async with sse_client("http://localhost:5000/mcp") as (read, write):
        async with MCPToolset(read, write) as toolset:
            
            print("\n📞 Calling optimize_portfolio_bl directly...")
            
            # Direct tool call
            result = await toolset.call_tool(
                "optimize_portfolio_bl",
                {
                    "tickers": ["AAPL", "MSFT", "GOOGL"],
                    "start_date": "2023-01-01",
                    "views": {"AAPL": 0.10},
                    "confidence": 0.7
                }
            )
            
            print(f"\n📊 Result:")
            import json
            print(json.dumps(result, indent=2))


async def main():
    """Run all tests."""
    
    print("\n🧪 Black-Litterman MCP Server Tests\n")
    
    # Check if MCP server is running
    try:
        import requests
        response = requests.get("http://localhost:5000/mcp", timeout=2)
        print("✅ MCP server is running at http://localhost:5000/mcp\n")
    except:
        print("❌ MCP server is not running!")
        print("   Start it with: python start_http.py\n")
        return
    
    # Run tests
    try:
        await test_direct_tool_call()
        await test_basic_optimization()
        await test_with_views()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
