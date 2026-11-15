"""Route metrics for paper §2 (Equations 1–2), §5.2 and §7.4."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from assurance import PairedRoutes, RouteOutcome


@dataclass(frozen=True)
class Rate:
    numerator: int
    denominator: int

    @property
    def value(self) -> float | None:
        """An empty population yields an undefined rate."""
        return self.numerator / self.denominator if self.denominator else None


@dataclass(frozen=True)
class RouteMetrics:
    discoverability: Rate
    mean_evidence_coverage: float | None
    unsupported_return_rate: Rate


@dataclass(frozen=True)
class RouteComparison:
    before: RouteMetrics
    after: RouteMetrics
    positive_regression: Rate

    @property
    def unsupported_return_increase(self) -> float | None:
        before = self.before.unsupported_return_rate.value
        after = self.after.unsupported_return_rate.value
        return after - before if before is not None and after is not None else None


def evidence_coverage(outcome: RouteOutcome) -> float | None:
    """EC_B(q). Take the best covered sufficient set, including its context."""
    reached = outcome.trace.reached_evidence
    return max(
        (len(required & reached) / len(required) for required in outcome.query.sufficient_sets),
        default=None,
    )


def score_routes(outcomes: tuple[RouteOutcome, ...]) -> RouteMetrics:
    """Compute D_B, mean EC_B and FPR_B over their respective query subsets."""
    positives = [row for row in outcomes if row.query.sufficient_sets]
    negatives = [row for row in outcomes if not row.query.sufficient_sets]
    coverage = [value for row in positives if (value := evidence_coverage(row)) is not None]
    return RouteMetrics(
        discoverability=Rate(sum(row.complete_discovery for row in positives), len(positives)),
        mean_evidence_coverage=mean(coverage) if coverage else None,
        unsupported_return_rate=Rate(
            sum(row.trace.unsupported_return for row in negatives), len(negatives)
        ),
    )


def compare_routes(routes: PairedRoutes) -> RouteComparison:
    """Compute RegressionRate against the baseline's complete discoveries."""
    before = {row.query.id: row for row in routes.before}
    after = {row.query.id: row for row in routes.after}
    if (len(before) != len(routes.before) or len(after) != len(routes.after)
            or before.keys() != after.keys()
            or any(row.query != after[key].query for key, row in before.items())):
        raise ValueError("Paired routes require identical queries and evidence annotations.")

    previously_complete = [key for key, row in before.items() if row.complete_discovery]
    lost = sum(not after[key].complete_discovery for key in previously_complete)
    return RouteComparison(
        score_routes(routes.before), score_routes(routes.after),
        Rate(lost, len(previously_complete)),
    )
