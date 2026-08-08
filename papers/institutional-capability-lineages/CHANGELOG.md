# Changelog

All notable changes to the ICLA paper companion are recorded here.

## Unreleased

### Added

- A standalone capability-proposal schema shared by the OAuth candidate and a
  submitted-proposal formation trace.
- A deterministic governed formation service that assigns one new capability
  identity and appends one complete immutable CKC v1 without activating it.
- Separate initial activation, `before -> formed -> active` Registry snapshots,
  formation-origin lineage, and positive, negative, and no-partial-effect tests.
- A public conformance matrix separating machine-checked formation behavior
  from discovery quality and institutional judgment.

- A machine-checkable pre-resolution `CAP-IAM` impact path for the OAuth
  example, covering the identity-policy change, affected interpretation and
  temporal validity, Registry relation traversal, governance, `CKC-IAM v8`
  activation, and preservation of a historical v7 assembly.
- Bounded operational mandates on contextual assemblies.
- Explicit CEE autonomy over reasoning, working state, local stores, tools,
  coordination, and iteration.
- Contract-selected evidence checkpoints without wholesale working-state
  capture.
- Event-driven re-resolution policy for changes in intent, coverage,
  authority, freshness, risk, or assurance.
- Governed access-handle materialization without source-payload copying.
- Executable lineage edges linking an execution to its CEE, mandate,
  materialization, evidence, and candidate knowledge.
- Decision-linked successor deltas that identify changed CKC commitments,
  rationale, supporting evidence, authorization, and rollback.

### Changed

- Updated the preferred paper citation to the SSRN preprint *Institutional
  Capability Lineages: A Registry-centered Reference Architecture for Governed
  and Evolving AI*, DOI `10.2139/ssrn.7172438`, and removed provisional
  publication fields.
- Aligned the public terminology and evaluation boundary with manuscript v45:
  ICLA denotes the architecture, a capability lineage denotes its modeled
  authority-preserving structure, and a lineage trace denotes a concrete
  retained instantiation. Evidence informs governed change rather than
  changing canonical state directly, and complete crystallization promotion is
  recorded as future companion work.
- Aligned the public methodological description with the paper's iterative DSR
  account: literature synthesis positions, refines, and justifies the artifact
  boundaries; requirement-to-component links express traceability rather than
  a linear derivation; and artificial technical evaluation remains distinct
  from prospective comparison and future organizational validation.
- Extended impact analysis output with affected source bindings, exact CKC
  versions, traversed relations, retained CEEs, and version-aware assembly
  matching, aligned with the paper's expanded Organizational Memory model.
- Updated the OAuth 2.1 reference trace and public architecture diagrams to
  match the paper dated 2026-07-22.
- Strengthened ICLA-3, ICLA-5, ICLA-6, and ICLA-8 conformance checks around
  CEE autonomy, mandate identity, and evidence boundaries.
- Published the current paper and machine-readable citation metadata.
- Aligned the companion assessment scope with the paper's
  two-dimensional evolution model. OAuth remains an unpromoted candidate case;
  a separate trace now exercises the bounded governed capability-formation path.
- Made CLI conformance output state both the profile and assessment scope.
