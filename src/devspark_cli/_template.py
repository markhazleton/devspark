"""Template download, extraction, and file-management helpers."""

import json
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import httpx
import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ._app import console
from ._github import _format_rate_limit_error, _github_auth_headers, ssl_context
from ._utils import StepTracker

# Paths that are never overwritten when the destination file already exists.
# Everything under .documentation/ is user-owned work product.
PROTECTED_PREFIXES = (
    ".documentation/",
)


def _is_protected(rel_path: str) -> bool:
    """Return True if *rel_path* (forward-slash, relative to project root)
    falls inside a protected directory that should never be overwritten."""
    normalized = rel_path.replace("\\", "/")
    return any(normalized.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def handle_vscode_settings(sub_item, dest_file, rel_path, verbose=False, tracker=None) -> None:
    """Handle merging or copying of .vscode/settings.json files."""
    def log(message, color="green"):
        if verbose and not tracker:
            console.print(f"[{color}]{message}[/] {rel_path}")

    try:
        with open(sub_item, 'r', encoding='utf-8') as f:
            new_settings = json.load(f)

        if dest_file.exists():
            merged = merge_json_files(dest_file, new_settings, verbose=verbose and not tracker)
            with open(dest_file, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=4)
                f.write('\n')
            log("Merged:", "green")
        else:
            shutil.copy2(sub_item, dest_file)
            log("Copied (no existing settings.json):", "blue")

    except Exception as e:
        log(f"Warning: Could not merge, copying instead: {e}", "yellow")
        shutil.copy2(sub_item, dest_file)


def merge_json_files(existing_path: Path, new_content: dict, verbose: bool = False) -> dict:
    """Merge new JSON content into existing JSON file.

    Performs a deep merge where:
    - New keys are added
    - Existing keys are preserved unless overwritten by new content
    - Nested dictionaries are merged recursively
    - Lists and other values are replaced (not merged)

    Args:
        existing_path: Path to existing JSON file
        new_content: New JSON content to merge in
        verbose: Whether to print merge details

    Returns:
        Merged JSON content as dict
    """
    try:
        with open(existing_path, 'r', encoding='utf-8') as f:
            existing_content = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is invalid, just use new content
        return new_content

    def deep_merge(base: dict, update: dict) -> dict:
        """Recursively merge update dict into base dict."""
        result = base.copy()
        for key, value in update.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = deep_merge(result[key], value)
            else:
                # Add new key or replace existing value
                result[key] = value
        return result

    merged = deep_merge(existing_content, new_content)

    if verbose:
        console.print(f"[cyan]Merged JSON file:[/cyan] {existing_path.name}")

    return merged


def download_template_from_github(ai_assistant: str, download_dir: Path, *, script_type: str = "sh", release_tag: Optional[str] = None, verbose: bool = True, show_progress: bool = True, client: httpx.Client = None, debug: bool = False, github_token: str = None) -> Tuple[Path, dict]:
    repo_owner = "MarkHazleton"
    repo_name = "devspark"
    if client is None:
        client = httpx.Client(verify=ssl_context)

    if verbose:
        if release_tag:
            console.print(f"[cyan]Fetching release information for tag:[/cyan] {release_tag}")
        else:
            console.print("[cyan]Fetching latest release information...[/cyan]")
    latest_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"

    def _find_matching_asset(assets: list[dict], expected_pattern: str) -> Optional[dict]:
        for candidate in assets:
            name = candidate.get("name", "")
            if expected_pattern in name and name.endswith(".zip"):
                return candidate
        return None

    def _fetch_release(url: str) -> dict:
        response = client.get(
            url,
            timeout=30,
            follow_redirects=True,
            headers=_github_auth_headers(github_token),
        )
        status = response.status_code
        if status != 200:
            error_msg = _format_rate_limit_error(status, response.headers, url)
            if debug:
                error_msg += f"\n\n[dim]Response body (truncated 500):[/dim]\n{response.text[:500]}"
            raise RuntimeError(error_msg)
        try:
            return response.json()
        except ValueError as je:
            raise RuntimeError(f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}")

    def _fetch_release_by_tag(tag: str) -> dict:
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/tags/{tag}"
        return _fetch_release(url)

    try:
        if release_tag:
            release_data = _fetch_release_by_tag(release_tag)
        else:
            release_data = _fetch_release(latest_api_url)
    except Exception as e:
        console.print(f"[red]Error fetching release information[/red]")
        console.print(Panel(str(e), title="Fetch Error", border_style="red"))
        raise typer.Exit(1)

    assets = release_data.get("assets", [])
    latest_tag = release_data.get("tag_name", "unknown")
    pattern = f"devspark-template-{ai_assistant}-{script_type}"
    asset = _find_matching_asset(assets, pattern)
    resolved_via_fallback = False
    resolved_release_tag = latest_tag
    scanned_release_count = 1

    # Fallback: latest release can exist without packaged assets.
    # Search recent releases to find the newest published asset bundle.
    if asset is None and not release_tag:
        if verbose:
            console.print(
                "[yellow]Latest release has no matching template asset; checking recent releases...[/yellow]"
            )
        releases_api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases?per_page=20"
        try:
            releases = _fetch_release(releases_api_url)
            if isinstance(releases, list):
                latest_id = release_data.get("id")
                for candidate_release in releases:
                    if latest_id is not None and candidate_release.get("id") == latest_id:
                        continue
                    scanned_release_count += 1
                    candidate_assets = candidate_release.get("assets", [])
                    asset = _find_matching_asset(candidate_assets, pattern)
                    if asset is not None:
                        resolved_via_fallback = True
                        release_data = candidate_release
                        assets = candidate_assets
                        resolved_release_tag = candidate_release.get("tag_name", "unknown")
                        break
        except Exception:
            # Keep existing error behavior below if no matching asset is found.
            pass

        # If still unresolved, scan older releases page-by-page.
        if asset is None:
            try:
                for page in range(2, 6):
                    paged_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases?per_page=20&page={page}"
                    page_releases = _fetch_release(paged_url)
                    if not isinstance(page_releases, list) or not page_releases:
                        break
                    for candidate_release in page_releases:
                        scanned_release_count += 1
                        candidate_assets = candidate_release.get("assets", [])
                        asset = _find_matching_asset(candidate_assets, pattern)
                        if asset is not None:
                            resolved_via_fallback = True
                            release_data = candidate_release
                            assets = candidate_assets
                            resolved_release_tag = candidate_release.get("tag_name", "unknown")
                            break
                    if asset is not None:
                        break
            except Exception:
                pass

    if asset is None:
        console.print(f"[red]No matching release asset found[/red] for [bold]{ai_assistant}[/bold] (expected pattern: [bold]{pattern}[/bold])")
        asset_names = [a.get('name', '?') for a in assets]
        console.print(Panel("\n".join(asset_names) or "(no assets)", title="Available Assets", border_style="yellow"))
        guidance_lines = [
            f"Latest release [cyan]{latest_tag}[/cyan] does not currently contain template assets.",
            f"Scanned [cyan]{scanned_release_count}[/cyan] release(s) for a matching template.",
            "",
            "Try one of these options:",
            "- retry in a few minutes (release assets may still be publishing)",
            "- run with a GitHub token: [cyan]--github-token <token>[/cyan]",
            "- pin a release directly with [cyan]--release-tag[/cyan]",
            "- use a known release tag with assets:",
            f"  [cyan]uvx --refresh --from git+https://github.com/{repo_owner.lower()}/{repo_name}.git@v2.1.0 devspark init --here --force --ai {ai_assistant} --script {script_type} --ignore-agent-tools[/cyan]",
        ]
        if ai_assistant == "claude":
            guidance_lines.extend(
                [
                    "",
                    "Claude Code quickstart (prompt-first):",
                    "[cyan]https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_claudecode.md[/cyan]",
                ]
            )
        elif ai_assistant == "copilot":
            guidance_lines.extend(
                [
                    "",
                    "GitHub Copilot quickstart (prompt-first):",
                    "[cyan]https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_copilot.md[/cyan]",
                ]
            )
        console.print(Panel("\n".join(guidance_lines), title="Recovery Guidance", border_style="cyan"))
        raise typer.Exit(1)

    download_url = asset["browser_download_url"]
    filename = asset["name"]
    file_size = asset["size"]

    if verbose:
        if resolved_via_fallback:
            console.print(
                f"[yellow]Using template from earlier release:[/yellow] [cyan]{resolved_release_tag}[/cyan] (latest is [cyan]{latest_tag}[/cyan])"
            )
        console.print(f"[cyan]Found template:[/cyan] {filename}")
        console.print(f"[cyan]Size:[/cyan] {file_size:,} bytes")
        console.print(f"[cyan]Release:[/cyan] {release_data['tag_name']}")

    zip_path = download_dir / filename
    if verbose:
        console.print(f"[cyan]Downloading template...[/cyan]")

    try:
        with client.stream(
            "GET",
            download_url,
            timeout=60,
            follow_redirects=True,
            headers=_github_auth_headers(github_token),
        ) as response:
            if response.status_code != 200:
                # Handle rate-limiting on download as well
                error_msg = _format_rate_limit_error(response.status_code, response.headers, download_url)
                if debug:
                    error_msg += f"\n\n[dim]Response body (truncated 400):[/dim]\n{response.text[:400]}"
                raise RuntimeError(error_msg)
            total_size = int(response.headers.get('content-length', 0))
            with open(zip_path, 'wb') as f:
                if total_size == 0:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        f.write(chunk)
                else:
                    if show_progress:
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[progress.description]{task.description}"),
                            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                            console=console,
                        ) as progress:
                            task = progress.add_task("Downloading...", total=total_size)
                            downloaded = 0
                            for chunk in response.iter_bytes(chunk_size=8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                progress.update(task, completed=downloaded)
                    else:
                        for chunk in response.iter_bytes(chunk_size=8192):
                            f.write(chunk)
    except Exception as e:
        console.print(f"[red]Error downloading template[/red]")
        detail = str(e)
        if zip_path.exists():
            zip_path.unlink()
        console.print(Panel(detail, title="Download Error", border_style="red"))
        raise typer.Exit(1)
    if verbose:
        console.print(f"Downloaded: {filename}")
    metadata = {
        "filename": filename,
        "size": file_size,
        "release": release_data["tag_name"],
        "asset_url": download_url,
        "resolved_via_fallback": resolved_via_fallback,
        "latest_release": latest_tag,
        "scanned_release_count": scanned_release_count,
    }
    return zip_path, metadata


def download_and_extract_template(project_path: Path, ai_assistant: str, script_type: str, is_current_dir: bool = False, *, release_tag: Optional[str] = None, verbose: bool = True, tracker: Optional[StepTracker] = None, client: httpx.Client = None, debug: bool = False, github_token: str = None):
    """Download the latest release and extract it to create a new project.
    Returns (project_path, release_tag). Uses tracker if provided (with keys: fetch, download, extract, cleanup)
    """
    current_dir = Path.cwd()
    release_tag = ""

    if tracker:
        tracker.start("fetch", "contacting GitHub API")
    try:
        zip_path, meta = download_template_from_github(
            ai_assistant,
            current_dir,
            script_type=script_type,
            release_tag=release_tag,
            verbose=verbose and tracker is None,
            show_progress=(tracker is None),
            client=client,
            debug=debug,
            github_token=github_token
        )
        release_tag = meta.get("release", "")
        if tracker:
            tracker.complete("fetch", f"release {meta['release']} ({meta['size']:,} bytes)")
            tracker.add("download", "Download template")
            tracker.complete("download", meta['filename'])
    except Exception as e:
        if tracker:
            tracker.error("fetch", str(e))
        else:
            if verbose:
                console.print(f"[red]Error downloading template:[/red] {e}")
        raise

    if tracker:
        tracker.add("extract", "Extract template")
        tracker.start("extract")
    elif verbose:
        console.print("Extracting template...")

    try:
        if not is_current_dir:
            project_path.mkdir(parents=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_contents = zip_ref.namelist()
            if tracker:
                tracker.start("zip-list")
                tracker.complete("zip-list", f"{len(zip_contents)} entries")
            elif verbose:
                console.print(f"[cyan]ZIP contains {len(zip_contents)} items[/cyan]")

            if is_current_dir:
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    zip_ref.extractall(temp_path)

                    extracted_items = list(temp_path.iterdir())
                    if tracker:
                        tracker.start("extracted-summary")
                        tracker.complete("extracted-summary", f"temp {len(extracted_items)} items")
                    elif verbose:
                        console.print(f"[cyan]Extracted {len(extracted_items)} items to temp location[/cyan]")

                    source_dir = temp_path
                    if len(extracted_items) == 1 and extracted_items[0].is_dir():
                        source_dir = extracted_items[0]
                        if tracker:
                            tracker.add("flatten", "Flatten nested directory")
                            tracker.complete("flatten")
                        elif verbose:
                            console.print(f"[cyan]Found nested directory structure[/cyan]")

                    skipped_files: list[str] = []

                    for item in source_dir.iterdir():
                        dest_path = project_path / item.name
                        if item.is_dir():
                            if dest_path.exists():
                                if verbose and not tracker:
                                    console.print(f"[yellow]Merging directory:[/yellow] {item.name}")
                                for sub_item in item.rglob('*'):
                                    if sub_item.is_file():
                                        rel_path = sub_item.relative_to(source_dir)
                                        dest_file = project_path / rel_path
                                        # Never overwrite existing files in protected directories
                                        if dest_file.exists() and _is_protected(str(rel_path)):
                                            skipped_files.append(str(rel_path))
                                            continue
                                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                                        # Special handling for .vscode/settings.json - merge instead of overwrite
                                        if dest_file.name == "settings.json" and dest_file.parent.name == ".vscode":
                                            handle_vscode_settings(sub_item, dest_file, rel_path, verbose, tracker)
                                        else:
                                            shutil.copy2(sub_item, dest_file)
                            else:
                                # New directory — but still check protected paths for individual files
                                for sub_item in item.rglob('*'):
                                    if sub_item.is_file():
                                        rel_path = sub_item.relative_to(source_dir)
                                        dest_file = project_path / rel_path
                                        if dest_file.exists() and _is_protected(str(rel_path)):
                                            skipped_files.append(str(rel_path))
                                            continue
                                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                                        shutil.copy2(sub_item, dest_file)
                        else:
                            if dest_path.exists() and verbose and not tracker:
                                console.print(f"[yellow]Overwriting file:[/yellow] {item.name}")
                            shutil.copy2(item, dest_path)

                    if skipped_files:
                        if tracker:
                            tracker.add("protected", "Preserved user customizations")
                            tracker.complete("protected", f"{len(skipped_files)} file(s) kept")
                        elif verbose:
                            console.print(f"[green]Preserved {len(skipped_files)} customized file(s):[/green]")
                            for sf in skipped_files:
                                console.print(f"  [dim]{sf}[/dim]")
                    if verbose and not tracker:
                        console.print(f"[cyan]Template files merged into current directory[/cyan]")
            else:
                zip_ref.extractall(project_path)

                extracted_items = list(project_path.iterdir())
                if tracker:
                    tracker.start("extracted-summary")
                    tracker.complete("extracted-summary", f"{len(extracted_items)} top-level items")
                elif verbose:
                    console.print(f"[cyan]Extracted {len(extracted_items)} items to {project_path}:[/cyan]")
                    for item in extracted_items:
                        console.print(f"  - {item.name} ({'dir' if item.is_dir() else 'file'})")

                if len(extracted_items) == 1 and extracted_items[0].is_dir():
                    nested_dir = extracted_items[0]
                    temp_move_dir = project_path.parent / f"{project_path.name}_temp"

                    shutil.move(str(nested_dir), str(temp_move_dir))

                    project_path.rmdir()

                    shutil.move(str(temp_move_dir), str(project_path))
                    if tracker:
                        tracker.add("flatten", "Flatten nested directory")
                        tracker.complete("flatten")
                    elif verbose:
                        console.print(f"[cyan]Flattened nested directory structure[/cyan]")

    except Exception as e:
        if tracker:
            tracker.error("extract", str(e))
        else:
            if verbose:
                console.print(f"[red]Error extracting template:[/red] {e}")
                if debug:
                    console.print(Panel(str(e), title="Extraction Error", border_style="red"))

        if not is_current_dir and project_path.exists():
            shutil.rmtree(project_path)
        raise typer.Exit(1)
    else:
        if tracker:
            tracker.complete("extract")
    finally:
        if tracker:
            tracker.add("cleanup", "Remove temporary archive")

        if zip_path.exists():
            zip_path.unlink()
            if tracker:
                tracker.complete("cleanup")
            elif verbose:
                console.print(f"Cleaned up: {zip_path.name}")

    return project_path, release_tag


def ensure_executable_scripts(project_path: Path, tracker: Optional[StepTracker] = None) -> None:
    """Ensure POSIX .sh scripts under .devspark/scripts (recursively) have execute bits (no-op on Windows)."""
    if os.name == "nt":
        return  # Windows: skip silently
    scripts_root = project_path / ".devspark" / "scripts"
    if not scripts_root.is_dir():
        return
    failures: list[str] = []
    updated = 0
    for script in scripts_root.rglob("*.sh"):
        try:
            if script.is_symlink() or not script.is_file():
                continue
            try:
                with script.open("rb") as f:
                    if f.read(2) != b"#!":
                        continue
            except Exception:
                continue
            st = script.stat(); mode = st.st_mode
            if mode & 0o111:
                continue
            new_mode = mode
            if mode & 0o400: new_mode |= 0o100
            if mode & 0o040: new_mode |= 0o010
            if mode & 0o004: new_mode |= 0o001
            if not (new_mode & 0o100):
                new_mode |= 0o100
            os.chmod(script, new_mode)
            updated += 1
        except Exception as e:
            failures.append(f"{script.relative_to(scripts_root)}: {e}")
    if tracker:
        detail = f"{updated} updated" + (f", {len(failures)} failed" if failures else "")
        tracker.add("chmod", "Set script permissions recursively")
        (tracker.error if failures else tracker.complete)("chmod", detail)
    else:
        if updated:
            console.print(f"[cyan]Updated execute permissions on {updated} script(s) recursively[/cyan]")
        if failures:
            console.print("[yellow]Some scripts could not be updated:[/yellow]")
            for f in failures:
                console.print(f"  - {f}")


def _seed_user_artifacts(project_path: Path) -> None:
    """On first init, create the .documentation/memory/ directory structure.

    The constitution is user-owned and NEVER seeded, copied, or overwritten
    by install or upgrade operations. Users create it via /devspark.constitution
    or /devspark.discover-constitution.
    """
    doc_dir = project_path / ".documentation"
    memory_dir = doc_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)


def repair_agent_shim_frontmatter(project_path: Path) -> int:
    """Repair malformed YAML scalar quoting in Copilot agent shim frontmatter.

    Some bootstrap flows have produced lines like:
      name: ""devspark.specify""
      description: ""DevSpark specify command shim""

    This normalizes those lines to valid YAML quoting:
      name: "devspark.specify"
      description: "DevSpark specify command shim"

    Returns the number of files rewritten.
    """
    agents_dir = project_path / ".github" / "agents"
    if not agents_dir.is_dir():
        return 0

    repaired = 0
    bad_quote_re = re.compile(r'^(name|description):\s*""(.*)""\s*$')

    for shim_path in agents_dir.glob("devspark.*.agent.md"):
        try:
            original = shim_path.read_text(encoding="utf-8")
        except Exception:
            continue

        if not original.startswith("---"):
            continue

        newline = "\r\n" if "\r\n" in original else "\n"
        fence = f"---{newline}"
        if fence not in original:
            continue

        parts = original.split(fence, 2)
        if len(parts) < 3:
            continue

        # parts[1] is frontmatter content between the first two --- fences.
        frontmatter = parts[1]
        body = parts[2]
        updated_lines = []
        changed = False
        for line in frontmatter.splitlines():
            match = bad_quote_re.match(line)
            if match:
                key = match.group(1)
                value = match.group(2)
                updated_lines.append(f'{key}: "{value}"')
                changed = True
            else:
                updated_lines.append(line)

        if not changed:
            continue

        repaired_frontmatter = newline.join(updated_lines)
        rewritten = f"---{newline}{repaired_frontmatter}{newline}---{newline}{body}"
        shim_path.write_text(rewritten, encoding="utf-8")
        repaired += 1

    return repaired
