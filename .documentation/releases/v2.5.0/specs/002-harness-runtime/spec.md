# Feature Specification: Sample Harness Workflow

**Status**: Complete

This file is a fixture used by `sample.harness.yaml` to demonstrate the
DevSpark harness runtime. It satisfies the harness validation rules
(`spec-heading` and `spec-has-rationale`) so the sample can run end-to-end.

## Rationale Summary

The harness runtime lets you describe a multi-step AI workflow in YAML and
execute it via `devspark harness run`. This spec stub exists so that
`sample.harness.yaml` (which ships with the repository) works as a runnable
demo without requiring a live feature spec to be in progress.

## Context

See `.documentation/harness-engineering.md` for full harness documentation.
See `.documentation/releases/v2.1.0/specs/002-harness-runtime/spec.md` for
the completed Harness Runtime feature specification.
See `CHANGELOG.md` (v2.1.0, "Tiered Workflow Engine Foundation") for the
released changelog entry covering the completed harness runtime work.
