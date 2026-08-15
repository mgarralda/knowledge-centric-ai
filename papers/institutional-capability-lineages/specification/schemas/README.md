# ICLA Artifact Schemas

These YAML documents express JSON Schema Draft 2020-12 contracts for
`icla-spec: 0.1.0`. They validate the stable envelope, identity, provenance,
and principal relations of each reference object while permitting extensions.

The schemas are intentionally limited to the implemented conformance claims
while permitting non-normative extensions. `additionalProperties` is enabled
so the specification can evolve without invalidating the reference traces.
The companion-wide mapping from those invariants to schemas, traces, tests, and
governed judgments is maintained in
[`../conformance-matrix.md`](../conformance-matrix.md).

Where relevant, contracts expose `semantic`, `procedural`, and `episodic` as
overlapping knowledge-role annotations. They describe how governed knowledge
functions for a capability; they are not storage partitions, and a source may
declare more than one role.

The Intent, Resolution, Assembly, and Evidence contracts pin the situated CEE
boundary and the configuration attributes needed for resolution,
authorization, assurance, traceability, and evidence interpretation. The
Resolution record additionally retains the matcher identifier/version and
explicit confidence semantics; the reference trace marks qualitative ranking
as non-calibrated rather than presenting it as probability. Its outcome uses
the canonical `admitted`, `rejected`, or `escalated` vocabulary. An admitted
outcome requires a nonempty exact capability-to-active-CKC selection; rejected
and escalated outcomes may have an empty selection and do not authorize
assembly. The
Assembly also makes the admitted operational mandate explicit:
execution-scoped authority, local CEE autonomy, evidence-only disclosure, and
event-driven re-resolution triggers. The Evidence Bundle records an autonomous
execution interval and contract-selected submission without requiring working
state disclosure. Assembly correctness traces additionally retain the applied
`RequiredCovered` assessment method and applicable validator, model, or
review-policy version. Evidence lineage conditionally retains any versioned
transformation used to construct the submitted report. These are nested
commitments, not new principal object types.
The Evidence Gateway receipt records schema conformity and measurement
conformity separately from qualification status.
The same assembly correctness trace records every applicable conflict through
its assembly-compatible resolution outcome and versioned policy basis. A
successful successor append remains an implementation operation rather than a
new artifact type and requires the latest appended CKC as predecessor.

The Registry contract can also retain a pre-resolution change-and-impact
history. In the OAuth trace this records the identity-policy version change,
its authorized interpretation and temporal-validity dimensions, the traversed
`CAP-IAM` relation path, governance decision, inactive `CKC-IAM v8` append,
subsequent activation, and the
historical assembly that remains linked to v7. This is a nested Registry
history governed by the existing contract, not a ninth principal schema.

Capability records use only institutional lifecycle states and require an
active CKC pointer only in the `active` state. The pre-institutional
`candidate` and `submitted` states belong exclusively to Capability Proposal;
they cannot be assigned to a `CAP-*` identity. Governance decisions identify an authorized successor delta
with changed CKC commitments, rationale, supporting evidence, authorizing
decision, and rollback reference. The append record adds the complete successor
to its CKC lineage with inactive status and does not move the Registry pointer.
Activation must reference that exact append. The delta explains change and is
not a reconstruction patch. A separately authorized `reactivation` may point
to an eligible retained CKC without claiming a new append; it records the
current pointer as the prior state.

The standalone capability-proposal schema represents the same pre-institutional
object in `candidate` and `submitted` states. It never carries an assigned
capability identity or institutional CKC identifier. Optional
`proposed_relations` refer directionally to existing `CAP-*` identities without
preassigning the future capability identity. Its
`supporting_record_refs` may identify unresolved intents, realized work,
strategic decisions, process-analysis records, onboarding records, or other
authorized retained records; a pattern signal is not universally required.
The existing `generated_from.supporting_records` metadata resolves each such
reference through its record type, repository, locator, version, and provenance
references. It is provenance metadata, not another principal object type.
Submission records a justified expectation of recurrence or continuing
institutional need over a declared horizon, using observed, prospective, or
mixed grounds. OAuth keeps the proposal as a candidate because one execution
does not satisfy its history-driven review criteria. The formation trace
submits the same proposed responsibility after multiple retained records are
declared.

The governance-decision schema uses its existing `capability_formation` boundary
to distinguish an unpromoted proposal reference from governed formation. A
positive formation records the submitted proposal, authorized review, assigned
identity and metadata, any approved capability-to-capability Registry relations,
initial CKC v1, and inactive formation append. Registry relations use only
capability endpoints; links from the new identity or CKC to proposals and other
non-capability supporting records belong to the broader lineage instead. Initial activation is
optional at formation time and, when present, must remain a separate effect that
references the exact formation append. The CKC schema conditionally requires
proposal, decision, formation, and supporting-record origins when CKC v1 declares
`formation_origin: crystallization`.

| Schema | Applies to |
|---|---|
| [`capability.schema.yaml`](./capability.schema.yaml) | Standalone institutional capability |
| [`capability-proposal.schema.yaml`](./capability-proposal.schema.yaml) | Pre-institutional capability proposal |
| [`ckc.schema.yaml`](./ckc.schema.yaml) | Standalone Capability Knowledge Contract |
| [`capability-registry.schema.yaml`](./capability-registry.schema.yaml) | Registry snapshot |
| [`intent.schema.yaml`](./intent.schema.yaml) | Operational intent |
| [`resolution.schema.yaml`](./resolution.schema.yaml) | Resolution and admission |
| [`assembly.schema.yaml`](./assembly.schema.yaml) | Contextual assembly |
| [`evidence-bundle.schema.yaml`](./evidence-bundle.schema.yaml) | Execution evidence bundle |
| [`governance-decision.schema.yaml`](./governance-decision.schema.yaml) | Governance decision, successor append, and activation |
