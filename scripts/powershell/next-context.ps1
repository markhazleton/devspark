#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
    Detect DevSpark lifecycle state and recommend one next action. Read-only.
#>
[CmdletBinding()]
param(
    [switch]$Auto,
    [switch]$Json,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

. (Join-Path $PSScriptRoot 'common.ps1')
. (Join-Path $PSScriptRoot 'platform.ps1')

foreach ($arg in @($RemainingArgs)) {
    if ($arg -eq '--auto') { $Auto = $true }
}

$repoRoot = Get-RepoRoot
$hasGit = Test-HasGit
$branch = 'none'
$gitDirty = $false
$upstream = ''
$ahead = 0
$behind = 0

if ($hasGit) {
    $branch = (git -C $repoRoot branch --show-current 2>$null)
    if (-not $branch) { $branch = 'detached' }
    $gitDirty = [bool](git -C $repoRoot status --porcelain --untracked-files=normal 2>$null)
    $upstream = (git -C $repoRoot rev-parse --abbrev-ref '@{upstream}' 2>$null)
    if ($LASTEXITCODE -ne 0) { $upstream = '' }
    if ($upstream) {
        $counts = (git -C $repoRoot rev-list --left-right --count "$upstream...HEAD" 2>$null) -split '\s+'
        if ($counts.Count -ge 2) {
            $behind = [int]$counts[0]
            $ahead = [int]$counts[1]
        }
    }
}

$constitutionExists = Test-Path -LiteralPath (Join-Path $repoRoot '.knowledge/governance/constitution.md')
$featureDir = ''
$specPath = ''
$planPath = ''
$tasksPath = ''
$workKind = 'none'

$branchSpecDir = Join-Path $repoRoot ".devspark.work/specs/$branch"
if ($branch -notin @('none', 'detached') -and (Test-Path -LiteralPath $branchSpecDir -PathType Container)) {
    $featureDir = ".devspark.work/specs/$branch"
    $workKind = 'spec'
    $specPath = Join-Path $branchSpecDir 'spec.md'
    $planPath = Join-Path $branchSpecDir 'plan.md'
    $tasksPath = Join-Path $branchSpecDir 'tasks.md'
} elseif ($branch -notin @('none', 'detached')) {
    $quickfixDir = Join-Path $repoRoot '.devspark.work/quickfixes'
    if (Test-Path -LiteralPath $quickfixDir) {
        $quickfix = Get-ChildItem -LiteralPath $quickfixDir -Filter '*.md' -File -ErrorAction SilentlyContinue |
            Where-Object { Select-String -LiteralPath $_.FullName -SimpleMatch "- **Branch**: $branch" -Quiet } |
            Sort-Object Name |
            Select-Object -Last 1
        if ($quickfix) {
            $featureDir = '.devspark.work/quickfixes'
            $workKind = 'quickfix'
            $specPath = $quickfix.FullName
            $tasksPath = $quickfix.FullName
        }
    }
}

$hasSpec = [bool]($specPath -and (Test-Path -LiteralPath $specPath -PathType Leaf))
$hasPlan = [bool]($planPath -and (Test-Path -LiteralPath $planPath -PathType Leaf))
$hasTasks = [bool]($tasksPath -and (Test-Path -LiteralPath $tasksPath -PathType Leaf))
$specStatus = 'missing'
$requiredGates = ''
$artifactContent = ''
if ($hasSpec) {
    $artifactContent = Get-Content -LiteralPath $specPath -Raw
    if ($artifactContent -match '(?m)^\*\*Status\*\*:\s*([^<\r\n]+)') {
        $specStatus = $matches[1].Trim()
    } else {
        $specStatus = 'unknown'
    }
    if ($artifactContent -match '(?m)^required_gates:\s*(.*)$') {
        $requiredGates = $matches[1].ToLowerInvariant()
    }
}

$tasksComplete = 0
$tasksIncomplete = 0
if ($hasTasks) {
    if (-not $artifactContent -or $tasksPath -ne $specPath) {
        $artifactContent = Get-Content -LiteralPath $tasksPath -Raw
    }
    $tasksComplete = [regex]::Matches($artifactContent, '(?im)^\s*-\s+\[[x]\]').Count
    $tasksIncomplete = [regex]::Matches($artifactContent, '(?m)^\s*-\s+\[ \]').Count
}
$tasksTotal = $tasksComplete + $tasksIncomplete

function Get-GateState {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return 'missing' }
    $content = Get-Content -LiteralPath $Path -Raw
    $status = if ($content -match '(?m)^status:\s*(\S+)') { $matches[1].ToLowerInvariant() } else { '' }
    $blocking = if ($content -match '(?m)^blocking:\s*(\S+)') { $matches[1].ToLowerInvariant() } else { '' }
    if ($blocking -eq 'true' -or $status -eq 'fail') { return 'fail' }
    if ($status -in @('pass', 'warn')) { return $status }
    return 'fail'
}

