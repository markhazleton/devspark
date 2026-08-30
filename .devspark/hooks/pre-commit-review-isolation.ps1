#!/usr/bin/env pwsh
# Optional pre-commit guard for v4 ephemeral work isolation.

$staged = @(git diff --cached --name-only)
$work = @($staged | Where-Object { $_ -like '.devspark.work/*' })

if ($work.Count -gt 0) {
    Write-Error "DevSpark: .devspark.work files must not be staged. Remove temporary work artifacts from this commit."
    Write-Error "Work files staged:  $($work -join ', ')"
    exit 1
}
