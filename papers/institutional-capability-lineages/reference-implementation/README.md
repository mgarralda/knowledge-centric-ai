# ICLA Reference Implementation

Deterministic Python demonstrator for the **Institutional Capability Lineage
Architecture (ICLA)**, a registry-centered architecture for governing
capability evolution in AI-enabled organizations.

This package provides an inspectable execution model for the companion ICLA
specification. It demonstrates how stable capability identity, versioned
Capability Knowledge Contracts (CKCs), contextual assembly, evidence,
governance, successor append, activation, and lineage fit together without requiring a database,
LLM, MCP server, or cloud infrastructure.

The project is an architectural reference implementation, not a production
platform.

## Relationship to the ICLA artifacts

- The reviewed manuscript defines the concepts, invariants, lifecycle, and
  evaluation claims; reviewer packages intentionally omit the manuscript.
- [Reference schemas](../specification/schemas/README.md) — nine JSON Schema
  Draft 2020-12 contracts.
- [OAuth 2.1 reference trace](../specification/reference-traces/oauth-042/README.md)
  — eight linked artifacts corresponding to the paper's worked example.
- [Capability-formation trace](../specification/reference-traces/auth-evolution-formation/README.md)
  — six linked artifacts for submitted proposal, governed formation, and
  separate initial activation.
- [Implementation architecture](ARCHITECTURE.md) — direct mapping from the
  paper and specification to Python modules and services.
- [Conformance and claim boundary](CONFORMANCE.md) — construct-to-artifact
  coverage and the exact limits of the executable evidence.
- [Invariant conformance coverage](../specification/conformance-matrix.md) —
  ICLA-1–ICLA-11 mapping from machine-checkable clauses to supporting
  artifacts, executable tests, and governed-judgment remainders.

The paper defines the architecture. The sibling `../specification/` directory
defines the reference artifact contracts. This package makes both the
resolution-to-succession path and the deterministic governed capability-
formation transition executable and testable.

The paper develops ICLA as an iteratively refined design-science artifact. This
implementation provides requirement-to-component traceability and artificial
technical evaluation; it does not imply a linear derivation from literature or
constitute organizational validation.

## Implemented scope

The implementation includes:

- Registry navigation and filtering by metadata, lifecycle, policy, and
  conditions;
- overlapping semantic, procedural, and episodic knowledge-role annotations
  without imposing storage partitions;
- intent resolution, relation traversal, constraint checking, and admission;
- explicit `admitted`, `rejected`, and `escalated` resolution outcomes; only an
  admitted outcome has a mandatory nonempty exact capability-to-CKC map and
  may proceed to assembly;
- retained matcher identity/version and explicit, non-calibrated confidence
  semantics for resolution auditability;
- immutable contextual assembly with an execution-scoped operational mandate
  and exact CKC, source, policy, evaluation, and transformation versions;
- bundle, payload, workspace, and governed-access-handle materialization;
- execution-scoped CEE boundaries whose relevant configuration is pinned from
  intent through evidence, plus situated, non-authoritative candidate knowledge;
- Evidence Gateway schema and measurement-conformity validation, evidence
  qualification, and receipt generation;
- explicit governance decisions and impact records;
- ordered, event-identified impact analysis for continuous change streams,
  including affected bindings, exact CKC versions, traversed Registry
  relations, retained assemblies, and situated CEEs;
- authorized append of complete successor CKCs as inactive lineage versions,
  followed by separate active-pointer transitions for future resolutions and
  separately authorized reactivation of an eligible retained CKC;
- a connected lineage trace across retained CKCs, source versions,
  materializations, executions, evidence, decisions, and lifecycle records,
  with historical preservation;
- episodic evidence records and governed transition of accepted precedents into
  semantic or procedural CKC commitments;
- a standalone pre-institutional capability proposal with only `candidate` and
  `submitted` states, general supporting-record references, identity-free
  directional proposed relations to existing capabilities, and an observed,
  prospective, or mixed continuity justification; supporting references retain
  repository, locator, version, and provenance metadata;
- institutional capability lifecycle states that exclude those
  pre-institutional proposal states;
- governed formation from a submitted proposal to exactly one new capability
  with approved metadata and proposal-traceable capability relations, plus one
  complete immutable initial CKC v1, without implicit activation;
- a subsequent initial activation that publishes the already formed CKC for
  future resolutions through a separately identifiable record;
- schema, artifact, profile, and cross-artifact conformance validation.

YAML reference artifacts remain the source of truth for the worked trace.
Runtime persistence uses local append-only YAML records.

