# Authentication and Authorization Troubleshooting

## Purpose
General guidance for diagnosing API authentication and authorization failures. This is sample educational content, not an identity-provider-specific security policy.

## Authentication versus authorization
Authentication establishes or verifies an identity. Authorization determines whether that identity is allowed to perform a requested action.

A request can be authenticated successfully and still be denied because the identity lacks the required permission.

## Diagnosing 401 Unauthorized
Check:
1. Whether the request includes the expected authentication header or credential mechanism.
2. Whether the token is expired, malformed, revoked, or issued for a different audience.
3. Whether the token issuer and signature are accepted by the service.
4. Whether the client is using the correct environment and identity provider.
5. Whether server clock skew could affect time-based token validation.

Use approved tools to inspect token claims. Do not paste live access tokens or secrets into chat tools, source code, logs, or public issue trackers.

## Diagnosing 403 Forbidden
Check:
1. Which identity the service authenticated.
2. Whether the identity has the required role, scope, group membership, or resource permission.
3. Whether a policy, tenant boundary, or resource-level rule blocks access.
4. Whether the request targets the correct resource and environment.
5. Whether the permission change has propagated, if the system documents propagation delays.

Refreshing a token alone may not resolve a genuine permission denial.

## Common client configuration mistakes
- Using a token from a different environment.
- Sending a token in the wrong header or format.
- Requesting scopes that do not cover the required operation.
- Using a client ID or service identity that lacks permission.
- Confusing authentication configuration with authorization policy.
- Accidentally removing required headers when constructing a request.

Confirm expected configuration from the service's official documentation or administrator.

## Safe debugging practices
- Redact tokens, passwords, cookies, client secrets, and personal information.
- Use a non-production test identity where possible.
- Avoid weakening access controls to make a test pass.
- Do not grant broad permissions without a documented need and authorized review.
- Record the sanitized error, timestamp, target endpoint, and correlation ID where available.

## Suggested diagnostic sequence
1. Capture the sanitized request and status code.
2. Confirm which identity and environment the client is using.
3. Distinguish 401 authentication failure from 403 authorization denial.
4. Check token validity and relevant claims using approved methods.
5. Verify permissions with the service owner or administrator.
6. Retest with an authorized identity and minimal required permissions.

## When to ask for more information
Request the status code, sanitized response body, authentication method, target environment, expected permission, and whether the same identity can access other permitted endpoints.

## Limitations
Authentication behavior varies by protocol, identity provider, and application. This document is generic guidance and does not replace the service's actual security configuration or access policy.
