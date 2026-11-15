"""Deterministic adaptation of the TLS 1.3 worked example (paper §4.4).

Fixture-specific adapters exercise Algorithms 1 and 2. Run this file from
any directory with Python 3.10+. No model or external services are needed.
"""

from __future__ import annotations

from dataclasses import replace
import re

from assurance import (
    AssurancePipeline, AssuranceReport, Attempt, Budget, Check, Diagnosis, Diagnostic, DiagnosticReplay,
    PairedRoutes, Query, QuerySplits, RepairConfig, RouteOutcome, RouteTrace,
    Status,
)
from contracts import Cue, Directory, Document, EvidenceUnit, Index, IndexEntry, RepositorySnapshot, SourceRef
from rsic import ComposedDirectory, ExtractedDocument, RSICBuilder, SubtreeDescription

ROOT = "root"
SECURITY = "security"
OPERATIONS = "operations"
TRANSPORT = "transport_compatibility.md"
CONTROLS = "encryption_controls.md"
TLS_EVIDENCE = frozenset({"E-17", "E-17-context"})
CONTROL_EVIDENCE = frozenset({"E-18"})

# The example source text and its context are pinned by the fixture version.
SOURCES = {
    TRANSPORT: {
        "E-17": "Service A negotiates TLS 1.3 only when the flag is enabled; Relay B supports TLS 1.2 only.",
        "E-17-context": "The feature flag controls whether Service A negotiates TLS 1.3.",
    },
    CONTROLS: {"E-18": "TLS encryption controls require an annual certificate review."},
}
TLS_CUE = Cue("compatibility", "TLS 1.3 compatibility restrictions for Service A and Relay B", TLS_EVIDENCE)
SECURITY_CUE = Cue("topic", "TLS encryption controls and certificate review", CONTROL_EVIDENCE)
OPERATIONS_CUE = Cue("topic", "Feature flag configuration", frozenset({"E-17-context"}))
# These exact cues were checked against SOURCES for this fixed fixture.
# This allowlist makes the support check reproducible without a semantic judge.
SUPPORTED_CUES = {
    SECURITY: (SECURITY_CUE,),
    CONTROLS: (SECURITY_CUE,),
    OPERATIONS: (OPERATIONS_CUE, TLS_CUE),
    TRANSPORT: (TLS_CUE,),
}
MISSING_CUE = Diagnostic("cue omission", ROOT, "Operations lacks the supported TLS 1.3 cue.")
LIMIT = Budget(3, 0, 0, 0)
CONFIG = RepairConfig(2, 1.0, 0.0, ("missing_tls_cue",))

SPLITS = QuerySplits(
    repair=(
        Query("r-tls", "TLS 1.3 compatibility restrictions", (TLS_EVIDENCE,)),
        Query("r-control", "Encryption controls", (CONTROL_EVIDENCE,)),
        Query("r-negative", "Quantum telemetry", ()),
    ),
    gate=(
        Query("g-tls", "Service A TLS restrictions", (TLS_EVIDENCE,)),
        Query("g-negative", "Inventory limits", ()),
    ),
    test=(
        Query("t-tls", "Can Relay B accept Service A traffic?", (TLS_EVIDENCE,)),
        Query("t-negative", "Database retention", ()),
    ),
)


def root_index(snapshot: RepositorySnapshot) -> Index:
    return next(index for index in snapshot.indexes if index.node_id == ROOT)


