# Harness Engineering and Agent Development Patterns for DevSpark

<!-- markdownlint-disable MD032 MD036 -->

## Executive summary

Harness engineering is emerging as the next practical layer after prompt and context engineering: instead of optimizing *only* what you say to a model (prompts) or what information you feed it (context), you optimize the *entire operating environment* in which agents work—tooling, constraints, validation, feedback loops, traces, governance, and durable, repo-native knowledge artifacts. citeturn32view3turn32view4turn32view5turn32view1turn27view0

Two strong, converging themes show up across recent primary sources:

First, “agent performance” is often bottlenecked less by model intelligence and more by underspecified environments: missing abstractions, missing structure, missing tools, and missing “systems of record” that agents can actually access. entity["company","OpenAI","ai research company"]’s harness engineering write-up explicitly describes early progress being slow because “the environment was underspecified” and the agent “lacked the tools, abstractions, and internal structure required to make progress.” citeturn32view3

Second, reliability comes from building *outer harnesses* that (a) increase the probability an agent succeeds on the first pass and (b) create feedback loops that self-correct before humans must review. entity["people","Martin Fowler","software engineer"] frames this outer harness as an engineering practice whose purpose is reduced review toil, higher system quality, and fewer wasted tokens. citeturn32view1

DevSpark is already aligned with these principles: it explicitly centers “just markdown files,” repo-local prompts/templates/scripts, and a centralized, agent-agnostic registry for agent-specific integration metadata. citeturn28view0turn7view0 The key opportunity is to add an **optional, additive harness runtime** to the existing CLI—one that can execute/validate lifecycle steps, emit structured traces, and close the loop with deterministic and rubric-based validation—without replacing DevSpark’s existing prompt-first workflow.

## Definitions and distinctions

### Prompt engineering

Prompt engineering is the practice of writing effective instructions so the model consistently produces output that meets requirements. citeturn22search0 This stage is dominated by instruction clarity, output contracts, examples/few-shot patterns, and “shape-of-output” control (schemas, formats).

**Primary responsibility:** write the right words, structure, and constraints.

**Primary artifact:** prompts (templates, system/developer messages), usually as text/Markdown. citeturn22search0

### Context engineering

Context engineering generalizes prompt engineering to the full set of tokens available to the model at inference time, including instructions, tools, external data, retrieved documents, and message history. entity["company","Anthropic","ai research company"] defines context engineering as strategies for curating and maintaining the optimal set of tokens during inference, beyond “the prompt” alone. citeturn24view3

This stage includes retrieval-augmented methods (RAG) that retrieve relevant information from a knowledge base and append it to the prompt, which was formalized early in RAG research. citeturn23search0 It also includes pragmatic retrieval improvements (e.g., contextual retrieval) that target fewer failed retrievals and better downstream responses. citeturn29view3

**Primary responsibility:** decide what the model sees *right now*, and keep that context coherent over time.

**Primary artifacts:** retrieval pipelines, memory policies, context compaction/summarization rules, and in-repo “maps” that point to deeper sources of truth. citeturn24view3turn32view5

### Agent engineering

Agent engineering focuses on multi-turn, tool-using systems that can execute actions and adapt based on intermediate results. A foundational research pattern is ReAct: interleaving reasoning traces and actions to interface with external environments, improving factuality and success in interactive tasks. citeturn22search2

Modern agent systems institutionalize “agentic loops” (gather context → take action → verify), with tool calls feeding results back into subsequent turns. Claude Code documentation describes this loop explicitly and frames the harness as what makes the system agentic (tools + context management + execution environment). citeturn29view1turn29view2

Agent research also emphasizes:
- Tool use competence (e.g., Toolformer’s self-supervised approach to deciding *which* tools to call and *when*). citeturn23search2  
- Learning from feedback without weight updates (e.g., Reflexion using linguistic feedback in an episodic memory). citeturn23search3

