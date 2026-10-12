# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for the optional Azure DevOps work-tracking integration.

Covers the configuration schema, the review standard's binding to its calibration
corpus, and the dual-language work-item helper pair.
"""

from __future__ import annotations

import collections
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import jsonschema
import pytest

ROOT = Path(__file__).resolve().parent.parent

CONFIG_SCHEMA = json.loads(
    (ROOT / "templates/devspark-config.schema.json").read_text(encoding="utf-8")
)
CORPUS_PATH = ROOT / "tests/fixtures/workitem-review/calibration-corpus.json"
CORPUS = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))
STANDARD_PATH = ROOT / "templates/workitem-standard.md"


def _validate(config: dict) -> None:
    jsonschema.validate(instance=config, schema=CONFIG_SCHEMA)


# --------------------------------------------------------------------------
# Configuration schema
# --------------------------------------------------------------------------


def test_config_validates_without_work_tracking() -> None:
    """An unconfigured repository must remain valid and therefore untouched."""
    _validate({"platform": "azdo", "organization": "example-org", "project": "Example Project"})


def test_config_validates_with_work_tracking() -> None:
    _validate(
        {
            "platform": "azdo",
            "organization": "example-org",
            "project": "Example Project",
            "work_tracking": {
                "default_area_path": "Example Project\\Example Area",
                "default_iteration_path": "Example Project\\Iteration 1",
                "default_work_item_type": "User Story",
                "tags": ["example-tag"],
                "review_on_specify": True,
            },
        }
    )


def test_config_rejects_organization_inside_work_tracking() -> None:
    """Identity is read from the top-level fields so the two can never disagree."""
    with pytest.raises(jsonschema.ValidationError):
        _validate(
            {
                "platform": "azdo",
                "work_tracking": {
                    "default_area_path": "Example Project\\Example Area",
                    "organization": "example-org",
                },
            }
        )


def test_config_rejects_work_tracking_without_default_area_path() -> None:
    with pytest.raises(jsonschema.ValidationError):
        _validate({"platform": "azdo", "work_tracking": {"default_work_item_type": "User Story"}})


# --------------------------------------------------------------------------
# Review standard bound to its calibration corpus
# --------------------------------------------------------------------------


def test_corpus_matches_its_declared_schema() -> None:
    """A mistyped dimension key must fail here rather than during a grading run."""
    corpus_schema = {
        "type": "object",
        "required": ["corpus_version", "purpose", "dimensions", "cases"],
        "additionalProperties": False,
        "properties": {
            "corpus_version": {"type": "integer", "minimum": 1},
            "purpose": {"type": "string", "minLength": 1},
            "dimensions": {
                "type": "array",
                "minItems": 1,
                "uniqueItems": True,
                "items": {"type": "string", "pattern": "^[a-z_]+$"},
            },
            "cases": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["id", "intent", "item", "expected", "expected_deficiencies"],
                    "additionalProperties": False,
                    "properties": {
                        "id": {"type": "string", "pattern": "^WI-CAL-[0-9]{3}$"},
                        "intent": {"type": "string", "minLength": 1},
                        "item": {
                            "type": "object",
                            "required": ["work_item_type", "title", "description"],
                            "additionalProperties": False,
                            "properties": {
                                "work_item_type": {"type": "string", "minLength": 1},
                                "title": {"type": "string", "minLength": 1},
                                "description": {"type": "string", "minLength": 1},
                                "acceptance_criteria": {"type": "string"},
                                "tags": {"type": "array", "items": {"type": "string"}},
                            },
                        },
                        "expected": {
                            "type": "object",
                            "additionalProperties": {"enum": ["pass", "fail"]},
                        },
                        "expected_deficiencies": {
                            "type": "object",
                            "additionalProperties": {"type": "string", "minLength": 1},
                        },
                    },
                },
            },
        },
    }
    jsonschema.validate(instance=CORPUS, schema=corpus_schema)


def test_every_case_grades_exactly_the_declared_dimensions() -> None:
    declared = set(CORPUS["dimensions"])
    for case in CORPUS["cases"]:
        assert set(case["expected"]) == declared, (
            f"{case['id']} grades {sorted(case['expected'])}, corpus declares {sorted(declared)}"
        )


def test_case_ids_are_unique() -> None:
    ids = [case["id"] for case in CORPUS["cases"]]
    assert len(ids) == len(set(ids))


def test_named_deficiencies_cover_exactly_the_failing_dimensions() -> None:
    """A deficiency note on a passing dimension, or a silent failure, is a corpus bug."""
    for case in CORPUS["cases"]:
        failing = {dim for dim, verdict in case["expected"].items() if verdict == "fail"}
        assert set(case["expected_deficiencies"]) == failing, (
            f"{case['id']} fails {sorted(failing)} but names deficiencies for "
            f"{sorted(case['expected_deficiencies'])}"
        )


def test_standard_records_the_corpus_version_it_is_calibrated_against() -> None:
    """The drift guard: the pair moves together or the calibration is void."""
    text = STANDARD_PATH.read_text(encoding="utf-8")
    match = re.search(r"`corpus_version:\s*(\d+)`", text)
    assert match is not None, "the standard must record the corpus_version it was calibrated against"
    assert int(match.group(1)) == CORPUS["corpus_version"], (
        "templates/workitem-standard.md and the calibration corpus have drifted apart; "
        "both must change in the same commit"
    )
    assert CORPUS_PATH.relative_to(ROOT).as_posix() in text.replace("\\", "/")


def test_standard_enumerates_the_same_dimensions_in_the_same_order() -> None:
    text = STANDARD_PATH.read_text(encoding="utf-8")
    headings = re.findall(r"^### `([a-z_]+)`$", text, re.MULTILINE)
    assert headings == CORPUS["dimensions"]


def test_standard_declares_the_same_verdict_vocabulary_as_the_corpus() -> None:
    text = STANDARD_PATH.read_text(encoding="utf-8")
    corpus_verdicts = {verdict for case in CORPUS["cases"] for verdict in case["expected"].values()}
    declared = set(re.findall(r"exactly two values: `(\w+)` and `(\w+)`", text)[0])
    assert declared == corpus_verdicts


def test_standard_requires_every_dimension_to_be_reported() -> None:
    """The multi-failure case only means something if partial reporting is banned."""
    text = STANDARD_PATH.read_text(encoding="utf-8").lower()
    assert "every" in text and "dimension" in text
    multi_failure = [c for c in CORPUS["cases"] if list(c["expected"].values()).count("fail") > 1]
    assert multi_failure, "the corpus must retain a case that fails more than one dimension"


# --------------------------------------------------------------------------
# Helper pair: execution harness
#
# Every assertion below runs against the recorded fixture, so none of them needs
# an Azure DevOps organization, a credential, or a network.
# --------------------------------------------------------------------------

PS_HELPER = ROOT / "scripts/powershell/workitem.ps1"
SH_HELPER = ROOT / "scripts/bash/workitem.sh"
FIXTURE = ROOT / "tests/fixtures/workitem/recorded-responses.json"
GOLDEN_READ = ROOT / "tests/fixtures/workitem/expected-read-4242.json"

ORG = "Contoso"
PROJECT = "Platform"

ENVELOPE_KEYS = ["contract", "operation", "ok", "error", "warnings", "data"]
SNAPSHOT_KEYS = [
    "id",
    "rev",
    "type",
    "title",
    "state",
    "area_path",
    "iteration_path",
    "tags",
    "description",
    "acceptance_criteria",
    "story_points",
    "assigned_to",
    "url",
    "truncated",
]
ERROR_CODES = [
    "cli_missing",
    "extension_missing",
    "auth_failed",
    "item_unresolvable",
    "type_unsupported",
    "context_unresolved",
]
# The contract also declares `existing_link`, which only the pull-request linkage path can
# raise. It is deliberately absent here: asserting that a helper mentions a code it has no
# occasion to emit would make this list a spelling check rather than a coverage check.
WARNING_CODES = [
    "area_mismatch",
    "story_points_unsupported",
    "iteration_missing",
    "content_truncated",
    "fixture_mode",
]

OPEN_MARKER = "<<<UNTRUSTED-WORKITEM-DATA"
CLOSE_MARKER = "UNTRUSTED-WORKITEM-DATA"
NEUTRALISED = "UNTRUSTED_WORKITEM_DATA_NEUTRALIZED"


def _find_bash() -> str | None:
    """Locate a bash that can actually reach jq.

    On Windows the first bash on PATH is usually the WSL stub, which runs against a
    different filesystem and does not inherit the Windows PATH, so jq is absent there
    even when it is installed. Git Bash does inherit it. The probe decides rather than
    the name, so this keeps working wherever the test happens to run.
    """
    candidates: list[str] = []
    if os.name == "nt":
        candidates.append(r"C:\Program Files\Git\bin\bash.exe")
    on_path = shutil.which("bash")
    if on_path:
        candidates.append(on_path)
    for candidate in candidates:
        if not Path(candidate).exists():
            continue
        try:
            probe = subprocess.run(
                [candidate, "-c", "command -v jq"], capture_output=True, timeout=60
            )
        except OSError:
            continue
        if probe.returncode == 0:
            return candidate
    return None


PWSH = shutil.which("pwsh")
BASH = _find_bash()

requires_pwsh = pytest.mark.skipif(PWSH is None, reason="PowerShell is not installed")
requires_bash = pytest.mark.skipif(BASH is None, reason="no bash with jq is installed")
requires_both = pytest.mark.skipif(
    PWSH is None or BASH is None, reason="both helper languages are required"
)

_PWSH_FLAGS = {
    "id": "-Id",
    "url": "-Url",
    "fixture": "-Fixture",
    "organization": "-Organization",
    "project": "-Project",
    "area_path": "-AreaPath",
    "rev": "-Rev",
    "text": "-Text",
    "type": "-Type",
    "title": "-Title",
    "description_html": "-DescriptionHtml",
    "acceptance_criteria_html": "-AcceptanceCriteriaHtml",
}
_BASH_FLAGS = {
    "id": "--id",
    "url": "--url",
    "fixture": "--fixture",
    "organization": "--organization",
    "project": "--project",
    "area_path": "--area-path",
    "rev": "--rev",
    "text": "--text",
    "type": "--type",
    "title": "--title",
    "description_html": "--description-html",
    "acceptance_criteria_html": "--acceptance-criteria-html",
}

# The area the fixture's first item sits under, and an area it demonstrably does not.
CONFIGURED_AREA = "Contoso\\Platform"
FOREIGN_AREA = "Contoso\\Elsewhere"


def _run(
    language: str,
    operation: str,
    *,
    fields: dict[str, str] | None = None,
    references: list[str] | None = None,
    confirmed: bool = False,
    cwd: Path | None = None,
    **options: object,
) -> subprocess.CompletedProcess[bytes]:
    """Invoke one helper and return its raw bytes.

    Output is never decoded by an intermediate shell. The helpers promise UTF-8 on
    standard output, and routing that through a console would re-encode it in the host
    code page and destroy the very property these tests exist to check.
    """
    supplied = {key: value for key, value in options.items() if value is not None}
    if language == "pwsh":
        argv: list[str] = [str(PWSH), "-NoProfile", "-File", str(PS_HELPER), "-Operation", operation]
        for key, value in supplied.items():
            argv += [_PWSH_FLAGS[key], str(value)]
        for name, value in (fields or {}).items():
            argv += ["-Field", name, "-Value", value]
        # PowerShell spells "more than one" as an array rather than a repeated flag.
        if references:
            argv += ["-Reference", ",".join(references)]
        if confirmed:
            argv.append("-Confirmed")
        argv.append("-Json")
    else:
        argv = [str(BASH), SH_HELPER.as_posix(), "--operation", operation]
        for key, value in supplied.items():
            argv += [_BASH_FLAGS[key], str(value)]
        for name, value in (fields or {}).items():
            argv += ["--field", name, "--value", value]
        for reference in references or ():
            argv += ["--reference", reference]
        if confirmed:
            argv.append("--confirmed")
        argv.append("--json")
    return subprocess.run(argv, capture_output=True, cwd=cwd or ROOT, timeout=60)


def _read(
    language: str,
    item_id: int = 4242,
    fixture: Path = FIXTURE,
    **options: object,
) -> subprocess.CompletedProcess[bytes]:
    return _run(
        language,
        "read",
        id=item_id,
        fixture=fixture,
        organization=ORG,
        project=PROJECT,
        **options,
    )


def _parse(completed: subprocess.CompletedProcess[bytes]) -> dict:
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    return json.loads(
        completed.stdout.decode("utf-8"), object_pairs_hook=collections.OrderedDict
    )


def _unwrap(value: str) -> str:
    """Strip the untrusted-data envelope and return the body it guards."""
    assert value.startswith(OPEN_MARKER + "\n")
    assert value.endswith("\n" + CLOSE_MARKER)
    return value[len(OPEN_MARKER) + 1 : -(len(CLOSE_MARKER) + 1)]


# --------------------------------------------------------------------------
# Canonical response form
# --------------------------------------------------------------------------


@requires_pwsh
def test_response_is_one_utf8_line_without_a_bom() -> None:
    raw = _read("pwsh").stdout
    assert raw.endswith(b"\n")
    assert raw.count(b"\n") == 1, "the response is a single line terminated once"
    assert b"\r" not in raw, "a carriage return would break byte-for-byte comparison"
    assert not raw.startswith(b"\xef\xbb\xbf"), "a byte-order mark is not part of the contract"
    raw.decode("utf-8")


@requires_pwsh
def test_envelope_declares_its_keys_in_the_pinned_order() -> None:
    payload = _parse(_read("pwsh"))
    assert list(payload.keys()) == ENVELOPE_KEYS


@requires_pwsh
def test_snapshot_declares_its_keys_in_the_pinned_order() -> None:
    payload = _parse(_read("pwsh"))
    assert list(payload["data"].keys()) == SNAPSHOT_KEYS


@requires_pwsh
def test_absent_values_are_null_rather_than_omitted_or_empty() -> None:
    """A reader distinguishes "not set" from "set to nothing" only if one form is banned."""
    payload = _parse(_read("pwsh", item_id=4243, area_path=CONFIGURED_AREA))
    assert payload["error"] is None
    assert payload["data"]["iteration_path"] is None
    assert payload["data"]["story_points"] is None
    assert "" not in payload["data"].values()


# --------------------------------------------------------------------------
# Cross-language parity
# --------------------------------------------------------------------------


@requires_both
@pytest.mark.parametrize("item_id", [4242, 4243])
def test_both_languages_emit_identical_bytes_for_read(item_id: int) -> None:
    from_pwsh = _read("pwsh", item_id=item_id, area_path=CONFIGURED_AREA)
    from_bash = _read("bash", item_id=item_id, area_path=CONFIGURED_AREA)
    assert from_pwsh.stdout == from_bash.stdout


@requires_both
def test_both_languages_emit_identical_bytes_for_check() -> None:
    """`check` reports the local environment, so its content varies by machine.

    What cannot vary is that the two implementations agree about it. A committed
    golden file would only encode whichever machine produced it.
    """
    from_pwsh = _run("pwsh", "check", organization=ORG, project=PROJECT)
    from_bash = _run("bash", "check", organization=ORG, project=PROJECT)
    assert from_pwsh.stdout == from_bash.stdout


@requires_pwsh
def test_pwsh_read_matches_the_committed_golden() -> None:
    assert _read("pwsh", area_path=CONFIGURED_AREA).stdout == GOLDEN_READ.read_bytes()


@requires_bash
def test_bash_read_matches_the_committed_golden() -> None:
    """Checked against the same file as PowerShell.

    Comparing the two languages to each other proves they agree; comparing both to a
    committed file is what catches them drifting together.
    """
    assert _read("bash", area_path=CONFIGURED_AREA).stdout == GOLDEN_READ.read_bytes()


# --------------------------------------------------------------------------
# Untrusted retrieved content
# --------------------------------------------------------------------------


@requires_pwsh
def test_retrieved_free_text_is_wrapped_in_the_untrusted_envelope() -> None:
    data = _parse(_read("pwsh"))["data"]
    for field in ("description", "acceptance_criteria"):
        assert data[field].startswith(OPEN_MARKER + "\n")
        assert data[field].endswith("\n" + CLOSE_MARKER)


@requires_pwsh
def test_an_embedded_marker_cannot_close_the_envelope_early() -> None:
    body = _unwrap(_parse(_read("pwsh"))["data"]["acceptance_criteria"])
    assert CLOSE_MARKER not in body
    assert NEUTRALISED in body


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
@pytest.mark.parametrize(
    "fragment",
    [
        "Line one\r\nLine two",
        "\ttabbed",
        "`cmd`",
        "$sigil",
        "%percent%",
        '"double"',
        "'single'",
        "<script>alert(1)</script>",
        "&amp;",
        "C:\\temp\\path",
        "café",
        "—",
        "naïve",
        "日本語",
    ],
)
def test_hostile_content_survives_the_round_trip(language: str, fragment: str) -> None:
    """Nothing is escaped away, re-encoded, or helpfully cleaned up in transit."""
    body = _unwrap(_parse(_read(language))["data"]["description"])
    assert fragment in body


@requires_pwsh
def test_title_is_carried_through_without_escaping() -> None:
    assert _parse(_read("pwsh"))["data"]["title"] == 'Quoted "title" with <angle> & ampersand'


# --------------------------------------------------------------------------
# Bounded retrieval
# --------------------------------------------------------------------------

# The cap the helpers declare. A field one character longer must be cut; a field exactly
# this long must not, because an off-by-one here silently shortens honest content.
MAX_FIELD_CHARS = 8000


def _oversized_fixture(tmp_path: Path, *, description: int, acceptance: int) -> Path:
    """Write a fixture whose free text is as long as the caller asks for.

    Generated rather than committed: eight thousand characters of filler in the
    repository would be eight thousand characters every reader has to scroll past to
    find the two that matter.
    """
    path = tmp_path / "oversized.json"
    path.write_text(
        json.dumps(
            {
                "fixture_version": 1,
                "purpose": "Generated for the retrieval bound.",
                "responses": {
                    "read:4242": {
                        "id": 4242,
                        "rev": 1,
                        "fields": {
                            "System.Rev": 1,
                            "System.WorkItemType": "User Story",
                            "System.Title": "Oversized",
                            "System.State": "Active",
                            "System.AreaPath": "Contoso\\Platform",
                            "System.IterationPath": "Contoso\\Sprint 1",
                            "System.Description": "d" * description,
                            "Microsoft.VSTS.Common.AcceptanceCriteria": "a" * acceptance,
                            "Microsoft.VSTS.Scheduling.StoryPoints": 1,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return path


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_oversized_text_is_cut_to_the_declared_cap(language: str, tmp_path: Path) -> None:
    """The bound is the point. Text arriving over it leaves at exactly the limit."""
    fixture = _oversized_fixture(tmp_path, description=MAX_FIELD_CHARS + 1, acceptance=10)
    payload = _parse(_read(language, fixture=fixture))
    assert len(_unwrap(payload["data"]["description"])) == MAX_FIELD_CHARS


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_truncation_names_the_fields_it_cut(language: str, tmp_path: Path) -> None:
    """A warning says something was shortened; only the list says which thing.

    Without the names a caller holding a long item cannot tell whether the body, the
    acceptance criteria, or both are now incomplete -- so they must re-fetch all of it
    to find out, which is the cost the list exists to remove.
    """
    fixture = _oversized_fixture(
        tmp_path, description=MAX_FIELD_CHARS + 1, acceptance=MAX_FIELD_CHARS + 1
    )
    payload = _parse(_read(language, fixture=fixture))
    assert "content_truncated" in payload["warnings"]
    assert payload["data"]["truncated"] == ["description", "acceptance_criteria"]


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_only_the_oversized_field_is_named(language: str, tmp_path: Path) -> None:
    """A list that names an untouched field is a false report of data loss."""
    fixture = _oversized_fixture(tmp_path, description=10, acceptance=MAX_FIELD_CHARS + 1)
    payload = _parse(_read(language, fixture=fixture))
    assert payload["data"]["truncated"] == ["acceptance_criteria"]


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_content_at_the_cap_is_left_whole(language: str, tmp_path: Path) -> None:
    """Exactly at the limit is within it, and reports no loss at all."""
    fixture = _oversized_fixture(tmp_path, description=MAX_FIELD_CHARS, acceptance=10)
    payload = _parse(_read(language, fixture=fixture))
    assert payload["data"]["truncated"] == []
    assert "content_truncated" not in payload["warnings"]


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_an_item_within_the_bound_reports_nothing_truncated(language: str) -> None:
    """The field is always present, so a caller never has to test for its absence."""
    assert _parse(_read(language))["data"]["truncated"] == []


# --------------------------------------------------------------------------
# Warnings
# --------------------------------------------------------------------------


@requires_pwsh
def test_fixture_backed_output_identifies_itself() -> None:
    """A caller must never mistake recorded data for something read from the service."""
    assert "fixture_mode" in _parse(_read("pwsh"))["warnings"]


@requires_pwsh
def test_warnings_describe_the_item_rather_than_the_request() -> None:
    payload = _parse(_read("pwsh", item_id=4243, area_path=CONFIGURED_AREA))
    assert set(payload["warnings"]) == {
        "fixture_mode",
        "area_mismatch",
        "iteration_missing",
        "story_points_unsupported",
    }


@requires_pwsh
def test_an_item_inside_the_configured_area_raises_no_mismatch() -> None:
    payload = _parse(_read("pwsh", area_path=CONFIGURED_AREA))
    assert "area_mismatch" not in payload["warnings"]


@requires_pwsh
def test_an_item_outside_the_configured_area_raises_a_mismatch() -> None:
    payload = _parse(_read("pwsh", area_path=FOREIGN_AREA))
    assert "area_mismatch" in payload["warnings"]


@requires_both
def test_both_languages_agree_on_warnings() -> None:
    from_pwsh = _parse(_read("pwsh", item_id=4243, area_path=CONFIGURED_AREA))
    from_bash = _parse(_read("bash", item_id=4243, area_path=CONFIGURED_AREA))
    assert from_pwsh["warnings"] == from_bash["warnings"]


# --------------------------------------------------------------------------
# Failures
# --------------------------------------------------------------------------


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_an_unknown_item_fails_with_a_cause_and_an_action(language: str) -> None:
    payload = _parse(_read(language, item_id=9999))
    assert payload["ok"] is False
    assert payload["data"] == {}
    failure = payload["error"]
    assert failure["code"] == "item_unresolvable"
    assert failure["cause"] and failure["action"]
    assert failure["cause"] != failure["action"]


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_an_unresolved_context_is_named_as_such(language: str, tmp_path: Path) -> None:
    """Run outside any repository, so nothing can quietly supply the missing project.

    Invoked from this repository the helper would resolve a project from local
    configuration and the test would pass without ever reaching the code it names.
    """
    completed = _run(
        language, "read", id=4242, fixture=FIXTURE, organization=ORG, cwd=tmp_path
    )
    payload = _parse(completed)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "context_unresolved"


@requires_both
def test_both_languages_fail_the_same_way() -> None:
    """Identical diagnosis, each phrased in the flags its own caller would type.

    The corrective action is the one part that cannot be byte-identical: telling a
    PowerShell caller to drop `--fixture` would be advice they cannot follow.
    """
    from_pwsh = _parse(_read("pwsh", item_id=9999))["error"]
    from_bash = _parse(_read("bash", item_id=9999))["error"]
    assert from_pwsh["code"] == from_bash["code"]
    assert from_pwsh["cause"] == from_bash["cause"]
    assert "-Fixture" in from_pwsh["action"]
    assert "--fixture" in from_bash["action"]


def test_every_declared_code_appears_in_both_implementations() -> None:
    """A code named in the contract but never raised is a promise nothing keeps."""
    sources = {
        "powershell": PS_HELPER.read_text(encoding="utf-8"),
        "bash": SH_HELPER.read_text(encoding="utf-8"),
    }
    for language, text in sources.items():
        for code in ERROR_CODES + WARNING_CODES:
            assert code in text, f"{code} is missing from the {language} helper"


def test_failure_causes_and_actions_are_distinct_from_one_another() -> None:
    """An action that restates the cause tells the reader nothing they did not have.

    Distinctness is checked in three directions, because each one fails differently.
    A cause repeated across two codes means the caller cannot tell which failure they
    hit. An action repeated across two codes means the same remedy is being offered for
    two different problems, and at most one of them can be right. And an action equal to
    its own cause is a diagnosis wearing the label of a fix.
    """
    text = PS_HELPER.read_text(encoding="utf-8")
    pattern = re.compile(
        r"Write-Failure\s+'(?P<code>\w+)'\s+`\s*\n\s*(?P<cause>[\"'].*?[\"'])\s+`\s*\n\s*(?P<action>[\"'].*?[\"'])",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(text))
    assert len(matches) >= len(ERROR_CODES), "every declared failure must be raised somewhere"
    raised = {match.group("code") for match in matches}
    assert raised == set(ERROR_CODES)
    for match in matches:
        assert match.group("cause") != match.group("action")

    # One code may be raised from more than one place, so the comparison is between
    # codes rather than between raise sites.
    causes: dict[str, set[str]] = {}
    actions: dict[str, set[str]] = {}
    for match in matches:
        causes.setdefault(match.group("code"), set()).add(match.group("cause"))
        actions.setdefault(match.group("code"), set()).add(match.group("action"))
    for code, texts in causes.items():
        others = {t for other, group in causes.items() if other != code for t in group}
        assert not (texts & others), f"{code} shares a cause with another failure"
    for code, texts in actions.items():
        others = {t for other, group in actions.items() if other != code for t in group}
        assert not (texts & others), f"{code} shares its corrective action with another failure"


def test_every_failure_offers_something_the_caller_can_do() -> None:
    """A failure without a next step leaves the caller exactly where they started.

    The check is on the opening word rather than on length, because a long string that
    only elaborates on what went wrong is still not a way out of it. Holding the set
    closed is the point: a corrective action that opens with a new verb is either a
    remedy the caller has not been taught to expect, or a description wearing an
    imperative's clothes, and both are worth a second look before they ship.
    """
    text = PS_HELPER.read_text(encoding="utf-8")
    pattern = re.compile(
        r"Write-Failure\s+'(?P<code>\w+)'\s+`\s*\n\s*[\"'].*?[\"']\s+`\s*\n\s*[\"'](?P<action>.*?)[\"']",
        re.MULTILINE,
    )
    vocabulary = {"add", "check", "confirm", "install", "retry", "run", "set"}
    seen = set()
    for match in pattern.finditer(text):
        action = match.group("action").strip()
        assert action, f"{match.group('code')} names no corrective action"
        opening = re.split(r"[\s:,]", action, maxsplit=1)[0].lower()
        assert opening in vocabulary, (
            f"{match.group('code')} opens with {opening!r}, which is not one of the "
            f"corrective verbs the helper promises: {sorted(vocabulary)}"
        )
        seen.add(opening)
    assert seen == vocabulary, f"unused corrective verbs: {sorted(vocabulary - seen)}"


# --------------------------------------------------------------------------
# Write gating
# --------------------------------------------------------------------------


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
@pytest.mark.parametrize("operation", ["apply-update", "apply-create", "comment"])
def test_a_write_without_confirmation_is_a_usage_error(language: str, operation: str) -> None:
    """Refused before anything is attempted, and refused as a usage error.

    The flag is a required argument, so its absence is a malformed request rather than
    a request that was tried and failed. That distinction is what stops a caller from
    treating the refusal as a retryable condition.

    No fixture is supplied, because a fixture is what stands in for confirmation when
    there is no service to write to. This is the live path, and it must stop here --
    before the capability probe, before authentication, before any call goes out.
    """
    completed = _run(
        language,
        operation,
        id=4242,
        rev=3,
        text="a comment",
        title="New title",
        description_html="<p>why</p>",
        acceptance_criteria_html="<p>done when</p>",
        organization=ORG,
        project=PROJECT,
        fields={"title": "New title"},
    )
    assert completed.returncode == 2
    assert completed.stdout == b"", "a refused write emits no response envelope"
    message = completed.stderr.decode("utf-8", "replace").lower()
    assert "confirmed" in message


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_confirming_a_write_against_recorded_data_is_a_usage_error(language: str) -> None:
    """Confirmation means a person approved a real change; there is nothing here to approve."""
    completed = _run(
        language,
        "apply-update",
        id=4242,
        rev=3,
        fixture=FIXTURE,
        organization=ORG,
        project=PROJECT,
        fields={"title": "New title"},
        confirmed=True,
    )
    assert completed.returncode == 2
    assert completed.stdout == b""


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_proposing_a_change_requires_no_confirmation(language: str) -> None:
    """The proposal is what a person reads before confirming, so it must be reachable."""
    payload = _parse(
        _run(
            language,
            "propose-update",
            id=4242,
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            fields={"title": "New title"},
        )
    )
    assert payload["ok"] is True
    proposed = payload["data"]["proposed"]
    assert [entry["field"] for entry in proposed] == ["title"]
    assert proposed[0]["proposed"] == "New title"


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_proposal_reports_the_revision_it_was_built_against(language: str) -> None:
    payload = _parse(
        _run(
            language,
            "propose-update",
            id=4242,
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            fields={"title": "New title"},
        )
    )
    assert payload["data"]["rev"] == _parse(_read(language))["data"]["rev"]


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_write_against_a_stale_revision_is_refused(language: str) -> None:
    """Approval covers a specific version of the item, not the item forever."""
    current = _parse(_read(language))["data"]["rev"]
    payload = _parse(
        _run(
            language,
            "apply-update",
            id=4242,
            rev=current - 1,
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            fields={"title": "New title"},
        )
    )
    assert payload["ok"] is True, "a stale revision is a refusal, not a failure"
    assert payload["data"]["refused"] == "stale_revision"
    assert payload["data"]["written"] is False, "nothing may be sent when the item has moved"


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_write_against_the_current_revision_is_not_refused(language: str) -> None:
    current = _parse(_read(language))["data"]["rev"]
    payload = _parse(
        _run(
            language,
            "apply-update",
            id=4242,
            rev=current,
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            fields={"title": "New title"},
        )
    )
    assert payload["data"]["refused"] is None


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_proposal_shows_current_values_inside_the_untrusted_envelope(language: str) -> None:
    payload = _parse(
        _run(
            language,
            "propose-update",
            id=4242,
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            fields={"description": "replacement"},
        )
    )
    current = payload["data"]["proposed"][0]["current"]
    assert current.startswith(OPEN_MARKER + "\n")


# --------------------------------------------------------------------------
# The record an applied write leaves behind
# --------------------------------------------------------------------------


def _applied(language: str, rev: int = 7) -> dict:
    return _parse(
        _run(
            language,
            "apply-update",
            id=4242,
            rev=rev,
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            fields={"title": "New title"},
        )
    )


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_an_applied_write_records_what_it_changed(language: str) -> None:
    """Which run touched which item, and which fields moved.

    The keys are asserted as an ordered whole rather than one at a time: the record is
    compared across the two implementations byte for byte elsewhere, and that comparison
    only means something if the shape itself is pinned here.
    """
    audit = _applied(language)["data"]["audit"]
    assert list(audit) == ["operation", "id", "fields", "rev_before", "rev_after"]
    assert audit["operation"] == "apply-update"
    assert audit["id"] == "4242"
    assert audit["fields"] == ["title"]


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_the_record_names_fields_without_quoting_their_values(language: str) -> None:
    """An audit trail that repeats the body it wrote is a second copy of that body.

    The record travels on the redacted channel, so a value reaching it would put
    work-item text somewhere the redaction rules assume text never goes.
    """
    audit = _applied(language)["data"]["audit"]
    assert "New title" not in json.dumps(audit)


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_refused_write_leaves_no_record(language: str) -> None:
    """Nothing changed, so there is nothing to account for.

    A record here would be indistinguishable from one left by a write that landed, and
    the whole value of the trail is that its entries mean something happened.
    """
    payload = _applied(language, rev=1)
    assert payload["data"]["refused"] == "stale_revision"
    assert payload["data"]["audit"] is None


# --------------------------------------------------------------------------
# Create, then read back what a reviewer would grade
#
# The verdict itself is a judgement, and a judgement needs the calibrated standard
# rather than a test. What a test can settle is everything underneath it: that the
# material each dimension is graded on reaches the reviewer intact. A round trip that
# drops a paragraph turns a passing item into a failing one for a reason that has
# nothing to do with how it was written.
# --------------------------------------------------------------------------


def _passing_case() -> dict:
    """The corpus case that must pass all five dimensions."""
    cases = [case for case in CORPUS["cases"] if not case["expected_deficiencies"]]
    assert cases, "the corpus must retain a case that passes every dimension"
    return cases[0]


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_drafted_item_carries_every_graded_dimension(language: str) -> None:
    """Each dimension is graded on text the draft has to be able to hold."""
    case = _passing_case()
    draft = _parse(
        _run(
            language,
            "propose-create",
            type="Task",
            title=case["item"]["title"],
            description_html=case["item"]["description"],
            acceptance_criteria_html=case["item"]["acceptance_criteria"],
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            area_path=CONFIGURED_AREA,
        )
    )["data"]["draft"]
    assert draft["title"] == case["item"]["title"]
    assert draft["description"] == case["item"]["description"]
    assert draft["acceptance_criteria"] == case["item"]["acceptance_criteria"]


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_created_text_reaches_the_reviewer_unchanged(language: str, tmp_path: Path) -> None:
    """The half of SC-013 a fixture can settle.

    Whether the item then passes all five dimensions is for the calibrated standard to
    say. What this establishes is that the standard would be grading the item as
    written, rather than a copy the round trip quietly reflowed -- an item whose scope
    paragraph lost its line breaks reads as a wall of text and fails `scope` on
    presentation alone.
    """
    case = _passing_case()
    fixture = tmp_path / "created.json"
    fixture.write_text(
        json.dumps(
            {
                "fixture_version": 1,
                "purpose": "The item as the create path wrote it.",
                "responses": {
                    "read:4242": {
                        "id": 4242,
                        "rev": 1,
                        "fields": {
                            "System.Rev": 1,
                            "System.WorkItemType": case["item"]["work_item_type"],
                            "System.Title": case["item"]["title"],
                            "System.State": "New",
                            "System.AreaPath": CONFIGURED_AREA,
                            "System.IterationPath": "Contoso\\Sprint 1",
                            "System.Tags": AGENT_TAG,
                            "System.Description": case["item"]["description"],
                            "Microsoft.VSTS.Common.AcceptanceCriteria": case["item"][
                                "acceptance_criteria"
                            ],
                            "Microsoft.VSTS.Scheduling.StoryPoints": 3,
                        },
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    payload = _parse(_read(language, fixture=fixture))["data"]
    assert payload["title"] == case["item"]["title"]
    assert _unwrap(payload["description"]) == case["item"]["description"]
    assert _unwrap(payload["acceptance_criteria"]) == case["item"]["acceptance_criteria"]
    assert payload["truncated"] == []
    assert AGENT_TAG in payload["tags"]


# --------------------------------------------------------------------------
# Naming a work item
# --------------------------------------------------------------------------


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_url_supplies_the_item_the_organization_and_the_project(language: str) -> None:
    """One string carries all three, which is three fewer chances to mismatch them by hand."""
    payload = _parse(
        _run(
            language,
            "read",
            url=f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems/edit/4242",
            fixture=FIXTURE,
            area_path=CONFIGURED_AREA,
        )
    )
    assert payload["ok"] is True
    assert payload["data"]["id"] == 4242


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_url_and_an_id_that_disagree_are_refused(language: str) -> None:
    """Silently preferring one would write to whichever item the caller did not mean."""
    completed = _run(
        language,
        "read",
        id=4243,
        url=f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems/edit/4242",
        fixture=FIXTURE,
    )
    assert completed.returncode == 2
    assert completed.stdout == b""


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_something_that_is_not_a_work_item_url_is_refused(language: str) -> None:
    completed = _run(language, "read", url="https://example.com/whatever", fixture=FIXTURE)
    assert completed.returncode == 2


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_field_without_a_value_is_refused(language: str) -> None:
    """A dangling field name would otherwise write an empty string over real content."""
    if language == "pwsh":
        # PowerShell's repeat idiom is an array, and under -File it arrives as one string.
        argv = [
            str(PWSH), "-NoProfile", "-File", str(PS_HELPER), "-Operation", "propose-update",
            "-Id", "4242", "-Fixture", str(FIXTURE), "-Organization", ORG, "-Project", PROJECT,
            "-Field", "title,state", "-Value", "only one", "-Json",
        ]
    else:
        argv = [
            str(BASH), SH_HELPER.as_posix(), "--operation", "propose-update",
            "--id", "4242", "--fixture", str(FIXTURE), "--organization", ORG, "--project", PROJECT,
            "--field", "title", "--field", "state", "--value", "only one", "--json",
        ]
    completed = subprocess.run(argv, capture_output=True, cwd=ROOT, timeout=60)
    assert completed.returncode == 2


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_reference_is_accepted_in_the_forms_people_actually_write(language: str) -> None:
    payload = _parse(
        _run(
            language,
            "verify-link",
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            area_path=CONFIGURED_AREA,
            references=[
                "AB#4242",
                "#4243",
                f"https://dev.azure.com/{ORG}/{PROJECT}/_workitems/edit/4242",
            ],
        )
    )
    references = payload["data"]["references"]
    assert [entry["id"] for entry in references] == [4242, 4243], "a repeat is reported once"
    assert all(entry["resolves"] for entry in references)


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_reference_that_names_nothing_is_refused(language: str) -> None:
    """Guessing at what was meant would link the wrong person's work item."""
    completed = _run(
        language,
        "verify-link",
        fixture=FIXTURE,
        organization=ORG,
        project=PROJECT,
        references=["see the ticket"],
    )
    assert completed.returncode == 2


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_create_proposal_carries_the_supplied_content(language: str) -> None:
    payload = _parse(
        _run(
            language,
            "propose-create",
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            area_path=CONFIGURED_AREA,
            type="Bug",
            title="A title",
            description_html="<p>why it matters</p>",
            acceptance_criteria_html="<p>done when</p>",
        )
    )
    draft = payload["data"]["draft"]
    assert draft["work_item_type"] == "Bug"
    assert draft["title"] == "A title"
    assert draft["description"] == "<p>why it matters</p>"
    assert draft["acceptance_criteria"] == "<p>done when</p>"


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
@pytest.mark.parametrize("omitted", ["title", "description_html", "acceptance_criteria_html"])
def test_a_create_proposal_without_its_required_content_is_refused(
    language: str, omitted: str
) -> None:
    """An item created without a reason or a finish line is the thing this feature exists to prevent."""
    supplied = {
        "title": "A title",
        "description_html": "<p>why</p>",
        "acceptance_criteria_html": "<p>done when</p>",
    }
    del supplied[omitted]
    completed = _run(
        language,
        "propose-create",
        fixture=FIXTURE,
        organization=ORG,
        project=PROJECT,
        area_path=CONFIGURED_AREA,
        **supplied,
    )
    assert completed.returncode == 2


