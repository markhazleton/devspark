# Knowledge

DevSpark treats code, tests, and knowledge as one durable product. Code expresses what the system does, tests provide executable evidence, and `.knowledge/` explains the current behavior, constraints, and operational choices a future contributor needs. A change is complete when those three surfaces agree. For the reasoning behind this model, see [Philosophy](../why/philosophy.md); for where `.knowledge/` sits among the four roots, see [How It Works](../get-started/how-it-works.md#four-roots).

## What belongs in knowledge

Only `.knowledge/` is the durable knowledge base. Content is rewritten in place when behavior changes, and Git preserves earlier versions. Planning records can link forward to code and knowledge, but durable files never point back to temporary planning paths.

Knowledge is organized as typed nodes:

- **Entities** (directories) describe architecture, behavior, interfaces, or operations in layers.
- **Flat documents** cover topics that do not need an entity.
- **Governance** documents record project rules; **decisions** record why a choice was made, one current file per topic. A decision declares the entities it constrains, and each entity carries a reciprocal reference.

The index builder uses the taxonomy and entity layout to detect unclassified files, missing layers, unresolved relations, and behavior-bearing code with no corresponding knowledge.

Tests are a durable pillar alongside code and knowledge: durable, repeatable evidence, curated (added, updated or retired) rather than only accumulated. Knowledge is the claim, tests are the evidence, and code is the subject.

A spec's own knowledge is consumed by purpose. Requirements and success criteria authorize plan work, domain invariants, architectural constraints and accepted limitations constrain it, and context informs it without becoming scope.

## Evidence beside the behavior

Each node names its source of truth and cites evidence:

- **Executable evidence:** a test that is rerun and currently passes.
- **Inspection evidence:** a reviewed code path, with the reason a test was not used.

`appliesTo` patterns, evidence entries, and an optional `last_verified` date connect a statement to the code that supports it. The Knowledge index is built in memory from the Markdown, so discovery never depends on a committed file. The optional derived `.knowledge/index.json` and ontology coverage report make these links machine-readable and expose invalid paths, broken governance links, and stale metadata, but a stale or missing copy never blocks a change.

### Content-drift detection (optional)

Dates are only a currency signal. For content-based drift detection, a source claim can record its path, a canonical digest, a comparison profile, and a retained baseline under `.knowledge/evidence/source-baselines/`.

- Preview conversion with `python scripts/build_knowledge_index.py --migrate-source-claims`, review it, then apply with `--write`. Migrated claims are marked `pinned-unverified`.
- Enforcement is opt-in: set `"knowledge_drift": { "enforcement": "pinned-claims" }` in `.devspark.work/devspark.json`.
- Routine evaluation needs explicit `--base` and `--head` commits; without Git history use `--detect-drift --full-inventory`.
- Profiles: `python-token-v1` (ignores comments and layout), `exact-text-v1`, and `binary-v1`.
- To re-verify a changed claim, run `/devspark-explain <topic>`, inspect the baseline diff, and confirm rotation. Baselines rotate one claim at a time.

Reports contain paths and digests, never source bodies.

## Who keeps knowledge aligned

| Skill | Knowledge question | Scope |
|---|---|---|
| `/devspark-implement` | What must change together with the code? | Updates the affected nodes in the same change; checks that Knowledge still builds |
| `/devspark-explain` | Is this one topic documented accurately? | One topic; detects and repairs drift |
| `/devspark-pr-review` | Does this diff contradict or under-document knowledge? | The diff (`PRD1` to `PRD5`) |
| `/devspark-site-audit` | Is the whole knowledge model consistent? | The repository (`DELTA`, `KNOW1` to `KNOW6`) |
| `/devspark-release` | Is the window already audited? | Requires a current knowledge-scope audit; does not repeat it |

PR review and site audit are described in [Review and Audit](review-and-audit.md). `/devspark-discover-knowledge` proposes gaps, weak mappings, and contradictions for human review, and `/devspark-context-projection` inspects the knowledge graph directly.

## Explain a topic

`/devspark-explain` answers "how is X done?" from current code and verifies that `.knowledge/` agrees, for an existing article or an undocumented topic.

```text
/devspark-explain how is authentication done
/devspark-explain --dry-run how is the knowledge index built
```

1. It resolves the topic against the knowledge index and source tree.
2. It checks matched knowledge against the code and tests it describes, using the same `DELTA` and `KNOW1` to `KNOW4` finding codes as site audit, scoped to the topic.
3. It answers in prose, citing `path:line` for every nontrivial claim.
4. Missing or drifted knowledge is reported, not automatically promoted into work. When the developer requests a correction or draft, it clarifies ambiguous ownership or intent, shows the proposed update, and writes only after that update's own explicit approval. It then re-checks that the Knowledge builds and re-verifies.

`--dry-run` only proposes and never writes, which suits CI or chained agents. Output has three sections: **Answer**, **Findings**, and an **Agent Summary** JSON block. Saving a run to `.devspark.work/explain/<topic>-<date>.md` needs a separate approval, never bundled with the Knowledge update; the trace is replaceable work, not durable truth.

Explain documents existing behavior only. It never creates a planning record or new code; confirmed code defects are offered to `/devspark-quickfix`, and unimplemented behavior to `/devspark-specify`. Explain builds the index in memory on every run, so there is no stale index to repair; if the Knowledge does not build it reports the error first. Durable knowledge may cite durable code and tests only, never a spec, plan, task, `.devspark.work/`, or `.archive/` path.

## Practical rule

When behavior changes, update the code, the tests that prove it, and the knowledge node or guide that explains it. When a document looks stale, verify the cited code and tests before touching its metadata. When the behavior does not exist yet, record the gap as planned work instead of writing current knowledge for an unimplemented design.