**Primary responsibility:** design the loop (planning, acting, verifying), tool interfaces, safety boundaries, and memory behavior.

**Primary artifacts:** tool specs, agent-loop orchestrators, tool routers, memory stores, and evaluation harnesses.

### Harness engineering

Harness engineering pushes beyond building an agent to engineering the operational system around it: scaffolding, repo structure, constraints, validation gates, self-review loops, telemetry, and merging/release practices aligned to agent throughput.

OpenAI’s harness engineering article highlights multiple core harness concerns:
- Engineers shift toward “systems, scaffolding, and leverage.” citeturn32view3  
- Agents can only use what’s accessible in-context; repo-local, versioned artifacts become crucial. citeturn32view4  
- Driving work to completion becomes an iterative loop: run agent → open PR → self-review → request other reviews → respond to feedback → repeat. citeturn32view5  
- Architectural coherence needs mechanically enforced invariants, not just docs. citeturn32view6  
- Merge philosophy changes when agent throughput far exceeds human attention. citeturn32view7

Martin Fowler’s “outer harness” framing emphasizes feedforward controls (preconditions) and feedback controls (sensing/correction). citeturn32view1

A very concrete research definition appears in the 2026 “Building Effective AI Coding Agents for the Terminal” paper (OpenDev): it defines a harness as the runtime orchestration layer wrapping the reasoning loop and coordinating tool execution, context management, safety enforcement, and session persistence—distinct from scaffolding, which assembles the agent before the first prompt. citeturn30view0

**Primary responsibility:** make agent work *repeatable, verifiable, observable, and governable* in real repos and teams.

**Primary artifacts:** harness specs (steps, validations, retries), durable event logs/traces, repo-native knowledge bases, structural tests/linters, safety policies.

### Responsibility and artifact comparison

| Stage | Primary goal | Typical responsibilities | Typical artifacts | Failure modes if skipped |
|---|---|---|---|---|
| Prompt engineering | Instruction correctness | Output contracts, constraint language, examples | Prompt templates, system/dev messages citeturn22search0 | Ambiguous output, wrong format, inconsistent behavior |
| Context engineering | Right information at the right time | Retrieval, memory, compaction, “map not manual” organization | RAG pipelines, in-repo docs/maps, memory policies citeturn24view3turn32view5turn23search0 | Hallucinations, missed repo knowledge, context bloat |
| Agent engineering | Multi-turn action in an environment | Tool routing, planning/acting loops, tool design | Tool specs, agent loops, subagents, safety gating citeturn22search2turn29view2turn23search2 | Thrashing, unsafe actions, tool misuse, nondeterministic drift |
| Harness engineering | System-level reliability and throughput | Scaffolding + runtime orchestration + validation + telemetry + governance | Harness specs, validators, traces/events, structural tests, release gates citeturn32view3turn32view6turn27view0turn32view1turn30view0 | “Underspecified environment,” untestable agent changes, brittle workflows, opaque failures |

## Practical patterns and best practices for Harness Engineering

### A practical mental model: map, loop, and invariants

OpenAI explicitly reports that agents need “a map,” with repo knowledge treated as a structured system of record rather than a giant monolithic instruction wall. citeturn32view5 This maps directly onto DevSpark’s “just markdown files” posture and suggests a harness goal: **make repo knowledge legible and navigable to agents** (and humans).

In practice, harness engineering patterns cluster into three concerns:

**Map:** curate repo-local “sources of truth” and index them so the agent can find them (e.g., README-level table-of-contents patterns; DevSpark already uses heavy Markdown + structured directories). citeturn28view0turn32view5

**Loop:** formalize iterative improvement cycles with explicit checkpoints (self-review, tests, validations, PR feedback). citeturn32view5turn32view1

**Invariants:** enforce architectural and workflow constraints mechanically (linters, structural tests, schema validation) rather than hoping documentation prevents drift. citeturn32view6turn30view0

### Agent-agnostic adapters

