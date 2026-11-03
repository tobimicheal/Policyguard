import argparse
from contextlib import closing
from datetime import datetime, timezone

from app.exception_audit import record_event
from app.exception_store import connect, initialise


REVIEWER = "local-demo-security-reviewer"


def main():
    parser = argparse.ArgumentParser(
        description="Human review of fictional exception requests."
    )
    parser.add_argument("request_id")
    args = parser.parse_args()

    initialise()

    with closing(connect()) as connection:
        row = connection.execute(
            "SELECT * FROM exception_requests WHERE request_id = ?",
            (args.request_id,),
        ).fetchone()

    if row is None:
        print("Request not found.")
        return

    if row["status"] != "pending":
        print(f"Request already reviewed: {row['status']}")
        return

    if row["requester"] == REVIEWER:
        print("Self-approval is not permitted.")
        return

    print("\nFICTIONAL LOCAL DEMO — SECURITY REVIEW")
    print(f"Request ID: {row['request_id']}")
    print(f"Resource: {row['resource_id']}")
    print(f"Requester: {row['requester']}")
    print(f"Team: {row['requester_team']}")
    print(f"Created: {row['created_at']}")
    print(f"\nReason:\n{row['reason']}")
    print(f"\nProposed controls:\n{row['proposed_controls']}")
    print("\nApproval records a decision only; it changes no resources.")

    decision = input(
        "\nType approve, reject, or cancel: "
    ).strip().lower()

    if decision not in {"approve", "reject"}:
        print("Cancelled. No decision recorded.")
        return

    confirmation = input(
        "Confirm by typing the full request ID: "
    ).strip()

    if confirmation != args.request_id:
        print("Confirmation did not match. No decision recorded.")
        return

    status = "approved" if decision == "approve" else "rejected"
    reviewed_at = datetime.now(timezone.utc).isoformat()

    # Save the decision and audit event in the same transaction.
    # Only update the exact pending request shown to the reviewer.
    with closing(connect()) as connection:
        with connection:
            cursor = connection.execute(
                """
                UPDATE exception_requests
                SET status = ?, reviewer = ?, reviewed_at = ?
                WHERE request_id = ?
                  AND status = 'pending'
                  AND resource_id = ?
                  AND requester = ?
                  AND requester_team = ?
                  AND reason = ?
                  AND proposed_controls = ?
                  AND created_at = ?
                  AND reviewer IS NULL
                  AND reviewed_at IS NULL
                """,
                (
                    status,
                    REVIEWER,
                    reviewed_at,
                    row["request_id"],
                    row["resource_id"],
                    row["requester"],
                    row["requester_team"],
                    row["reason"],
                    row["proposed_controls"],
                    row["created_at"],
                ),
            )

            if cursor.rowcount != 1:
                print("Request changed or was reviewed. Reopen it.")
                return

            record_event(
                connection,
                row["request_id"],
                REVIEWER,
                "review_exception",
                status,
            )

    print(f"\nDecision recorded: {status}")
    print(f"Reviewer: {REVIEWER}")


if __name__ == "__main__":
    main()
