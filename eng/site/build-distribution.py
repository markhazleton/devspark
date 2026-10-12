"""Assemble the public DocFX site, release archives, and quickstart install tree."""

from __future__ import annotations

import argparse
import html
import json
import shutil
import tomllib
from datetime import datetime, timezone
from pathlib import Path


def build(repo: Path, output: Path) -> dict:
    version = tomllib.loads((repo / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    tag = f"v{version}"
    if not (output / "index.html").is_file():
        raise ValueError("Build site/docfx.json before assembling the distribution")
    archives = sorted((repo / ".genreleases").glob(f"devspark-template-*-{tag}.zip"))
    if not archives:
        raise ValueError(f"Build release packages for {tag} before assembling the distribution")
    raw = output / "raw"
    if raw.exists():
        if raw.resolve().parent != output.resolve():
            raise ValueError("The generated raw tree must remain within the output directory")
        shutil.rmtree(raw)
    install = []
    for directory in ("templates", "scripts", "quickstart"):
        for source in sorted((repo / directory).rglob("*")):
            if not source.is_file() or "__pycache__" in source.parts or source.suffix == ".pyc":
                continue
            relative = source.relative_to(repo).as_posix()
            target = raw / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if directory == "quickstart":
                continue
            if relative.startswith("templates/consumer-skills/"):
                if source.name != "SKILL.md":
                    continue
                dest = f".github/skills/{source.parent.name}/SKILL.md"
                category = "skill"
            elif source.parent == repo / "templates/commands" and source.suffix == ".md":
                dest = f".devspark/defaults/commands/devspark.{source.stem}.md"
                category = "command"
            else:
                dest = f".devspark/{relative}"
                category = "template" if directory == "templates" else "script"
            install.append({"source": relative, "dest": dest, "category": category})
    shutil.copyfile(repo / "agents-registry.json", raw / "agents-registry.json")
    install.append({"source": "agents-registry.json", "dest": "agents-registry.json", "category": "registry"})
    constitution = raw / ".knowledge/governance/constitution.md"
    constitution.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(repo / ".knowledge/governance/constitution.md", constitution)
    release = output / "dist" / tag
    release.mkdir(parents=True, exist_ok=True)
    for archive in archives:
        shutil.copyfile(archive, release / archive.name)
    released = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    current = {"version": version, "tag": tag, "path": f"dist/{tag}", "released": released, "assets": [p.name for p in archives]}
    manifest = {
        "latest": version, "tag": tag, "path": current["path"], "released": released,
        "assets": current["assets"], "raw_base": "https://dev.makeboldspark.com/raw",
        "devspark_root": ["VERSION", "defaults", "templates", "scripts"],
        "install": install, "versions": [current],
    }
    (output / "dist/manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (output / ".nojekyll").touch()
    (output / "CNAME").write_text("dev.makeboldspark.com\n", encoding="utf-8")
    # GitHub Pages does not consume Azure Static Web App route configuration.
    routes = json.loads((repo / "staticwebapp.config.json").read_text(encoding="utf-8"))["routes"]
    for route in routes:
        if route.get("statusCode") != 301 or not route.get("redirect") or not route["route"].endswith(".html"):
            continue
        target = output / route["route"].lstrip("/")
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        url = html.escape(route["redirect"], quote=True)
        target.write_text(f'<!doctype html><html lang="en"><meta charset="utf-8"><title>DevSpark</title><meta http-equiv="refresh" content="0;url={url}"><link rel="canonical" href="{url}"><a href="{url}">Continue to DevSpark</a></html>\n', encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    manifest = build(repo, args.output.resolve() if args.output else repo / "site/_site")
    print(f"Built v{manifest['latest']}: {len(manifest['install'])} install entries, {len(manifest['assets'])} release archives")