DevSpark already implements a “centralized agent registry” concept as a JSON file describing where agent shims live and how to format them. The registry shows keys like `copilot`, `claude`, `gemini`, `cursor-agent`, `codex`, etc., with per-agent locations for command directories and context files. citeturn7view0turn7view3

A harness runtime can reuse this approach by treating agent integrations purely as **adapters** with stable interface boundaries:

- **Input:** a canonical “step” request (goal + required artifacts + constraints)  
- **Output:** a canonical “step result” (produced artifacts + trace + validation signals)

Adapters can be:
- **Manual adapters**: render instructions/prompts for a human to run in their preferred tool (ideal for IDE agents that aren’t cleanly automatable).
- **CLI adapters**: invoke agent CLIs (e.g., Codex CLI, Claude Code CLI) where automation exists.
- **Remote adapters**: call hosted APIs when allowed.

This matches the broader “harnesses encode assumptions” theme: keep stable interfaces while harness implementations evolve. citeturn27view0

### Validation engines and eval-driven development

Both major vendors converge on the same lesson: you do not get reliable agent behavior “by vibes.” You need evals and validations.

OpenAI’s eval guidance defines evals as structured tests and emphasizes “log everything” and “evaluate early and often.” citeturn24view5 Its agent-skill eval post makes this more concrete: an eval is “a prompt → a captured run (trace + artifacts) → checks → score,” and recommends small deterministic checks first (e.g., expected commands ran, expected files exist), then rubric-based grading when rules fall short. citeturn25view0turn26search34

Anthropic’s eval guidance similarly argues that agent capabilities (multi-turn tool calls, state changes) are precisely what makes them hard to evaluate, which requires evaluation strategies that match that complexity and catch problems before production. citeturn24view4

**Harness best practice:** treat validations as first-class, composable objects tied to steps:
- deterministic checks (filesystem, command exit codes, schema conformance)
- behavioral checks (did the agent follow required process gates?)
- rubric scoring (style/convention adherence) when determinism is insufficient

### Tool- and protocol-level integration

A modern harness should assume tools are external and change over time. The (protocol) standardization push is a direct response: Model Context Protocol (MCP) is specified as an open protocol using JSON-RPC that standardizes exposing tools and exchanging context between hosts/clients/servers. entity["organization","Model Context Protocol","tool integration standard"] citeturn29view5turn29view4

From a harness perspective, MCP is useful because it encourages:
- stable discovery and tool schema metadata
- explicit tool boundaries and security considerations (authorization frameworks, lifecycle) citeturn26search4turn26search33
- composable integrations (swap tools without rewriting the whole harness)

Even if DevSpark doesn’t implement MCP itself, it can design **HarnessSpec tool steps** in a way that can later map to MCP, shell scripts, or direct SDK calls.

### Safety and governance patterns that work in practice

Two particularly actionable safety principles from recent work:

**Make dangerous actions structurally harder, not just “blocked.”**  
The OpenDev paper argues that permission checks at runtime are not the best primary abstraction for agent safety; schema gating (making unsafe tools invisible) is more robust. citeturn30view0 This aligns well with a harness approach that supports “plan mode” (read-only steps) vs “execute mode” (write steps), where the allowed tool set changes across steps.

**Separate sandboxes, harnesses, and durable session logs.**  
Anthropic’s “Managed Agents” architecture describes virtualizing an agent into a session log (append-only record), harness (loop), and sandbox (execution). It explicitly treats the session log as durable and independent so the harness can crash and restart, and discusses keeping credentials out of sandboxes to reduce exfiltration risk. citeturn27view0

For DevSpark, this translates into:
- store harness run state in repo-local or repo-adjacent logs (e.g., `.devspark/runs/<id>/events.jsonl`)
- keep secrets out of “agent writable” artifacts
- make policy decisions explicit and inspectable

## Integrating Harness Engineering into DevSpark

### DevSpark’s current strengths to build on

