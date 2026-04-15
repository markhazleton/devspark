"""Validation engine for harness step rules."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from .spec_models import RunContext, ValidationFinding, ValidationRule


class ValidationEngine:
    """Evaluate harness validation rules against the current run context."""

    def evaluate(self, rule: ValidationRule, context: RunContext, step_dir: Path) -> ValidationFinding:
        repo_root = Path(context.repo_root)

        if rule.type == "always.pass":
            return ValidationFinding(rule_id=rule.id, type=rule.type, status="passed", severity=rule.severity, message="Rule passed")

        if rule.type == "file.exists":
            path = Path(rule.path)
            status = "passed" if path.exists() else "failed"
            return ValidationFinding(rule_id=rule.id, type=rule.type, status=status, severity=rule.severity, message=f"File {path} {'exists' if path.exists() else 'is missing'}")

        if rule.type == "file.contains":
            path = Path(rule.path)
            if not path.exists():
                return ValidationFinding(rule_id=rule.id, type=rule.type, status="failed", severity=rule.severity, message=f"File {path} is missing")
            content = path.read_text(encoding="utf-8", errors="ignore")
            status = "passed" if rule.contains in content else "failed"
            return ValidationFinding(rule_id=rule.id, type=rule.type, status=status, severity=rule.severity, message=f"Substring {'found' if status == 'passed' else 'missing'} in {path}")

        if rule.type == "command.exit_code":
            completed = subprocess.run(
                rule.command,
                cwd=repo_root,
                shell=True,
                text=True,
                capture_output=True,
                check=False,
            )
            stdout_path = step_dir / "stdout.txt"
            stdout_path.write_text((completed.stdout or "") + (completed.stderr or ""), encoding="utf-8")
            status = "passed" if completed.returncode == rule.expected_exit else "failed"
            return ValidationFinding(rule_id=rule.id, type=rule.type, status=status, severity=rule.severity, message=f"Command exited with {completed.returncode}; expected {rule.expected_exit}")

        if rule.type == "json.schema":
            schema_path = Path(rule.schema_file)
            target_path = Path(rule.target_file)
            if not schema_path.exists() or not target_path.exists():
                missing = schema_path if not schema_path.exists() else target_path
                return ValidationFinding(rule_id=rule.id, type=rule.type, status="failed", severity=rule.severity, message=f"Missing file {missing}")
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            if target_path.suffix.lower() in {".yaml", ".yml"}:
                target = yaml.safe_load(target_path.read_text(encoding="utf-8"))
            else:
                target = json.loads(target_path.read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema).iter_errors(target))
            if errors:
                return ValidationFinding(rule_id=rule.id, type=rule.type, status="failed", severity=rule.severity, message=errors[0].message)
            return ValidationFinding(rule_id=rule.id, type=rule.type, status="passed", severity=rule.severity, message=f"{target_path.name} matched schema")

        if rule.type == "git.clean":
            completed = subprocess.run(["git", "status", "--porcelain", "--", rule.path], cwd=repo_root, text=True, capture_output=True, check=False)
            status = "passed" if completed.stdout.strip() == "" else "failed"
            return ValidationFinding(rule_id=rule.id, type=rule.type, status=status, severity=rule.severity, message="Git working tree clean" if status == "passed" else "Git working tree has changes")

        if rule.type == "regex.match":
            path = Path(rule.path)
            if not path.exists():
                return ValidationFinding(rule_id=rule.id, type=rule.type, status="failed", severity=rule.severity, message=f"File {path} is missing")
            content = path.read_text(encoding="utf-8", errors="ignore")
            status = "passed" if re.search(rule.pattern or "", content, re.MULTILINE) else "failed"
            return ValidationFinding(rule_id=rule.id, type=rule.type, status=status, severity=rule.severity, message=f"Pattern {'matched' if status == 'passed' else 'did not match'} in {path}")

        return ValidationFinding(rule_id=rule.id, type=rule.type, status="skipped", severity=rule.severity, message="Rule not implemented")