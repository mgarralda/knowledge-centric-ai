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
| Candidate proposal | `capability-proposal.schema.yaml`; OAuth `PROP-AUTH-EVOL-01` | None: proposal generation is outside the deterministic kernel | Candidate carries no institutional capability or CKC identity, may reference any authorized supporting-record type, and may propose directional relations to existing capabilities without preassigning its future identity |
| Submitted proposal | Same proposal type in `auth-evolution-formation` | Validated input to formation | A justified continuity expectation and declared horizon are present; the published trace uses observed history, while tests also admit prospective strategic, unresolved-intent, and onboarding references |
| Supporting-record provenance | Proposal `generated_from.supporting_records` metadata | Checked before governed formation | Every supporting reference resolves to an identified repository, locator, version, and provenance-reference set; bundled companion locators resolve to published files |
| Authorized review | `governance-decision.schema.yaml` | Declared decision consumed by `CapabilityFormationService` | Authority and ownership, distinctiveness, overlap, value, and evidence review results are present |
| Governed promotion | Decision `governed_promotion` and `formation_append` | `CapabilityFormationService.promote` | Exactly one new identity and one complete immutable CKC v1 are appended; approved metadata and proposal-traceable capability relations are recorded |
| Formed state | `REG-SNAP-AUTH-EVOL-FORMED` | Immutable snapshot returned by promotion | Capability is `approved`, has no active pointer, prior entries are unchanged, and Registry relations equal the prior graph plus the approved relations |
| Initial activation | Decision `activation` block | Existing `ActivationService.activate` initial branch | Exact formation append is required; a separate activation publishes CKC v1 |
| Active state | `REG-SNAP-AUTH-EVOL-ACTIVE` | Immutable snapshot returned by activation | Capability is `active`; exact pointer is `CKC-AUTH-EVOL v1` |
| Formation lineage | Proposal, supporting records, decision, CKC provenance, transition edges | `LineageService` extractors | Supporting records, proposal, decision, formation append, identity, CKC, and activation are connected |
| Resolution outcome | `resolution.schema.yaml`; OAuth admitted resolution | `ResolutionService` plus `AssemblyService` | Outcomes use `admitted`, `rejected`, or `escalated`; admitted selection is nonempty and only admitted resolutions can be assembled |
| Assembly lineage | OAuth assembly, source snapshots, and materializations | `LineageService` | Exact source-version and materialization nodes remain linked to the retained assembly |
| CKC succession and reactivation | OAuth decision, successor CKC, append and activation records; constructed reactivation decision | `SuccessionService` plus `ActivationService` | Successor append and activation remain separate; an eligible retained CKC requires a new activation decision and unrelated pointers remain unchanged |

## Machine-checked claims

The companion supports the following bounded claims for its constructed
fixtures and deterministic implementation:

- candidate and submitted proposals are pre-institutional and identity-free;
- promotion accepts only a submitted proposal and an approved, authorized
  decision with the declared review results;
- promotion assigns one previously unused capability identifier and records the
  approved capability metadata;
- proposed relations remain identity-free until promotion; approved relations
  must involve the formed capability, point to an existing capability, and be
  traceable to the proposal;
- the formed Registry relation set is the prior relation set plus those approved
  relations, and initial activation does not alter it;
- promotion appends one complete canonical CKC v1 without a predecessor;
- proposal, decision, retained supporting records, capability, and CKC provenance agree;
- every supporting-record reference has identifiable and resolvable provenance
  metadata before formation can append canonical state;
- supporting records are not restricted to pattern signals, and the submitted
  proposal may justify continuity prospectively without observed frequency;
- formation produces an immutable snapshot with no active pointer for the new
  capability;
- initial activation is a later service call and references the exact formation
  append;
- resolution outcomes use the canonical `admitted`, `rejected`, and
  `escalated` vocabulary; an admitted selection is nonempty and rejected or
  escalated outcomes cannot enter the assembly service;
- assembly lineage contains the exact selected CKCs, bound source versions,
  and materialization records used by the fixture;
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
- reactivation of an eligible retained CKC requires a distinct approved
  activation decision and changes only the target pointer mapping;
- OAuth succession and its historical references continue to pass regression
  tests.

These are implementation-conformance claims for the exercised governed
capability-formation path. They are not a general validation of crystallization.

## Governed judgments and unassessed claims

The implementation consumes, but does not decide, whether:

- the supporting records justify expected recurrence or continuing
  institutional need adequately;
- the declared continuity horizon is sufficient;
- the proposed responsibility has a sound institutional boundary;
- the candidate owner is accountable and appropriate;
- overlap with existing capabilities is acceptable;
- expected value or risk reduction justifies formation;
- organizational outcomes improve longitudinally.

Likewise, retaining the identifier and version of a submitted-report
transformation makes it auditable but does not establish semantic fidelity or
substantive correctness. No machine-checked semantic-correctness claim is made.

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
