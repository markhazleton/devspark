"""Validation engine for harness step rules."""

from __future__ import annotations

import json
import fnmatch
import re
import subprocess
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from .spec_models import RunContext, ValidationFinding, ValidationRule


class ValidationEngine:
    """Evaluate harness validation rules against the current run context."""

    @staticmethod
    def _changed_paths(repo_root: Path, base_ref: str) -> list[str]:
        paths: set[str] = set()
        commands = [
            ["git", "diff", f"{base_ref}...HEAD", "--name-only", "--", "src/", "test/"],
            ["git", "diff", "--cached", "--name-only", "--", "src/", "test/"],
            ["git", "diff", "--name-only", "--", "src/", "test/"],
        ]
        for command in commands:
            completed = subprocess.run(
                command,
                cwd=repo_root,
                text=True,
                errors="replace",
                capture_output=True,
                check=False,
                timeout=30,
            )
            if completed.returncode == 0:
                for line in (completed.stdout or "").splitlines():
                    value = line.strip()
                    if value:
                        paths.add(value.replace("\\", "/"))

        status_completed = subprocess.run(
            ["git", "status", "--porcelain", "--", "src/", "test/"],
            cwd=repo_root,
            text=True,
            errors="replace",
            capture_output=True,
            check=False,
            timeout=30,
        )
        if status_completed.returncode == 0:
            for line in (status_completed.stdout or "").splitlines():
                candidate = line[3:].strip() if len(line) > 3 else ""
                if candidate:
                    paths.add(candidate.replace("\\", "/"))
        return sorted(paths)

    def evaluate(self, rule: ValidationRule, context: RunContext, step_dir: Path) -> ValidationFinding:
        # Phase 5: respect enabled flag — disabled rules are skipped without error
        if not rule.enabled:
            return ValidationFinding(rule_id=rule.id, type=rule.type, status="skipped", severity=rule.severity, message="Rule disabled (enabled=false)")

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
            # Phase 2: skip side-effectful commands in plan mode
            if context.execution_mode == "plan":
                return ValidationFinding(rule_id=rule.id, type=rule.type, status="skipped", severity=rule.severity, message="Skipped in plan mode (command may have side effects)")
            timeout_seconds = rule.timeout_seconds or 300
            try:
                # SECURITY NOTE: rule.command comes from committed harness spec YAML, not user input.
                # Injection risk is limited to developers with repo write access. No untrusted input flows here.
                # See .documentation/specs/*/gates/security-audit.md for full analysis.
                completed = subprocess.run(
                    rule.command,
                    cwd=repo_root,
                    shell=True,
                    text=True,
                    errors="replace",
                    capture_output=True,
                    check=False,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired:
                return ValidationFinding(
                    rule_id=rule.id,
                    type=rule.type,
                    status="failed",
                    severity=rule.severity,
                    message=f"Command timed out after {timeout_seconds}s",
                )

            combined_output = (completed.stdout or "") + (completed.stderr or "")
            stdout_path = step_dir / "stdout.txt"
            stdout_path.write_text(combined_output, encoding="utf-8")
            status = "passed" if completed.returncode == rule.expected_exit else "failed"
            decode_note = " (decode replacements applied)" if "\ufffd" in combined_output else ""
            return ValidationFinding(
                rule_id=rule.id,
                type=rule.type,
                status=status,
                severity=rule.severity,
                message=f"Command exited with {completed.returncode}; expected {rule.expected_exit}{decode_note}",
            )

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

        if rule.type == "git.changed_count":
            changed = self._changed_paths(repo_root, rule.git_base_ref)
            count = len(changed)
            status = "passed" if count >= rule.min_changed_count else "failed"
            return ValidationFinding(
                rule_id=rule.id,
                type=rule.type,
                status=status,
                severity=rule.severity,
                message=(
                    f"Found {count} changed file(s) under src/test against {rule.git_base_ref}"
                    if status == "passed"
                    else f"Found {count} changed file(s) under src/test against {rule.git_base_ref}; expected >= {rule.min_changed_count}"
                ),
            )

        if rule.type == "git.changed_path_match":
            changed = self._changed_paths(repo_root, rule.git_base_ref)
            patterns = rule.path_patterns or ["src/**", "test/**"]
            matched = [p for p in changed if any(fnmatch.fnmatch(p, pat) for pat in patterns)]
            status = "passed" if matched else "failed"
            return ValidationFinding(
                rule_id=rule.id,
                type=rule.type,
                status=status,
                severity=rule.severity,
                message=(
                    f"Matched changed path(s): {', '.join(matched[:5])}"
                    if status == "passed"
                    else f"No changed paths matched patterns {patterns} against {rule.git_base_ref}"
                ),
            )

        if rule.type == "regex.match":
            path = Path(rule.path)
            if not path.exists():
                return ValidationFinding(rule_id=rule.id, type=rule.type, status="failed", severity=rule.severity, message=f"File {path} is missing")
            content = path.read_text(encoding="utf-8", errors="ignore")
            status = "passed" if re.search(rule.pattern or "", content, re.MULTILINE) else "failed"
            return ValidationFinding(rule_id=rule.id, type=rule.type, status=status, severity=rule.severity, message=f"Pattern {'matched' if status == 'passed' else 'did not match'} in {path}")

        if rule.type == "llm.rubric":
            # Phase 3: LLM rubric scoring — delegate to grader CLI, no credentials in harness
            output_path = step_dir / "output.txt"
            if not output_path.exists():
                return ValidationFinding(rule_id=rule.id, type=rule.type, status="failed", severity=rule.severity, message="No output.txt found for rubric evaluation")

            output_content = output_path.read_text(encoding="utf-8", errors="ignore")

            # rubric may be inline text or a path to a rubric file
            rubric_text = rule.rubric or ""
            rubric_file = Path(rubric_text)
            if rubric_file.exists() and rubric_file.is_file():
                rubric_text = rubric_file.read_text(encoding="utf-8", errors="ignore")

            grading_prompt = (
                f"RUBRIC:\n{rubric_text}\n\n"
                f"OUTPUT TO SCORE:\n{output_content}\n\n"
                "Score 1-5 on the first line (just the integer). 1=poor, 5=excellent."
            )

            # SECURITY NOTE: rule.grader_command comes from committed harness spec YAML, not user input.
            # Injection risk is limited to developers with repo write access. Grading prompt is constructed
            # from file contents, not external input. See security-audit.md for full analysis.
            completed = subprocess.run(
                rule.grader_command,
                shell=True,
                input=grading_prompt,
                text=True,
                errors="replace",
                capture_output=True,
                check=False,
                cwd=repo_root,
                timeout=rule.timeout_seconds or 300,
            )

            rubric_result_path = step_dir / "rubric_result.txt"
            rubric_result_path.write_text((completed.stdout or "") + (completed.stderr or ""), encoding="utf-8")

            if completed.returncode != 0:
                return ValidationFinding(rule_id=rule.id, type=rule.type, status="failed", severity=rule.severity, message=f"Grader exited with code {completed.returncode}")

            first_line = (completed.stdout or "").strip().splitlines()[0] if (completed.stdout or "").strip() else ""
            try:
                score = int(first_line.split()[0])
            except (ValueError, IndexError):
                return ValidationFinding(rule_id=rule.id, type=rule.type, status="failed", severity=rule.severity, message=f"Could not parse score from grader output: {first_line!r}")

            threshold = rule.pass_threshold
            if score >= threshold:
                return ValidationFinding(rule_id=rule.id, type=rule.type, status="passed", severity=rule.severity, message=f"Rubric score {score} >= threshold {threshold}")
            return ValidationFinding(rule_id=rule.id, type=rule.type, status="failed", severity=rule.severity, message=f"Rubric score {score} < threshold {threshold}")

        return ValidationFinding(rule_id=rule.id, type=rule.type, status="skipped", severity=rule.severity, message="Rule not implemented")