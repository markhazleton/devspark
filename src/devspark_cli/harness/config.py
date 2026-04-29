"""User configuration for harness adapter defaults."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir


DEFAULT_ADAPTER = None
DEFAULT_RUN_RETENTION_LIMIT = 20
DEFAULT_WRITE_STEP_TIMEOUT_SECONDS = 300
DEFAULT_DELIVERY_GIT_BASE_REF = "origin/main"
DEFAULT_DELIVERY_PATH_PATTERNS = ("src/**", "test/**")


def config_path() -> Path:
    return Path(user_config_dir("devspark")) / "config.json"


def read_user_config() -> dict[str, Any]:
    path = config_path()
    if not path.is_file():
        return {"default_adapter": DEFAULT_ADAPTER, "run_retention_limit": DEFAULT_RUN_RETENTION_LIMIT}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"default_adapter": DEFAULT_ADAPTER, "run_retention_limit": DEFAULT_RUN_RETENTION_LIMIT}
    return {
        "default_adapter": raw.get("default_adapter") if isinstance(raw.get("default_adapter"), str) else None,
        "run_retention_limit": raw.get("run_retention_limit") if isinstance(raw.get("run_retention_limit"), int) and raw.get("run_retention_limit") > 0 else DEFAULT_RUN_RETENTION_LIMIT,
    }


def write_user_config(data: dict[str, Any]) -> Path:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def load_adapter_default() -> str | None:
    value = read_user_config().get("default_adapter")
    return value if isinstance(value, str) and value.strip() else None


def load_run_retention_limit() -> int:
    value = read_user_config().get("run_retention_limit")
    return value if isinstance(value, int) and value > 0 else DEFAULT_RUN_RETENTION_LIMIT


def save_adapter_default(name: str) -> Path:
    data = read_user_config()
    data["default_adapter"] = name
    return write_user_config(data)