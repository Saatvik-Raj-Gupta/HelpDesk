# Database Troubleshooting

## Connection pool exhaustion

Connection pool exhaustion can cause application requests and SQL queries to time out. Confirm the configured pool size, active connection count, connection lifetime, and whether connections are returned after each request.

## Investigation steps

1. Capture the database error and the time window of the failures.
2. Check active connections and compare them with the configured pool limit.
3. Review slow queries, blocked sessions, and recent schema or migration changes.
4. Confirm that application code closes or returns connections after use.
5. Reproduce the issue in a test environment before changing pool or database settings.

## Migration-related checks

Review the migration logs and verify that the application and database schema versions are compatible. Test queries against the migrated schema and inspect indexes or locks when query latency increases.

This document provides general diagnostic guidance. It does not identify a specific root cause without application and database evidence.
