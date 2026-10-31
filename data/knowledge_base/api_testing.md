# REST API Testing Troubleshooting

## Purpose
General guidance for diagnosing REST API test failures. This is sample educational content, not a system-specific API contract.

## Start with the request and response
For a failing request, capture:
- HTTP method and endpoint path
- Request headers, with secrets and tokens redacted
- Request body, with personal or confidential data removed
- Response status code and response body
- Relevant request or correlation ID, if available
- Environment and test data used

Compare the request with the API's current specification and expected test behavior.

## Common HTTP status codes
### 400 Bad Request
The server could not process the request because it was invalid or malformed. Check JSON syntax, required fields, field types, validation constraints, and parameter formats.

### 401 Unauthorized
The request is missing valid authentication credentials or the credentials were not accepted. Check whether the token is present, correctly formatted, unexpired, and intended for the target environment. Do not paste secrets into logs or bug reports.

### 403 Forbidden
The server understood the request but refused authorization. Check the authenticated identity, assigned roles or scopes, and endpoint access policy. A 403 is not necessarily fixed by obtaining a new token.

### 404 Not Found
Check the base URL, endpoint path, API version, resource identifier, and whether the resource is available in the selected environment. Some systems intentionally use 404 to avoid revealing whether a resource exists.

### 429 Too Many Requests
The service may be applying a rate limit. Check response headers and documented retry behavior. Use bounded retries and backoff only when appropriate; do not retry indefinitely.

### 5xx Server Errors
The server or an upstream dependency failed to process the request. Capture response details and a correlation ID, then consult service logs or the service owner. Avoid repeatedly retrying requests that may cause side effects.

## Newman and Postman collection checks
When a Postman collection is executed with Newman:
1. Confirm the intended collection and environment are selected.
2. Check required environment variables and collection variables.
3. Verify the base URL and authentication configuration.
4. Inspect assertion failures separately from transport or setup failures.
5. Check whether test data and endpoint schemas are current.
6. Save command output and exit status as test evidence.

Do not assume a collection is correct just because it runs. If its expected response schema or assertions are outdated, compare them with the current API specification and confirm changes with the API owner.

## Swagger / OpenAPI specification issues
An OpenAPI document can become outdated as endpoints, request fields, response schemas, or authentication requirements change.

When a test collection disagrees with a specification:
1. Identify the exact endpoint and method.
2. Compare the specification with the observed request and response.
3. Determine which source is authoritative for the current environment.
4. Record mismatches and confirm intended behavior with the API owner.
5. Update test inputs or assertions only after expected behavior is verified.

Do not automatically treat observed behavior as correct or rewrite test expectations solely to make tests pass.

## Safe handling of evidence
Before sharing request logs or generating evidence reports:
- Redact tokens, passwords, API keys, cookies, and personal data.
- Include timestamps and test names where useful.
- Distinguish passed assertions from failed assertions.
- Keep enough context to reproduce the issue without exposing secrets.

## When to ask for more information
Request the endpoint path and method, status code, sanitized request and response, test assertion output, environment, and relevant OpenAPI version.

## Limitations
This document gives generic API-testing guidance. It does not define the behavior of a particular service or prove that a failing test is a product defect.
