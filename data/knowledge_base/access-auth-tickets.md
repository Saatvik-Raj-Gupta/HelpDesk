# Access and authentication troubleshooting

## Symptoms

Users report login failures, expired sessions, or unauthorized requests after an identity provider change.

## Likely causes

- The application is still using the old OAuth issuer URL.
- The configured audience or client ID no longer matches the provider.
- Tokens are being cached beyond their expiration window.

## Recommended checks

1. Compare the expected issuer, audience, and client ID values.
2. Review the identity provider logs for rejected token exchange requests.
3. Confirm the front-end and back-end are using the same session configuration.
4. Validate token expiration and refresh flow in the browser or API client.

## Mitigation

Update the provider configuration and re-test with a valid, non-expired token. Keep the authentication and session settings aligned across the app and the identity provider.