# --------------------------------------------------------------------------
# Redaction
# --------------------------------------------------------------------------

def test_neither_helper_prints_a_credential() -> None:
    """The Azure CLI's own diagnostics are the likeliest place for one to leak."""
    for helper in (PS_HELPER, SH_HELPER):
        text = helper.read_text(encoding="utf-8")
        assert "--debug" not in text, "the CLI's debug output can carry tokens"
        assert "--verbose" not in text
        assert "[redacted]" in text, "captured diagnostics must be scrubbed before they surface"


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_failure_carries_no_field_bodies(language: str) -> None:
    """A diagnostic names what went wrong; it does not quote the item back."""
    completed = _read(language, item_id=9999)
    combined = (completed.stdout + completed.stderr).decode("utf-8", "replace")
    assert "Ignore previous instructions" not in combined
    assert "café" not in combined


# Shapes a credential takes in CLI diagnostics. Keyword-anchored rather than
# entropy-based: a rule that flags any long opaque run would fire on legitimate
# prose and get relaxed until it caught nothing.
CREDENTIAL_SHAPES = [
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)\b(pat|token|password|secret|authorization)\s*[=:]\s*\S+"),
]


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_full_cycle_emits_nothing_credential_shaped(language: str) -> None:
    """Every operation, one after another, with both streams captured.

    Checked as a cycle rather than per operation because the risk is a single path
    that skips the scrub while its neighbours apply it, and a per-operation test
    passes happily while that one path leaks. Running the whole sequence is also what
    makes the check a standing one: the scan re-runs whenever a new operation is added,
    instead of being a capture someone took once and pasted into a gate.
    """
    cycle = [
        ("read", {"id": 4242}),
        ("propose-update", {"id": 4242, "fields": {"title": "New title"}}),
        ("apply-update", {"id": 4242, "rev": 7, "fields": {"title": "New title"}}),
        ("comment", {"id": 4242, "rev": 7, "text": "a comment"}),
        (
            "propose-create",
            {
                "type": "Task",
                "title": "A title",
                "description_html": "<p>why</p>",
                "area_path": CONFIGURED_AREA,
            },
        ),
        ("verify-link", {"references": ["AB#4242"], "area_path": CONFIGURED_AREA}),
        ("read", {"id": 9999}),  # the failure path, which is where diagnostics surface
    ]
    for operation, options in cycle:
        fields = options.pop("fields", None)
        references = options.pop("references", None)
        completed = _run(
            language,
            operation,
            fields=fields,
            references=references,
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            **options,
        )
        combined = (completed.stdout + completed.stderr).decode("utf-8", "replace")
        for shape in CREDENTIAL_SHAPES:
            assert not shape.search(combined), (
                f"{operation} emitted something credential-shaped: {shape.pattern}"
            )


