# ICLA Artifact Schemas

These YAML documents express JSON Schema Draft 2020-12 contracts for
`icla-spec: 0.1.0`. They validate the stable envelope, identity, provenance,
and principal relations of each reference object while permitting extensions.

The schemas are intentionally minimal at this stage. `additionalProperties` is
enabled so the specification can evolve without invalidating the OAuth 2.1
reference trace.

Where relevant, contracts expose `semantic`, `procedural`, and `episodic` as
overlapping knowledge-role annotations. They describe how governed knowledge
functions for a capability; they are not storage partitions, and a source may
declare more than one role.

The Intent, Resolution, Assembly, and Evidence contracts pin the situated CEE
boundary and the configuration attributes needed for resolution,
authorization, assurance, traceability, and evidence interpretation. The
Assembly also makes the admitted operational mandate explicit:
execution-scoped authority, local CEE autonomy, evidence-only disclosure, and
event-driven re-resolution triggers. The Evidence Bundle records an autonomous
execution interval and contract-selected submission without requiring working
state disclosure. These are nested commitments, not new principal object
types.

The Registry contract can also retain a pre-resolution change-and-impact
history. In the OAuth trace this records the identity-policy version change,
its authorized interpretation and temporal-validity dimensions, the traversed
`CAP-IAM` relation path, governance decision, inactive `CKC-IAM v8` append,
subsequent activation, and the
historical assembly that remains linked to v7. This is a nested Registry
history governed by the existing contract, not a ninth principal schema.

Capability records require an active CKC pointer only in the `active`
lifecycle state. Governance decisions identify an authorized successor delta
with changed CKC commitments, rationale, supporting evidence, authorizing
decision, and rollback reference. The append record adds the complete successor
to its CKC lineage with inactive status and does not move the Registry pointer.
Activation must reference that exact append. The delta explains change and is
not a reconstruction patch.

The governance-decision schema can represent the unpromoted discovery proposal
in the worked scenario, but the eight-schema set has no standalone
capability-proposal contract. Complete promotion, new Registry identity
assignment, initial CKC creation, and preserved promotion-origin links are not
machine-validated by this version of the companion. The paper identifies a
standalone proposal contract, positive and negative proposal validation,
retention without promotion, governed identity assignment, initial immutable
CKC creation, and preserved `derived_from` links as future companion work.

| Schema | Applies to |
|---|---|
| [`capability.schema.yaml`](./capability.schema.yaml) | Standalone institutional capability |
| [`ckc.schema.yaml`](./ckc.schema.yaml) | Standalone Capability Knowledge Contract |
| [`capability-registry.schema.yaml`](./capability-registry.schema.yaml) | Registry snapshot |
| [`intent.schema.yaml`](./intent.schema.yaml) | Operational intent |
| [`resolution.schema.yaml`](./resolution.schema.yaml) | Resolution and admission |
| [`assembly.schema.yaml`](./assembly.schema.yaml) | Contextual assembly |
| [`evidence-bundle.schema.yaml`](./evidence-bundle.schema.yaml) | Execution evidence bundle |
| [`governance-decision.schema.yaml`](./governance-decision.schema.yaml) | Governance decision, successor append, and activation |
