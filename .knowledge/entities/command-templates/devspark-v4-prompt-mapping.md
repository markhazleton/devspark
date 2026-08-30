# DevSpark v4: Prompt Inventory Mapped to Philosophy

Companion to `devspark-v4-philosophy.md`. Each `devspark.*` command grouped
by lifecycle phase, with what v4 changes about its purpose — not a rewrite
of every prompt, but a note on where the current one-line purpose is silent
about a v4 discipline it now needs to enforce.

## Plan & build — produces the ephemeral spec package

| Command | v4 guidance |
|---|---|
| **specify** | No behavior change to the spec's own content, but the artifact it creates is now explicitly ephemeral from creation — nothing it writes should assume it will exist after `implement` completes. |
| **clarify** | Unchanged in mechanism. Answers still get encoded into the spec; the spec still dies with everything else in the package. |
| **plan** | **New responsibility**: this is where the multi-hop ontology traversal happens and gets pinned down as `context_resolved` in the spec package. Design-time budget is generous (2–3 hops or until traversal stops finding new relevant edges) — this is the phase where retrieval complexity gets worked out so `implement` never has to. |
| **tasks** | **New responsibility**: each generated task carries empty `code_ref` / `knowledge_ref` placeholders from the start, not added later. `tasks` sets up the linkage contract that `implement` fills and `analyze`/verify-before-archive later checks. |
| **analyze** | **New responsibility**, added to its existing cross-artifact consistency check: validate that every entity and relation named in `context_resolved` actually resolves against the current ontology. Mechanical, hard-stop — a stale or hallucinated reference fails analyze outright, the same class of check the generator runs on `relations[].object`. |
| **critic** | **New responsibility**, added to its existing adversarial risk pass: judge whether `context_resolved` is *sufficient* for the delta being planned — not whether it resolves (that's analyze's job), but whether something the spec obviously touches was never resolved at all. Judgment-based, not a hard stop. |
| **checklist** | Unchanged — still an ephemeral planning aid, same lifecycle as the rest of the package. |
| **quickfix** | Bypasses the full spec, but should still populate a minimal `context_resolved` and task-level `code_ref`/`knowledge_ref` for whatever it touches — "lightweight" should mean less ceremony, not exemption from the linkage that makes verify-before-archive possible. Worth deciding explicitly whether quickfix skips analyze/critic entirely or runs a lighter version of the same two checks. |

## Implementation — applies the delta

| Command | v4 guidance |
|---|---|
| **implement** | This prompt now carries the heaviest v4 discipline, matching what the philosophy calls "the cost deliberately moved to implement": (1) consumes `context_resolved` as already-resolved context — never traverses more than one hop itself; escalation past one hop is logged and attributable, not silent; (2) updates code and knowledge together in one pass, preferring test evidence over code-only evidence, recording `test_attempted`/`fallback_reason` when it falls back; (3) populates `code_ref`/`knowledge_ref` on every task as it completes it; (4) never writes a spec, task, or plan identifier into a code comment (rule 1/5); (5) only moves the spec package to `.archive/YYYY-MM-DD/<topic>/` after every task's linkage is verified populated — this is where verify-before-archive actually executes, not just gets checked. |

## Validation — carries assimilation forward, enforces the permanent record