The OAuth fixture also records the pre-resolution identity-policy change from
v7 to v8. Its Registry history links `CHG-IDENTITY-POLICY-008` to
`BIND-IDENTITY-POLICY`, `IMP-IAM-008`, the affected `CAP-IAM` relation path,
`DEC-IAM-008`, `DELTA-IAM-007-008`, inactive append `APPEND-IAM-008`, and
`ACT-IAM-008`. The representative
historical assembly `ASM-IAM-HIST-007` remains linked to `CKC-IAM v7`; the
later OAuth assembly consumes the activated v8 contract.

## Executable differentiators

The companion is more than a collection of example YAML files. Its tests make
several architectural boundaries from the paper executable:

- **authority without micromanagement**: admission grants a bounded mandate,
  while conformance rejects step-wise Registry control of CEE execution;
- **autonomy without opacity**: a CEE may keep local working state private,
  but selected evidence must retain contract, execution, and producer lineage;
- **access without copying**: governed access handles can materialize an
  assembly without moving source payloads or changing source authority;
- **event-driven re-resolution**: the mandate is reused until intent, coverage,
  authority, freshness, risk, or assurance invalidates it;
- **learning without self-promotion**: candidate knowledge can affect canonical
  state only through Evidence Gateway qualification and governance.
- **evolution without reconstruction patches**: adjudication authorizes a
  complete immutable successor CKC and an explanatory delta; append adds it to
  the lineage without moving the active pointer, and a separate activation can
  then make that exact appended version current for future resolutions.
- **reactivation without lineage rewriting**: an eligible retained CKC can be
  selected again only through a new approved activation decision, while other
  capability pointers remain unchanged.
- **formation without automatic discovery**: the implementation accepts a
  submitted proposal with authorized supporting records and a declared
  institutional decision, forms the identity and initial CKC, and activates
  them separately; it neither requires a pattern signal nor infers that the
  proposal is valuable or institutionally correct.

## Requirements

- Python 3.11 or later;
- Poetry 2.x;
- access to the companion `specification/` directory, either as a sibling
  checkout or through explicit configuration.

## Quick start

Run the following commands from this directory:

```console
poetry install
poetry run icla validate-schemas
poetry run icla run-trace oauth-042
poetry run icla run-trace auth-evolution-formation
poetry run pytest
```

The conformance commands should report:

```text
Validated 9 schema(s)
Validated 8 artifact(s); ICLA-Governed trace conformance passed; ICLA-11 pre-institutional proposal boundaries passed
Validated 6 artifact(s); ICLA-Evolving trace conformance passed; governed capability formation and separate initial activation are represented; proposal-generation or discovery effectiveness and institutional judgment were not assessed
```

For the complete development verification:

```console
poetry check
poetry run ruff check src tests
poetry run pytest --cov=icla --cov-report=term
poetry build
```

## Command-line interface

```console
poetry run icla schemas
poetry run icla validate path/to/artifact.yaml
poetry run icla validate path/to/artifact-directory
poetry run icla run-trace oauth-042
poetry run icla run-trace auth-evolution-formation
poetry run icla run-trace oauth-042 --trace-dir ../specification/reference-traces/oauth-042
```

The commands have distinct responsibilities:

- `schemas` lists the nine available contracts;
- `validate-schemas` validates the schema documents themselves;
- `validate` validates one artifact or all artifacts in a directory;
- `run-trace` validates cross-artifact identity, version, formation, activation,
  and lineage continuity. Profile `auto` selects `ICLA-Evolving` for a positive
  formation trace and `ICLA-Governed` otherwise; `--profile` can select an
  explicit cumulative profile.

`run-trace` validates retained artifacts; it does not execute institutional
transitions. The end-to-end pytest scenarios replay both paths. OAuth runs
resolution, Evidence Gateway qualification, governance persistence, inactive
successor append, separate activation, historical-snapshot checks, and lineage.
The formation replay consumes the published submitted proposal and decision,
creates the inactive identity and CKC v1 state, performs initial activation,
and matches both published successor snapshots exactly.

## Specification location

When running from the repository, the implementation discovers
`../specification/` automatically.

Use the global `--specification-dir` option before the subcommand to select a
different specification checkout:

```console
poetry run icla --specification-dir /path/to/specification run-trace oauth-042
```

Alternatively, set `ICLA_SPECIFICATION_DIR` to the directory that contains
`schemas/` and `reference-traces/`. This is required when the Python package is
installed outside the companion repository layout.

## Repository layout

