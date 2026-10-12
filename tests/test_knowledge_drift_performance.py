# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""Bounded, offline, same-process benchmark for the knowledge-drift comparison profiles.

Compares the retained, simpler `exact-text-v1` whole-file canonicalization (the pre-existing
approach) against the added `python-token-v1` tokenization-based canonicalization (which suppresses
comment/trivia differences) over the same fixed, committed corpus
(`tests/fixtures/knowledge-drift/performance-corpus/`). Never spawns a subprocess per run and never
depends on the network or this repository's own Git history.
"""

from __future__ import annotations

import importlib.util
import json
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "scripts" / "build_knowledge_index.py"
CORPUS = ROOT / "tests" / "fixtures" / "knowledge-drift" / "performance-corpus"
SOURCE_DIR = CORPUS / "source"

RUN_TIMEOUT_SECONDS = 30
WARMUP_RUNS = 1
MEASURED_RUNS = 7
# The exact-text profile is dominated by file I/O while tokenization adds CPU work, so their ratio
# varies with OS and filesystem cache state. Bound the 60-file token sweep directly instead.
MAX_TOKEN_SWEEP_SECONDS = 0.05


def _load_engine():
    spec = importlib.util.spec_from_file_location("build_knowledge_index", ENGINE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sweep(engine, profile: str) -> list[float]:
    files = sorted(SOURCE_DIR.glob("*.py"))
    durations: list[float] = []
    for run_index in range(WARMUP_RUNS + MEASURED_RUNS):
        engine.reset_canonicalization_cache()
        start = time.perf_counter()
        for path in files:
            engine.canonicalize_source(path, profile)
        elapsed = time.perf_counter() - start
        assert elapsed <= RUN_TIMEOUT_SECONDS, (
            f"single {profile} sweep exceeded the {RUN_TIMEOUT_SECONDS}s bound: {elapsed:.2f}s"
        )
        if run_index < WARMUP_RUNS:
            continue
        durations.append(elapsed)
    return durations


def test_python_token_v1_stays_within_the_absolute_runtime_budget(tmp_path: Path) -> None:
    del tmp_path  # unused: the fixed corpus is read directly, never mutated
    engine = _load_engine()
    expected = json.loads((CORPUS / "expected-inventory.json").read_text(encoding="utf-8"))

    files = sorted(SOURCE_DIR.glob("*.py"))
    assert len(files) == expected["source_files"], (
        "performance-corpus/source/ file count no longer matches expected-inventory.json -- "
        "corpus was edited; regenerate deterministically and update the manifest"
    )

    legacy_durations = _sweep(engine, "exact-text-v1")
    object_durations = _sweep(engine, "python-token-v1")

    assert len(legacy_durations) == MEASURED_RUNS
    assert len(object_durations) == MEASURED_RUNS

    legacy_median = statistics.median(legacy_durations)
    object_median = statistics.median(object_durations)
    assert object_median <= MAX_TOKEN_SWEEP_SECONDS, (
        f"python-token-v1 sweep median ({object_median:.4f}s) exceeded the absolute "
        f"{MAX_TOKEN_SWEEP_SECONDS:.2f}s budget over {len(files)} files; "
        f"exact-text-v1 median was {legacy_median:.4f}s"
    )
