"""Validation for upgrade release-asset preflight diagnostics."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

agent_registry_spec = importlib.util.spec_from_file_location(
    "devspark_cli.agent_registry",
    str(SRC / "devspark_cli" / "agent_registry.py"),
)
agent_registry_module = importlib.util.module_from_spec(agent_registry_spec)
sys.modules["devspark_cli.agent_registry"] = agent_registry_module
assert agent_registry_spec.loader is not None
agent_registry_spec.loader.exec_module(agent_registry_module)

cli_spec = importlib.util.spec_from_file_location(
    "devspark_cli",
    str(SRC / "devspark_cli" / "__init__.py"),
    submodule_search_locations=[str(SRC / "devspark_cli")],
)
cli_module = importlib.util.module_from_spec(cli_spec)
sys.modules["devspark_cli"] = cli_module
assert cli_spec.loader is not None
cli_spec.loader.exec_module(cli_module)

from devspark_cli.commands.upgrade import discover_upgrade_release_assets


LATEST_URL = "https://api.github.com/repos/MarkHazleton/devspark/releases/latest"
RELEASES_URL = "https://api.github.com/repos/MarkHazleton/devspark/releases?per_page=20"
RELEASES_PAGE_2_URL = "https://api.github.com/repos/MarkHazleton/devspark/releases?per_page=20&page=2"


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, text: str = "", headers=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {}

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, get_map: dict[str, _FakeResponse]):
        self._get_map = get_map
        self.get_calls: list[str] = []

    def get(self, url: str, **kwargs):
        del kwargs
        self.get_calls.append(url)
        response = self._get_map.get(url)
        if response is None:
            raise AssertionError(f"Unexpected GET URL: {url}")
        return response


def test_preflight_discovers_fallback_release_asset() -> None:
    latest_release = {
        "id": 100,
        "tag_name": "v2.2.1",
        "assets": [],
    }
    previous_release = {
        "id": 99,
        "tag_name": "v2.2.0",
        "assets": [
            {
                "name": "devspark-template-copilot-ps-v2.2.0.zip",
                "browser_download_url": "https://example.invalid/devspark-template-copilot-ps-v2.2.0.zip",
                "size": 12,
            }
        ],
    }

    client = _FakeClient(
        get_map={
            LATEST_URL: _FakeResponse(payload=latest_release),
            RELEASES_URL: _FakeResponse(payload=[latest_release, previous_release]),
        }
    )

    report = discover_upgrade_release_assets(
        "copilot",
        "ps",
        client=client,
    )

    assert report["matching_asset_name"] == "devspark-template-copilot-ps-v2.2.0.zip"
    assert report["resolved_release_tag"] == "v2.2.0"
    assert report["resolved_via_fallback"] is True
    assert report["scanned_release_count"] >= 2


def test_preflight_reports_no_match_when_assets_missing() -> None:
    latest_release = {
        "id": 100,
        "tag_name": "v2.2.1",
        "assets": [],
    }
    non_matching_release = {
        "id": 99,
        "tag_name": "v2.2.0",
        "assets": [
            {
                "name": "devspark-template-copilot-sh-v2.2.0.zip",
                "browser_download_url": "https://example.invalid/devspark-template-copilot-sh-v2.2.0.zip",
                "size": 1,
            }
        ],
    }

    client = _FakeClient(
        get_map={
            LATEST_URL: _FakeResponse(payload=latest_release),
            RELEASES_URL: _FakeResponse(payload=[latest_release, non_matching_release]),
            RELEASES_PAGE_2_URL: _FakeResponse(payload=[]),
        }
    )

    report = discover_upgrade_release_assets(
        "copilot",
        "ps",
        client=client,
    )

    assert report["matching_asset_name"] is None
    assert report["resolved_release_tag"] == "v2.2.1"
    assert report["resolved_via_fallback"] is False