DevSpark’s README describes a “structured development process for AI coding assistants,” delivered as prompts/templates/scripts, with an optional CLI to scaffold installation. citeturn28view0turn5view0 It emphasizes:
- “Just markdown files — no install required.” citeturn28view0  
- A canonical agent registry (`agents-registry.json`) describing supported agent integrations. citeturn28view0turn7view0  
- Multi-app governance via registry + scoping (`.documentation/devspark.json`, profiles, app-local overrides). citeturn28view4turn11view2turn12view4  
- Contract-style tests that enforce prompt/template invariants (e.g., “prompt gate contract” checks ensure certain templates include shared validation contracts and “gate acknowledgements”). citeturn15view0turn28view2  
- A release workflow that builds package variants and enforces version parity (release version vs pyproject). citeturn21view0turn5view0

These are already harness-friendly ingredients: repo-local artifacts, explicit contracts, registry-driven indirection, and governance checks.

### What “Harness Runtime” means inside DevSpark

Here, “harness runtime” should be interpreted as:

An optional CLI subsystem that can:
- load a harness specification (YAML/JSON)
- execute a sequence of steps (some automated, some manual)
- validate each step with deterministic rules and/or rubric graders
- produce a structured run result (JSON) and an event stream (JSONL)
- integrate with DevSpark’s existing scoping system (repo vs app)

This is **additive**: it does not replace `/devspark.*` prompt commands; it provides an executable layer for teams who want repeatability, CI hooks, and traceable validations.

### CLI-first architecture patterns to reuse

DevSpark’s existing Python CLI already demonstrates:
- packaging and entrypoint wiring (`devspark = "devspark_cli:main"`) citeturn5view0  
- a registry loader for agent metadata (`load_agent_registry`) citeturn11view1turn14view0  
- resolution chains for overrides and constitution composition (with weakening detection) citeturn12view4turn12view1turn15view2

That implies a natural location for harness-engineering functionality: **new modules under `src/devspark_cli/`** that import and reuse existing components (registry, resolution, scope) rather than re-inventing them.

### Proposed Python module and class architecture

A practical, incremental architecture (designed for minimal disruption) looks like this:

#### Modules

- `devspark_cli/harness/spec_models.py`  
  Pydantic models for HarnessSpec, StepSpec, ValidationRule, RetryPolicy, RunResult.

- `devspark_cli/harness/spec_loader.py`  
  Load/validate YAML or JSON; resolve relative paths; apply app scoping defaults.

- `devspark_cli/harness/runner.py`  
  `HarnessRunner` orchestrates step execution, retries, and validations.

- `devspark_cli/harness/adapters/base.py`  
  `AgentAdapter` interface and `ShellAdapter`, `ManualAdapter`, `NoopAdapter`.

- `devspark_cli/harness/validation.py`  
  `ValidationEngine` + rule implementations. Deterministic first.

- `devspark_cli/harness/telemetry.py`  
  Event emission to JSONL, optional OpenTelemetry spans, and summary metrics.

- `devspark_cli/harness/cli.py`  
  Typer subcommands wired into the existing CLI (e.g., `devspark harness run`).

This structure mirrors the OpenDev separation of scaffolding vs harness runtime orchestration, keeping spec parsing separate from execution. citeturn30view0

#### Core class/interface definitions (method signatures)

**HarnessRunner**
- `run(spec: HarnessSpec, *, repo_root: Path, app_id: str|None, adapter: AgentAdapter, telemetry: TelemetrySink) -> RunResult`
- `run_step(step: StepSpec, ctx: RunContext) -> StepResult`
- `apply_retry(policy: RetryPolicy, attempt: int, last_error: Exception|None) -> None`

**AgentAdapter (protocol/interface)**
- `name: str`
- `prepare(step: StepSpec, ctx: RunContext) -> PreparedStep`  
- `execute(prepared: PreparedStep, ctx: RunContext) -> ExecutionResult`
- `supports(mode: StepMode) -> bool`

