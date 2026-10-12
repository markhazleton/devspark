# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Contract tests for content-aware knowledge discovery.

Knowledge that exists but cannot be found is indistinguishable from knowledge that does not
exist, so these tests pin the behavior that lets a document be reached by the concepts it
explains -- its headings, its body, and its declared aliases -- and not only by its id, title,
path, or source mappings. They also pin the ranking precedence and its explainability, because a
silent reordering would change which knowledge reaches an implementation without any other signal.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "build_knowledge_index.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "explain_context", ROOT / "scripts" / "explain-context.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def explain_context():
    return _load_module()


def _write_doc(
    repo: Path,
    relpath: str,
    *,
    title: str,
    body: str,
    aliases: list[str] | None = None,
    applies_to: list[str] | None = None,
) -> Path:
    doc = repo / relpath
    doc.parent.mkdir(parents=True, exist_ok=True)
    metadata: dict[str, object] = {"id": doc.stem, "type": "architecture", "title": title}
    if aliases is not None:
        metadata["aliases"] = aliases
    if applies_to is not None:
        metadata["appliesTo"] = applies_to
    frontmatter = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True)
    doc.write_text(f"---\n{frontmatter}---\n\n{body}", encoding="utf-8")
    return doc


def _build(repo: Path) -> dict:
    result = subprocess.run(
        [sys.executable, str(ENGINE), "--repo-root", str(repo), "--stdout"],
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    index = json.loads(result.stdout)
    # Retrieval rebuilds body text from the working tree, so helpers must know where it lives.
    index["_repo"] = str(repo)
    return index


def _node(index: dict, node_id: str) -> dict:
    return next(node for node in index["nodes"] if node["id"] == node_id)


def _match(explain_context, index: dict, topic: str, limit: int = 8) -> list[dict]:
    keywords = explain_context.tokenize(topic)
    body_text = explain_context.load_body_text(Path(index["_repo"]), index["nodes"])
    return explain_context.match_knowledge_nodes(index, keywords, limit, topic, body_text)


def _match_ids(explain_context, index: dict, topic: str, limit: int = 8) -> list[str]:
    return [node["id"] for node in _match(explain_context, index, topic, limit)]


LIFECYCLE_BODY = """# Conversation Lifecycle

## Disconnect and Abandonment

A conversation that ends without a resolution is recorded with outcome abandoned.

## CRM Transfer

## Completion
"""


def _lifecycle_repo(tmp_path: Path, **kwargs) -> Path:
    _write_doc(
        tmp_path,
        ".knowledge/architecture/conversation-lifecycle.md",
        title=kwargs.pop("title", "Conversation Lifecycle"),
        body=LIFECYCLE_BODY,
        **kwargs,
    )
    return tmp_path


def test_metadata_match_remains_valid(explain_context, tmp_path: Path) -> None:
    """A node still resolves from its id, title, path, and appliesTo alone."""
    _write_doc(
        tmp_path,
        ".knowledge/architecture/routing.md",
        title="Routing",
        body="Unrelated prose.\n",
        applies_to=["src/dispatcher/**"],
    )
    index = _build(tmp_path)
    assert _match_ids(explain_context, index, "how does routing work") == ["routing"]
    assert _match_ids(explain_context, index, "what lives in the dispatcher") == ["routing"]


def test_heading_only_discovery(explain_context, tmp_path: Path) -> None:
    """Section headings are retrievable even when the term appears nowhere else."""
    index = _build(_lifecycle_repo(tmp_path))
    assert _node(index, "conversation-lifecycle")["headings"] == [
        "Conversation Lifecycle",
        "Disconnect and Abandonment",
        "CRM Transfer",
        "Completion",
    ]
    assert _match_ids(explain_context, index, "where is crm transfer handled") == [
        "conversation-lifecycle"
    ]


def test_body_only_discovery(explain_context, tmp_path: Path) -> None:
    """Body prose is retrievable: the term appears in no heading and no metadata field."""
    index = _build(_lifecycle_repo(tmp_path))
    assert "search_text" not in _node(index, "conversation-lifecycle")
    assert _match_ids(explain_context, index, "what marks a conversation without resolution") == [
        "conversation-lifecycle"
    ]


def test_alias_discovery(explain_context, tmp_path: Path) -> None:
    """A declared alias bridges the author's vocabulary and the reader's."""
    index = _build(
        _lifecycle_repo(
            tmp_path,
            title="Conversation Disconnect",
            aliases=[
                "abandoned conversation",
                "user disconnect",
                "session termination",
                "conversation exit",
            ],
        )
    )
    assert _node(index, "conversation-lifecycle")["aliases"][0] == "abandoned conversation"
    assert _match_ids(
        explain_context, index, "why did the conversation end with outcome abandoned"
    ) == ["conversation-lifecycle"]


def test_frontmatter_is_not_indexed_as_body(explain_context, tmp_path: Path) -> None:
    """Declared metadata scores as metadata, never as prose the author wrote."""
    build_module = explain_context
    assert build_module.normalize_search_text("Prose only.\n") == "prose only."

    _write_doc(
        tmp_path,
        ".knowledge/architecture/routing.md",
        title="Routing",
        body="Prose only.\n",
        aliases=["dispatch fanout"],
    )
    index = _build(tmp_path)
    matches = _match(explain_context, index, "dispatch fanout")
    assert matches[0]["id"] == "routing"
    assert any(hit.startswith("alias:") for hit in matches[0]["matched_on"])
    assert not any(hit.startswith("body:") for hit in matches[0]["matched_on"])


def test_body_text_is_never_committed_to_the_index(tmp_path: Path) -> None:
    """Body text is rebuilt per query; committing it inflates a file reviewed on every edit."""
    index = _build(_lifecycle_repo(tmp_path))
    assert all("search_text" not in node for node in index["nodes"])


def test_exact_title_outranks_incidental_body_mention(explain_context, tmp_path: Path) -> None:
    _write_doc(tmp_path, ".knowledge/architecture/retry-policy.md", title="Retry Policy", body="x\n")
    _write_doc(
        tmp_path,
        ".knowledge/architecture/ingest.md",
        title="Ingest",
        body="The ingest worker defers to the retry policy owned elsewhere.\n",
    )
    index = _build(tmp_path)
    assert _match_ids(explain_context, index, "retry policy")[0] == "retry-policy"


def test_heading_and_alias_outrank_weak_body_mention(explain_context, tmp_path: Path) -> None:
    _write_doc(
        tmp_path,
        ".knowledge/architecture/queueing.md",
        title="Queueing",
        body="# Queueing\n\n## Backpressure\n\nHow the queue sheds load.\n",
    )
    _write_doc(
        tmp_path,
        ".knowledge/architecture/limits.md",
        title="Limits",
        body="Tuning knobs, including backpressure, are listed below.\n",
    )
    _write_doc(
        tmp_path,
        ".knowledge/architecture/intake.md",
        title="Intake",
        body="Intake accepts work.\n",
        aliases=["backpressure signals"],
    )
    ranked = _match_ids(explain_context, _build(tmp_path), "backpressure")
    assert ranked.index("queueing") < ranked.index("limits")
    assert ranked.index("intake") < ranked.index("limits")


def test_incidental_path_match_does_not_outrank_relevant_content(
    explain_context, tmp_path: Path
) -> None:
    """A term that only appears in a path mapping loses to one explained in headings and prose."""
    _write_doc(
        tmp_path,
        ".knowledge/architecture/naming.md",
        title="Naming",
        body="Unrelated prose about file naming conventions.\n",
        applies_to=["src/timeout/**"],
    )
    _write_doc(
        tmp_path,
        ".knowledge/architecture/http-client.md",
        title="HTTP Client",
        body="# HTTP Client\n\n## Timeout\n\nThe client aborts a request after the timeout.\n",
    )
    ranked = _match_ids(explain_context, _build(tmp_path), "how is timeout handled")
    assert ranked[0] == "http-client"


def test_match_evidence_explains_the_score(explain_context, tmp_path: Path) -> None:
    index = _build(_lifecycle_repo(tmp_path))
    matches = _match(explain_context, index, "disconnect with outcome abandoned")
    assert matches[0]["score"] > 0
    assert "heading: Disconnect and Abandonment" in matches[0]["matched_on"]
    assert any(entry.startswith("body: ") for entry in matches[0]["matched_on"])
    # The normalized body is a retrieval input, not agent payload.
    assert "search_text" not in matches[0]


def test_discovery_fields_are_deterministic_across_rebuilds(tmp_path: Path) -> None:
    repo = _lifecycle_repo(tmp_path, aliases=["abandoned conversation"])
    first = _build(repo)
    second = _build(repo)
    first["generated"] = second["generated"] = {}
    assert first == second


# --- 7.5.1 ranking-normalization regressions -----------------------------------------------
#
# 7.5 scored each matching field of a class (each heading, each source_of_truth entry) as an
# independent addition, so a broad document could out-rank a precise one purely by repeating a
# term in many places. These pin the fix: an evidence class contributes its weight at most once
# per query term, no matter how many fields of that class repeat the term.


def test_repeated_heading_matches_do_not_inflate_score(explain_context, tmp_path: Path) -> None:
    """Test A/B: a broad document must not out-rank a precise one by heading repetition, and
    adding more repeated headings for the same term must not raise its score further."""
    _write_doc(
        tmp_path,
        ".knowledge/architecture/precise.md",
        title="Complaint Selection",
        body="# Complaint Selection\n\nHow a chief complaint is selected for a conversation.\n",
    )
    _write_doc(
        tmp_path,
        ".knowledge/architecture/broad.md",
        title="Catalog",
        body=(
            "# Catalog\n\n## Complaint mapping\n\n## Complaint lifecycle\n\n"
            "## Complaint routing\n\n## Complaint escalation\n\nUnrelated catalog prose.\n"
        ),
    )
    scores_before = {e["id"]: e["score"] for e in _match(explain_context, _build(tmp_path), "complaint")}
    assert scores_before["precise"] > scores_before["broad"]

    _write_doc(
        tmp_path,
        ".knowledge/architecture/broad.md",
        title="Catalog",
        body=(
            "# Catalog\n\n## Complaint mapping\n\n## Complaint lifecycle\n\n"
            "## Complaint routing\n\n## Complaint escalation\n\n## Complaint archival\n\n"
            "## Complaint history\n\n## Complaint audit\n\nUnrelated catalog prose.\n"
        ),
    )
    scores_after = {e["id"]: e["score"] for e in _match(explain_context, _build(tmp_path), "complaint")}
    assert scores_after["broad"] == scores_before["broad"]
    assert scores_after["precise"] > scores_after["broad"]


def test_heading_count_normalization(explain_context, tmp_path: Path) -> None:
    """Test B: one matching heading and ten equivalent matching headings score the same
    heading-class contribution for the query term; matched_on evidence may still differ."""
    _write_doc(
        tmp_path,
        ".knowledge/architecture/single-heading.md",
        title="Single",
        body="# Single\n\n## Retry policy\n\nProse.\n",
    )
    _write_doc(
        tmp_path,
        ".knowledge/architecture/many-headings.md",
        title="Many",
        body="# Many\n\n" + "\n\n".join(f"## Retry policy {i}" for i in range(10)) + "\n\nProse.\n",
    )
    index = _build(tmp_path)
    matches = {e["id"]: e for e in _match(explain_context, index, "retry policy")}
    assert matches["single-heading"]["score"] == matches["many-headings"]["score"]
    assert len(matches["many-headings"]["matched_on"]) >= len(matches["single-heading"]["matched_on"])


def test_metadata_count_normalization(explain_context, tmp_path: Path) -> None:
    """Test C: one matching source_of_truth-style path (appliesTo) and many equivalent matching
    paths must not gain a ranking advantage from path count alone."""
    _write_doc(
        tmp_path,
        ".knowledge/architecture/one-path.md",
        title="Ingest",
        body="Ingest prose.\n",
        applies_to=["src/dispatch/**"],
    )
    one_score = next(
        e["score"] for e in _match(explain_context, _build(tmp_path), "dispatch") if e["id"] == "one-path"
    )

    _write_doc(
        tmp_path,
        ".knowledge/architecture/one-path.md",
        title="Ingest",
        body="Ingest prose.\n",
        applies_to=[f"src/dispatch/module{i}/**" for i in range(10)],
    )
    many_score = next(
        e["score"] for e in _match(explain_context, _build(tmp_path), "dispatch") if e["id"] == "one-path"
    )
    assert many_score == one_score


def test_ranking_order_scores_and_evidence_are_deterministic(explain_context, tmp_path: Path) -> None:
    """Test G: repeated runs against unchanged source produce identical ranking order, scores,
    and match reasons -- not merely an identical index."""
    repo = _lifecycle_repo(tmp_path, aliases=["abandoned conversation"])
    topic = "disconnect with outcome abandoned"
    first = _match(explain_context, _build(repo), topic)
    second = _match(explain_context, _build(repo), topic)
    snapshot = [(e["id"], e["score"], e["matched_on"]) for e in first]
    assert snapshot == [(e["id"], e["score"], e["matched_on"]) for e in second]


def test_aliases_must_be_a_list_of_non_empty_strings(tmp_path: Path) -> None:
    doc = tmp_path / ".knowledge/architecture/routing.md"
    doc.parent.mkdir(parents=True)
    doc.write_text(
        "---\nid: routing\ntype: architecture\ntitle: Routing\naliases: dispatch\n---\n\nBody.\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(ENGINE), "--repo-root", str(tmp_path), "--stdout"],
        text=True,
        capture_output=True,
        timeout=60,
    )
    assert result.returncode != 0
    assert "aliases must be an array of strings" in result.stderr


def test_headings_inside_code_fences_are_not_indexed(tmp_path: Path) -> None:
    _write_doc(
        tmp_path,
        ".knowledge/architecture/routing.md",
        title="Routing",
        body="# Routing\n\n```sh\n# not-a-heading\necho hi\n```\n\n## Real Section\n",
    )
    assert _node(_build(tmp_path), "routing")["headings"] == ["Routing", "Real Section"]
