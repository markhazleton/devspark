# Critic Command Guide

## Overview

The `/speckit.critic` command performs adversarial risk analysis on your specification, implementation plan, and task breakdown. It acts as a skeptical technical expert identifying risks, architectural flaws, implementation hazards, and failure scenarios that could prevent successful delivery.

This is a **pre-mortem** analysis tool—it imagines the project has already failed in production and explains why.

> **Note**: Unlike `/speckit.pr-review` and `/speckit.site-audit`, this command is **part of the Spec-Driven Development workflow**. It requires completed spec.md, plan.md, and tasks.md files to analyze. If you're not using the spec workflow, use `/speckit.site-audit` instead for codebase analysis.

## Prerequisites

- **Required**: Completed feature specification at `spec.md`
- **Required**: Implementation plan at `plan.md`
- **Required**: Task breakdown at `tasks.md`
- **Required**: Project constitution at `/memory/constitution.md`

## When to Use

Run `/speckit.critic` **after** `/speckit.tasks` and **before** `/speckit.implement`:

```
/speckit.specify → /speckit.plan → /speckit.tasks → /speckit.critic → /speckit.implement
```

Use this command when you want:
- A skeptical review of your implementation plan
- To identify risks the team may have overlooked
- A Go/No-Go recommendation before investing in implementation
- To catch showstoppers before they cause production issues

## Quick Start

### Basic Usage

```bash
/speckit.critic
```

### Focus on Specific Concerns

```bash
/speckit.critic Focus on scalability and database performance
/speckit.critic Review security aspects carefully
/speckit.critic Analyze async/concurrency handling
```

## Key Distinction from /speckit.analyze

| Aspect | /speckit.analyze | /speckit.critic |
|--------|------------------|-----------------|
| **Purpose** | Consistency checking | Risk identification |
| **Mindset** | Neutral validator | Adversarial skeptic |
| **Focus** | Alignment across artifacts | Production failure modes |
| **Severity** | Quality issues | Business impact |
| **Output** | Remediation suggestions | Go/No-Go recommendation |

**Summary**: 
- `/speckit.analyze` = Are the artifacts aligned and complete?
- `/speckit.critic` = What will fail in production?

## Understanding Severity Levels

### SHOWSTOPPER
```
❌ STOP - Cannot proceed to implementation
```

Will cause:
- Production outage
- Data loss
- Security breach
- Constitution violation

**Examples**:
- No authentication on protected endpoints
- Blocking I/O causing event loop starvation
- Missing connection pooling in high-traffic API
- SQL injection vectors
- Any constitution violation

### CRITICAL
```
⚠️ Fix before proceeding
```

Will cause:
- Major user-facing issues
- Costly rework post-launch
- Significant technical debt

**Examples**:
- Missing pagination on list endpoints
- No error handling strategy
- Missing health check endpoints
- No database migration strategy

### HIGH
```
⚠️ Should fix
```

Will cause:
- Technical debt accumulation
- Operational burden
- Developer frustration

**Examples**:
- Missing structured logging
- Hardcoded configuration values
- No rollback procedure
- Missing type checking

### MEDIUM
```
ℹ️ Consider addressing
```

Will cause:
- Slower development
- Minor issues in production

**Examples**:
- Suboptimal query patterns
- Missing edge case handling
- Inconsistent code style

## Risk Categories Analyzed

### Architectural Risks

#### Async/Concurrency Risks
- Blocking I/O in async contexts
- Wrong database driver (sync vs async)
- Connection pool exhaustion
- Missing timeout configuration
- Race conditions and deadlocks

#### Scale Naivety
- N+1 query patterns in ORM usage
- Missing pagination on list endpoints
- No caching strategy for hot paths
- Database schema without proper indexes
- Single-instance deployment

#### Distributed System Blindness
- Missing network partition handling
- No eventual consistency strategy
- Assuming atomic cross-service operations
- Missing circuit breakers
- No distributed tracing

### Security & Compliance Risks

#### Authentication/Authorization
- Missing or incomplete auth middleware
- No API key validation on protected endpoints
- Overly permissive CORS configuration
- Missing rate limiting
- Secrets not in vault

#### Input Validation
- Unvalidated path parameters
- Missing input sanitization
- No request size limits
- SQL injection vectors
- XSS vulnerabilities

#### Regulatory Blindness
- No GDPR consideration for user data
- Missing data retention policies
- No backup/restore procedures
- Inadequate PII handling

### Operational Hazards

#### Observability Gaps
- No structured logging strategy
- Missing metrics/monitoring
- No alerting thresholds
- Inadequate error tracking
- Missing health check endpoints

#### Deployment Risks
- Zero-downtime deployment not addressed
- Missing database migration strategy
- No rollback procedure
- Missing feature flags
- No graceful shutdown handling

#### Testing Gaps
- Missing integration test strategy
- No database fixtures
- No API contract testing
- No load/performance testing

### Implementation Traps

#### Optimistic Estimates
- Integration tasks without API issue buffer
- No time for debugging race conditions
- Missing performance optimization tasks
- Inadequate testing time

#### Missing Dependencies
- Tasks referencing undefined models
- Parallel tasks with hidden shared resources
- No infrastructure provisioning tasks
- Missing CI/CD pipeline setup

## Report Structure

The critic produces a structured risk assessment:

