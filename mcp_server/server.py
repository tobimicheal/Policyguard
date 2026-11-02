import json
from datetime import datetime, timezone
from pathlib import Path

from mcp.server import MCPServer

mcp = MCPServer("PolicyGuard Tools")

# Fixed local demo identity, not supplied by the model.
CURRENT_TEAM = "payments"

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESOURCE_FILE = PROJECT_ROOT / "data" / "resources.json"
AUDIT_FILE = PROJECT_ROOT / "logs" / "audit.jsonl"


def record_lookup(resource_id, outcome):
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": "local-demo-payments-engineer",
        "team": CURRENT_TEAM,
        "tool": "get_resource_configuration",
        "resource_id": resource_id,
        "outcome": outcome,
    }

    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with AUDIT_FILE.open("a", encoding="utf-8") as log:
        log.write(json.dumps(event) + "\n")


@mcp.tool()
def get_resource_configuration(resource_id: str) -> dict:
    """Read a fictional resource if the current team may access it."""
    resources = json.loads(
        RESOURCE_FILE.read_text(encoding="utf-8")
    )

    resource = resources.get(resource_id)

    if resource is None:
        record_lookup(resource_id, "not_found")
        return {
            "status": "not_found",
            "message": "Resource unavailable.",
        }

    if resource.get("owner_team") != CURRENT_TEAM:
        record_lookup(resource_id, "denied")
        return {
            "status": "denied",
            "message": "Current team cannot access this resource.",
        }

    record_lookup(resource_id, "success")
    return {
        "status": "success",
        "resource_id": resource_id,
        "configuration": resource,
    }
