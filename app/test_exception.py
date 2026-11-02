import asyncio
import json
from contextlib import closing

from mcp import Client
from mcp_server.server import mcp
from app.exception_store import connect


async def main():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "create_exception_request",
            {
                "resource_id": "payments-supplier-upload",
                "reason": "Fictional demo: supplier needs temporary access.",
                "proposed_controls": (
                    "Authenticated uploads, least privilege, "
                    "and access removed after the transfer."
                ),
            },
        )

        assert not result.is_error, "MCP tool returned an error."

        text = "\n".join(
            block.text
            for block in result.content
            if block.type == "text"
        )
        data = json.loads(text)

        assert data["status"] == "success", data
        assert data["request_status"] == "pending", data

        with closing(connect()) as connection:
            row = connection.execute(
                """
                SELECT resource_id, requester_team, status, reviewer
                FROM exception_requests
                WHERE request_id = ?
                """,
                (data["request_id"],),
            ).fetchone()

        assert row is not None, "Request was not stored."
        assert row["resource_id"] == "payments-supplier-upload"
        assert row["requester_team"] == "payments"
        assert row["status"] == "pending"
        assert row["reviewer"] is None

        print("PASS: Exception created and stored as pending.")
        print("PASS: No reviewer assigned.")
        print(f"Request ID: {data['request_id']}")


if __name__ == "__main__":
    asyncio.run(main())