**ValidationEngine**
- `validate(step: StepSpec, exec_result: ExecutionResult, ctx: RunContext) -> list[ValidationFinding]`
- `validate_rule(rule: ValidationRule, ctx: ValidationContext) -> ValidationFinding`

**TelemetrySink**
- `emit(event: HarnessEvent) -> None`
- `flush() -> None`

#### Architecture diagram

```mermaid
flowchart LR
  CLI[devspark CLI\n(Typer)] --> HL[Harness Loader\n(spec_loader)]
  HL --> HR[HarnessRunner\n(runner)]
  HR --> AD[AgentAdapter\n(adapters/*)]
  HR --> VE[ValidationEngine\n(validation)]
  HR --> TS[TelemetrySink\n(telemetry)]
  AD --> ENV[Execution Environment\n(shell / agent CLI / manual)]
  VE --> ART[Repo Artifacts\n(files, diffs, reports)]
  TS --> LOGS[events.jsonl + run_result.json]
  TS --> OTEL[Optional OpenTelemetry spans]
```

### Where this fits into DevSpark’s existing repo concepts

- **Agent-agnostic integration:** reuse `agents-registry.json` for any adapter that needs agent-specific files/paths. citeturn7view0turn7view3  
- **Repo/app scoping:** reuse multi-app registry and `--app <id>` conventions, and incorporate constitution resolution (repo + overlay) into run context for governance-aware validations. citeturn28view4turn12view4turn10view5  
- **Override chains:** reuse `build_script_chain` / `build_prompt_chain` style logic (already present) to locate harness specs, validators, and scripts with consistent override precedence. citeturn12view0turn15view2

## HarnessSpec schemas and sample artifacts

The goal of a HarnessSpec is not to be “yet another workflow language,” but to standardize four things that eval and harness literature repeatedly emphasizes:

- **Step intent** (what should happen)  
- **Artifacts** (what should exist after)  
- **Validation** (how we know it worked) citeturn25view0turn24view5  
- **Traceability** (captured events and results that can be re-scored later) citeturn25view0turn27view0

### Recommended schema shapes

#### HarnessSpec (YAML/JSON)

Key fields:
- `apiVersion`, `kind`, `name`
- `scope`: `repo` or `app`
- `steps`: list of StepSpec
- `defaults`: retry, timeouts, mode, workingDir
- `telemetry`: where to write JSONL + summary JSON

#### StepSpec

Key fields:
- `id`, `name`, `mode` (`manual|shell|agent`)
- `inputs` / `outputs` (file paths, globs)
- `action` (command/prompt reference/instructions)
- `validation`: list of ValidationRule
- `retry`: RetryPolicy override

#### ValidationRule

Key types:
- `file.exists`, `file.contains`, `json.schema`, `command.exit_code`, `git.clean`, `regex.match`, `report.junit`
- Use minimal, deterministic checks first (per eval best practice), then optional rubric scoring hooks. citeturn25view0turn26search34

#### RetryPolicy

Key fields:
- `maxAttempts`, `backoff` (`none|fixed|exponential`)
- `retryOn` (error types: `tool_error`, `timeout`, `validation_fail`)
- `requireHumanAfter`: attempts threshold for escalation

### Sample minimal harness spec

```yaml
apiVersion: devspark.ai/v1
kind: HarnessSpec
name: "noop-example"
scope:
  type: repo
telemetry:
  runDir: ".devspark/runs"
  emitJsonl: true
defaults:
  retry:
    maxAttempts: 1
    backoff: none
steps:
  - id: "S1"
    name: "No-op step for wiring"
    mode: agent
    action:
      adapter: noop
      prompt: "Do nothing. Confirm you ran."
    outputs:
      files: []
    validation:
      - id: "V1"
        type: "always.pass"
        severity: "error"
```

### Sample run result JSON

