# Test Constitution — fixture-20-app

## NON-NEGOTIABLE

1. **All services MUST expose a health-check endpoint** — Every deployable service must implement `/healthz` returning HTTP 200 when healthy.
2. **No direct database access from web-app services** — Web-app services must call runtime-api services; they must never connect to a database directly.
3. **Every public API change requires a spec update** — Any modification to a public-facing API must be reflected in the corresponding spec.md before merge.
4. **Shared dependencies must be pinned to exact versions** — All cross-service shared packages must use exact version pins, never ranges.
