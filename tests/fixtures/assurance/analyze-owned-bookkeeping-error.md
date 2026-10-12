---
expected_owner: analyze
expected_applicable: false
signals: []
---

# Analyze-owned bookkeeping error

## Shape

The planning record contradicts itself. Everything needed to prove the defect
is present in the artifacts; no knowledge of the running system is required.

```text
Case 1:  A task is marked complete while its linkage is still `pending`,
         so the record claims work that no recorded edit supports.
Case 2:  A task cites a requirement anchor that spec.md does not define.
Case 3:  A field name used in tasks.md contradicts the name the plan's own
         data model declares.
Case 4:  A task's declared prerequisite is ordered after it.
```

## Why Analyze owns it

Each case is a closed-world contradiction. Analyze can prove it by reading the
artifacts against each other and against the contracts the artifacts themselves
declare.

## Why Critic must not emit it

Emitting these as risk findings is the lane leakage this contract exists to
stop: it duplicates Analyze, inflates the finding count, and trains readers to
skim. If Critic notices one, it routes it with `owner: analyze` and moves on.

## Applicability

A pure bookkeeping correction exhibits no change-shape signal, so Critic is not
automatically applicable. That is not a prohibition — an explicit invocation
still runs, with a correspondingly narrow scope.
