# Behavior-neutral snapshot baseline

Values captured once from the unchanged tree by `tests/snapshot_baseline_helpers.py`:

- `command-bodies.json` maps each stock command to the SHA-256 of its body after spelling
  normalization (a hyphenated slash invocation of a stock command is read as the dotted form, and
  line endings are normalized to LF).
- `lifecycle-outputs.json` maps each gate bundle in `../stage-evidence/` to the verdict from
  `scripts/judge.py lifecycle` and to the selected fields reported by both `next-context` twins.

Regenerate only from an unchanged tree, with `PYTHONPATH=src python tests/snapshot_baseline_helpers.py`.
An intended change is recorded as a reason-annotated named delta in the snapshot test, not by
silently regenerating these files. All content is synthetic.

For Make Bold branding, the command hashes were derived from the unchanged pre-9
tree at commit `cad947e410d7d17785d2a06d5fa516e1a3a05a9e` after applying the same
product-name, distribution-URL, and version-stamp
normalization used by this repository. Each original hash was verified before
rebranding. The v9.0 command changes and their named deltas remain independently
checked against that earlier baseline.
