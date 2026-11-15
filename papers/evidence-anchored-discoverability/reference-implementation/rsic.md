# RSIC construction

Typed algorithmic scaffold for Algorithm 1 (§5.1). The artifact contract comes
from §4.2–4.3, and the TLS example from §4.4 illustrates what the builder has
to preserve.

## Inputs and outputs

The input is an organizational tree and a frozen source snapshot. An evidence
unit identifies its source, version, and locator and carries any required
context references. A subtree description carries typed cues, the exact
critical fields those cues express, and links to their supporting evidence.
A parent consumes these records when composing its own entries.

The output is a candidate repository snapshot. Its navigation links define
the routes a reader can take. Evidence, context, and provenance dependencies
are also recorded. A dependency becomes navigable only if explicitly exposed
as a navigation link (§6).

See [`RSICBuilder.build()`](rsic.py) for the typed traversal and the `RSICOperations` protocol for extraction, composition, and artifact checks.

## Implementation decisions

- **Source support.** Resolve exact locators and version IDs mechanically.
  Check whether each cue faithfully expresses its evidence, including
  conditions and negation. Text overlap alone establishes neither fidelity
  nor completeness. Keep uncertain semantic checks explicit for the audit.
- **Sibling discrimination.** Compose entries with their neighboring entries
  in view. In the TLS fixture, a branch cue should retain the protocol
  constraint and the condition that makes it applicable, with links to the
  source and required context.
- **Reproducibility.** A first demonstrator can supply fixture-backed evidence
  extraction and composition. If a model is later used, retain its inputs,
  configuration and outputs with the candidate version for replay.
- **Incremental maintenance.** §6 adds dependency-aware review of affected
  nodes and ancestors after source updates. Keep this as an extension to
  the initial full build.

The [assurance algorithm](assurance.md) accepts the resulting snapshot through
the same contract used for a compatible existing index.
