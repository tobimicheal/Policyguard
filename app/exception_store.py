import sqlite3
from pathlib import Path

DATABASE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "exceptions.sqlite3"
)


def connect():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialise():
    DATABASE.parent.mkdir(parents=True, exist_ok=True)

    with connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS exception_requests (
                request_id TEXT PRIMARY KEY,
                resource_id TEXT NOT NULL,
                requester TEXT NOT NULL,
                requester_team TEXT NOT NULL,
                reason TEXT NOT NULL,
                proposed_controls TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'approved', 'rejected')),
                created_at TEXT NOT NULL,
                reviewer TEXT,
                reviewed_at TEXT
            )
        """)


if __name__ == "__main__":
    initialise()
    print("Exception request database ready.")
