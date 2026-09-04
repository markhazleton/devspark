# DevSpark Release

`/devspark.release` is the final validation and archival command. It runs at a
human-selected release event after completed work has been implemented, reviewed,
and merged. It is the only DevSpark command allowed to write to `.archive/`.

## Lifecycle position

```text
specify -> clarify when needed -> plan -> tasks -> required gates
-> implement -> focused verify when needed -> create-pr
-> pr-review <-> address-pr-review -> merge

human-selected release event -> /devspark.release
```

Release is not automatically chained from `/devspark.next`. A team may release
after one merged change or batch several completed packages into one release.

## What release validates

For every candidate under `.devspark.work/`, release confirms:

- the package and every task are complete;
- each task has resolvable `code_ref`, `test_ref`, and `knowledge_ref`
  values, or an explained `n/a`;
- governance-changing tasks have a resolvable `governance_ref`;
- referenced tests and the repository release suite pass;
- touched knowledge entities and decisions contain valid evidence;
- generated ontology files are current;
- permanent source and knowledge contain no references to specs, tasks, plans,
  review threads, work-package paths, or archive paths.

If any candidate fails, release leaves it unchanged in `.devspark.work/`,
does not update the version, and reports the exact blockers.

## What release changes

After every validation passes, release:

1. Updates `.devspark/VERSION`.
2. Moves each eligible package intact to
   `.archive/YYYY-MM-DD/<topic>/`.
3. Processes validated items under `.devspark.work/release-candidates/`.
4. Produces release notes from Git commits, merged pull requests, and current
   code and knowledge.

Release never derives current truth or release notes from archive contents.

## Archive boundary

`.archive/` is a human-only recovery buffer outside the DevSpark retrieval
model:

- no DevSpark command reads, lists, enumerates, globs, or summarizes it;
- permanent code, tests, and `.knowledge/` never reference archive paths;
- humans decide when archived material can be deleted.

## Usage

```text
/devspark.release
```

Review the reported candidates, validation commands, next version, archive
destinations, and blockers before treating the release as complete.