def fixture_invariants(snapshot: RepositorySnapshot) -> Check:
    """Check the fixture's hierarchy-only navigation and evidence contract."""
    children: dict[str, frozenset[str]] = {}
    documents: dict[str, SourceRef] = {}

    def collect(node: Directory | Document) -> None:
        if node.id in children or node.id in documents:
            raise ValueError(f"Duplicate tree node: {node.id}")
        if isinstance(node, Document):
            documents[node.id] = node.source
            return
        children[node.id] = frozenset(child.id for child in node.children)
        for child in node.children:
            collect(child)

    try:
        collect(snapshot.tree)
    except ValueError as error:
        return Check(Status.FAIL, str(error))

    indexes = {index.node_id: index for index in snapshot.indexes}
    if len(indexes) != len(snapshot.indexes) or indexes.keys() != children.keys():
        return Check(Status.FAIL, "Every directory must have exactly one index.")

    evidence = {unit.id: unit for unit in snapshot.evidence}
    required = TLS_EVIDENCE | CONTROL_EVIDENCE
    if len(evidence) != len(snapshot.evidence) or not required <= evidence.keys():
        return Check(Status.FAIL, "Missing or duplicate fixture evidence.")
    for unit in evidence.values():
        if (documents.get(unit.source.document_id) != unit.source
                or unit.source.version != "v1"
                or unit.id != unit.locator
                or unit.locator not in SOURCES.get(unit.source.document_id, {})
                or not unit.context_ids <= evidence.keys()):
            return Check(Status.FAIL, f"Invalid source or context reference: {unit.id}")
    if not {"E-17-context"} <= evidence["E-17"].context_ids:
        return Check(Status.FAIL, "E-17 must retain its required context link.")

    for index in indexes.values():
        for entry in index.entries:
            if entry.target_id not in children[index.node_id]:
                return Check(Status.FAIL, f"Link to {entry.target_id} must target an immediate child.")
            for cue in entry.cues:
                if (cue not in SUPPORTED_CUES.get(entry.target_id, ())
                        or not cue.evidence_ids <= evidence.keys()):
                    return Check(Status.FAIL, f"Unsupported cue on entry {entry.target_id}: {cue.text}")

    reachable = {snapshot.tree.id}
    pending = [snapshot.tree.id]
    while pending:
        index = indexes.get(pending.pop())
        if index is None:
            continue
        for entry in index.entries:
            if entry.target_id not in reachable:
                reachable.add(entry.target_id)
                pending.append(entry.target_id)

    for evidence_id in sorted(required):
        if evidence[evidence_id].source.document_id not in reachable:
            return Check(Status.FAIL, f"No root route to required evidence {evidence_id}.")
    return Check(Status.PASS, "Fixture topology, source, context, and cue support checks.")


class FixtureBuilder:
    """Compose the declared hierarchy bottom-up, seeding the root cue omission."""

    def extract(self, document: Document, source_snapshot_id: str) -> ExtractedDocument:
        units = tuple(
            EvidenceUnit(key, document.source, key,
                         frozenset({"E-17-context"}) if key == "E-17" else frozenset())
            for key in SOURCES[document.id]
        )
        cue = TLS_CUE if document.id == TRANSPORT else SECURITY_CUE
        return ExtractedDocument(
            SubtreeDescription(document.id, (cue,), frozenset(unit.id for unit in units)), units
        )

    def compose(self, directory: Directory, children: tuple[SubtreeDescription, ...]) -> ComposedDirectory:
        cues = tuple(cue for child in children for cue in child.cues)
        entries = tuple(
            IndexEntry(child.node_id, (OPERATIONS_CUE,)
                       if child.node_id == OPERATIONS else child.cues)
            for child in children
        )
        return ComposedDirectory(
            Index(directory.id, entries),
            SubtreeDescription(directory.id, cues, frozenset().union(
                *(child.evidence_ids for child in children)
            )),
        )

    def check_artifact_contract(self, candidate: RepositorySnapshot) -> None:
        if fixture_invariants(candidate).status is not Status.PASS:
            raise ValueError("Invalid TLS fixture.")


def build_fixture() -> RepositorySnapshot:
    def branch(id: str, filename: str) -> Directory:
        return Directory(id, (Document(filename, SourceRef(filename, "v1")),))

    tree = Directory(ROOT, (branch(SECURITY, CONTROLS), branch(OPERATIONS, TRANSPORT)))
    return RSICBuilder(FixtureBuilder()).build(tree, snapshot_id="initial", source_snapshot_id="fixture-v1")


def words(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.casefold()))


