---
fixture_kind: route-escalation
---

# Quickfix route escalation

## Stays a quickfix

A null dereference in one function, fixed in one file, pinned by one test.
No new contract, no new dependency, no boundary crossed, no persisted shape
changed. Nothing is surfaced; the route's assumptions still hold, and a
prompt that escalated here would train the developer to dismiss escalation.

## Escalation surfaced — new architectural contract

The fix turns out to require an interface that did not previously exist, and
a second subsystem must now depend on it.

```text
Route Escalation Check

This change has outgrown the assumptions of the quickfix route.
Signal: new architectural contract — the fix introduces an interface that a
        second subsystem must now depend on

Continue as quickfix, or promote to a full spec?
```

## Escalation surfaced — trust boundary

The root cause is that an input crosses a trust boundary unvalidated.
Correcting it is small in lines and large in consequence, which is exactly
the case effort-based warnings miss.

## Who decides

The framework surfaces; the developer chooses. Either answer is legitimate —
a deliberate "continue as quickfix" is a different fact from an unexamined
one, and recording which it was is the point. The route is chosen rather
than inherited.