```json
{
  "runId": "run_2026-04-14T19-30-00Z_a1b2c3",
  "harness": { "name": "noop-example", "apiVersion": "devspark.ai/v1" },
  "scope": { "type": "repo", "appId": null },
  "status": "passed",
  "startedAt": "2026-04-14T19:30:00Z",
  "finishedAt": "2026-04-14T19:30:01Z",
  "steps": [
    {
      "id": "S1",
      "status": "passed",
      "attempts": 1,
      "adapter": "noop",
      "artifacts": { "created": [], "modified": [], "deleted": [] },
      "validation": [
        { "id": "V1", "type": "always.pass", "status": "passed", "severity": "error" }
      ]
    }
  ],
  "metrics": {
    "durationMs": 1000,
    "validationFailures": 0
  }
}
```

### No-op AgentAdapter (Python)

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StepSpec:
  id: str
  name: str
  mode: str
  prompt: str


@dataclass(frozen=True)
class PreparedStep:
  step_id: str
  rendered_prompt: str


@dataclass(frozen=True)
class ExecutionResult:
  ok: bool
  message: str


class AgentAdapter(Protocol):
  name: str
  def supports(self, mode: str) -> bool: ...
  def prepare(self, step: StepSpec) -> PreparedStep: ...
  def execute(self, prepared: PreparedStep) -> ExecutionResult: ...


class NoopAgentAdapter:
  name = "noop"

  def supports(self, mode: str) -> bool:
    return mode == "agent"

  def prepare(self, step: StepSpec) -> PreparedStep:
    return PreparedStep(step_id=step.id, rendered_prompt=step.prompt)

  def execute(self, prepared: PreparedStep) -> ExecutionResult:
    # Intentionally do nothing; useful for wiring and unit tests.
    return ExecutionResult(ok=True, message=f"Noop executed for {prepared.step_id}")