class LexicalNavigator:
    """Greedy parent-to-child traversal with stable ties and a node budget."""

    id = "fixture-lexical-v1"

    def navigate(self, snapshot: RepositorySnapshot, question: str, budget: Budget) -> RouteTrace:
        indexes = {index.node_id: index for index in snapshot.indexes}
        query_tokens = words(question)
        visited: list[str] = []
        node = snapshot.tree.id
        reached: frozenset[str] = frozenset()

        def relevance(entry: IndexEntry) -> int:
            return max((len(query_tokens & words(cue.text)) for cue in entry.cues), default=0)

        while len(visited) < budget.nodes:
            visited.append(node)
            if node not in indexes:
                reached = frozenset(
                    unit.id for unit in snapshot.evidence if unit.source.document_id == node
                )
                break
            entry = max(indexes[node].entries, key=relevance, default=None)
            if entry is None or relevance(entry) == 0:
                break
            node = entry.target_id

        # Traversal retrieves candidates for inspection without asserting support.
        return RouteTrace(tuple(visited), reached, Budget(len(visited), 0, 0, 0))


def repair_root(snapshot: RepositorySnapshot, *, preserve_security: bool) -> RepositorySnapshot:
    entries = tuple(
        replace(entry, cues=entry.cues + (TLS_CUE,)) if entry.target_id == OPERATIONS
        else replace(entry, cues=()) if not preserve_security else entry
        for entry in root_index(snapshot).entries
    )
    return replace(
        snapshot, id="minimal-repair" if preserve_security else "regressive-control",
        indexes=tuple(replace(index, entries=entries) if index.node_id == ROOT else index
                      for index in snapshot.indexes),
    )


class FixtureAssurance:
    """Check the seeded defect through a same-policy, same-budget replay."""

    def __init__(self, navigator: LexicalNavigator, budget: Budget, *, try_regressive_control: bool):
        self.navigator = navigator
        self.budget = budget
        self.try_regressive_control = try_regressive_control

    def audit_invariants(
        self, snapshot: RepositorySnapshot
    ) -> tuple[frozenset[Diagnostic], frozenset[Diagnostic]]:
        if fixture_invariants(snapshot).status is Status.PASS:
            return frozenset(), frozenset()
        return frozenset({Diagnostic("invalid fixture", ROOT, "A structural invariant failed.")}), frozenset()

    def diagnose(self, snapshot: RepositorySnapshot, routes: tuple[RouteOutcome, ...]) -> Diagnosis:
        missed = next((row for row in routes if row.query.id == "r-tls" and not row.complete_discovery), None)
        if missed is None:
            return Diagnosis(frozenset())

        has_cue = any(TLS_CUE in entry.cues for entry in root_index(snapshot).entries
                      if entry.target_id == OPERATIONS)
        repaired = snapshot if has_cue else repair_root(snapshot, preserve_security=True)

        def replay(candidate: RepositorySnapshot, budget: Budget, intervention: str) -> DiagnosticReplay:
            trace = self.navigator.navigate(candidate, missed.query.text, budget)
            if not budget.allows(trace.usage):
                raise ValueError("A diagnostic replay exceeded its declared budget.")
            return DiagnosticReplay(
                intervention, candidate.id, self.navigator.id, budget,
                RouteOutcome(missed.query, trace),
            )

        probes = []
        if not has_cue:
            cue_probe = replay(repaired, self.budget, "Restore the Operations cue")
            if cue_probe.outcome.complete_discovery:
                return Diagnosis(frozenset({replace(MISSING_CUE, replays=(cue_probe,))}))
            probes.append(cue_probe)

        # Isolate budget from the cue intervention. A combined rescue does
        # not establish that budget alone caused the miss.
        expanded = replace(self.budget, nodes=max(self.budget.nodes, LIMIT.nodes))
        if expanded != self.budget:
            budget_probe = replay(snapshot, expanded, "Add node reads on the original index")
            probes.append(budget_probe)
            if budget_probe.outcome.complete_discovery:
                return Diagnosis(frozenset(), frozenset({Diagnostic(
                    "budget insufficiency", ROOT, "Extra reads recover the original route.", tuple(probes)
                )}))

            if not has_cue:
                combined = replay(repaired, expanded, "Restore the cue and add node reads")
                probes.append(combined)
                if combined.outcome.complete_discovery:
                    return Diagnosis(frozenset(), frozenset({Diagnostic(
                        "mixed cue and budget failure", ROOT,
                        "Discovery requires both interventions.", tuple(probes),
                    )}))

        return Diagnosis(frozenset(), frozenset({
            Diagnostic("unresolved", ROOT, "No probe restored discovery.", tuple(probes))
        }))

    def propose(self, snapshot: RepositorySnapshot, targets: frozenset[Diagnostic],
                attempts: tuple[Attempt, ...]) -> RepositorySnapshot | None:
        if not any(target.label == MISSING_CUE.label for target in targets):
            return None
        return repair_root(snapshot, preserve_security=bool(attempts) or not self.try_regressive_control)

    def check_preservation(self, base: RepositorySnapshot, candidate: RepositorySnapshot) -> Check:
        # The fixture allows root-entry cue edits, with known source support.
        if base.tree != candidate.tree or base.evidence != candidate.evidence:
            return Check(Status.FAIL, "The edit violates the fixture contract.")
        return fixture_invariants(candidate)

    def check_progress(self, base: RepositorySnapshot, candidate: RepositorySnapshot,
                       routes: PairedRoutes, targets: frozenset[Diagnostic], config: RepairConfig) -> Check:
        before = next(row for row in routes.before if row.query.id == "r-tls")
        after = next(row for row in routes.after if row.query.id == "r-tls")
        improved = not before.complete_discovery and after.complete_discovery
        return Check(Status.PASS if improved else Status.FAIL, "Target TLS route recovery.")

    def check_hard_invariants(self, snapshot: RepositorySnapshot) -> Check:
        return fixture_invariants(snapshot)


