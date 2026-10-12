---
id: autonomy-execution-model
type: architecture
title: "Autonomy Execution Model"
appliesTo:
  - templates/commands/**
---

<!-- markdownlint-disable MD025 -->

# Autonomy Execution Model

Autonomy changes how known choices and guardrail breaches are handled; it never weakens constitution
requirements, required verification, or delivery evidence.

## Levels and Overrides

Assisted execution pauses at declared review points. Autonomous execution may select a prompt's
stated recommended option and record that selection, but cannot auto-bypass constitution violations,
showstoppers, explicit manual gates, or failed verification.

## Guardrails and Remediation

File-count, changed-line, and restricted-path guardrails evaluate each workflow step. Autonomous mode
hard-fails a breach; assisted mode pauses. A finding is evidence, not work: Judge dispositions decide
which planning findings become tasks, the legacy merge without a Judge artifact selects only
genuinely blocking compatibility work under autonomy (never Medium or Low), and PR remediation
selects only open blocking findings. Remediation beyond the approved Plan's shape needs Judge or
explicit human authority. Implementation resolves findings only when the associated change and
verification complete.

## Full-Cycle Behavior

A full-cycle workflow chains authoring, implementation, and downstream stages without mandatory
mid-run pauses only when its workflow definition omits pause markers and relies on guardrails.
Revalidation telemetry records checks; it must not be represented as a repeated invocation unless the
runner actually executes that invocation.
