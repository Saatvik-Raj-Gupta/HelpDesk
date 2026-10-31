# Application Deployment and Runtime Troubleshooting

## Purpose
General guidance for diagnosing application startup and deployment failures. This is sample educational content, not a production deployment procedure.

## Gather the failure evidence
Record:
- Deployment environment and release identifier
- Application version and runtime version
- Exact failure time and time zone
- Startup logs and complete exception chain
- Health-check output
- Recent configuration, dependency, or infrastructure changes
- Whether the problem affects all instances or only some

Redact secrets and sensitive data before sharing logs.

## Application fails to start
Check the earliest relevant exception rather than only the final summary message. Common investigation areas include:
- Missing or invalid configuration
- Missing environment variables
- Incorrect file paths or permissions
- Port conflicts
- Unavailable external dependencies
- Runtime and library incompatibilities
- Database connectivity or migration failures

Do not assume the first visible warning caused the failure. Follow the exception chain and correlate timestamps.

## Environment variable and configuration problems
Confirm that required configuration values are present in the target environment and that their names match what the application expects.

Check whether configuration differs between local development, CI, staging, and production. Never place credentials directly in source code or commit real secret values to version control.

If a secret is missing or invalid, use the approved secret-management process to correct it. Do not print the secret value to diagnose the issue.

## Port and health-check failures
If a service fails a health check:
1. Confirm the process is running.
2. Verify the configured port and bind address.
3. Check whether the health endpoint path and expected status code are correct.
4. Inspect startup logs for delayed initialization or dependency failures.
5. Confirm network rules and routing only with relevant infrastructure evidence.

A failed health check does not by itself prove the application process has crashed.

## Safe deployment validation
Before a deployment, confirm the artifact, configuration, dependencies, test results, and rollback plan.

After deployment:
1. Check deployment status and application startup logs.
2. Verify health checks.
3. Run agreed smoke tests.
4. Check key logs and metrics for new errors.
5. Confirm the expected application version is running.
6. Follow the team's rollback or incident procedure if validation fails.

Do not restart services, roll back releases, or change production configuration solely on an AI-generated suggestion. Follow the organization's authorization and change-management process.

## Distinguishing application and infrastructure issues
An application error may be caused by code, configuration, dependencies, a network path, or an external service. Gather evidence before assigning ownership. Compare behavior across instances and environments where safe and permitted.

## When to ask for more information
Request the deployment environment, release identifier, runtime version, sanitized startup logs, health-check result, recent changes, and scope of impact.

## Limitations
This document is general guidance. It does not establish a root cause or authorize operational changes in any environment.