# --------------------------------------------------------------------------
# Review command template
#
# The template is the public interface: packaging derives the canonical prompt
# and every platform shim from it, so what it declares is what ships.
# --------------------------------------------------------------------------

REVIEW_TEMPLATE = ROOT / "templates/commands/workitem-review.md"


def _flat(path: Path) -> str:
    """Prose wraps; a phrase spanning a line break is still the phrase."""
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))

# The nine mutable fields a review must be able to promise it left alone.
PROTECTED_FIELDS = [
    "title",
    "state",
    "area_path",
    "iteration_path",
    "tags",
    "description",
    "acceptance_criteria",
    "story_points",
    "assigned_to",
]

REVIEW_MODES = ["full", "grade-only", "comment-only"]


def test_review_template_declares_three_modes() -> None:
    text = _flat(REVIEW_TEMPLATE)
    for mode in REVIEW_MODES:
        assert f"`{mode}`" in text, f"the review command must declare the {mode!r} mode"


def test_review_template_declares_the_non_mutating_modes_non_mutating() -> None:
    """A mode advertised as safe is only safe if the promise names what it spares."""
    text = REVIEW_TEMPLATE.read_text(encoding="utf-8")
    claim = re.search(
        r"\*\*`grade-only` and `comment-only` leave all nine protected fields unchanged\*\*"
        r"(.+?)(?=\n## )",
        text,
        re.DOTALL,
    )
    assert claim is not None, "the non-mutating claim must be stated explicitly"
    body = claim.group(1)
    for field in PROTECTED_FIELDS:
        assert f"`{field}`" in body, f"the non-mutating claim must name {field!r}"