$checklistState = 'not-required'
$analyzeState = 'not-required'
$criticState = 'not-required'
if ($workKind -eq 'spec' -and $featureDir) {
    if ($requiredGates.Contains('checklist')) {
        $checklistState = Get-GateState (Join-Path $repoRoot "$featureDir/gates/checklist.md")
    }
    if (-not $requiredGates -or $requiredGates.Contains('analyze')) {
        $analyzeState = Get-GateState (Join-Path $repoRoot "$featureDir/gates/analyze.md")
    }
    if (-not $requiredGates -or $requiredGates.Contains('critic')) {
        $criticState = Get-GateState (Join-Path $repoRoot "$featureDir/gates/critic.md")
    }
}

$prNumber = ''
$prState = 'none'
$prUrl = ''
$prBase = ''
$prReviewDecision = ''
$prMergeState = ''
$platformCliAvailable = [bool](Get-Command $DevSparkPlatform.PrCli -ErrorAction SilentlyContinue)
$platformAuthenticated = $false

if ($platformCliAvailable) {
    try { $platformAuthenticated = [bool](& $DevSparkPlatform.AuthCheck) } catch { $platformAuthenticated = $false }
    if ($platformAuthenticated) {
        try {
            switch ($DevSparkPlatform.Name) {
                'github' {
                    $pr = gh pr view --json number,state,url,baseRefName,reviewDecision,mergeStateStatus 2>$null | ConvertFrom-Json
                    if ($pr) {
                        $prNumber = [string]$pr.number
                        $prState = ([string]$pr.state).ToLowerInvariant()
                        $prUrl = [string]$pr.url
                        $prBase = [string]$pr.baseRefName
                        $prReviewDecision = ([string]$pr.reviewDecision).ToUpperInvariant()
                        $prMergeState = ([string]$pr.mergeStateStatus).ToUpperInvariant()
                    }
                }
                'azdo' {
                    $prs = az repos pr list --source-branch $branch --status all --top 1 --output json 2>$null | ConvertFrom-Json
                    if ($prs.Count -gt 0) {
                        $prNumber = [string]$prs[0].pullRequestId
                        $prState = ([string]$prs[0].status).ToLowerInvariant()
                        $prUrl = [string]$prs[0].url
                        $prBase = ([string]$prs[0].targetRefName) -replace '^refs/heads/', ''
                    }
                }
                'gitlab' {
                    $pr = glab mr view --output json 2>$null | ConvertFrom-Json
                    if ($pr) {
                        $prNumber = [string]$pr.iid
                        $prState = ([string]$pr.state).ToLowerInvariant()
                        $prUrl = [string]$pr.web_url
                        $prBase = [string]$pr.target_branch
                    }
                }
            }
        } catch { }
    }
}

$reviewPath = ''
$reviewState = 'missing'
$reviewOpenFindings = 0
if ($prNumber) {
    $candidateReview = Join-Path $repoRoot ".devspark.work/pr-reviews/pr-$prNumber.md"
    if (Test-Path -LiteralPath $candidateReview -PathType Leaf) {
        $reviewPath = ".devspark.work/pr-reviews/pr-$prNumber.md"
        $reviewState = Get-GateState $candidateReview
        $reviewContent = Get-Content -LiteralPath $candidateReview -Raw
        $reviewOpenFindings = [regex]::Matches(
            $reviewContent,
            '(?m)^\s*-\s+\[ \]\s+\*\*(C|H|M|L|CON)-[0-9]+'
        ).Count
    }
}

function New-DevSparkRecommendation {
    param([string]$Command, [string]$Reason, [string]$State, [bool]$SafeToAuto)
    [ordered]@{
        command = $Command; reason = $Reason; state = $State; kind = 'devspark'
        safe = $SafeToAuto; boundary = 'none'; manual = ''
    }
}
function New-ManualRecommendation {
    param([string]$Command, [string]$Reason, [string]$State, [string]$Boundary, [string]$Manual)
    [ordered]@{
        command = $Command; reason = $Reason; state = $State; kind = 'manual'
        safe = $false; boundary = $Boundary; manual = $Manual
    }
}

$recommendation = [ordered]@{
    command = 'none'; reason = 'The detected workflow is complete.'; state = 'complete'
    kind = 'complete'; safe = $false; boundary = 'none'; manual = ''
}

