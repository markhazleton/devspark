"""Issue adapter for `suggest-improvement` workflow.

Always targets ``markhazleton/devspark`` and constructs the payload as a Python
dict that is JSON-serialized to ``gh api`` via stdin. No model-generated content
ever flows through argv.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable

CANONICAL_REPO = "markhazleton/devspark"
ENDPOINT = f"repos/{CANONICAL_REPO}/issues"

# Exit codes (mirror contracts/exit-codes.md)
EXIT_GH_UNAVAILABLE = 10
EXIT_GH_UNAUTHENTICATED = 11
EXIT_GH_API = 12
EXIT_GH_NETWORK = 13
EXIT_AUTONOMY_REQUIRED = 20

CLASSIFICATION_LABELS = {
    "bug": "bug",
    "enhancement": "enhancement",
    "prompt-quality": "area:prompts",
    "workflow-design": "area:workflows",
    "documentation": "documentation",
}

_TITLE_MAX = 200


@dataclass
class IssueProposal:
    title: str
    classification: str
    context: str
    current_behavior: str
    expected_behavior: str
    suggested_fix: str | None = None
    run_id: str | None = None


class IssueAdapterError(Exception):
    def __init__(self, exit_code: int, message: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.message = message


def build_payload(proposal: IssueProposal) -> dict:
    if proposal.classification not in CLASSIFICATION_LABELS:
        raise IssueAdapterError(
            EXIT_GH_API, f"unknown classification: {proposal.classification!r}"
        )
    title = (proposal.title or "").strip()[:_TITLE_MAX]
    body_lines = [
        f"> Filed by `/devspark.suggest-improvement` (workflow run `{proposal.run_id or 'n/a'}`)",
        "",
        "### Classification",
        "",
        f"`{proposal.classification}`",
        "",
        "### Context",
        "",
        proposal.context.strip(),
        "",
        "### Current behavior",
        "",
        proposal.current_behavior.strip(),
        "",
        "### Expected behavior",
        "",
        proposal.expected_behavior.strip(),
        "",
    ]
    if proposal.suggested_fix:
        body_lines += ["### Suggested fix", "", proposal.suggested_fix.strip(), ""]
    return {
        "title": title,
        "body": "\n".join(body_lines),
        "labels": [CLASSIFICATION_LABELS[proposal.classification]],
    }


def _check_gh() -> None:
    if shutil.which("gh") is None:
        raise IssueAdapterError(
            EXIT_GH_UNAVAILABLE,
            "gh CLI is not installed. Install from https://cli.github.com/",
        )


def _confirm(proposal: IssueProposal, payload: dict, *, assume_yes: bool, non_interactive: bool, stream=sys.stderr) -> None:
    summary = (
        f"About to file an issue in {CANONICAL_REPO}:\n"
        f"  title:          {payload['title']}\n"
        f"  classification: {proposal.classification}\n"
        f"  labels:         {payload['labels']}\n"
    )
    print(summary, file=stream)
    if assume_yes:
        return
    if non_interactive:
        raise IssueAdapterError(
            EXIT_AUTONOMY_REQUIRED,
            "non-interactive run cannot file an issue without --yes",
        )
    print("Proceed? [y/N]: ", end="", file=stream, flush=True)
    answer = sys.stdin.readline().strip().lower()
    if answer not in ("y", "yes"):
        raise IssueAdapterError(EXIT_AUTONOMY_REQUIRED, "user declined to file issue")


def file_issue(
    proposal: IssueProposal,
    *,
    assume_yes: bool = False,
    non_interactive: bool = False,
    runner=subprocess.run,
) -> str:
    """File the issue and return its URL.

    ``runner`` is injectable for tests; default is ``subprocess.run``.
    """
    _check_gh()
    payload = build_payload(proposal)
    _confirm(proposal, payload, assume_yes=assume_yes, non_interactive=non_interactive)

    argv = ["gh", "api", ENDPOINT, "-X", "POST", "--input", "-"]
    try:
        result = runner(
            argv,
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise IssueAdapterError(EXIT_GH_UNAVAILABLE, str(exc))

    if result.returncode != 0:
        stderr = (result.stderr or "").lower()
        if "not authenticated" in stderr or "gh auth login" in stderr:
            raise IssueAdapterError(
                EXIT_GH_UNAUTHENTICATED,
                "gh is not authenticated. Run `gh auth login`.",
            )
        if "could not resolve host" in stderr or "network" in stderr or "dial tcp" in stderr:
            raise IssueAdapterError(EXIT_GH_NETWORK, result.stderr or "network unreachable")
        raise IssueAdapterError(EXIT_GH_API, result.stderr or "gh api failed")

    try:
        body = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise IssueAdapterError(EXIT_GH_API, f"could not parse gh response: {exc}")
    url = body.get("html_url")
    if not url:
        raise IssueAdapterError(EXIT_GH_API, "gh response missing html_url")
    return url
