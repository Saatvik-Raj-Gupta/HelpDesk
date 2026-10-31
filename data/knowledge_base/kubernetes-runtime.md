# Kubernetes runtime issues

## Symptom

Pods fail to become ready because the application container exits immediately after startup.

## Likely causes

- A required environment variable is missing.
- The application cannot bind to the expected port.
- The container image is built for the wrong architecture or uses an incompatible Java runtime.

## Recommended checks

1. Inspect the pod logs for the first startup failure.
2. Confirm container environment variables and secret mounts.
3. Verify the readiness and liveness probes are aligned with the startup path.
4. Review resource limits and memory pressure in the node.

## Mitigation

Fix the startup configuration before redeploying. If the application exits instantly, ensure the entrypoint, health probes, and environment variables are consistent with the runtime image.
