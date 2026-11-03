import asyncio
import json
from contextlib import closing

from mcp import Client
from mcp_server.server import mcp
from app.exception_store import connect, initialise


def request_count():
    with closing(connect()) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM exception_requests"
        ).fetchone()[0]


async def call_request(client, arguments):
    result = await client.call_tool(
        "create_exception_request",
        arguments,
    )

    assert not result.is_error, "Unexpected MCP tool error."

    text = "\n".join(
        block.text
        for block in result.content
        if block.type == "text"
    )
    return json.loads(text)


async def main():
    initialise()
    before = request_count()

    async with Client(mcp) as client:
        available = await client.list_tools()
        names = {tool.name for tool in available.tools}

        assert names == {
            "get_resource_configuration",
            "create_exception_request",
        }, f"Unexpected tool list: {names}"

        print("PASS: Only inspection and request-creation tools exposed.")

        creation_tool = next(
            tool for tool in available.tools
            if tool.name == "create_exception_request"
        )
        fields = set(
            creation_tool.input_schema.get("properties", {})
        )

        assert fields == {
            "resource_id",
            "reason",
            "proposed_controls",
        }, f"Unexpected request fields: {fields}"

        print("PASS: No approval, reviewer or identity input fields exposed.")

        denied = await call_request(client, {
            "resource_id": "analytics-export",
            "reason": "Fictional cross-team request test.",
            "proposed_controls": "Authenticated access.",
        })
        assert denied["status"] == "denied", denied
        assert "request_id" not in denied, denied

        print("PASS: Cross-team exception request denied.")

        invalid = await call_request(client, {
            "resource_id": "payments-supplier-upload",
            "reason": "",
            "proposed_controls": "Authenticated access.",
        })
        assert invalid["status"] == "invalid", invalid
        assert "request_id" not in invalid, invalid

        print("PASS: Empty justification rejected.")

        missing = await call_request(client, {
            "resource_id": "nonexistent-bucket",
            "reason": "Fictional missing-resource test.",
            "proposed_controls": "Authenticated access.",
        })
        assert missing["status"] == "not_found", missing
        assert "request_id" not in missing, missing

        print("PASS: Unknown resource rejected.")

    assert request_count() == before, (
        "An unsuccessful request unexpectedly created a database record."
    )
    print("PASS: No new exception records created.")
    print("\nAll exception security checks passed.")


if __name__ == "__main__":
    asyncio.run(main())
