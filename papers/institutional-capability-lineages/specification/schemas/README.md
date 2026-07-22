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

The Assembly contract also makes the admitted operational mandate explicit:
execution-scoped authority, local CEE autonomy, evidence-only disclosure, and
event-driven re-resolution triggers. The Evidence Bundle records an autonomous
execution interval and contract-selected submission without requiring working
state disclosure. These are nested commitments, not new principal object
types.

| Schema | Applies to |
|---|---|
| [`capability.schema.yaml`](./capability.schema.yaml) | Standalone institutional capability |
| [`ckc.schema.yaml`](./ckc.schema.yaml) | Standalone Capability Knowledge Contract |
| [`capability-registry.schema.yaml`](./capability-registry.schema.yaml) | Registry snapshot |
| [`intent.schema.yaml`](./intent.schema.yaml) | Operational intent |
| [`resolution.schema.yaml`](./resolution.schema.yaml) | Resolution and admission |
| [`assembly.schema.yaml`](./assembly.schema.yaml) | Contextual assembly |
| [`evidence-bundle.schema.yaml`](./evidence-bundle.schema.yaml) | Execution evidence bundle |
| [`governance-decision.schema.yaml`](./governance-decision.schema.yaml) | Governance decision and activation |
