from __future__ import annotations

SAMPLE_TICKETS = [
    {
        "name": "Java dependency missing class",
        "text": "After upgrading a Java dependency, the application fails to start because of a missing class.",
    },
    {
        "name": "API timeout after deploy",
        "text": "The API gateway times out for all requests after our latest deployment. We see intermittent 502 errors and startup still appears healthy.",
    },
    {
        "name": "Kubernetes pod crash loop",
        "text": "The pod enters a crash loop in production after a new image rollout. The container exits immediately and the service is unavailable.",
    },
    {
        "name": "Database connection pool exhaustion",
        "text": "Database connections are exhausted and queries are timing out in the application after the weekend migration.",
    },
    {
        "name": "401 after token refresh",
        "text": "Users receive 401 Unauthorized after token refresh. The session is valid but the API rejects the new token.",
    },
]
