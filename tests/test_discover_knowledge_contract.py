"""Contracts for /devspark.discover-knowledge: evidence-backed proposals, never silent writes."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ("build_knowledge_index.py", "discover-knowledge-context.py")
GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com"]


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(text), encoding="utf-8")


def _entity(repo: Path, entity_id: str, name: str, source: str, body: str, test: str) -> None:
    base = repo / ".knowledge" / "entities" / entity_id
    _write(
        base / "_entity.yaml",
        f"id: {entity_id}\nname: {name}\nkind: knowledge-model\nsummary: {name}.\n"
        f"evidence:\n- type: test\n  ref: {test}\n  verified_by: execution\n",
    )
    _write(base / "architecture.md", f"---\nsource_of_truth:\n- {source}\nlast_verified: '2026-09-01'\n---\n\n{body}")


@pytest.fixture(scope="module")
def shop(tmp_path_factory: pytest.TempPathFactory) -> Path:
    repo = tmp_path_factory.mktemp("shop")
    for name in SCRIPTS:
        target = repo / ".devspark" / "scripts" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / "scripts" / name, target)
    _write(repo / "README.md", "# Shop\n\nRun `make dev` to start locally.\n")
    _write(repo / "src/orders/checkout.py", """\
        from src.payments.authorize import authorize_payment

        MAX_RETRIES = 5


        class OrderCheckout:
            def __init__(self, shipping_address_text):
                self.shipping_address_text = shipping_address_text


        def place_order_checkout(shipping_address_text):
            return authorize_payment(OrderCheckout(shipping_address_text))
        """)
    _write(repo / "src/orders/fulfillment.py", """\
        def validate_shipping_address(shipping_address_text):
            return shipping_address_text.strip().lower()
        """)
    _write(repo / "src/payments/authorize.py", "def authorize_payment(order):\n    return {'authorized': order}\n")
    _write(repo / "src/payments/model.py", "class PaymentAuthorization:\n    pass\n")
    _write(repo / "src/config/settings.py", "CONFIGURATION_DEFAULTS = {'region': 'us'}\n")
    for name in ("queue", "slots", "rules"):
        _write(repo / f"src/scheduler/{name}.py", f"class Scheduler{name.title()}:\n    appointment_slot_window = 30\n")
    for index in range(4):
        _write(repo / f"src/reports/report_{index}.py", f"def build_report_{index}():\n    return {index}\n")
    _write(repo / "tests/test_scheduler.py", "from src.scheduler import queue, slots\n\ndef test_queue():\n    assert queue\n")
    _write(repo / "tests/test_checkout_flow.py", """\
        from src.orders.checkout import place_order_checkout
        from src.payments.authorize import authorize_payment

        def test_flow():
            assert place_order_checkout("1 Main St")
            assert authorize_payment
        """)
    _entity(repo, "order-checkout", "Order Checkout", "src/orders", """\
        # Order Checkout

        Checkout places an order and retries 3 times through
        `src/orders/legacy_router.py`.

        Previously, orders were routed through a static table that was replaced in 2023.
        """, "tests/test_checkout_flow.py")
    _entity(repo, "payment-authorization", "Payment Authorization", "src/payments", "# Payment Authorization\n\nPayments are authorized for orders.\n", "tests/test_checkout_flow.py")
    _entity(repo, "configuration", "Configuration", "src", "# Configuration\n\nDefaults live in settings.\n", "tests/test_checkout_flow.py")
    _write(repo / ".knowledge/guides/local-setup.md", "---\nsource_of_truth:\n- README.md\nlast_verified: '2026-09-01'\n---\n\n# Local Setup\n\nRun `make dev`.\n")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run([*GIT, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*GIT, "commit", "-qm", "fixture"], cwd=repo, check=True)
    return repo


def _discover(repo: Path, *args: str) -> dict:
    before = sorted(str(path) for path in repo.rglob("*") if ".git" not in path.parts)
    result = subprocess.run(
        [sys.executable, str(repo / ".devspark/scripts/discover-knowledge-context.py"), "--root", str(repo), *args],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    after = sorted(str(path) for path in repo.rglob("*") if ".git" not in path.parts)
    assert before == after, "discovery must never write"
    return json.loads(result.stdout)


@pytest.fixture(scope="module")
def report(shop: Path) -> dict:
    return _discover(shop, "--all")


def test_unmapped_behavior_is_reported_not_created(report: dict, shop: Path) -> None:
    clusters = {item["area"]: item for item in report["source_clusters"]}
    scheduler = clusters["src/scheduler/**"]
    assert scheduler["production_files"] == 3
    assert scheduler["mapped_by"] == ["configuration"], "only the over-broad mapping touches it"
    assert "tests/test_scheduler.py" in scheduler["sample_tests"]
    assert not (shop / ".knowledge/entities/scheduler").exists()


def test_missing_relationship_is_proposed_with_evidence(report: dict) -> None:
    pairs = {tuple(item["pair"]): item for item in report["relationship_signals"]}
    signal = pairs[("order-checkout", "payment-authorization")]
    assert signal["code_dependencies"]["order-checkout -> payment-authorization"] == ["src/orders/checkout.py"]
    assert "tests/test_checkout_flow.py" in signal["tests_together"]
    assert signal["context_path"]["lexical_seed"] == "order-checkout"


def test_over_broad_mapping_is_identified(report: dict) -> None:
    rows = [item for item in report["mapping_breadth"] if item["node"] == "configuration"]
    assert rows[0]["mapping"] == "src" and rows[0]["code_files"] == 12
    assert rows[0]["concept_density"] < 0.2
    overlaps = {tuple(item["nodes"]) for item in report["ownership_overlaps"]}
    assert ("configuration", "order-checkout") in overlaps


def test_alias_candidate_comes_from_repository_vocabulary(report: dict) -> None:
    aliases = {item["node"]: [c["candidate"] for c in item["candidates"]] for item in report["alias_signals"]}
    assert "shipping address" in aliases["order-checkout"]


def test_contradiction_signal_cites_the_stale_claim(report: dict) -> None:
    stale = [(item["document"], item["reference"]) for item in report["stale_references"]]
    assert (".knowledge/entities/order-checkout/architecture.md", "src/orders/legacy_router.py") in stale


def test_historical_leakage_is_flagged_not_deleted(report: dict, shop: Path) -> None:
    history = {item["document"]: item for item in report["historical_signals"]}
    doc = ".knowledge/entities/order-checkout/architecture.md"
    assert {line["pattern"] for line in history[doc]["lines"]} & {"previously", "replaced"}
    assert "Previously" in (shop / doc).read_text(encoding="utf-8")


def test_simple_guide_gets_no_pressure_to_become_an_entity(report: dict) -> None:
    shapes = {item.get("node") or item.get("area"): item for item in report["node_shape"]}
    assert shapes["local-setup"]["signal_count"] == 0


def test_scopes_are_explicit(shop: Path) -> None:
    missing = subprocess.run(
        [sys.executable, str(shop / ".devspark/scripts/discover-knowledge-context.py"), "--root", str(shop)],
        text=True, capture_output=True, check=False,
    )
    assert missing.returncode == 2, "repository-wide discovery must be explicit"
    by_entity = _discover(shop, "order-checkout")
    assert by_entity["scope"]["mode"] == "node"
    assert by_entity["scope"]["neighbors"] == []
    by_path = _discover(shop, "src/scheduler")
    assert [item["area"] for item in by_path["source_clusters"]] == ["src/scheduler/**"]
    by_term = _discover(shop, "checkout")
    assert "order-checkout" in by_term["scope"]["matched_nodes"]


def test_prompt_contract() -> None:
    command = (ROOT / "templates/commands/discover-knowledge.md").read_text(encoding="utf-8")
    for heading in (
        "Knowledge Gaps", "Mapping Gaps", "Mapping Ambiguities", "Relationship Candidates",
        "Alias Candidates", "Contradictions", "Historical Leakage", "Potential Entity Candidates",
    ):
        assert heading in command
    for phrase in (
        "Discovery proposes. Evidence supports. Humans approve.",
        "PROVEN CONTRADICTION",
        "POSSIBLE INCONSISTENCY — HUMAN REVIEW REQUIRED",
        "flat knowledge document",
        "entity candidate",
        "discover-knowledge-context.py",
        "Do not bulk-apply",
        "--bootstrap",
    ):
        assert phrase in command, phrase
    site_audit = (ROOT / "templates/commands/site-audit.md").read_text(encoding="utf-8")
    assert "/devspark.discover-knowledge" in site_audit


def _large_repo(root: Path, entities: int, files: int) -> Path:
    """Entities whose modules import the next entity's module of the same name."""
    for index in range(entities):
        name, following = f"domain{index:02d}", f"domain{(index + 1) % entities:02d}"
        for number in range(files):
            _write(
                root / "src" / name / f"module_{number:03d}.py",
                f"from src.{following}.module_{number:03d} import helper\n\n"
                + "".join(f"def {name}_step_{step}(value):\n    return helper(value)\n\n" for step in range(15)),
            )
        _write(root / "tests" / f"test_{name}.py", f"from src.{name}.module_000 import helper\n")
        _entity(root, name, f"Domain {index}", f"src/{name}", f"# Domain {index}\n", f"tests/test_{name}.py")
    for name in SCRIPTS:
        target = root / ".devspark" / "scripts" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / "scripts" / name, target)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run([*GIT, "add", "-A"], cwd=root, check=True)
    subprocess.run([*GIT, "commit", "-qm", "large"], cwd=root, check=True)
    return root


def test_large_repositories_stay_fast_deterministic_and_precise(tmp_path: Path) -> None:
    import os
    import time

    repo = _large_repo(tmp_path / "large", entities=20, files=40)
    command = [sys.executable, str(repo / ".devspark/scripts/discover-knowledge-context.py"), "--root", str(repo), "--all"]
    outputs = []
    for seed in ("1", "2"):
        started = time.monotonic()
        result = subprocess.run(command, text=True, capture_output=True, check=True, env={**os.environ, "PYTHONHASHSEED": seed})
        # 800 files across 20 entities took over a minute with per-needle regex scans.
        assert time.monotonic() - started < 15, "discovery must scale to large repositories"
        outputs.append(result.stdout)
    assert outputs[0] == outputs[1], "output must not depend on hash ordering"

    pairs = {tuple(item["pair"]) for item in json.loads(outputs[0])["relationship_signals"]}
    assert ("domain00", "domain01") in pairs, "a real import is a relationship signal"
    assert ("domain00", "domain05") not in pairs, "a shared module name inside another package's dotted path is not"
