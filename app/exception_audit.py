from datetime import datetime, timezone
from uuid import uuid4


def record_event(connection, request_id, actor, action, outcome):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS exception_audit (
            event_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            request_id TEXT NOT NULL,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            outcome TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        INSERT INTO exception_audit (
            event_id,
            timestamp,
            request_id,
            actor,
            action,
            outcome
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            str(uuid4()),
            datetime.now(timezone.utc).isoformat(),
            request_id,
            actor,
            action,
            outcome,
        ),
    )
