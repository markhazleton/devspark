"""Tests for template asset discovery across GitHub releases."""

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

from devspark_cli._template import download_template_from_github


LATEST_URL = "https://api.github.com/repos/MarkHazleton/devspark/releases/latest"
RELEASES_URL = "https://api.github.com/repos/MarkHazleton/devspark/releases?per_page=10"


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, text: str = "", headers=None, chunks=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {}
        self._chunks = chunks or []

    def json(self):
        return self._payload

    def iter_bytes(self, chunk_size: int = 8192):
        del chunk_size
        for chunk in self._chunks:
            yield chunk

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        del exc_type, exc, tb
        return False


class _FakeClient:
    def __init__(self, get_map: dict[str, _FakeResponse], stream_map: dict[str, _FakeResponse]):
        self._get_map = get_map
        self._stream_map = stream_map
        self.get_calls: list[str] = []

    def get(self, url: str, **kwargs):
        del kwargs
        self.get_calls.append(url)
        response = self._get_map.get(url)
        if response is None:
            raise AssertionError(f"Unexpected GET URL: {url}")
        return response

    def stream(self, method: str, url: str, **kwargs):
        del kwargs
        if method != "GET":
            raise AssertionError(f"Unexpected method: {method}")
        response = self._stream_map.get(url)
        if response is None:
            raise AssertionError(f"Unexpected stream URL: {url}")
        return response


def test_download_template_falls_back_to_previous_release(tmp_path):
    requested_pattern = "devspark-template-claude-ps"
    download_url = "https://example.invalid/devspark-template-claude-ps-v2.2.0.zip"

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
                "name": "devspark-template-claude-ps-v2.2.0.zip",
                "browser_download_url": download_url,
                "size": 12,
            }
        ],
    }

    client = _FakeClient(
        get_map={
            LATEST_URL: _FakeResponse(payload=latest_release),
            RELEASES_URL: _FakeResponse(payload=[latest_release, previous_release]),
        },
        stream_map={
            download_url: _FakeResponse(headers={"content-length": "12"}, chunks=[b"hello", b" world!"])
        },
    )

    zip_path, metadata = download_template_from_github(
        "claude",
        tmp_path,
        script_type="ps",
        verbose=False,
        show_progress=False,
        client=client,
    )

    assert requested_pattern in metadata["filename"]
    assert metadata["release"] == "v2.2.0"
    assert zip_path.exists()
    assert zip_path.read_bytes() == b"hello world!"
    assert client.get_calls == [LATEST_URL, RELEASES_URL]


def test_download_template_errors_when_no_release_has_requested_asset(tmp_path):
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
        },
        stream_map={},
    )

    import typer

    try:
        download_template_from_github(
            "claude",
            tmp_path,
            script_type="ps",
            verbose=False,
            show_progress=False,
            client=client,
        )
        assert False, "Expected typer.Exit when no matching release asset exists"
    except typer.Exit as exc:
        assert exc.exit_code == 1
