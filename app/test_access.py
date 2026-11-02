import asyncio
import json

from mcp import Client
from mcp_server.server import mcp


async def check_resource(client, resource_id, expected_status):
    result = await client.call_tool(
        "get_resource_configuration",
        {"resource_id": resource_id},
    )

    assert not result.is_error, "Unexpected MCP tool error"

    text = "\n".join(
        block.text
        for block in result.content
        if block.type == "text"
    )
    data = json.loads(text)

    assert data["status"] == expected_status, (
        f"{resource_id}: expected {expected_status}, "
        f"received {data['status']}"
    )

    if expected_status == "success":
        assert data["resource_id"] == resource_id
        assert data["configuration"]["owner_team"] == "payments"
    else:
        assert "configuration" not in data, (
            "Denied or missing resource leaked configuration"
        )

    print(f"PASS: {resource_id} -> {expected_status}")


async def main():
    async with Client(mcp) as client:
        await check_resource(
            client, "payments-supplier-upload", "success"
        )
        await check_resource(
            client, "analytics-export", "denied"
        )
        await check_resource(
            client, "nonexistent-bucket", "not_found"
        )

    print("\nAll 3 access-control tests passed.")


if __name__ == "__main__":
    asyncio.run(main())
