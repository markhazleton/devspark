# Knowledge Drift Performance Corpus

Fixed, offline, deterministic corpus for `tests/test_knowledge_drift_performance.py`.
Never regenerate by hand-editing individual files -- corpus size and content must stay
byte-identical between benchmark runs so medians are comparable across sessions.

- `source/` -- 60 committed Python source files, identically shaped, used to
  benchmark `canonicalize_source` under both the retained `exact-text-v1` profile
  (whole-file byte comparison, the simpler pre-existing approach) and the added
  `python-token-v1` profile (tokenization-based comment/trivia suppression) over the
  same fixed file set.
- `expected-inventory.json` -- the file count a benchmark run must observe; a mismatch
  means the corpus was edited and medians from prior sessions are no longer comparable.
