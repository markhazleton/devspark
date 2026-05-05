"""Shared version-stamp helpers used by both init and upgrade commands."""

from datetime import datetime
from pathlib import Path
from typing import Optional


def write_version_stamp(project_path: Path, ai_assistant: str, release_version: str = "") -> None:
    """Write .devspark/VERSION to record the installed version and agent.

    Uses release_version (the GitHub release tag that was downloaded) when available,
    falling back to the installed CLI metadata version.
    Format (key-value):
        version: <version>
        installed: <YYYY-MM-DD>
        method: <install-method>
        migrated-from: <source>
    """
    # Prefer the release tag from the downloaded template (e.g. "v1.2.2")
    version = release_version.lstrip("v") if release_version else ""

    if not version:
        import importlib.metadata
        try:
            version = importlib.metadata.version("devspark-cli")
        except Exception:
            try:
                import tomllib
                pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
                if pyproject_path.exists():
                    with open(pyproject_path, "rb") as f:
                        data = tomllib.load(f)
                        version = data.get("project", {}).get("version", "unknown")
            except Exception:
                version = "unknown"

    devspark_dir = project_path / ".devspark"
    devspark_dir.mkdir(parents=True, exist_ok=True)

    stamp_path = devspark_dir / "VERSION"
    install_date = datetime.now().strftime("%Y-%m-%d")

    legacy_markers = []
    if (project_path / ".specify").exists() or (project_path / ".specify.old").exists():
        legacy_markers.append("legacy-specify")
    if (project_path / ".documentation" / "defaults").exists():
        legacy_markers.append("documentation-defaults")
    migrated_from = ",".join(legacy_markers) if legacy_markers else "fresh"

    try:
        stamp_path.write_text(
            f"version: {version}\n"
            f"installed: {install_date}\n"
            f"method: {ai_assistant}-quickstart\n"
            f"migrated-from: {migrated_from}\n",
            encoding="utf-8",
        )
    except Exception:
        pass  # Non-fatal — never break init/upgrade for a stamp write failure


def read_version_stamp(project_path: Path) -> Optional[dict]:
    """Read .devspark/VERSION and return a dict with version/date/agent,
    or None if the file is absent or unreadable."""
    stamp_path = project_path / ".devspark" / "VERSION"
    # Fallback to old location for projects not yet migrated
    if not stamp_path.exists():
        stamp_path = project_path / ".documentation" / "DEVSPARK_VERSION"
    if not stamp_path.exists():
        return None
    try:
        lines = stamp_path.read_text(encoding="utf-8").splitlines()
        result: dict[str, str] = {}
        if lines and ":" not in lines[0]:
            result["version"] = lines[0].strip() if lines else "unknown"
            for line in lines[1:]:
                if line.startswith("installed:"):
                    result["installed"] = line.split(":", 1)[1].strip()
                elif line.startswith("agent:"):
                    result["agent"] = line.split(":", 1)[1].strip()
                    result.setdefault("method", f"{result['agent']}-quickstart")
        else:
            for line in lines:
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                result[key.strip()] = value.strip()
            if "method" in result and "agent" not in result:
                method = result["method"]
                if method.endswith("-quickstart"):
                    result["agent"] = method[: -len("-quickstart")]
        if "version" not in result:
            result["version"] = "unknown"
        return result
    except Exception:
        return None
