# Review and Audit

These skills judge what will ship, not the planning prose that led to it. They read the Git diff, current code and configuration, test evidence, current `.knowledge/`, and the constitution. A missing plan is never a problem. None of them require a spec.

| Skill | Scope | Use it to |
|---|---|---|
| `/devspark-verify` | The change | Produce proof (tests and other evidence) and close out the work |
| `/devspark-create-pr` | The change | Draft the PR description from the verified delta |
| `/devspark-update-pr` | The change | Refresh the description after more commits or a rebase |
| `/devspark-pr-review` | The diff | Review the PR against the constitution and current knowledge |
| `/devspark-address-pr-review` | Review findings | Fix findings with commits kept separate from review-file updates |
| `/devspark-site-audit` | The whole repository | Audit compliance, knowledge, and code health on a schedule |

Typical sequence after `/devspark-implement`: `/devspark-verify`, `/devspark-create-pr`, `/devspark-pr-review`, then `/devspark-address-pr-review` and a re-review while findings are open.

## Prerequisites

- A constitution at `.knowledge/governance/constitution.md`. Without one, the skills stop and tell you to run `/devspark-constitution`.
- For PR skills: a hosted repository (GitHub or Azure DevOps) and its CLI installed and authenticated: `gh` for GitHub, or `az` with the `azure-devops` extension for Azure DevOps. The host is detected from `.devspark.work/devspark.json` (`platform`) or the `origin` remote.

## Create a PR

`/devspark-create-pr` believes the work is complete and ready for other people to review. Before it opens or updates a PR, it runs one deterministic check against the pushed HEAD: the committed Knowledge must build. A build failure stops it; the derived index files and `last_verified` dates are never compared. Planning review and closeout results are carried into the description, so a reviewer sees gate acknowledgements without hunting for them.

## PR review

```text
/devspark-pr-review          # the PR for your current branch
/devspark-pr-review 123      # a specific PR (open, closed, or merged)
```

The review is saved to `.devspark.work/pr-review/pr-{number}.md`. Re-reviewing after new commits replaces the report and its revision log; Git keeps earlier versions. PR review judges a change that already claims readiness, so it is not completion detection.

**Evidence first, tests second.** Before running anything, the review looks for existing test evidence for the reviewed commit: a Test Evidence Record from `/devspark-verify`, CI results for the head SHA, or the author's record in the PR description. A record is reused when it is for the same commit (or only planning and review files changed since), came from a clean tree with exit code 0, ran in the same environment, and covers the changed tests. It re-runs tests only on a named trigger: no valid record, a high-risk change backed only by the author's own evidence, a repository policy that requires independent execution, or behavior no recorded run exercises. Every run or reuse is written into the report's Test Evidence section, so an unverified result is stated as unverified rather than implied.

**Risk-sized reviews.** Context helpers compute review tiers and an auditable rating from the full
changed-file set before sampling. Knowledge ownership can raise a file's tier; the reviewer may
escalate but never lower the supplied floor. Low, medium, and high risk select short, standard,
and full report forms. A deterministic validator checks report metadata, findings, recommendation,
and risk consistency. Calibration compares recorded outcomes by producer version; it does not
prove reviewer quality.

**Durable-delta gates.** Each produces a tracked finding ID and blocks:

| ID | Blocks on |
|---|---|
| `PRD1` | Code or configuration contradicts current knowledge |
| `PRD2` | The diff adds an unsupported claim to knowledge |
| `PRD3` | Changed behavior without proportionate test coverage |
| `PRD4` | A planning identifier leaked into durable files |
| `PRD5` | Significant new behavior that touches no `.knowledge/` node |

**Attribution.** A finding is labeled *introduced* (normal), *exposed* (materiality judged), *pre-existing but material*, or *pre-existing and unrelated*. Pre-existing and unrelated issues never block; they appear as Observations or deferred work.

**Severity.** Findings carry a severity (critical, high, medium, low) and a classification (blocking defect, accepted limitation, deferred work, learning). Only blocking defects are mandatory work. Constitution violations are flagged against the principle they break, so concrete, testable principles ("all endpoints must authenticate") produce sharper reviews than vague ones ("write good code").

Use `/devspark-address-pr-review` to work through open findings. Under `--auto` it selects only open critical or high findings and blocking delta findings; ordinary medium and low findings are reported, and constitution findings route to `/devspark-evolve-constitution`.

## Site audit

`/devspark-site-audit` is repository-wide, not diff-scoped. Run it before a release, on a cadence, or when onboarding to an unfamiliar codebase.

```text
/devspark-site-audit                    # full audit (default)
/devspark-site-audit --scope=knowledge
```

| Scope | Checks |
|---|---|
| `full` | Everything below (default) |
| `constitution` | Constitution compliance only |
| `packages` | Dependency analysis only |
| `quality` | Code quality metrics only |
| `unused` | Unused code and dependencies |
| `duplicate` | Duplicate code |
| `comments` | Stale comments and escaped planning references |
| `evidence` | Re-runs tests cited as knowledge evidence; scans for contradictions between related knowledge |
| `knowledge` | Knowledge completeness and mapping accuracy (`KNOW1` to `KNOW6`) |

The repo-wide delta checks (`DELTA1` to `DELTA3`) are the counterpart of PR review's `PRD` gates. `/devspark-release` requires a current `knowledge` scope result with `KNOW1` to `KNOW6` clean. Reports are saved under `.devspark.work/` and are replaceable; compare runs through Git history. Contradiction findings are warnings for human review, never gates.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Constitution not found" | Run `/devspark-constitution` (or `/devspark-discover-constitution` for an existing codebase) |
| PR not detected | Pass the PR number, and confirm the platform CLI is authenticated |
| Audit is slow | Use a narrower `--scope` |
| `pip-audit` unavailable | Install it, or skip the package scope |

## Related

- [Constitution Guide](constitution-guide.md): write principles that reviews can enforce.
- [Knowledge](knowledge-management.md): what `PRD` and `KNOW` findings check.
- [Troubleshooting](troubleshooting-usage.md): where review sits in the `/devspark-next` flow.