def run_fixture(
    budget: Budget = LIMIT, *, try_regressive_control: bool = False,
    initial: RepositorySnapshot | None = None,
) -> AssuranceReport:
    navigator = LexicalNavigator()
    operations = FixtureAssurance(navigator, budget, try_regressive_control=try_regressive_control)
    snapshot = build_fixture() if initial is None else initial
    return AssurancePipeline(navigator, operations).run(snapshot, SPLITS, budget, CONFIG)


def main() -> None:
    healthy = repair_root(build_fixture(), preserve_security=True)
    for label, budget, control, initial in (
        ("Paper example", LIMIT, False, None),
        ("Regression control", LIMIT, True, None),
        ("Budget control", replace(LIMIT, nodes=2), False, healthy),
        ("Mixed control", replace(LIMIT, nodes=2), False, None),
    ):
        report = run_fixture(budget, try_regressive_control=control, initial=initial)
        print(f"{label} (node budget {budget.nodes})")
        for phase, routes in (("repair", report.repair), ("gate", report.gate), ("test", report.test)):
            for before, after in zip(routes.before, routes.after):
                if before.query.sufficient_sets:
                    print(f"  {phase}/{before.query.id}: {before.trace.visited_nodes} -> {after.trace.visited_nodes}")
                    print(f"    evidence: {sorted(after.trace.reached_evidence)}")
        for attempt in report.attempts:
            labels = ", ".join(sorted(item.label for item in attempt.targets))
            print(f"  {attempt.candidate.id} [{labels}]: accepted={attempt.accepted}")
            print(f"    {attempt.regression.detail}")
        diagnostics = report.diagnostics.union(*(attempt.targets for attempt in report.attempts))
        for diagnosis in sorted(diagnostics, key=lambda item: item.label):
            print(f"  {diagnosis.label}: {diagnosis.detail}")
            for probe in diagnosis.replays:
                print(f"    {probe.intervention} ({probe.snapshot_id}, nodes={probe.budget.nodes}): "
                      f"{probe.outcome.trace.visited_nodes}, "
                      f"complete={probe.outcome.complete_discovery}")
        print(f"  attempts={len(report.attempts)}; qualification={report.qualification.status.value}")


if __name__ == "__main__":
    main()
