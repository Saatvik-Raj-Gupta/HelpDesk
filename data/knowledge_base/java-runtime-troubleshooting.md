# Java dependency upgrade troubleshooting

## Symptom

After upgrading a Java dependency, the application fails to start because of a missing class.

## Likely causes

- The runtime classpath does not include the new dependency.
- A transitive dependency was removed or renamed by the upgraded package.
- The application is running with an older JDK than the dependency expects.

## Recommended checks

1. Review the exact dependency version diff.
2. Run the app with a dependency tree or classpath inspection tool.
3. Confirm that the missing class is present in the packaged artifact.
4. Verify the Java runtime version against the dependency requirements.

## Mitigation

Keep the dependency graph consistent and rebuild the application before redeploying. If the class is truly missing, restore the compatible dependency version or update the runtime configuration to match the supported Java version.