```markdown
## Technical Risk Assessment

**Analysis Date:** [timestamp]
**Risk Posture:** [RED/YELLOW/GREEN]
**Detected Stack:** Python + FastAPI + PostgreSQL

### Executive Summary
[2-3 sentence verdict on readiness for implementation]

### Showstopper Risks (Must Fix Before Implementation)
| ID | Category | Location | Risk Description | Mitigation Required |
|----|----------|----------|------------------|---------------------|

### Critical Risks (High Probability of Costly Issues)
| ID | Category | Location | Risk Description | Recommended Action |
|----|----------|----------|------------------|-------------------|

### Framework-Specific Red Flags
[Checklist based on detected technology stack]

### Missing Critical Tasks
- Observability: [list]
- Operations: [list]
- Testing: [list]
- Security: [list]

### Go/No-Go Recommendation
[ ] STOP - Showstoppers present
[ ] CONDITIONAL - Fix critical risks first
[ ] PROCEED WITH CAUTION - Document acknowledged risks
```

## Framework-Specific Analysis

The critic applies stack-specific knowledge:

### Python + FastAPI
- Blocking I/O in async endpoints?
- Using sync psycopg2 instead of asyncpg?
- Missing Pydantic validation constraints?
- Debug mode in production config?

### Node.js + Express
- Unhandled promise rejections?
- Missing async error middleware?
- Callback hell without structure?
- Missing TypeScript strict mode?

### Go + Gin/Fiber
- Goroutine leaks?
- Missing context cancellation?
- Improper error handling?
- Missing structured logging?

### Java + Spring Boot
- Missing @Transactional boundaries?
- N+1 queries in JPA/Hibernate?
- No connection pool tuning?
- Missing actuator endpoints?

## Common Workflows

### Workflow 1: Standard Development

```bash
# After completing plan and tasks
/speckit.critic

# If showstoppers found:
# - Fix issues in plan.md
# - Regenerate tasks.md
# - Re-run critic

/speckit.critic

# When clean, proceed
/speckit.implement
```

### Workflow 2: Focus on Specific Concerns

```bash
# Security-focused review
/speckit.critic Pay special attention to authentication and authorization

# Performance-focused review
/speckit.critic Focus on database performance and caching

# Scalability review
/speckit.critic Analyze for high-traffic scenarios
```

### Workflow 3: Team Review

```bash
# Generate critic report for team discussion
/speckit.critic

# Share findings in team meeting
# Discuss and prioritize risks
# Update plan based on team decisions

# Re-run to verify improvements
/speckit.critic
```

## Interpreting the Go/No-Go Recommendation

### STOP
Showstoppers are present. Implementation will likely fail or cause serious issues.

**Required Actions**:
1. Address every showstopper finding
2. Update plan.md with fixes
3. Regenerate tasks.md
4. Re-run `/speckit.critic`
5. Only proceed when clean

### CONDITIONAL
Critical risks exist that should be addressed.

**Recommended Actions**:
1. Fix critical risks if time permits
2. If proceeding, document each accepted risk
3. Add monitoring/alerting for risk areas
4. Plan mitigation tasks post-MVP

### PROCEED WITH CAUTION
No showstoppers, but some concerns exist.

**Checklist**:
- [ ] Acknowledge documented risks
- [ ] Add mitigation tasks to backlog
- [ ] Set up monitoring for risk areas
- [ ] Plan for technical debt paydown

## Best Practices

### 1. Run Before Every Implementation
Never skip the critic review. Hidden risks compound quickly.

### 2. Don't Ignore Showstoppers
Showstoppers are non-negotiable. Fix them before proceeding.

### 3. Document Accepted Risks
If you proceed with known risks, document them explicitly.

### 4. Use Focus Arguments
When concerned about specific areas, use arguments to focus the analysis.

### 5. Combine with /speckit.analyze
Run both commands for comprehensive validation:
```bash
/speckit.analyze  # Check consistency
/speckit.critic   # Check risks
```

### 6. Learn from Findings
Use recurring findings to improve your constitution and planning process.

## Comparison to Other Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/speckit.analyze` | Consistency check | After tasks, before critic |
| `/speckit.critic` | Risk analysis | After tasks, before implement |
| `/speckit.site-audit` | Codebase audit | After implementation, ongoing |
| `/speckit.pr-review` | PR review | During code review |

## Troubleshooting

### "Required file missing"

**Problem**: spec.md, plan.md, or tasks.md not found

**Solution**: Run the prerequisite commands first:
```bash
/speckit.specify [requirements]
/speckit.plan [tech stack]
/speckit.tasks
/speckit.critic
```

### "Constitution missing"

**Problem**: `/memory/constitution.md` not found

**Solution**:
```bash
/speckit.constitution Create project principles
```

### Too many showstoppers

**Problem**: Report has many showstoppers, feels overwhelming

**Mitigation**:
1. Prioritize by business impact
2. Address most critical first
3. Consider phased approach
4. Simplify the plan if over-engineered

### Disagree with finding

**Problem**: A finding seems incorrect for your context

**Actions**:
1. Document why you disagree
2. If proceeding, note as accepted risk
3. Set up monitoring for that area
4. Consider if constitution needs updating

## Support

If you encounter issues:
- Check [Troubleshooting](#troubleshooting) section above
- Review [Spec Kit Issues](https://github.com/MarkHazleton/spec-kit/issues)

---

*Part of the Spec Kit - Spec-Driven Development Toolkit*  
*For more information: https://github.com/MarkHazleton/spec-kit*