if (-not $hasGit) {
    $recommendation = New-ManualRecommendation 'none' 'DevSpark workflow detection requires a Git repository.' 'git-required' 'repository' 'git init'
} elseif (-not $constitutionExists) {
    $recommendation = New-DevSparkRecommendation '/devspark.constitution' 'No project constitution exists yet; lifecycle work needs current governance first.' 'constitution-missing' $false
    $recommendation.boundary = 'governance'
    $recommendation.manual = '/devspark.constitution'
} elseif (-not $hasSpec) {
    $recommendation = New-DevSparkRecommendation '/devspark.specify' "No spec or branch-linked quickfix work package exists for '$branch'." 'work-not-started' $false
    $recommendation.boundary = 'branch'
    $recommendation.manual = '/devspark.specify <describe the requested change>'
} elseif ($workKind -eq 'spec' -and -not $hasPlan) {
    $recommendation = New-DevSparkRecommendation '/devspark.plan' 'The spec exists, but plan.md has not been created.' 'spec-ready' $true
} elseif ($workKind -eq 'spec' -and -not $hasTasks) {
    $recommendation = New-DevSparkRecommendation '/devspark.tasks' 'The implementation plan exists, but tasks.md has not been created.' 'plan-ready' $true
} elseif ($workKind -eq 'spec' -and $checklistState -eq 'missing') {
    $recommendation = New-DevSparkRecommendation '/devspark.checklist' 'The spec requires the checklist gate and no checklist gate result exists.' 'checklist-required' $true
} elseif ($workKind -eq 'spec' -and $checklistState -eq 'fail') {
    $recommendation = New-ManualRecommendation '/devspark.checklist' 'The checklist gate is blocking and needs human-guided requirement repair.' 'checklist-blocked' 'gate' "Review $featureDir/gates/checklist.md, repair the requirements, then run /devspark.checklist"
} elseif ($workKind -eq 'spec' -and $analyzeState -eq 'missing') {
    $recommendation = New-DevSparkRecommendation '/devspark.analyze' 'Tasks exist, but the required cross-artifact analysis gate has not run.' 'analyze-required' $true
} elseif ($workKind -eq 'spec' -and $analyzeState -eq 'fail') {
    $recommendation = New-ManualRecommendation '/devspark.analyze' 'The analyze gate is blocking and its findings need to be resolved.' 'analyze-blocked' 'gate' "Review $featureDir/gates/analyze.md, repair the cited artifacts, then run /devspark.analyze"
} elseif ($workKind -eq 'spec' -and $criticState -eq 'missing') {
    $recommendation = New-DevSparkRecommendation '/devspark.critic' 'Analysis is complete, but the required adversarial risk gate has not run.' 'critic-required' $true
} elseif ($workKind -eq 'spec' -and $criticState -eq 'fail') {
    $recommendation = New-ManualRecommendation '/devspark.critic' 'The critic gate is blocking and its risks need a human decision or repair.' 'critic-blocked' 'gate' "Review $featureDir/gates/critic.md, repair or acknowledge the risks, then run /devspark.critic"
} elseif ($tasksIncomplete -gt 0 -or $tasksTotal -eq 0) {
    $recommendation = New-DevSparkRecommendation '/devspark.implement' "$tasksIncomplete implementation task(s) remain incomplete." 'implementation-ready' $true
} elseif ($workKind -eq 'spec' -and $specStatus.ToLowerInvariant() -ne 'complete') {
    $recommendation = New-DevSparkRecommendation '/devspark.implement' 'All tasks are checked off, but the spec lifecycle status still needs completion validation.' 'implementation-finalization' $true
} elseif ($gitDirty) {
    $recommendation = New-ManualRecommendation 'git commit' 'Implementation is complete, but code/test/knowledge changes are still uncommitted.' 'commit-required' 'commit' 'git status --short && git add <code-test-knowledge-files> && git commit -m "<message>"'
} elseif ($behind -gt 0) {
    $recommendation = New-ManualRecommendation 'git rebase' "The branch is $behind commit(s) behind its upstream and must be synchronized by a human." 'sync-required' 'sync' "git fetch origin && git rebase $upstream"
} elseif ($ahead -gt 0) {
    $recommendation = New-ManualRecommendation 'git push' "The branch is $ahead commit(s) ahead of its upstream; pushing is a shared operation." 'push-required' 'sync' 'git push'
} elseif (-not $prNumber -and -not $upstream) {
    $recommendation = New-ManualRecommendation 'git push' 'The completed branch has no upstream; publishing it is a shared operation.' 'push-required' 'sync' "git push -u origin $branch"
} elseif (-not $prNumber -and -not $platformCliAvailable) {
    $recommendation = New-ManualRecommendation '/devspark.create-pr' 'The platform CLI is unavailable, so PR state cannot be verified or created safely.' 'platform-cli-required' 'shared-service' "Install $($DevSparkPlatform.PrCli) from $($DevSparkPlatform.PrCliInstallUrl), then run /devspark.create-pr"
} elseif (-not $prNumber -and -not $platformAuthenticated) {
    $recommendation = New-ManualRecommendation '/devspark.create-pr' 'The platform CLI is not authenticated, so PR state cannot be verified or created safely.' 'platform-auth-required' 'shared-service' "$($DevSparkPlatform.PrCli) auth login"
} elseif (-not $prNumber) {
    $recommendation = New-DevSparkRecommendation '/devspark.create-pr' 'Implementation is committed and synchronized, but no pull request exists.' 'pr-required' $true
} elseif ($prState -in @('merged', 'completed')) {
    $recommendation = [ordered]@{ command = 'none'; reason = "PR $prNumber is merged; this development flow is complete. Release remains a separate human-triggered event."; state = 'merged'; kind = 'complete'; safe = $false; boundary = 'none'; manual = '' }
} elseif ($prState -in @('closed', 'abandoned')) {
    $reopen = switch ($DevSparkPlatform.Name) { 'github' { "gh pr reopen $prNumber" } 'gitlab' { "glab mr reopen $prNumber" } default { "Review PR $prNumber in Azure DevOps" } }
    $recommendation = New-ManualRecommendation '/devspark.create-pr' "PR $prNumber is closed without merge; reopening or replacing it needs a human decision." 'pr-closed' 'pull-request' $reopen
} elseif ($prMergeState -eq 'BEHIND') {
    $recommendation = New-ManualRecommendation 'sync branch' "PR $prNumber is behind '$prBase'; review cannot proceed until a human synchronizes it." 'pr-sync-required' 'sync' "gh pr update-branch $prNumber"
} elseif ($prReviewDecision -eq 'CHANGES_REQUESTED' -or $reviewOpenFindings -gt 0 -or $reviewState -eq 'fail') {
    $recommendation = New-ManualRecommendation '/devspark.address-pr-review' "PR $prNumber has unresolved review findings; the repair flow may create commits." 'review-findings' 'commit' "/devspark.address-pr-review $prNumber"
} elseif ($reviewState -in @('missing', 'unknown')) {
    $recommendation = New-DevSparkRecommendation '/devspark.pr-review' "PR $prNumber exists, but no current local PR-review gate result is available." 'review-required' $true
} else {
    $merge = switch ($DevSparkPlatform.Name) { 'github' { "gh pr merge $prNumber" } 'azdo' { "az repos pr update --id $prNumber --status completed" } 'gitlab' { "glab mr merge $prNumber" } }
    $recommendation = New-ManualRecommendation 'merge PR' "PR $prNumber has a non-blocking review result; merging is a human-owned shared operation." 'merge-ready' 'merge' $merge
}

