"""GitHub release asset resolution and fallback helpers."""

from typing import Optional

import httpx
import typer
from rich.panel import Panel

from ._app import console
from ._github import _format_rate_limit_error, _github_auth_headers

REPO_OWNER = "MarkHazleton"
REPO_NAME = "devspark"


def _find_matching_asset(assets: list[dict], expected_pattern: str) -> Optional[dict]:
    for candidate in assets:
        name = candidate.get("name", "")
        if expected_pattern in name and name.endswith(".zip"):
            return candidate
    return None


def _fetch_release(client: httpx.Client, url: str, github_token: str | None, debug: bool) -> dict:
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
        raise RuntimeError(
            f"Failed to parse release JSON: {je}\nRaw (truncated 400): {response.text[:400]}"
        )


def _fetch_release_by_tag(client: httpx.Client, tag: str, github_token: str | None, debug: bool) -> dict:
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/tags/{tag}"
    return _fetch_release(client, url, github_token, debug)


def _resolve_asset_with_fallback(
    client: httpx.Client,
    release_data: dict,
    pattern: str,
    github_token: str | None,
    debug: bool,
    verbose: bool,
) -> tuple[Optional[dict], dict, bool, str, int]:
    """Search release assets for *pattern*, falling back to recent releases when absent.

    Returns (asset, release_data, resolved_via_fallback, resolved_release_tag, scanned_count).
    """
    assets = release_data.get("assets", [])
    latest_tag = release_data.get("tag_name", "unknown")
    asset = _find_matching_asset(assets, pattern)
    resolved_via_fallback = False
    resolved_release_tag = latest_tag
    scanned_count = 1

    if asset is not None:
        return asset, release_data, False, latest_tag, scanned_count

    if verbose:
        console.print(
            "[yellow]Latest release has no matching template asset; checking recent releases...[/yellow]"
        )

    releases_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases?per_page=20"
    try:
        releases = _fetch_release(client, releases_url, github_token, debug)
        if isinstance(releases, list):
            latest_id = release_data.get("id")
            for candidate in releases:
                if latest_id is not None and candidate.get("id") == latest_id:
                    continue
                scanned_count += 1
                candidate_assets = candidate.get("assets", [])
                asset = _find_matching_asset(candidate_assets, pattern)
                if asset is not None:
                    return asset, candidate, True, candidate.get("tag_name", "unknown"), scanned_count
    except Exception:
        pass

    # Page through older releases
    try:
        for page in range(2, 6):
            paged_url = (
                f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
                f"/releases?per_page=20&page={page}"
            )
            page_releases = _fetch_release(client, paged_url, github_token, debug)
            if not isinstance(page_releases, list) or not page_releases:
                break
            for candidate in page_releases:
                scanned_count += 1
                candidate_assets = candidate.get("assets", [])
                asset = _find_matching_asset(candidate_assets, pattern)
                if asset is not None:
                    return asset, candidate, True, candidate.get("tag_name", "unknown"), scanned_count
    except Exception:
        pass

    return None, release_data, False, latest_tag, scanned_count


def _print_no_asset_guidance(
    ai_assistant: str,
    pattern: str,
    latest_tag: str,
    scanned_count: int,
    assets: list[dict],
) -> None:
    console.print(
        f"[red]No matching release asset found[/red] for [bold]{ai_assistant}[/bold] "
        f"(expected pattern: [bold]{pattern}[/bold])"
    )
    asset_names = [a.get("name", "?") for a in assets]
    console.print(Panel("\n".join(asset_names) or "(no assets)", title="Available Assets", border_style="yellow"))
    guidance_lines = [
        f"Latest release [cyan]{latest_tag}[/cyan] does not currently contain template assets.",
        f"Scanned [cyan]{scanned_count}[/cyan] release(s) for a matching template.",
        "",
        "Try one of these options:",
        "- retry in a few minutes (release assets may still be publishing)",
        "- run with a GitHub token: [cyan]--github-token <token>[/cyan]",
        "- pin a release directly with [cyan]--release-tag[/cyan]",
        "- use a known release tag with assets:",
        f"  [cyan]uvx --refresh --from git+https://github.com/{REPO_OWNER.lower()}/{REPO_NAME}.git@v2.1.0 "
        f"devspark init --here --force --ai {ai_assistant} --script sh --ignore-agent-tools[/cyan]",
    ]
    quickstarts = {
        "claude": ("Claude Code", "claudecode"),
        "copilot": ("GitHub Copilot", "copilot"),
        "codex": ("Codex", "codex"),
    }
    if ai_assistant in quickstarts:
        label, slug = quickstarts[ai_assistant]
        guidance_lines += [
            "",
            f"{label} quickstart (prompt-first):",
            f"[cyan]https://raw.githubusercontent.com/markhazleton/devspark/main/quickstart/devspark_quickstart_{slug}.md[/cyan]",
        ]
    console.print(Panel("\n".join(guidance_lines), title="Recovery Guidance", border_style="cyan"))
    raise typer.Exit(1)
