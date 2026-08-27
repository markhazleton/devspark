# Contract: Genuine Fix Discipline

## Shared Guidance

`templates/command-preamble-contract.md` must include:

- `## 9. Genuine Fix Discipline`
- `### 9.1 Intent Cues`
- `### 9.2 Constitution Citation Hook`

The guidance must state that commands resolve behavioral intent first and use metrics only as supporting evidence.

## Required Command References

The following command prompts must reference Genuine Fix Discipline:

- `templates/commands/implement.md`
- `templates/commands/quickfix.md`
- `templates/commands/pr-review.md`
- `templates/commands/address-pr-review.md`

## Finding Fields

Analyze and critic findings must include:

```yaml
intent_cue: <behavioral intent that must be repaired or preserved>
```

Site-audit findings must include:

```text
Intent: <behavioral intent that must be repaired or preserved>
```

## Verify Guard

`/devspark.verify` must reject a proof when all of the following are true:

- The proof only shows a metric decreasing or improving.
- The proof states or demonstrates unchanged behavior.
- No behavioral evidence supports the intended repair.

## Constitution Hook

`/devspark.constitution` must include a matching principle requiring genuine fixes to cite behavioral intent and, when applicable, the constitution principle they protect.

## Constitution Amendment Governance

Before implementation changes `.documentation/memory/constitution.md`, the implementer must record all of the following:

- Amendment rationale: add Genuine Fix Discipline as a governance principle so metric-only fixes cannot satisfy behavioral obligations.
- Approval: the user requested "apply all actions" and then `/devspark.implement` on 2026-08-27 after analyze/critic findings identified the constitution hook as required remediation.
- Version and sync impact: classify the amendment as MINOR (`v1.4.0` to `v1.5.0`) because it adds a new named principle. The constitution sync impact report must list command preamble, verify, analyze, critic, site-audit, implement, quickfix, pr-review, address-pr-review, constitution command, README, templates README, and contract tests as checked or updated.
- Migration plan: existing features remain valid; new command guidance applies prospectively, coverage validation remains fail-soft, and no existing JSON consumer is migrated.

The constitution amendment task is unblocked by this recorded evidence.
