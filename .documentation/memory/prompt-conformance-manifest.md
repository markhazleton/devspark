---
document: prompt-conformance-manifest
version: "1.0.0"
created: "2026-06-03"
scope: templates/commands/
---

# Prompt Conformance Manifest

This manifest defines the required governance elements that every command template in
`templates/commands/` must contain. It is evaluated by an AI agent via `/devspark.checklist`
— no new scripts or tool dependencies required.

> **Contributor obligation**: Run `/devspark.checklist` against this manifest before any
> PR that modifies files in `templates/commands/`. This is the re-run trigger for the
> conformance baseline.

## Required Elements — All Command Templates

For each file in `templates/commands/`, verify the following three elements:

### Element 1 — Constitution Authority Block

**Check**: The file contains a block referencing `constitution.md` as non-negotiable authority.

**Deterministic anchor**: The file MUST contain the string `constitution.md` AND the word
`non-negotiable` within 15 lines of each other.

**Finding if missing**:

```yaml
finding_id: conformance-{command-name}-01
severity: high
description: "Command template is missing a Constitution Authority block. The template
  does not reference constitution.md as non-negotiable within 15 lines. This allows
  implementations to drift from constitution principles without a documented gate."
recommended_action: "Add a '## Constitution Authority' section (or equivalent functional
  block) that references constitution.md as non-negotiable for this command's scope."
execution_mode: manual
status: open
outcome: ""
```

**Constitution reference**: `§IV.SHOWSTOPPER` (Governance Authority — all commands must
enforce constitution non-negotiability).

---

### Element 2 — Frontmatter Handoffs Block

**Check**: The YAML frontmatter block contains the key `handoffs:`.

**Deterministic anchor**: The file's YAML frontmatter (between the opening `---` and
closing `---`) MUST contain the key `handoffs:`.

**Finding if missing**:

```yaml
finding_id: conformance-{command-name}-02
severity: medium
description: "Command template frontmatter is missing the 'handoffs:' key. Without
  handoff declarations, downstream workflow routing is undefined and agents cannot
  surface next-step options to users."
recommended_action: "Add a 'handoffs:' block to the YAML frontmatter with at least
  one downstream agent label and prompt."
execution_mode: manual
status: open
outcome: ""
```

---

### Element 3 — Artifact Output Statement

**Check**: The file describes at least one artifact it produces or writes.

**Deterministic anchor**: The file MUST contain at least one of the following phrases
in a section describing what the command produces: `Write`, `Save`, `Create`, `Generate`,
`Output`. The phrase must appear in a context describing a command output (not just as
a verb in a general description).

**Finding if missing**:

```yaml
finding_id: conformance-{command-name}-03
severity: medium
description: "Command template does not contain a clear artifact output statement.
  Users and downstream tools cannot determine what artifact this command produces
  or where it is saved."
recommended_action: "Add an explicit statement describing the artifact this command
  creates or updates, including the file path where it is written."
execution_mode: manual
status: open
outcome: ""
```

---

## Default Behavior for Unlisted Templates

Any file in `templates/commands/` not explicitly mentioned in the Known Variant Headings
section below is evaluated against all three universal required elements above.

Findings for unlisted templates use the same `finding_id` pattern:
`conformance-{command-name}-{01|02|03}`

Failures for unlisted templates are flagged as **LOW** severity unless the missing element
is Element 1 (Constitution Authority), which is always **HIGH** regardless of whether the
template is listed or not.

---

## Known Variant Headings

The following commands use non-standard headings or structures for constitution authority
content. They are pre-documented to prevent false positives.

### `evolve-constitution.md`

**Variant**: Uses `## Lifecycle Position` instead of `## Constitution Authority`.

**Qualifying text present**: The section contains the phrase `constitution.md` and
references it as non-negotiable authority within the Lifecycle Position block.

**Status**: Acceptable — passes Element 1 check.

---

### `specify.md`

**Variant**: Has `## Constitution Authority` heading but uses "MUST align" rather than
"non-negotiable" as the authority phrase; references `constitution.md` in the section.

**Qualifying text present**: `## Constitution Authority` heading present; "MUST align with
mandated principles" is functionally equivalent to non-negotiable enforcement.

**Status**: Acceptable — passes Element 1 check via heading + constitution.md reference.

---

## Conformance Check Procedure

When invoked via `/devspark.checklist`:

1. List all files in `templates/commands/`
2. For each file, evaluate the three required elements using the deterministic anchors above
3. Check Known Variant Headings before flagging Element 1 failures
4. For any missing element, emit a finding using the Shared Review Resolution Contract schema
   (as defined in each element's "Finding if missing" block above)
5. Manually verify 3 known-good templates (`specify.md`, `plan.md`, `pr-review.md`) pass
   all three checks as a sanity test before accepting any full baseline

**Pass**: All three elements present in all templates → no findings emitted.

**Fail**: One finding per missing element per template.

---

## Baseline Results

*To be populated after T013 baseline run. Document pass/fail results per template here.*

<!-- BASELINE: Run 2026-06-03 against specify.md, plan.md, pr-review.md (sanity check).

Sanity results:
- plan.md: PASS (all 3 elements present; constitution.md + non-negotiable on same line)
- pr-review.md: PASS (all 3 elements present; non-negotiable in Guidelines/Constitution Authority section)
- specify.md: VARIANT — Element 1 uses "MUST align" with constitution.md rather than "non-negotiable";
  has ## Constitution Authority heading. Adding to Known Variant Headings below.

Full baseline across all templates/commands/ files: pending /devspark.checklist run.
Re-run before any PR that modifies files in templates/commands/.
-->