```text
reference-implementation/
├── src/icla/
│   ├── api/              Public facade and technology-neutral contracts
│   ├── models/           Specification-aligned information model
│   ├── policies/         Explicit resolution and evaluation rules
│   ├── repositories/     Persistence boundaries
│   ├── services/         Architectural operations and transitions
│   ├── specification/    Schema and conformance integration
│   └── storage/          Local immutable and append-only YAML storage
├── tests/
│   ├── conformance/      ICLA invariant and profile checks
│   ├── traces/           Executable OAuth 2.1 reference trace
│   └── unit/             Service, policy, lineage, and storage checks
├── ARCHITECTURE.md
└── pyproject.toml

../specification/
├── schemas/
└── reference-traces/oauth-042/
```

## Design guarantees

- CKC versions, assemblies, evidence, decisions, successor- and formation-append
  receipts, activations, and lineage records are append-only.
- Adjudication, successor append or capability formation, and activation are
  separate operations.
- Historical assemblies retain their exact CKC versions.
- Evidence submissions do not contain receipts; the Evidence Gateway produces
  and persists them during qualification.
- CEE-produced knowledge retains its execution and producer identity and
  cannot become institutional knowledge without qualification and governance.
- CEE reasoning, working memory, local stores, and intermediate artifacts are
  not disclosed unless selected by the evidence contract.
- Re-resolution is event-driven; it is not required for each local CEE step.
- The `RequiredCovered` trace retains its applied assessment method and the
  applicable validator, model, or review-policy identifier and version.
- Resolution retains the applicable matcher identifier/version and states
  whether confidence is qualitative or quantitative; the reference matcher's
  ranking is explicitly not calibrated as probability.
- Resolution uses the paper's `admitted`, `rejected`, and `escalated` outcome
  vocabulary. An admitted outcome requires a nonempty exact active-CKC map;
  rejected and escalated outcomes may retain an empty selection and cannot be
  assembled by the reference service.
- The `ConflictsResolved` trace retains each applicable conflict, its
  assembly-compatible outcome, and the governing policy identifier and version;
  unresolved conflicts cannot produce an authoritative assembly.
- Governed and non-standard measurements remain separate.
- Schema conformity is reported independently from evidence qualification and
  does not establish substantive correctness or evidential sufficiency.
- Evidence provenance conditionally retains any versioned transformation used
  to construct the submitted report. This makes the transformation auditable;
  it does not establish semantic fidelity or substantive correctness.
- Materializations cannot silently become canonical CKCs.
- Successor append requires the latest appended CKC as predecessor; a stale
  predecessor is rejected without branching or activating the candidate.
- Any retained eligible CKC can become current only through a new approved
  activation decision. The resulting snapshot changes only the target
  capability's active pointer; other capability entries remain unchanged.
- Impact analysis scopes review without directly mutating, invalidating, or
  blocking canonical state.
- OAuth's candidate proposal never assigns identity; only the separate
  submitted-proposal trace crosses the governed formation boundary.
- Formation creates an `approved` capability without an active pointer and
  records only the capability relations approved from its proposal; only a later
  initial activation makes it resolution-eligible as `active` and publishes CKC v1.
- Architecture decisions and validation failures carry machine-readable
  rationale.

Crystallization belongs to the complete ICLA model. OAuth retains
`PROP-AUTH-EVOL-01` in `candidate` state because one execution does not establish
recurrence under that trace's history-driven criteria. A separate constructed
trace represents the same responsibility after multiple retained records
support submission. The proposal schema also admits unresolved intents,
strategic decisions, process-analysis records, onboarding records, or other
authorized retained references; observed frequency is not universally
required. Its authorized decision assigns `CAP-AUTH-EVOL`, records the
approved capability metadata and Registry relations, appends complete
`CKC-AUTH-EVOL v1`, preserves formation provenance, and leaves the capability
not resolution-eligible until `ACT-AUTH-EVOL-001`.

This supports implementation-conformance claims for the exercised governed
capability-formation path. It does **not** validate automatic pattern discovery,
recurrence-detection quality, capability-boundary quality, ownership, value,
overlap resolution, or organizational effectiveness. Those remain inputs to or
judgments within governance, not deterministic conclusions of the reference
implementation.

## Non-goals

This demonstrator does not provide production authentication, distributed
transactions, a database, REST or MCP transports, operational observability,
automatic capability discovery, or a human workflow system. Those concerns can be implemented behind the
existing service and repository boundaries without changing the demonstrated
ICLA semantics.

## License

The Python reference implementation is licensed under the [MIT License](LICENSE).
The schemas, documentation, and reference traces are licensed under Creative
Commons Attribution 4.0 International; the reviewer package includes that
license at its root.
