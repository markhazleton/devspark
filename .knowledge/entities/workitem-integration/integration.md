---
id: workitem-integration-integration
type: entity-layer
title: "Work Item Integration - Boundary"
layer: integration
source_of_truth:
  - scripts/powershell/workitem.ps1
  - scripts/bash/workitem.sh
  - tests/test_workitem_contract.py
last_verified: 2026-10-13
aliases:
  - work item boundary
  - work tracking integration
  - propose and apply
---

<!-- markdownlint-disable MD025 -->

# Work Item Integration - Boundary

The **only** place in the framework that talks to the external work tracking system. Nothing else
calls it, and no workflow reaches around it.

Concentrating the boundary in one script is what makes the rest of the system testable: every other
component deals in a local result record rather than in network calls, credentials, and remote
state.

## Result contract

Every operation emits **exactly one canonical result line and exits successfully**, including when
the operation failed. Callers parse the result; they do not interpret an exit code.

| Exit | Meaning |
| --- | --- |
| Success | The operation ran. The emitted record says whether it succeeded. |
| Non-zero | The script was **invoked wrongly** - unknown operation, missing required argument. |

An operational failure - the remote system unreachable, the item not found, a write refused - is a
result, not a crash. Inverting this would force every caller to distinguish "you asked incorrectly"
from "the remote system said no" by parsing error text.

## Propose then apply

Writes are two-phase. A proposal is built and returned for inspection; applying it is a separate,
explicitly confirmed call. An agent never composes and commits a remote change in one step, which
is what keeps a human in the loop on anything leaving the repository.

## Concurrency is refused, not resolved

A proposal is built against a specific revision of the item, and applying it requires carrying that
revision forward. If the item moved in between, **the write is refused** and the result says so.

The boundary does not merge, retry, or overwrite. An agent working from a view that is no longer
current re-reads and rebuilds its proposal. Silently winning that race would overwrite a human
edit that nothing in the system ever recorded.

## Creation is narrow and never incidental

The boundary never creates a `User Story`. A create request that names one, or that relies on a
default resolving to one, is answered with the unsupported-type failure and a corrective action; the
default create type is `Task`. No lifecycle stage (specification, planning, implementation,
verification, closeout, pull request, release) creates a work item as a side effect, and a missing
external record is never a reason to make one. Existing items may be read, referenced and linked.

## Credentials

The script authenticates for the duration of a call and never persists a credential. Emitted output
and diagnostics are scrubbed of anything resembling a token or secret before leaving the process,
and the cleanup runs on every exit path including failure.

A boundary that writes a credential to disk turns one leaked artifact into standing access to the
tracking system.

## Dual-language parity

Two entry points, one per supported environment, accepting the same operations and emitting the
same record shape. **They change together, always.** Divergence means a documented instruction
behaves differently depending on which environment ran it, and that difference surfaces as
inconsistent remote state rather than as a local error.

## Offline verification

Behavior is verified against recorded fixtures rather than a live service, so the contract can be
exercised without credentials, network access, or a mutable remote project.
