# Application Constitution: Runtime API A

## Application-Specific Rules

- All runtime API endpoints MUST respond within 200ms at p95
- Runtime API A MUST maintain backward compatibility for 2 major versions
- Circuit breakers are MANDATORY for all external service calls
- Request tracing headers MUST be propagated through all middleware
