"""Tests for template asset discovery across GitHub releases."""

from __future__ import annotations

import importlib.util
import io
import sys
import zipfile
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

from devspark_cli._template import download_and_extract_template, download_template_from_github


LATEST_URL = "https://api.github.com/repos/MarkHazleton/devspark/releases/latest"
RELEASES_URL = "https://api.github.com/repos/MarkHazleton/devspark/releases?per_page=20"
RELEASES_PAGE_2_URL = "https://api.github.com/repos/MarkHazleton/devspark/releases?per_page=20&page=2"


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
    assert metadata["resolved_via_fallback"] is True
    assert metadata["latest_release"] == "v2.2.1"
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
            RELEASES_PAGE_2_URL: _FakeResponse(payload=[]),
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


def test_download_template_succeeds_from_latest_without_fallback(tmp_path):
    download_url = "https://example.invalid/devspark-template-copilot-ps-v2.2.1.zip"
    latest_release = {
        "id": 100,
        "tag_name": "v2.2.1",
        "assets": [
            {
                "name": "devspark-template-copilot-ps-v2.2.1.zip",
                "browser_download_url": download_url,
                "size": 4,
            }
        ],
    }

    client = _FakeClient(
        get_map={
            LATEST_URL: _FakeResponse(payload=latest_release),
        },
        stream_map={
            download_url: _FakeResponse(headers={"content-length": "4"}, chunks=[b"test"]),
        },
    )

    _, metadata = download_template_from_github(
        "copilot",
        tmp_path,
        script_type="ps",
        verbose=False,
        show_progress=False,
        client=client,
    )

    assert metadata["release"] == "v2.2.1"
    assert metadata["resolved_via_fallback"] is False
    assert metadata["latest_release"] == "v2.2.1"
    assert client.get_calls == [LATEST_URL]


def test_download_template_uses_explicit_release_tag(tmp_path):
    tagged_url = "https://example.invalid/devspark-template-claude-ps-v2.0.0.zip"
    tag_url = "https://api.github.com/repos/MarkHazleton/devspark/releases/tags/v2.0.0"
    tagged_release = {
        "id": 42,
        "tag_name": "v2.0.0",
        "assets": [
            {
                "name": "devspark-template-claude-ps-v2.0.0.zip",
                "browser_download_url": tagged_url,
                "size": 6,
            }
        ],
    }

    client = _FakeClient(
        get_map={
            tag_url: _FakeResponse(payload=tagged_release),
        },
        stream_map={
            tagged_url: _FakeResponse(headers={"content-length": "6"}, chunks=[b"v2", b".0.0"]),
        },
    )

    _, metadata = download_template_from_github(
        "claude",
        tmp_path,
        script_type="ps",
        release_tag="v2.0.0",
        verbose=False,
        show_progress=False,
        client=client,
    )

    assert metadata["release"] == "v2.0.0"
    assert metadata["resolved_via_fallback"] is False
    assert metadata["latest_release"] == "v2.0.0"
    assert client.get_calls == [tag_url]


def test_download_and_extract_template_preserves_explicit_release_tag(tmp_path, monkeypatch):
    tagged_url = "https://example.invalid/devspark-template-codex-ps-v2.8.0.zip"
    tag_url = "https://api.github.com/repos/MarkHazleton/devspark/releases/tags/v2.8.0"
    tagged_release = {
        "id": 84,
        "tag_name": "v2.8.0",
        "assets": [
            {
                "name": "devspark-template-codex-ps-v2.8.0.zip",
                "browser_download_url": tagged_url,
                "size": 10,
            }
        ],
    }

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as archive:
        archive.writestr(".devspark/VERSION", "version: 2.8.0\n")
        archive.writestr("AGENTS.md", "DevSpark\n")

    client = _FakeClient(
        get_map={
            tag_url: _FakeResponse(payload=tagged_release),
        },
        stream_map={
            tagged_url: _FakeResponse(
                headers={"content-length": str(len(zip_buffer.getvalue()))},
                chunks=[zip_buffer.getvalue()],
            )
        },
    )

    monkeypatch.chdir(tmp_path)
    project_path, resolved_release_tag = download_and_extract_template(
        tmp_path / "installed",
        "codex",
        "ps",
        release_tag="v2.8.0",
        verbose=False,
        client=client,
    )

    assert resolved_release_tag == "v2.8.0"
    assert (project_path / ".devspark" / "VERSION").read_text(encoding="utf-8") == "version: 2.8.0\n"
    assert client.get_calls == [tag_url]
