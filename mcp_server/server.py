import json
from pathlib import Path

from mcp.server import MCPServer

mcp = MCPServer("PolicyGuard Tools")

RESOURCE_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "resources.json"
)


@mcp.tool()
def get_resource_configuration(resource_id: str) -> dict:
    """Read a fictional cloud resource's configuration by its exact ID."""
    resources = json.loads(
        RESOURCE_FILE.read_text(encoding="utf-8")
    )

    if resource_id not in resources:
        return {
            "status": "not_found",
            "message": "Resource not found.",
        }

    return {
        "status": "success",
        "resource_id": resource_id,
        "configuration": resources[resource_id],
    }
