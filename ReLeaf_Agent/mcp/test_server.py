import asyncio
import json
from fastmcp import Client


SERVICE_URL = "http://0.0.0.0:8080"


async def test_server():
    # Test the MCP server using streamable-http transport.
    # Use "/sse" endpoint if using sse transport.
    url = f"{SERVICE_URL}/mcp/"
    async with Client(url) as client:
        # List available tools
        tools = await client.list_tools()
        for tool in tools:
            print(f">>> 🛠️  Tool found: {tool.name}")
        # # Call get_areas_where_more_trees_can_be_planted tool
        print(">>> 🪛  Calling get_areas_where_more_trees_can_be_planted tool")
        result = await client.call_tool("get_areas_where_more_trees_can_be_planted", {})
        print(f"<<< ✅ Result: {result.content[0].text}")
        result = json.loads(result.content[0].text)
        summary = result['summary']
        print("total_plantable_areas:", str(summary['total_plantable_areas']))
        print("total_plantable_area_m2:", str(summary['total_plantable_area_m2']))
        print("existing_trees_count:", str(summary['existing_trees_count']))
        print("original_areas_found:", str(summary['original_areas_found']))
        print("tree_suggestions:", str(summary['tree_suggestions']))


if __name__ == "__main__":
    asyncio.run(test_server())