def test_review_template_proves_the_claim_by_comparison_rather_than_assertion() -> None:
    text = _flat(REVIEW_TEMPLATE).lower()
    assert "snapshot" in text
    assert "divergence" in text or "reads them again" in text


def test_review_template_defers_to_the_calibrated_standard() -> None:
    """A paraphrased rubric here would be a second, uncalibrated copy of it."""
    text = _flat(REVIEW_TEMPLATE)
    assert "workitem-standard.md" in text
    for dimension in CORPUS["dimensions"]:
        assert f"`{dimension}`" in text
    assert "only when all five dimensions pass" in text


def test_review_template_carries_a_constitution_authority_block() -> None:
    lines = REVIEW_TEMPLATE.read_text(encoding="utf-8").splitlines()
    authority = [i for i, line in enumerate(lines) if "constitution.md" in line]
    negotiable = [i for i, line in enumerate(lines) if "non-negotiable" in line.lower()]
    assert authority and negotiable
    assert min(abs(a - n) for a in authority for n in negotiable) <= 15


def test_review_template_declares_both_script_variants() -> None:
    """Packaging fails with 'no script command found' when either is missing."""
    text = _flat(REVIEW_TEMPLATE)
    assert "sh: .devspark/scripts/bash/workitem.sh --operation check --json" in text
    assert "ps: .devspark/scripts/powershell/workitem.ps1 -Operation check -Json" in text


