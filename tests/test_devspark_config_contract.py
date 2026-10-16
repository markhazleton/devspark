# DevSpark - (c) 2026 Make Bold Solutions. Source: https://dev.makeboldspark.com
"""
Contract test: malformed devspark.json / devspark.user.json must produce a loud
warning (stderr / PowerShell Warning stream) instead of silently returning null,
in both PowerShell and Bash (Platform Parity, quickfix item #3).
"""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_PS1 = REPO_ROOT / "scripts" / "powershell" / "common.ps1"
COMMON_SH = REPO_ROOT / "scripts" / "bash" / "common.sh"


_GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"
_BASH = _GIT_BASH if Path(_GIT_BASH).exists() else shutil.which("bash")


def _init_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True, input="")
    work_dir = tmp_path / ".devspark.work"
    work_dir.mkdir(parents=True, exist_ok=True)
    return work_dir


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh not available")
def test_powershell_warns_on_malformed_devspark_json(tmp_path: Path):
    doc_dir = _init_repo(tmp_path)
    (doc_dir / "devspark.json").write_text("{ not valid json", encoding="utf-8")

    script = (
        f". '{COMMON_PS1}'; "
        f"Set-Location '{tmp_path}'; "
        "$out = Get-DevSparkConfig 3>&1; "
        "$warned = ($out | Where-Object { $_ -is [System.Management.Automation.WarningRecord] }).Count -gt 0; "
        "$resultNotNull = ($out | Where-Object { $_ -isnot [System.Management.Automation.WarningRecord] }).Count -gt 0; "
        "if ($resultNotNull) { Write-Output 'RESULT_NOT_NULL' } "
        "elseif ($warned) { Write-Output 'WARNED_AND_NULL' } "
        "else { Write-Output 'SILENT_FAILURE' }"
    )
    proc = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", script],
        capture_output=True, text=True, input="", cwd=tmp_path,
    )
    assert "WARNED_AND_NULL" in proc.stdout, proc.stdout + proc.stderr


@pytest.mark.skipif(shutil.which("pwsh") is None, reason="pwsh not available")
def test_powershell_json_mode_stays_clean_on_malformed_config(tmp_path: Path):
    """Warnings must never land inside JSON-mode stdout output."""
    doc_dir = _init_repo(tmp_path)
    (doc_dir / "devspark.json").write_text("{ not valid json", encoding="utf-8")

    script = (
        f". '{COMMON_PS1}'; "
        f"Set-Location '{tmp_path}'; "
        "$null = Get-DevSparkConfig 3>$null; "
        "@{ ok = $true } | ConvertTo-Json -Compress"
    )
    proc = subprocess.run(
        ["pwsh", "-NoProfile", "-Command", script],
        capture_output=True, text=True, input="", cwd=tmp_path,
    )
    assert proc.stdout.strip() == '{"ok":true}', proc.stdout + proc.stderr


@pytest.mark.skipif(_BASH is None or shutil.which("jq") is None, reason="bash/jq not available")
def test_bash_warns_on_malformed_devspark_json(tmp_path: Path):
    doc_dir = _init_repo(tmp_path)
    (doc_dir / "devspark.json").write_text("{ not valid json", encoding="utf-8")

    common_sh_str = COMMON_SH.as_posix()
    script = f"source '{common_sh_str}'; out=$(get_devspark_config_value '.platform' 2>/tmp/devspark_test_stderr.$$); echo \"OUT=[$out]\"; cat /tmp/devspark_test_stderr.$$; rm -f /tmp/devspark_test_stderr.$$"
    proc = subprocess.run(
        [_BASH, "-c", script],
        capture_output=True, text=True, input="", cwd=tmp_path,
    )
    assert "OUT=[]" in proc.stdout, proc.stdout + proc.stderr
    assert "failed to parse" in proc.stdout, proc.stdout + proc.stderr
