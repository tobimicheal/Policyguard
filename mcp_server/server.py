import json
from pathlib import Path

from mcp.server import MCPServer

mcp = MCPServer("PolicyGuard Tools")

# Trusted local demo setting, not supplied by the LLM.
CURRENT_TEAM = "payments"

RESOURCE_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "resources.json"
)


@mcp.tool()
def get_resource_configuration(resource_id: str) -> dict:
    """Read a fictional resource if the current team may access it."""
    resources = json.loads(
        RESOURCE_FILE.read_text(encoding="utf-8")
    )

    resource = resources.get(resource_id)

    if resource is None:
        return {
            "status": "not_found",
            "message": "Resource unavailable.",
        }

    if resource.get("owner_team") != CURRENT_TEAM:
        return {
            "status": "denied",
            "message": "Current team cannot access this resource.",
        }

    return {
        "status": "success",
        "resource_id": resource_id,
        "configuration": resource,
    }