[ordered]@{
    REPO_ROOT = $repoRoot
    BRANCH = $branch
    PLATFORM = $DevSparkPlatform.Name
    AUTO = [bool]$Auto
    HAS_GIT = $hasGit
    GIT_DIRTY = $gitDirty
    UPSTREAM = $upstream
    AHEAD = $ahead
    BEHIND = $behind
    WORK_KIND = $workKind
    FEATURE_DIR = $featureDir
    HAS_SPEC = $hasSpec
    HAS_PLAN = $hasPlan
    HAS_TASKS = $hasTasks
    SPEC_STATUS = $specStatus
    TASKS = [ordered]@{ total = $tasksTotal; complete = $tasksComplete; incomplete = $tasksIncomplete }
    GATES = [ordered]@{ checklist = $checklistState; analyze = $analyzeState; critic = $criticState }
    PR = [ordered]@{ number = $prNumber; state = $prState; url = $prUrl }
    REVIEW = [ordered]@{ state = $reviewState; open_findings = $reviewOpenFindings }
    ORIENTATION_STATE = $recommendation.state
    RECOMMENDED_COMMAND = $recommendation.command
    RECOMMENDATION_REASON = $recommendation.reason
    ACTION_KIND = $recommendation.kind
    SAFE_TO_AUTO = $recommendation.safe
    HUMAN_BOUNDARY = $recommendation.boundary
    MANUAL_COMMAND = $recommendation.manual
    READ_ONLY = $true
} | ConvertTo-Json -Depth 6