```

## Migration and incremental rollout plan

This plan is designed to be additive and to align with DevSpark’s existing philosophy: prompts remain the primary UX, while the harness runtime is optional for teams who want repeatable validations, traces, and CI integration. citeturn28view2turn28view0

### Timeline and checkpoints

| Time window | Delivery checkpoint | Output artifacts | Go/no-go criteria |
|---|---|---|---|
| Week 1 | Spec parsing + schema validation | `HarnessSpec` models, loader, `devspark harness validate` | Load YAML/JSON; clear error messages |
| Week 2 | Runner skeleton + dry-run execution | `devspark harness run --dry-run`, event writer | Produces run directory + event stream |
| Week 3 | Deterministic validation engine | file/command/json rules; step results | Deterministic checks pass/fail reliably |
| Week 4 | Adapter surface + manual mode | `ManualAdapter` instructions output | Works with IDE agents via copy/paste prompts |
| Weeks 5–6 | Optional CLI agent adapters + CI | Codex/Claude adapters (if desired), CI workflow | Automated runs reproducible in CI |
| Weeks 7–8 | Governance + observability hardening | policy gating, OTel spans, AppInsights events | Traces + security posture documented |

### Incremental rollout strategy

- **Start with validation-only:** use harness specs to validate repo state (checks), without executing any agent/tool actions. This matches “eval-driven development” advice: measure before optimizing. citeturn24view5turn25view0  
- **Add step execution gradually:** enable `shell` steps next (deterministic), then `manual` steps, then optional `agent` steps for automatable agents.
- **Gate risk by scope:** default to repo read-only steps; require explicit opt-in for destructive commands (mirrors the “plan mode” vs “normal mode” pattern in agent research). citeturn30view0

## Testing strategy and CI suggestions

### Testing approach

DevSpark already uses “contract tests” that run as standalone Python scripts to enforce invariant properties in templates and upgrade flows. citeturn15view0turn15view2turn15view4 The harness runtime should adopt the same philosophy:

- **Schema contract tests:** sample HarnessSpecs must validate; invalid ones must fail with stable error strings.  
- **Rule contract tests:** each ValidationRule type must behave deterministically on fixtures.  
- **Runner contract tests:** a dry-run must emit a run directory with expected files (`events.jsonl`, `run_result.json`).  
- **Regression fixtures:** keep a small set of harness specs in `tests/fixtures/harness/` and run them in CI.

### CI integration

DevSpark’s current GitHub Actions “lint” workflow covers markdown and shell scripts. citeturn18view0 Adding a separate workflow for Python contract tests would align with standard GitHub Actions guidance for building/testing Python. citeturn31search8

Suggested CI stages (conceptual):
- `python -m pip install -e .` (or use your preferred tool)
- run `python tests/test_*.py` (current style) or migrate to pytest later
- optionally run a validation-only harness: `devspark harness validate -f tests/fixtures/harness/sample.yaml`

## Observability, telemetry, and governance controls

### Telemetry event schema

A useful harness telemetry stream should support:
- replay and re-scoring (eval pattern: prompt → trace → checks → score) citeturn25view0
- post-mortem debugging (step boundaries and error categories)
- cost and throughput visibility (tokens/tool calls/runtime) citeturn29view0turn25view0

**Recommended JSONL event types:**
- `harness.run.started`, `harness.run.finished`
- `harness.step.started`, `harness.step.finished`
- `harness.step.validation` (per rule)
- `harness.tool.called` (shell command, agent invocation, MCP tool call)
- `harness.policy.blocked` (governance events)

This mirrors modern “session log” thinking: a durable append-only record outside the harness implementation that enables restart and analysis. citeturn27view0

### Optional OpenTelemetry alignment

OpenTelemetry now publishes semantic conventions for GenAI spans, including model inference spans and agent/framework spans. entity["organization","OpenTelemetry","observability framework"] citeturn31search1turn31search5

A pragmatic approach:
- emit OTel spans for `HarnessRunner.run` and each step
- attach attributes such as `harness.name`, `step.id`, `validation.count`, and (when applicable) GenAI attributes (`gen_ai.request.model`, etc.) consistent with the semantic conventions. citeturn31search1turn31search5

### Sample Application Insights “customEvents” payloads

Even if you only emit JSONL locally, it’s useful to define a stable event schema that can be mirrored into AppInsights later (or any log backend).

Example event (conceptual):
- name: `devspark.harness.step.finished`
- properties: `runId`, `stepId`, `status`, `durationMs`, `attempt`, `scopeType`, `appId`

### Sample Kusto queries for AppInsights

```kusto
customEvents
| where name == "devspark.harness.step.finished"
| summarize
    steps = count(),
    failures = countif(tostring(customDimensions.status) == "failed"),
    p95ms = percentile(todouble(customDimensions.durationMs), 95)
  by tostring(customDimensions.harnessName)
| order by failures desc
```

```kusto
customEvents
| where name startswith "devspark.harness."
| summarize count() by name, tostring(customDimensions.status)
| order by count_ desc
```

### Security and governance controls

A harness runtime should treat governance as “first-class,” not an afterthought—because autonomous tool use makes failures higher impact. citeturn24view4turn24view5

High-leverage controls:

- **Mode-based tool gating (schema gating):** plan steps expose only read tools; execute steps expose write tools. This aligns with the “make unsafe tools invisible, not blocked” safety lesson. citeturn30view0  
- **Credential isolation:** never place secrets/tokens in agent-writable sandboxes or artifacts; prefer out-of-band secret storage and scoped credentials (mirrors “tokens never reachable from the sandbox” guidance). citeturn27view0  
- **Constitution-aware validations:** reuse DevSpark’s constitution resolution and weakening detection to prevent app overlays from weakening mandatory repo rules. citeturn12view4turn12view1  
- **Guard rails on destructive shell commands:** treat deletes, force pushes, and credential-printing commands as policy-blocked unless explicitly allowed by spec.

## Prioritized roadmap

### MVP

- HarnessSpec models + loader (`validate`)
- Runner dry-run + event emission (`run --dry-run`)
- Deterministic ValidationRules: file exists/contains, command exit code, json schema
- ManualAdapter: prints copy/paste blocks for IDE-based agents
- Run artifact directory standardized: `.devspark/runs/<runId>/...`

### v1

- App-scoped harness: integrate with `.documentation/devspark.json` and `--app <id>` workflows citeturn28view4  
- Script/prompt resolution integration (reuse existing chain logic) citeturn12view0turn15view2  
- Optional adapters for automatable agents (where feasible)
- CI workflow that runs harness validations and contract tests

### Enterprise

- Policy packs: centrally managed governance rules, auditable changes
- Signed run artifacts / tamper-evident logs
- OTel + AppInsights integration templates
- MCP tool discovery integration (optional), aligned to MCP semantics and authorization frameworks citeturn29view5turn26search4  
- Multi-run analytics dashboard: regressions, flaky validations, throughput metrics

## Copilot Chat copy-paste blocks for the first three tasks

### Task one: add HarnessSpec models and loader

```markdown
You are working in the DevSpark repository.

