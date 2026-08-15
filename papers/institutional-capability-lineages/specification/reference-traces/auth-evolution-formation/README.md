# Governed Capability-Formation Reference Trace

This constructed trace exercises the deterministic institutional transition
that follows proposal generation and review. It does not generate a proposal
or decide whether it is institutionally valuable.

The trace is a valid history-driven instance. It begins with a pre-institutional
`submitted` proposal supported by multiple retained assembly and evidence
references. The proposal contract is more general: unresolved intents,
strategic decisions, process-analysis records, onboarding records, and other
authorized retained records may also support formation. An authorized governance
decision then assigns one new identity, records approved metadata and
capability-to-capability relations, and appends one complete initial CKC v1.
That formation state is retained before a separate activation publishes the CKC
for future resolutions.

```text
PROP-AUTH-EVOL-01 (submitted, no institutional identity)
        |
        v
DEC-AUTH-EVOL-FORMATION-001
        |
        v
FORM-AUTH-EVOL-001
        |----> CAP-AUTH-EVOL (approved, no active pointer)
        `----> CKC-AUTH-EVOL v1 (canonical, inactive)
                        |
                        v
              ACT-AUTH-EVOL-001
                        |
                        v
              CAP-AUTH-EVOL (active)
```

## Artifacts

1. [`capability-proposal.yaml`](./capability-proposal.yaml) records the
   submitted proposal, supporting-record references, history-driven continuity
   basis, and a provenance index with record identity, repository, locator,
   version, and provenance references, plus stable assembly rules and value basis,
   candidate owner, overlap review input, identity-free proposed relations to
   existing capabilities, and proposal-scoped CKC draft.
2. [`registry-before.yaml`](./registry-before.yaml) proves that
   `CAP-AUTH-EVOL` does not exist before promotion.
3. [`governance-decision.yaml`](./governance-decision.yaml) records the
   authorized review, assigned identity and metadata, approved Registry
   relations, formation append, and separately identifiable initial activation.
4. [`ckc-auth-evol-v1.yaml`](./ckc-auth-evol-v1.yaml) is the complete immutable
   initial contract, with no predecessor and with proposal, decision, formation,
   and supporting-record provenance.
5. [`registry-formed.yaml`](./registry-formed.yaml) records the intermediate
   state: the capability exists as `approved`, has the approved Registry
   relations, but has no active CKC pointer.
6. [`registry-active.yaml`](./registry-active.yaml) records the later activation
   of exactly `CKC-AUTH-EVOL v1`.

## Executable result

The reference implementation replays the decision in two calls:

```text
promote(submitted proposal, authorized decision)
    -> formed Registry snapshot + inactive-initial-CKC receipt

activate(formed capability, CKC v1, same declared governance transaction)
    -> active Registry snapshot + separate activation record
```

The tests require both generated snapshots to equal the published artifacts.
Negative cases reject candidate proposals, unauthorized actors, duplicate
identities, incomplete or wrongly linked CKCs, activation before formation,
wrong append references, unresolved supporting-record provenance, unreviewed
or non-capability Registry relations, and repeated promotion without leaving
partial state. Bundled companion locators are also
resolved to their published files. Organizational-Memory locators remain
external reference metadata; the companion does not claim retrieval of their
payloads. Registry `relations` are capability-to-capability edges; proposal,
decision, CKC, and supporting-record origin links in the formation lineage are
separate broader-lineage edges.

## Assessment boundary

This trace supports executable consistency for governed capability formation
and initial activation. It does not assess proposal-generation or pattern-
discovery effectiveness, the adequacy of observed or prospective continuity
justifications, boundary quality, ownership, value, overlap resolution, or
organizational effectiveness. Those remain declared inputs or institutional
judgments.
