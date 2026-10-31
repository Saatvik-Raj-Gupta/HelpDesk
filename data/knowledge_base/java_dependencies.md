# Java Dependency Troubleshooting

## Purpose
General diagnostic guidance for Java dependency and runtime linkage problems. This is sample educational content, not a production runbook.

## Runtime dependency conflicts
A Java application may compile successfully but fail at runtime when resolved library versions do not match the APIs expected by the calling code.

### Investigation steps
1. Read the complete exception and identify the missing class or method.
2. Inspect the resolved dependency tree using the project's build tool.
3. Check for conflicting direct and transitive dependencies.
4. Compare compile-time and runtime dependency versions.
5. Inspect the packaged artifact or runtime classpath when appropriate.
6. Reproduce the issue in a test environment before changing production dependencies.

## Common error distinctions
A `NoSuchMethodError` can indicate that a class was loaded from a library version that does not provide the method expected by the calling code.

A `ClassNotFoundException` indicates that an application or class loader could not locate a requested class.

A `NoClassDefFoundError` can indicate that a class definition needed at runtime is unavailable, or that class initialization previously failed. Review the full stack trace and underlying cause before deciding on a fix.

These errors are related to class loading or linkage but are not interchangeable. Diagnose the specific error and context.

## Maven dependency inspection
For Maven projects, `mvn dependency:tree` can show resolved dependencies and transitive relationships. Search for multiple versions of the same library and inspect dependency paths.

A dependency exclusion may be appropriate in some cases, but make exclusions only after confirming which dependency introduces the artifact and checking compatibility.

## Gradle dependency inspection
For Gradle projects, `./gradlew dependencies` displays dependency information. The `dependencyInsight` task can help explain why a version was selected for a particular configuration.

Use the correct configuration and module coordinates for the application being investigated.

## Safe remediation workflow
1. Record current dependency versions and the failing stack trace.
2. Identify the dependency path and the version actually used at runtime.
3. Check release notes or compatibility information for relevant libraries.
4. Make the smallest justified version change or exclusion.
5. Run relevant unit, integration, and startup tests.
6. Review the final dependency tree and packaged artifact.
7. Document the change and rollback approach.

Do not update unrelated dependencies simply to make an error disappear. Do not apply a dependency change directly to production without the normal review and release process.

## When to ask for more information
Request the full exception and stack trace, Java version, build tool, dependency coordinates and versions, and whether the failure occurs locally, in CI, or after deployment.

## Limitations
This document contains general troubleshooting advice. It does not identify a specific root cause without evidence from the affected application.
