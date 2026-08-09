# Conformance and Executable Claim Boundary

This document records what the companion can verify after the governed
capability-formation extension. The paper remains the authority for ICLA's
conceptual meaning; schemas and code are inspectable realizations of that
meaning.

The complete invariant-level evidentiary mapping is published in the
[ICLA conformance coverage matrix](../specification/conformance-matrix.md).
That matrix maps ICLA-1–ICLA-11 without assigning a score, pass/fail column, or
certification status. The construct matrix below focuses on the complementary
capability-formation path.

## Construct-to-artifact matrix

| Construct or transition | Schema / retained artifact | Executable operation | Principal verification |
|---|---|---|---|
| Candidate proposal | `capability-proposal.schema.yaml`; OAuth `PROP-AUTH-EVOL-01` | None: detection is outside the deterministic kernel | Candidate carries no institutional capability or CKC identity |
| Submitted proposal | Same proposal type in `auth-evolution-formation` | Validated input to formation | Recurrence is declared established and multiple retained signals are referenced |
| Authorized review | `governance-decision.schema.yaml` | Declared decision consumed by `CapabilityFormationService` | Authority and ownership, distinctiveness, overlap, value, and evidence review results are present |
| Governed promotion | Decision `governed_promotion` and `formation_append` | `CapabilityFormationService.promote` | Exactly one new identity and one complete immutable CKC v1 are appended |
| Formed state | `REG-SNAP-AUTH-EVOL-FORMED` | Immutable snapshot returned by promotion | Capability is `approved`, has no active pointer, and prior entries are unchanged |
| Initial activation | Decision `activation` block | Existing `ActivationService.activate` initial branch | Exact formation append is required; a separate activation publishes CKC v1 |
| Active state | `REG-SNAP-AUTH-EVOL-ACTIVE` | Immutable snapshot returned by activation | Capability is `active`; exact pointer is `CKC-AUTH-EVOL v1` |
| Formation lineage | Proposal, decision, CKC provenance, transition edges | `LineageService` extractors | History, proposal, decision, formation append, identity, CKC, and activation are connected |
| CKC succession | OAuth decision, successor CKC, append and activation records | `SuccessionService` plus `ActivationService` | Existing resolution-to-succession behavior remains unchanged |

## Machine-checked claims

The companion supports the following bounded claims for its constructed
fixtures and deterministic implementation:

- candidate and submitted proposals are pre-institutional and identity-free;
- promotion accepts only a submitted proposal and an approved, authorized
  decision with the declared review results;
- promotion assigns one previously unused capability identifier;
- promotion appends one complete canonical CKC v1 without a predecessor;
- proposal, decision, retained history, capability, and CKC provenance agree;
- formation produces an immutable snapshot with no active pointer for the new
  capability;
- initial activation is a later service call and references the exact formation
  append;
- invalid requests are rejected before append-only writes in the single-process
  reference flow;
- input snapshots and earlier trace records are not rewritten;
- resolution retains the matcher identifier/version and explicit confidence
  semantics without presenting qualitative ranking as calibrated probability;
- institutional capabilities cannot use the pre-institutional `candidate` or
  `submitted` states, which belong exclusively to Capability Proposal;
- the OAuth `RequiredCovered` trace pins its deterministic method and validator
  version;
- `ConflictsResolved` retains the applicable conflict, compatible outcome, and
  policy/version basis, while unresolved CKC conflicts block assembly;
- a submitted-report transformation, when declared, must retain an identifier
  and version in evidence provenance;
- a schema-valid bundle may still be rejected when governed evidence is
  insufficient;
- impact analysis identifies review scope without mutating canonical state;
- successor append rejects a stale predecessor before creating a branch or
  changing the active pointer;
- OAuth succession and its historical references continue to pass regression
  tests.

These are implementation-conformance claims for the exercised governed
capability-formation path. They are not a general validation of crystallization.

## Governed judgments and unassessed claims

The implementation consumes, but does not decide, whether:

- the retained history establishes recurrence adequately;
- the declared time horizon is sufficient;
- the proposed responsibility has a sound institutional boundary;
- the candidate owner is accountable and appropriate;
- overlap with existing capabilities is acceptable;
- expected value or risk reduction justifies formation;
- organizational outcomes improve longitudinally.

The companion also makes no claim of distributed or crash-atomic persistence.
It validates every deterministic precondition before writing and demonstrates
no partial effects for rejected requests in its single-process append-only
store. Production transaction, concurrency, and recovery semantics remain
outside scope.

## Verification commands

```console
poetry run icla validate-schemas
poetry run icla run-trace oauth-042
poetry run icla run-trace auth-evolution-formation
poetry run pytest
```
