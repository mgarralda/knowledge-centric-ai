"""Audit, repair and qualification orchestration (paper §5.2, Algorithm 2).

The final paired traces feed the research evaluation in §7. Benchmark
ablations and semantic operations are adapter responsibilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from contracts import RepositorySnapshot
from metrics import RouteComparison, compare_routes


@dataclass(frozen=True)
class Query:
    id: str
    text: str
    # An empty tuple denotes an independently checked negative query.
    # Each positive alternative includes all required context unit IDs.
    sufficient_sets: tuple[frozenset[str], ...]

    def __post_init__(self) -> None:
        if any(not group for group in self.sufficient_sets):
            raise ValueError("A sufficient evidence set must contain at least one unit.")


@dataclass(frozen=True)
class QuerySplits:
    repair: tuple[Query, ...]
    gate: tuple[Query, ...]
    test: tuple[Query, ...]

    def __post_init__(self) -> None:
        ids = [query.id for split in (self.repair, self.gate, self.test) for query in split]
        if len(ids) != len(set(ids)):
            raise ValueError("Query IDs must be unique across and within splits.")
        previous: set[str] = set()
        for split in (self.repair, self.gate, self.test):
            questions = {" ".join(query.text.casefold().split()) for query in split}
            if previous & questions:
                raise ValueError("Query text must not repeat across splits.")
            previous.update(questions)


@dataclass(frozen=True)
class Budget:
    nodes: int
    tokens: int
    calls: int
    seconds: float

    def allows(self, usage: Budget) -> bool:
        """Require every reported usage dimension to be within its limit."""
        return (
            0 <= usage.nodes <= self.nodes
            and 0 <= usage.tokens <= self.tokens
            and 0 <= usage.calls <= self.calls
            and 0 <= usage.seconds <= self.seconds
        )


@dataclass(frozen=True)
class RouteTrace:
    visited_nodes: tuple[str, ...]
    reached_evidence: frozenset[str]
    usage: Budget
    # True only when the policy explicitly presents evidence as support.
    unsupported_return: bool = False


@dataclass(frozen=True)
class RouteOutcome:
    query: Query
    trace: RouteTrace

    @property
    def complete_discovery(self) -> bool:
        return any(required <= self.trace.reached_evidence
                   for required in self.query.sufficient_sets)


@dataclass(frozen=True)
class RepairConfig:
    max_attempts: int
    minimum_discovery_rate: float
    regression_tolerance: float
    target_measures: tuple[str, ...]


@dataclass(frozen=True)
class DiagnosticReplay:
    """Record the intervention and its observed route."""

    intervention: str
    snapshot_id: str
    policy_id: str
    budget: Budget
    outcome: RouteOutcome


@dataclass(frozen=True)
class Diagnostic:
    """One attributed label and its supporting route or invariant detail."""

    label: str
    node_id: str | None
    detail: str
    replays: tuple[DiagnosticReplay, ...] = ()


@dataclass(frozen=True)
class Diagnosis:
    """Only attributable repository defects may enter the repair planner."""

    repairable: frozenset[Diagnostic]
    reported: frozenset[Diagnostic] = frozenset()


class Status(Enum):
    PASS = "pass"
    FAIL = "fail"
    UNEVALUABLE = "unevaluable"
    NOT_RUN = "not_run"


@dataclass(frozen=True)
class Check:
    status: Status
    detail: str


@dataclass(frozen=True)
class Attempt:
    base_id: str
    candidate: RepositorySnapshot
    targets: frozenset[Diagnostic]
    routes: tuple[RouteOutcome, ...]
    invariants: Check
    progress: Check
    regression: Check
    regression_scores: tuple[RouteComparison, ...]

    @property
    def accepted(self) -> bool:
        return all(check.status is Status.PASS
                   for check in (self.invariants, self.progress, self.regression))


@dataclass(frozen=True)
class PairedRoutes:
    before: tuple[RouteOutcome, ...]
    after: tuple[RouteOutcome, ...]


@dataclass(frozen=True)
class AssuranceReport:
    initial_id: str
    final: RepositorySnapshot
    policy_id: str
    budget: Budget
    config: RepairConfig
    qualification: Check
    residual_defects: frozenset[Diagnostic]
    diagnostics: frozenset[Diagnostic]
    attempts: tuple[Attempt, ...]
    repair: PairedRoutes
    gate: PairedRoutes
    test: PairedRoutes
    gate_scores: RouteComparison
    test_scores: RouteComparison


class Navigator(Protocol):
    """One configured policy for all paired runs."""

    id: str

    def navigate(self, snapshot: RepositorySnapshot, question: str, budget: Budget) -> RouteTrace:
        """Return evidence actually made available within budget, without annotations."""
        ...


class AssuranceOperations(Protocol):
    """Variation points for repository-specific checks and repairs."""

    def audit_invariants(
        self, snapshot: RepositorySnapshot
    ) -> tuple[frozenset[Diagnostic], frozenset[Diagnostic]]:
        """Return fatal and repairable invariant violations, respectively."""
        ...

    def diagnose(
        self, snapshot: RepositorySnapshot, routes: tuple[RouteOutcome, ...]
    ) -> Diagnosis:
        """Attribute failures independently, retaining mixed and unresolved cases."""
        ...

    def propose(
        self, snapshot: RepositorySnapshot, targets: frozenset[Diagnostic],
        attempts: tuple[Attempt, ...],
    ) -> RepositorySnapshot | None:
        """Return a new candidate with a distinct ID and unchanged source evidence."""
        ...

    def check_preservation(self, base: RepositorySnapshot, candidate: RepositorySnapshot) -> Check:
        """Check invariant preservation during candidate repair."""
        ...

    def check_progress(
        self,
        base: RepositorySnapshot,
        candidate: RepositorySnapshot,
        routes: PairedRoutes,
        targets: frozenset[Diagnostic],
        config: RepairConfig,
    ) -> Check:
        """Require strict improvement on a target and no worsening on other targets."""
        ...

    def check_hard_invariants(self, snapshot: RepositorySnapshot) -> Check:
        """Check the artifact criteria of the final qualification gate."""
        ...


def _check_route_regression(
    comparisons: tuple[RouteComparison, ...], tolerance: float
) -> Check:
    """Fail on any observed breach, retaining undefined rates in the report."""
    for comparison in comparisons:
        losses = comparison.positive_regression.value
        unsupported = comparison.unsupported_return_increase
        if losses is not None and losses > tolerance:
            return Check(Status.FAIL, "Positive-query regression exceeds tolerance.")
        if unsupported is not None and unsupported > tolerance:
            return Check(Status.FAIL, "Unsupported-return increase exceeds tolerance.")
    return Check(Status.PASS, "No observed regression exceeds tolerance.")


def _qualify(
    residual: frozenset[Diagnostic], invariants: Check, scores: RouteComparison,
    config: RepairConfig,
) -> Check:
    if residual:
        return Check(Status.FAIL, "Residual repository defects remain.")
    if invariants.status is not Status.PASS:
        return invariants
    regression = _check_route_regression((scores,), config.regression_tolerance)
    if regression.status is Status.FAIL:
        return regression
    discoverability = scores.after.discoverability.value
    if discoverability is not None and discoverability < config.minimum_discovery_rate:
        return Check(Status.FAIL, "Complete discovery is below the declared threshold.")
    if discoverability is None or scores.unsupported_return_increase is None:
        return Check(Status.UNEVALUABLE, "A required gate query subset is empty.")
    return Check(Status.PASS, "Artifact and route criteria passed.")


class AssurancePipeline:
    """Run the bounded loop and keep repair, qualification and testing separate."""

    def __init__(self, navigator: Navigator, operations: AssuranceOperations) -> None:
        self.navigator = navigator
        self.operations = operations

    def run(
        self, initial: RepositorySnapshot, splits: QuerySplits,
        budget: Budget, config: RepairConfig,
    ) -> AssuranceReport:
        """Return an inspectable record regardless of qualification outcome."""
        ops = self.operations

        def routes(snapshot: RepositorySnapshot, queries: tuple[Query, ...]) -> tuple[RouteOutcome, ...]:
            outcomes = []
            for query in queries:
                trace = self.navigator.navigate(snapshot, query.text, budget)
                # With aggregate usage alone there is no reliable way to recover
                # the evidence available before an overrun. Reject the trace.
                if not budget.allows(trace.usage):
                    raise ValueError(f"Trace for {query.id!r} exceeds the budget or has invalid usage.")
                outcomes.append(RouteOutcome(query, trace))
            return tuple(outcomes)

        current = initial
        baseline = current_routes = routes(initial, splits.repair)
        fatal, repairable = ops.audit_invariants(initial)
        attempts: list[Attempt] = []

        for _ in range(config.max_attempts):
            if fatal:
                break
            targets = ops.diagnose(current, current_routes).repairable | repairable
            if not targets:
                break
            candidate = ops.propose(current, targets, tuple(attempts))
            if candidate is None:
                break

            if candidate.id == current.id or candidate.id == initial.id or any(
                candidate.id == prior.candidate.id for prior in attempts
            ):
                raise ValueError("A repair must have a fresh candidate ID.")
            if (candidate.source_snapshot_id != initial.source_snapshot_id
                    or candidate.evidence != initial.evidence):
                raise ValueError("A repair must preserve the source snapshot and evidence.")

            # A candidate always gets its own trace, even if later rejected.
            candidate_routes = routes(candidate, splits.repair)
            invariants = ops.check_preservation(current, candidate)
            progress = ops.check_progress(
                current, candidate, PairedRoutes(current_routes, candidate_routes),
                targets, config,
            )
            regression = Check(Status.NOT_RUN, "Preservation or progress did not pass.")
            regression_scores: tuple[RouteComparison, ...] = ()
            if invariants.status is Status.PASS and progress.status is Status.PASS:
                references = (baseline,) if current.id == initial.id else (baseline, current_routes)
                regression_scores = tuple(
                    compare_routes(PairedRoutes(reference, candidate_routes))
                    for reference in references
                )
                regression = _check_route_regression(
                    regression_scores, config.regression_tolerance
                )

            attempt = Attempt(current.id, candidate, targets, candidate_routes,
                              invariants, progress, regression, regression_scores)
            attempts.append(attempt)
            if attempt.accepted:
                current, current_routes = candidate, candidate_routes
                fatal, repairable = ops.audit_invariants(current)

        diagnosis = ops.diagnose(current, current_routes)
        residual = diagnosis.repairable | repairable | fatal

        # Snapshots and configuration are immutable. Only repair queries
        # were visible to diagnosis and repair before reaching this point.
        gate = PairedRoutes(routes(initial, splits.gate), routes(current, splits.gate))
        gate_scores = compare_routes(gate)
        qualification = _qualify(residual, ops.check_hard_invariants(current),
                                 gate_scores, config)
        test = PairedRoutes(routes(initial, splits.test), routes(current, splits.test))
        return AssuranceReport(
            initial.id, current, self.navigator.id, budget, config, qualification,
            residual, diagnosis.reported, tuple(attempts),
            PairedRoutes(baseline, current_routes), gate, test,
            gate_scores, compare_routes(test),
        )