| Command | v4 guidance |
|---|---|
| **pr-review** | **Primary assimilation trigger.** Nothing merges without this, which is what makes it the reliable checkpoint (vs. harvest's old role as a sweep someone had to remember to run). Should now: run the ontology generator against the diff's touched entities, gate on gap-report failures for those entities, gate on rule 1 (no ephemeral-artifact references introduced in code or knowledge), and surface — as non-blocking warnings — missing `fallback_reason` entries and any contradiction candidates among graph-adjacent objects touched by the diff. |
| **address-pr-review** | Fixes review findings through code, test, documentation, or `.knowledge` changes while keeping `.devspark.work` review state out of commits. A fix that patches code must not introduce a spec/task reference to "explain" what review comment it addresses. |
| **create-pr / update-pr** | Should surface evidence and linkage status in the PR description itself — which tasks have populated `code_ref`/`knowledge_ref`, which evidence entries are test- vs. code-verified — so a human reviewer sees the v4 checklist state without having to dig for it. This turns pr-review's mechanical checks into something visible in the artifact humans actually read. |
| **verify** | Evidence mechanism engine. Produces empirical proof-of-change evidence, not document review, for declared verification modes. This is the prompt that runs cited tests and produces the pass/fail result that can be written into a knowledge object or decision evidence entry. |
| **audit / site-audit** | *(Note: only `site-audit` appears in the inventory as a standing command; if a separate repo-wide `audit` is planned per the philosophy's "audit" references, it may be this command under a different name — worth confirming there's one command, not two overlapping ones.)* Repo-wide, not diff-scoped. Should run: the accuracy pass (resolve every `execution`-type evidence entry and re-run its test — existence and accuracy are separate reports, per the philosophy), and the contradiction scan, scoped to graph-adjacent objects (same entity, entities sharing a `governs` decision, objects citing the same evidence) rather than brute-force comparison. Contradiction findings are warnings for human review, always — never a gate. |
| **harvest** | **Role shrinks under v4.** Its old purpose — "verify durable knowledge still matches the code" as a periodic sweep — is now pr-review's and audit's job, running continuously/at-merge instead of whenever someone remembers to run harvest. What's left for harvest: sweeping `.devspark.work` for orphaned or abandoned in-flight state (a spec package that stalled without completing verify-before-archive), not primary knowledge verification. Worth an explicit purpose-statement rewrite so it's not read as doing the same job as audit. |
| **taskstoissues** | Already fully aligned with v4 without any change needed — its entire purpose is explaining why ephemeral tasks don't get exported as durable records, which is rule 1 stated as a user-facing explanation rather than an enforcement mechanism. |

## Governance & framework — Constitution, framework lifecycle

| Command | v4 guidance |
|---|---|
| **constitution** | Should now be explicit that the Constitution is one of three current-truth categories (not documentation), and that dependent templates being kept "in sync" includes the `.knowledge/governance/decisions/` contract, not just prose templates. |
| **discover-constitution** | Unchanged in mechanism — discovering implicit patterns is a different activity than maintaining the current-truth categories, and doesn't need v4-specific revision. |
| **evolve-constitution** | Worth connecting explicitly to the decision-editing discipline: a constitution amendment that contradicts an existing current decision should trigger updating that decision in place, not leaving two governance documents making incompatible claims — the same one-current-file-per-topic rule extended to the Constitution/decision boundary. |
| **release** | Should confirm, before sealing, that every spec included in the release completed verify-before-archive (task linkage populated) rather than just checking the repository delta and knowledge are current — release is a natural second checkpoint for the same guarantee pr-review already checked once. |
| **commit-audit / repo-story** | These read Git history, not the repo's current-truth layer — they're naturally exempt from current-truth-only, since Git is explicitly *where* history is supposed to live under v4. No change needed; worth noting this exemption explicitly somewhere so it doesn't read as an inconsistency. |
| **quickstart install / repair** | Framework-version concern handled only through quickstart prompts. No command prompt owns install, upgrade, or repair as an in-repo lifecycle action. |

## App/framework operations — unaffected

**add-application, list-applications, migrate-registry, validate-registry,
personalize, next** — these manage the multi-app registry and framework
mechanics, not the knowledge/spec lifecycle. No v4-specific revision needed,
though `next` should be aware of the new gate order (plan → tasks → analyze
→ critic → implement, with `context_resolved` now part of what analyze and
critic check) when it decides what the next command is.

## Shim parity

The active v4 inventory has 29 command prompts. Claude and Copilot shims are
present for every active command, including `verify`, `fix-score`, and
`address-pr-review`.