def test_review_template_stops_cleanly_when_not_configured() -> None:
    text = _flat(REVIEW_TEMPLATE)
    assert "work_tracking_configured: false" in text


def test_review_template_passes_untrusted_data_through_intact() -> None:
    text = _flat(REVIEW_TEMPLATE).lower()
    assert "untrusted" in text
    assert "intact" in text
    assert "never remove it" in text


def test_review_template_exempts_confirmation_from_autonomy_overrides() -> None:
    """An autonomy instruction is exactly the thing that would otherwise bypass it."""
    text = _flat(REVIEW_TEMPLATE)
    assert "exempt from any autonomy override" in text
    assert "in this session" in text


def test_review_template_states_what_it_writes() -> None:
    text = _flat(REVIEW_TEMPLATE)
    assert "## Artifacts" in text
    assert "no repository files" in text


def test_review_template_operates_standalone() -> None:
    text = _flat(REVIEW_TEMPLATE).lower()
    assert "standalone" in text
    assert "no spec" in text and "no feature branch" in text


# --------------------------------------------------------------------------
# Create command template and the marker tag
# --------------------------------------------------------------------------

CREATE_TEMPLATE = ROOT / "templates/commands/workitem-create.md"
AGENT_TAG = "devspark-generated"


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_a_created_item_is_always_tagged_as_agent_generated(language: str) -> None:
    """A board with no way to tell agent items from human ones cannot be audited."""
    payload = _parse(
        _run(
            language,
            "propose-create",
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            area_path=CONFIGURED_AREA,
            type="Bug",
            title="A title",
            description_html="<p>why</p>",
            acceptance_criteria_html="<p>done when</p>",
        )
    )
    assert AGENT_TAG in payload["data"]["draft"]["tags"]


