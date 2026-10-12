# Verify

```yaml
gate: verify
devspark_version: "9.0.0"
generated: "2026-01-15T10:00:00Z"
status: pass
blocking: false
summary: "Pre-merge proof passed; the post-deploy criterion has no recorded home."
modes:
  - mode: regression-pinned
    stage: pre-merge
    evidence_class: automated
    status: pass
    evidence: |
      pytest tests/test_warmup.py -q
      3 passed in 0.4s
```
