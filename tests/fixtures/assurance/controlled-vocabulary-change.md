---
expected_owner: critic
expected_applicable: true
signals: [persistent-data-shape]
---

# Controlled vocabulary change

## Shape

A change adds, renames, or re-scopes members of a controlled vocabulary that is
written to durable storage — a status set, a category list, a type enumeration.
The artifacts describe the new vocabulary consistently.

```text
Change:       Adds two members to a persisted status vocabulary.
Baseline:     Existing rows carry the old members; three downstream readers
              branch exhaustively on the old set.
Consequence:  Readers encounter an unmodelled value; historical rows cannot
              be interpreted under the new scheme without a stated rule.
```

## Why Critic owns it

The hazard lives in the data already stored and in the consumers already
written, neither of which appears in the planning artifacts. A closed-world
reading of the spec finds the vocabulary perfectly coherent.

## What a correct finding looks like

Names the readers that branch exhaustively, states what they do on an unknown
member, and asks for the backfill or compatibility rule. One finding, one root
cause — not a separate finding per reader.