def test_the_marker_tag_is_not_configurable() -> None:
    """A tag a team could switch off would not be a reliable audit signal."""
    for helper in (PS_HELPER, SH_HELPER):
        text = helper.read_text(encoding="utf-8")
        assert f"'{AGENT_TAG}'" in text, "both helpers must carry the marker tag as a constant"


def test_create_template_creates_at_most_one_item() -> None:
    text = _flat(CREATE_TEMPLATE)
    assert "at most one work item per invocation" in text
    assert "never loops" in text


def test_create_template_declares_its_content_source() -> None:
    text = _flat(CREATE_TEMPLATE)
    assert "`spec`" in text and "`conversation`" in text
    assert "exactly two values" in text


def test_create_template_targets_the_dedicated_acceptance_criteria_field() -> None:
    """Criteria appended to the description are invisible to every board query."""
    text = _flat(CREATE_TEMPLATE)
    assert "dedicated acceptance-criteria field" in text
    assert "never appended to the description" in text


def test_create_template_requires_given_when_then_and_per_scope_decisions() -> None:
    text = _flat(CREATE_TEMPLATE)
    assert "given/when/then" in text
    assert "Given <starting condition>, when <action>, then <observable outcome>." in text
    assert "test decision for **each** scope" in text


def test_create_template_flags_inferred_details() -> None:
    text = _flat(CREATE_TEMPLATE)
    assert "flagged as unverified" in text
    assert "[inferred" in text


