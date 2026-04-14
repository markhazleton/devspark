"""Pydantic models for the DevSpark harness spec and run artifacts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


SUPPORTED_API_VERSION = "devspark.ai/v1"
JSON_SCHEMA_DRAFT = "https://json-schema.org/draft/2020-12/schema"

ScopeType = Literal["repo", "app"]
StepType = Literal["agent_task", "validation", "human_gate"]
StepMode = Literal["agent", "manual"]
Severity = Literal["error", "warning"]
ValidationStatus = Literal["passed", "failed", "skipped"]
StepStatus = Literal["passed", "failed", "skipped_dry_run", "aborted"]
RunStatus = Literal["running", "complete", "failed", "aborted"]
BackoffType = Literal["none", "fixed", "exponential"]
RetryTrigger = Literal["validation_fail", "tool_error", "timeout"]
RuleType = Literal[
    "always.pass",
    "file.exists",
    "file.contains",
    "command.exit_code",
    "json.schema",
    "git.clean",
    "regex.match",
]


class ScopeDeclaration(BaseModel):
    """Repository or application scope for a harness run."""

    type: ScopeType = "repo"
    app: str | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "ScopeDeclaration":
        if self.type == "app" and not self.app:
            raise ValueError("scope.app is required when scope.type is 'app'")
        if self.type != "app" and self.app:
            raise ValueError("scope.app is only valid when scope.type is 'app'")
        return self


class RetryPolicy(BaseModel):
    """Retry behavior for a harness step."""

    maxAttempts: int = 1
    backoff: BackoffType = "none"
    retryOn: list[RetryTrigger] = Field(default_factory=lambda: ["validation_fail"])
    requireHumanAfter: int | None = None
    repairPrompt: str | None = None

    @model_validator(mode="after")
    def validate_retry_policy(self) -> "RetryPolicy":
        if self.maxAttempts < 1:
            raise ValueError("retry.maxAttempts must be >= 1")
        if self.requireHumanAfter is not None and self.requireHumanAfter < 1:
            raise ValueError("retry.requireHumanAfter must be >= 1 when provided")
        return self


class ValidationRule(BaseModel):
    """Post-step validation rule."""

    id: str
    type: RuleType
    severity: Severity
    path: str | None = None
    contains: str | None = None
    command: str | None = None
    expected_exit: int = 0
    schema_file: str | None = None
    target_file: str | None = None
    pattern: str | None = None

    @model_validator(mode="after")
    def validate_rule(self) -> "ValidationRule":
        if not self.id:
            raise ValueError("validation.id must not be empty")

        required_fields = {
            "file.exists": ["path"],
            "file.contains": ["path", "contains"],
            "command.exit_code": ["command"],
            "json.schema": ["schema_file", "target_file"],
            "git.clean": ["path"],
            "regex.match": ["path", "pattern"],
            "always.pass": [],
        }
        missing = [field for field in required_fields[self.type] if getattr(self, field) in (None, "")]
        if missing:
            missing_text = ", ".join(missing)
            raise ValueError(f"validation rule '{self.id}' missing required field(s) for {self.type}: {missing_text}")
        return self


class StepDefaults(BaseModel):
    """Default execution attributes applied to steps."""

    adapter: str = "noop"
    retry: RetryPolicy = Field(default_factory=RetryPolicy)
    mode: StepMode = "agent"


class TelemetryConfig(BaseModel):
    """Telemetry output configuration."""

    emit_jsonl: bool = True
    run_dir: str = ".documentation/devspark/runs"


class StepSpec(BaseModel):
    """A single harness workflow step."""

    id: str
    name: str = ""
    type: StepType
    mode: StepMode | None = None
    adapter: str | None = None
    prompt_file: str | None = None
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    validation: list[ValidationRule] = Field(default_factory=list)
    retry: RetryPolicy | None = None
    on_success: str | None = None
    on_failure: str | None = None

    @model_validator(mode="after")
    def validate_step(self) -> "StepSpec":
        if not self.id:
            raise ValueError("step.id must not be empty")
        if self.type == "validation":
            if self.adapter is not None:
                raise ValueError(f"step '{self.id}' of type 'validation' must not declare adapter")
            if self.mode is not None:
                raise ValueError(f"step '{self.id}' of type 'validation' must not declare mode")
            if self.prompt_file is not None:
                raise ValueError(f"step '{self.id}' of type 'validation' must not declare prompt_file")
            if not self.validation:
                raise ValueError(f"step '{self.id}' of type 'validation' requires at least one validation rule")
        else:
            if not self.prompt_file:
                raise ValueError(f"step '{self.id}' requires prompt_file")
        if self.type == "human_gate" and self.mode not in (None, "manual"):
            raise ValueError(f"step '{self.id}' of type 'human_gate' must use manual mode")
        if self.type == "human_gate" and self.adapter not in (None, "manual"):
            raise ValueError(f"step '{self.id}' of type 'human_gate' must use the manual adapter when adapter is specified")
        return self


class HarnessSpec(BaseModel):
    """Top-level harness specification."""

    apiVersion: str
    kind: Literal["HarnessSpec"]
    name: str
    scope: ScopeDeclaration = Field(default_factory=ScopeDeclaration)
    defaults: StepDefaults = Field(default_factory=StepDefaults)
    steps: list[StepSpec]
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)

    @model_validator(mode="after")
    def validate_spec(self) -> "HarnessSpec":
        if self.apiVersion != SUPPORTED_API_VERSION:
            raise ValueError(
                f"Unsupported apiVersion {self.apiVersion!r}; supported value is {SUPPORTED_API_VERSION!r}"
            )
        if not self.name:
            raise ValueError("name must not be empty")
        if not self.steps:
            raise ValueError("steps must contain at least one step")

        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise ValueError("step.id values must be unique")

        step_id_set = set(step_ids)
        for step in self.steps:
            for attr in ("on_success", "on_failure"):
                target = getattr(step, attr)
                if target and target not in step_id_set:
                    raise ValueError(f"step '{step.id}' references unknown {attr} target {target!r}")
            rule_ids = [rule.id for rule in step.validation]
            if len(rule_ids) != len(set(rule_ids)):
                raise ValueError(f"step '{step.id}' has duplicate validation rule ids")

        return self


class ValidationFinding(BaseModel):
    rule_id: str
    type: str
    status: ValidationStatus
    severity: Severity
    message: str


class ArtifactDelta(BaseModel):
    created: list[str] = Field(default_factory=list)
    modified: list[str] = Field(default_factory=list)
    deleted: list[str] = Field(default_factory=list)


class RunMetrics(BaseModel):
    duration_ms: int = 0
    steps_total: int = 0
    steps_passed: int = 0
    steps_failed: int = 0
    validation_failures: int = 0


class StepResult(BaseModel):
    step_id: str
    status: StepStatus
    attempts: int = 0
    adapter: str = "noop"
    duration_ms: int = 0
    validation_findings: list[ValidationFinding] = Field(default_factory=list)
    artifacts: ArtifactDelta = Field(default_factory=ArtifactDelta)


class RunContext(BaseModel):
    run_id: str
    repo_root: str
    spec_path: str
    doc_root: str
    adapter: str
    dry_run: bool = False


class TelemetryEvent(BaseModel):
    event: str
    run_id: str
    ts: str


class Run(BaseModel):
    run_id: str
    status: RunStatus
    harness_name: str
    api_version: str
    scope: ScopeDeclaration
    started_at: str
    finished_at: str | None = None
    steps: list[StepResult] = Field(default_factory=list)
    metrics: RunMetrics = Field(default_factory=RunMetrics)
    context: RunContext | None = None


def harness_schema() -> dict:
    """Return the JSON schema for HarnessSpec with a draft marker."""

    schema = HarnessSpec.model_json_schema()
    schema.setdefault("$schema", JSON_SCHEMA_DRAFT)
    return schema