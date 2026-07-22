# ICLA Reference Implementation

Deterministic Python demonstrator for **Institutional Capability Lineages
(ICLA)**, a registry-centered reference architecture for governed and evolving
AI.

This package provides an inspectable execution model for the companion ICLA
specification. It demonstrates how stable capability identity, versioned
Capability Knowledge Contracts (CKCs), contextual assembly, evidence,
governance, activation, and lineage fit together without requiring a database,
LLM, MCP server, or cloud infrastructure.

The project is an architectural reference implementation, not a production
platform.

## Relationship to the ICLA artifacts

- [Paper overview](../README.md) — concepts, invariants, lifecycle, and
  evaluation claims.
- [Reference schemas](../specification/schemas/README.md) — eight JSON Schema
  Draft 2020-12 contracts.
- [OAuth 2.1 reference trace](../specification/reference-traces/oauth-042/README.md)
  — seven linked artifacts corresponding to the paper's worked example.
- [Implementation architecture](ARCHITECTURE.md) — direct mapping from the
  paper and specification to Python modules and services.

The paper defines the architecture. The sibling `../specification/` directory
defines the reference artifact contracts. This package makes their principal
behaviors executable and testable.

## Implemented scope

The implementation includes:

- Registry navigation and filtering by metadata, lifecycle, policy, and
  conditions;
- overlapping semantic, procedural, and episodic knowledge-role annotations
  without imposing storage partitions;
- intent resolution, relation traversal, constraint checking, and admission;
- immutable contextual assembly with an execution-scoped operational mandate
  and exact CKC, source, policy, evaluation, and transformation versions;
- bundle, payload, workspace, and governed-access-handle materialization;
- explicit CEE consumption of authorized assemblies and production of
  situated, non-authoritative candidate knowledge;
- Evidence Gateway validation, metric qualification, and receipt generation;
- explicit governance decisions and impact records;
- authorized CKC active-pointer transitions for future resolutions;
- connected institutional lineage and historical preservation;
- episodic evidence records and governed transition of accepted precedents into
  semantic or procedural CKC commitments;
- recurrence-based capability proposals without automatic promotion;
- schema, artifact, profile, and cross-artifact conformance validation.

YAML reference artifacts remain the source of truth for the worked trace.
Runtime persistence uses local append-only YAML records.

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
poetry run pytest
```

The conformance commands should report:

```text
Validated 8 schema(s)
Validated 7 artifact(s); ICLA-Evolving conformance passed
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
poetry run icla run-trace oauth-042 --trace-dir ../specification/reference-traces/oauth-042
```

The commands have distinct responsibilities:

- `schemas` lists the eight available contracts;
- `validate-schemas` validates the schema documents themselves;
- `validate` validates one artifact or all artifacts in a directory;
- `run-trace` validates the complete trace and applies the cumulative
  `ICLA-Evolving` profile, including cross-artifact identity and version
  continuity.

`run-trace` does not execute institutional transitions. The end-to-end pytest
scenario additionally runs resolution, Evidence Gateway qualification,
governance persistence, successor activation, historical snapshot checks, and
connected-lineage verification. The Gateway generates `RCPT-OAUTH-042`; the
test consumes, rather than synthesizes, the declared governance decision,
activation identifier, and successor CKC.

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

- CKC versions, assemblies, evidence, decisions, activations, and lineage
  records are append-only.
- Approval and activation are separate operations.
- Historical assemblies retain their exact CKC versions.
- Evidence submissions do not contain receipts; the Evidence Gateway produces
  and persists them during qualification.
- CEE-produced knowledge retains its execution and producer identity and
  cannot become institutional knowledge without qualification and governance.
- CEE reasoning, working memory, local stores, and intermediate artifacts are
  not disclosed unless selected by the evidence contract.
- Re-resolution is event-driven; it is not required for each local CEE step.
- Governed and non-standard measurements remain separate.
- Materializations cannot silently become canonical CKCs.
- Capability crystallization creates proposals, never institutional identity.
- Architecture decisions and validation failures carry machine-readable
  rationale.

The crystallization service intentionally implements recurrence-based proposal
generation only. Institutional promotion remains an external, governed review
process.

## Non-goals

This demonstrator does not provide production authentication, distributed
transactions, a database, REST or MCP transports, operational observability,
or a human workflow system. Those concerns can be implemented behind the
existing service and repository boundaries without changing the demonstrated
ICLA semantics.

## License

The Python reference implementation is licensed under the [MIT License](LICENSE).
The paper, schemas, documentation, and reference traces are licensed under
[Creative Commons Attribution 4.0 International](../README.md#license).