Implement an ADDITIVE harness runtime foundation.

Goal: introduce “HarnessSpec” Pydantic models + a loader that can parse YAML or JSON. Do NOT change existing CLI commands. Add new modules only.

Create:
- src/devspark_cli/harness/spec_models.py
- src/devspark_cli/harness/spec_loader.py
- src/devspark_cli/harness/__init__.py

Requirements:
- Use pydantic v2 (already in dependencies).
- Models: HarnessSpec, StepSpec, ValidationRule, RetryPolicy, TelemetrySpec.
- Support “apiVersion: devspark.ai/v1” and “kind: HarnessSpec”.
- Loader: load from path, detect YAML vs JSON by extension, validate model, normalize relative paths.
- Include at least 2 tiny unit/contract fixtures under tests/fixtures/harness/.

Then add a new lightweight contract test:
- tests/test_harness_spec_contract.py
that runs as a standalone python script (matching existing test style), loads the fixture, asserts validation passes and key fields are present.

Do not introduce pytest yet.
```

### Task two: add HarnessRunner skeleton and dry-run command

```markdown
In DevSpark, add an additive “devspark harness” CLI group.

Goal: implement a dry-run harness runner that emits:
- .devspark/runs/<runId>/events.jsonl
- .devspark/runs/<runId>/run_result.json

Create:
- src/devspark_cli/harness/runner.py
- src/devspark_cli/harness/telemetry.py
- src/devspark_cli/harness/cli.py

Wire into existing Typer app (src/devspark_cli/__init__.py) by adding a subcommand group:
- devspark harness validate -f <spec>
- devspark harness run -f <spec> --dry-run

Dry-run behavior:
- Validate spec
- Emit run.started event
- For each step emit step.started + step.finished with status “skipped_dry_run”
- Emit run.finished with status “passed” (unless spec invalid)

Constraints:
- No changes to existing commands.
- Keep code style consistent with repo.
- Make the runId deterministic-ish: timestamp + short random suffix.
- Add a contract test that runs dry-run and asserts files are created.
```

### Task three: implement a minimal deterministic ValidationEngine

```markdown
Extend the harness runtime with a minimal deterministic validation engine.

Create:
- src/devspark_cli/harness/validation.py

Implement ValidationRule types:
- always.pass
- file.exists (path)
- file.contains (path, substring)
- command.exit_code (command, expected=0)  [shell steps only; for now simulate in dry-run or run directly if not dry-run]

Update HarnessRunner to:
- after each step, run validations
- record validation findings into events.jsonl + run_result.json
- fail the run if any “severity: error” rule fails

Add fixtures:
- a tiny file under tests/fixtures/harness/files/hello.txt
- a harness spec that validates file.exists and file.contains

Add/extend a contract test:
- tests/test_harness_validation_contract.py
to verify pass and fail cases.
```
