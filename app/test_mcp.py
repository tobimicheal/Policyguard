import asyncio
import json

from mcp import Client
from mcp_server.server import mcp


async def main():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("Available tools:")
        for tool in tools.tools:
            print(tool.model_dump_json(indent=2, by_alias=True))

        result = await client.call_tool(
            "get_resource_configuration",
            {"resource_id": "analytics-export"},
        )
        print("\nTool result:")
        print(result.model_dump_json(indent=2, by_alias=True))

if __name__ == "__main__":
    asyncio.run(main())