def test_create_template_confirms_the_type_and_the_estimate() -> None:
    text = _flat(CREATE_TEMPLATE)
    assert "Propose the type and **confirm it**" in text
    assert "and its reasoning" in text
    assert "confirmed or overridden" in text


def test_create_template_warns_on_existing_linkage() -> None:
    text = _flat(CREATE_TEMPLATE)
    assert "already references a work item, warn and ask before continuing" in text


def test_create_template_records_the_identifier_only_where_it_is_temporary() -> None:
    """A durable file naming a work-item id goes stale the moment the board is reorganised."""
    text = _flat(CREATE_TEMPLATE)
    assert ".devspark.work/specs/" in text
    assert "and nowhere else" in text
    assert "Do not write the identifier into `.knowledge/`" in text


def test_create_template_carries_a_constitution_authority_block() -> None:
    lines = CREATE_TEMPLATE.read_text(encoding="utf-8").splitlines()
    authority = [i for i, line in enumerate(lines) if "constitution.md" in line]
    negotiable = [i for i, line in enumerate(lines) if "non-negotiable" in line.lower()]
    assert authority and negotiable
    assert min(abs(a - n) for a in authority for n in negotiable) <= 15


def test_create_template_declares_both_script_variants() -> None:
    text = _flat(CREATE_TEMPLATE)
    assert "sh: .devspark/scripts/bash/workitem.sh --operation check --json" in text
    assert "ps: .devspark/scripts/powershell/workitem.ps1 -Operation check -Json" in text


def test_create_template_stops_cleanly_when_not_configured() -> None:
    text = _flat(CREATE_TEMPLATE)
    assert "work_tracking_configured: false" in text


def test_create_template_exempts_confirmation_from_autonomy_overrides() -> None:
    text = _flat(CREATE_TEMPLATE)
    assert "exempt from any autonomy override" in text
    assert "in this session" in text


def test_create_template_passes_untrusted_data_through_intact() -> None:
    text = _flat(CREATE_TEMPLATE).lower()
    assert "untrusted" in text
    assert "intact" in text
    assert "never remove it" in text


# ---------------------------------------------------------------------------
# Grounding a spec in a work item
#
# The offer has to be made while nothing has been created yet. After the branch
# script runs, the route and the short name are already fixed, so anything read
# from the work item at that point can no longer influence them.
# ---------------------------------------------------------------------------

SPECIFY_TEMPLATE = ROOT / "templates/commands/specify.md"
BRANCH_STEP = "Create the new branch/spec via the script"


def test_specify_offers_grounding_only_when_work_tracking_is_configured() -> None:
    text = _flat(SPECIFY_TEMPLATE)
    assert "work_tracking_configured" in text
    assert "--operation check --json" in text
    assert "no trace of this step" in text


def test_specify_requires_an_explicit_reference_rather_than_a_search() -> None:
    """A guessed match grounds the spec in someone else's requirement."""
    text = _flat(SPECIFY_TEMPLATE)
    assert "named an item explicitly" in text.lower()
    assert "Never search for a plausible match" in text


def test_specify_makes_the_offer_before_anything_is_created() -> None:
    text = _flat(SPECIFY_TEMPLATE)
    grounding = text.index("## Work-Item Grounding")
    branch = text.index(BRANCH_STEP)
    assert grounding < branch, "the offer must precede branch and file creation"


def test_specify_continues_when_the_review_is_declined_or_unavailable() -> None:
    text = _flat(SPECIFY_TEMPLATE)
    assert "continue drafting from the feature description alone" in text
    assert "must never block authoring a spec" in text


def test_specify_carries_the_reviewed_item_as_source_evidence() -> None:
    text = _flat(SPECIFY_TEMPLATE)
    assert "source evidence" in text
    lowered = text.lower()
    assert "untrusted-data envelope" in lowered
    assert "keep that envelope" in lowered


