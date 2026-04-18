"""Contract tests for the issue adapter (T037)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from devspark_cli.issues import (
    CANONICAL_REPO,
    CLASSIFICATION_LABELS,
    EXIT_AUTONOMY_REQUIRED,
    EXIT_GH_API,
    EXIT_GH_UNAUTHENTICATED,
    ENDPOINT,
    IssueAdapterError,
    IssueProposal,
    build_payload,
    file_issue,
)


def _proposal(**overrides):
    base = dict(
        title="Some title",
        classification="bug",
        context="ctx",
        current_behavior="cur",
        expected_behavior="exp",
        suggested_fix="fix",
        run_id="run-1",
    )
    base.update(overrides)
    return IssueProposal(**base)


def test_canonical_repo_is_hardcoded():
    assert CANONICAL_REPO == "markhazleton/devspark"
    assert ENDPOINT == "repos/markhazleton/devspark/issues"


def test_classification_label_map():
    assert CLASSIFICATION_LABELS == {
        "bug": "bug",
        "enhancement": "enhancement",
        "prompt-quality": "area:prompts",
        "workflow-design": "area:workflows",
        "documentation": "documentation",
    }


def test_payload_uses_label_from_classification():
    p = build_payload(_proposal(classification="prompt-quality"))
    assert p["labels"] == ["area:prompts"]
    assert "Filed by `/devspark.suggest-improvement`" in p["body"]
    assert "## Suggested fix" in p["body"]


def test_payload_omits_suggested_fix_when_absent():
    p = build_payload(_proposal(suggested_fix=None))
    assert "## Suggested fix" not in p["body"]


def test_payload_truncates_title_to_200_chars():
    p = build_payload(_proposal(title="x" * 500))
    assert len(p["title"]) == 200


def test_unknown_classification_raises():
    with pytest.raises(IssueAdapterError) as exc:
        build_payload(_proposal(classification="unknown"))
    assert exc.value.exit_code == EXIT_GH_API


def test_adversarial_title_does_not_leak_into_argv():
    """A title like ``--repo evil/owner`` must NEVER appear as a flag in argv.

    The adapter sends the JSON payload via stdin and uses a fixed argv that
    never contains user-supplied content.
    """
    captured = {}

    def fake_runner(argv, input=None, capture_output=None, text=None, check=None):
        captured["argv"] = argv
        captured["stdin"] = input
        return SimpleNamespace(returncode=0, stdout=json.dumps({"html_url": "https://x"}), stderr="")

    p = _proposal(title="--repo evil/owner")
    url = file_issue(p, assume_yes=True, runner=fake_runner)
    assert url == "https://x"
    # argv MUST be exactly the fixed shape; no user content.
    assert captured["argv"] == ["gh", "api", ENDPOINT, "-X", "POST", "--input", "-"]
    assert "--repo" not in captured["argv"]
    # stdin carries title verbatim, but as a JSON value (data, not flag).
    body = json.loads(captured["stdin"])
    assert body["title"] == "--repo evil/owner"
    assert body["labels"] == ["bug"]


def test_non_interactive_without_yes_aborts(monkeypatch):
    def fake_runner(*a, **k):
        raise AssertionError("runner must not be called when confirmation aborts")

    with pytest.raises(IssueAdapterError) as exc:
        file_issue(_proposal(), non_interactive=True, runner=fake_runner)
    assert exc.value.exit_code == EXIT_AUTONOMY_REQUIRED


def test_unauthenticated_maps_to_exit_code():
    def fake_runner(*a, **k):
        return SimpleNamespace(returncode=1, stdout="", stderr="error: not authenticated; run gh auth login")

    with pytest.raises(IssueAdapterError) as exc:
        file_issue(_proposal(), assume_yes=True, runner=fake_runner)
    assert exc.value.exit_code == EXIT_GH_UNAUTHENTICATED
