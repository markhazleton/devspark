# Contract: HarnessSpec YAML Format

This file is a sample prompt used by `sample.harness.yaml` to demonstrate
the `prompt_file` field of an `agent_task` step.

## Required Top-Level Fields

- `apiVersion: devspark.ai/v1`
- `kind: HarnessSpec`
- `name: <string>`
- `steps: <list>`

## Step Types

- `agent_task` — runs an AI agent with a prompt and inputs/outputs
- `validation` — runs validators without an agent
- `human_gate` — pauses for human review
