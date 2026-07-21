
# Reference Objects

Reference objects are reusable, consumer-independent representations of the
information types defined by Institutional Capability Lineages. They differ
from [`reference-traces/`](../reference-traces/README.md), which serialize
complete executions and their governed transitions.

Organizational-memory roles are represented as overlapping annotations within
CKC bindings, assemblies, and evidence rather than as additional principal
object types. This preserves the eight-object contract model while making
semantic, procedural, and episodic knowledge functions inspectable.

The evidence bundle also preserves the other direction of the memory loop:
CEEs consume authorized assemblies but may produce situated observations,
artifacts, practices, and decisions. Such outputs remain candidate knowledge
until an identified evidence path and governance decision admit them.

The initial object catalog is defined through the schemas:

| Object | Structural contract |
|---|---|
| Institutional capability | [`capability.schema.yaml`](../schemas/capability.schema.yaml) |
| Capability Knowledge Contract | [`ckc.schema.yaml`](../schemas/ckc.schema.yaml) |
| Registry snapshot | [`capability-registry.schema.yaml`](../schemas/capability-registry.schema.yaml) |
| Operational intent | [`intent.schema.yaml`](../schemas/intent.schema.yaml) |
| Capability resolution | [`resolution.schema.yaml`](../schemas/resolution.schema.yaml) |
| Contextual assembly | [`assembly.schema.yaml`](../schemas/assembly.schema.yaml) |
| Evidence bundle | [`evidence-bundle.schema.yaml`](../schemas/evidence-bundle.schema.yaml) |
| Governance decision and activation | [`governance-decision.schema.yaml`](../schemas/governance-decision.schema.yaml) |

Generic reference instances will be added here only when they can remain
independent of a particular execution trace. This avoids presenting partial
templates as canonical objects.
