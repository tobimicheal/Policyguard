# Cloud Storage Security Policy

Document ID: POL-STORAGE-001
Version: 1.0
Access: All teams
Organisation: Fictional PolicyGuard Demo Company

## Public access

Cloud storage must be private by default.

Public read access is permitted only for approved public assets,
such as website images, that contain no confidential information.

Public write access is prohibited.

## Sensitive data

Customer records, credentials, internal source code and confidential
business documents must not be stored in publicly accessible storage.

## Supplier access

Suppliers must use authenticated, least-privilege access.
Where appropriate, use short-lived signed links rather than making
the entire bucket public.

## Exceptions

An engineer may submit an exception request containing:
- The resource identifier.
- The business justification.
- Proposed compensating controls.

Requests remain pending until a separate security reviewer approves
or rejects them. The assistant cannot approve exception requests.