# ---------------------------------------------------------------------------
# Linkage on the pull request
#
# Opening a pull request is not a reason to change the board. The check reads,
# reports, and leaves the item exactly as it found it.
# ---------------------------------------------------------------------------

PR_TEMPLATES = {
    "create-pr": ROOT / "templates/commands/create-pr.md",
    "update-pr": ROOT / "templates/commands/update-pr.md",
}


@pytest.mark.parametrize("command", sorted(PR_TEMPLATES))
def test_pr_linkage_is_guarded_on_configuration(command: str) -> None:
    text = _flat(PR_TEMPLATES[command])
    assert "work_tracking_configured: true" in text
    assert "say nothing about work items" in text


@pytest.mark.parametrize("command", sorted(PR_TEMPLATES))
def test_pr_linkage_uses_the_non_mutating_path(command: str) -> None:
    text = _flat(PR_TEMPLATES[command])
    assert "`verify-link`" in text
    assert "This operation only reads." in text
    assert "never posts a comment" in text
    assert "never changes a state" in text


@pytest.mark.parametrize("command", sorted(PR_TEMPLATES))
def test_pr_linkage_preserves_references_verbatim(command: str) -> None:
    """A rewritten reference stops matching the tooling that reads it."""
    text = _flat(PR_TEMPLATES[command])
    assert "Reproduce every reference verbatim" in text
    assert "failed to resolve" in text


@pytest.mark.parametrize("command", sorted(PR_TEMPLATES))
def test_pr_linkage_warns_without_blocking(command: str) -> None:
    text = _flat(PR_TEMPLATES[command])
    assert "does not resolve" in text
    assert "outside the configured area path" in text
    assert "advisory" in text.lower()


@pytest.mark.parametrize("command", sorted(PR_TEMPLATES))
def test_posting_back_to_the_item_is_opt_in_and_separately_confirmed(command: str) -> None:
    """Agreeing to open a pull request is not agreeing to write on someone's board."""
    text = _flat(PR_TEMPLATES[command])
    assert "off unless the repository opts in" in text
    assert "confirmed on its own" in text
    assert "autonomy instruction does not supply this confirmation" in text


# --------------------------------------------------------------------------
# No User Story creation, and no work item as a side effect
# --------------------------------------------------------------------------

COMMANDS_DIR = ROOT / "templates/commands"
CREATING_OPERATIONS = ("propose-create", "apply-create")
HELPER_NAMES = ("workitem.sh", "workitem.ps1")


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
@pytest.mark.parametrize("operation", CREATING_OPERATIONS)
@pytest.mark.parametrize("spelling", ["User Story", "user story", "  USER STORY "])
def test_a_user_story_is_never_created_or_proposed(language: str, operation: str, spelling: str) -> None:
    payload = _parse(
        _run(
            language,
            operation,
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            area_path=CONFIGURED_AREA,
            type=spelling,
            title="A title",
            description_html="<p>why</p>",
            acceptance_criteria_html="<p>done when</p>",
        )
    )
    assert payload["ok"] is False
    assert payload["data"] == {}
    assert payload["error"]["code"] == "type_unsupported"
    assert "User Story" in payload["error"]["cause"]


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_an_unnamed_type_never_falls_back_to_a_user_story(language: str) -> None:
    payload = _parse(
        _run(
            language,
            "propose-create",
            fixture=FIXTURE,
            organization=ORG,
            project=PROJECT,
            area_path=CONFIGURED_AREA,
            title="A title",
            description_html="<p>why</p>",
            acceptance_criteria_html="<p>done when</p>",
        )
    )
    assert payload["data"]["draft"]["work_item_type"] == "Task"


@requires_both
@pytest.mark.parametrize("language", ["pwsh", "bash"])
def test_existing_items_of_every_type_are_still_readable(language: str) -> None:
    """The prohibition covers creation only; reading and referencing an existing item is untouched."""
    payload = _parse(_read(language))
    assert payload["ok"] is True
    assert payload["data"]["id"] == 4242


def test_only_the_developer_invoked_create_command_can_create() -> None:
    """No lifecycle command carries a creating operation, a creating script call, or a handoff to one."""
    offenders = []
    for template in sorted(COMMANDS_DIR.glob("*.md")):
        if template.name == "workitem-create.md":
            continue
        text = template.read_text(encoding="utf-8")
        if any(operation in text for operation in CREATING_OPERATIONS):
            offenders.append(f"{template.name}: names a creating operation")
        if re.search(r"agent:\s*devspark[-.]workitem[-.]create", text):
            offenders.append(f"{template.name}: hands off to the creating command")
    assert not offenders, offenders


def test_no_script_other_than_the_work_item_helpers_can_create_a_work_item() -> None:
    scripts = [p for p in (ROOT / "scripts").rglob("*") if p.is_file() and p.suffix in {".sh", ".ps1", ".py"}]
    offenders = [
        p.name
        for p in scripts
        if p.name not in HELPER_NAMES
        and any(operation in p.read_text(encoding="utf-8", errors="replace") for operation in CREATING_OPERATIONS)
    ]
    assert not offenders, offenders


def test_lifecycle_scripts_never_reach_the_tracker() -> None:
    """Closeout and lifecycle checks decide from repository evidence, so no tracking record is a dependency."""
    judge = (ROOT / "scripts/judge.py").read_text(encoding="utf-8")
    assert "workitem" not in judge
    assert "az devops" not in judge and "boards" not in judge


def test_review_does_not_hand_off_to_creation() -> None:
    assert "devspark-workitem-create" not in REVIEW_TEMPLATE.read_text(encoding="utf-8")


def test_create_template_refuses_user_story_and_is_never_a_dependency() -> None:
    text = _flat(CREATE_TEMPLATE)
    assert "`User Story` is never created by this command" in text
    assert "No other command invokes or hands off to this one" in text
    assert "a missing work item is never a reason to run it" in text


def test_taskstoissues_still_exports_nothing() -> None:
    text = _flat(COMMANDS_DIR / "taskstoissues.md")
    assert "cannot be exported" in text
    assert not any(operation in text for operation in CREATING_OPERATIONS)


def test_constitution_carries_the_permanent_prohibition() -> None:
    text = re.sub(
        r"\s+", " ", (ROOT / ".knowledge/governance/constitution.md").read_text(encoding="utf-8")
    )
    assert "must never create an Azure DevOps work item of type `User Story`" in text
    assert "must never delegate to another command or integration to create one" in text
    assert "creates a work item of any type as a side effect" in text
    assert "a missing external tracking record is never a reason to create one" in text
    assert "Specification user stories are Markdown requirements" in text


def test_closeout_completes_on_an_existing_record_and_never_manufactures_one() -> None:
    """Implementation closes on pre-merge evidence; a deferral cites a record that already exists."""
    contract = _flat(ROOT / "templates/closeout-contract.md")
    assert "Closeout never creates a work item or any other external record" in contract
    assert "a missing external record is never a reason to create one" in contract
    assert "work item or tracker record" not in contract
    for name in ("closeout.md", "verify.md", "implement.md", "plan.md", "tasks.md", "specify.md"):
        text = _flat(COMMANDS_DIR / name)
        assert "real, persistent" not in text, name
        assert "persistent `captured_as`" not in text, name


def test_published_release_validation_stays_in_the_release_process() -> None:
    release = _flat(COMMANDS_DIR / "release.md")
    assert "declared release gates" in release
    assert "report publication status from the host" in release
    contract = _flat(ROOT / "templates/closeout-contract.md")
    assert "release verification record" in contract


