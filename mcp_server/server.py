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
@mcp.tool()
def create_exception_request(
    resource_id: str,
    reason: str,
    proposed_controls: str,
) -> dict:
    """Create a pending exception for an accessible resource. Cannot approve."""
    from contextlib import closing
    from uuid import uuid4

    from app.exception_store import connect, initialise

    fields = {
        "resource_id": (resource_id, 100),
        "reason": (reason, 2000),
        "proposed_controls": (proposed_controls, 2000),
    }

    for field, (value, maximum) in fields.items():
        if not value.strip() or len(value) > maximum:
            return {
                "status": "invalid",
                "message": f"{field} must contain 1–{maximum} characters.",
            }

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

    initialise()
    request_id = str(uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    with closing(connect()) as connection:
        with connection:
            connection.execute(
                """
                INSERT INTO exception_requests (
                    request_id,
                    resource_id,
                    requester,
                    requester_team,
                    reason,
                    proposed_controls,
                    status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    resource_id,
                    "local-demo-payments-engineer",
                    CURRENT_TEAM,
                    reason.strip(),
                    proposed_controls.strip(),
                    "pending",
                    created_at,
                ),
            )

    return {
        "status": "success",
        "request_id": request_id,
        "resource_id": resource_id,
        "request_status": "pending",
        "message": "Separate reviewer approval is required.",
    }
