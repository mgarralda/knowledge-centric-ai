# Metrics and scoring

[`metrics.py`](metrics.py) implements the route metrics defined in §2 and used
in Algorithm 2 (§5.2). Metrics are computed from route outcomes under a fixed
policy and budget. They are reported individually as specified in §7.4.

| Paper notation | Python | Population or denominator |
| --- | --- | --- |
| `A_{π,B}(q)` | `RouteTrace.reached_evidence` | Evidence made available within budget, including any context reached. |
| `G(q)` | `Query.sufficient_sets` | Independently annotated alternatives. Every alternative includes its required context. |
| `D_B`, Eq. 1 | `RouteMetrics.discoverability` | Answerable queries. Count a query once when any alternative is complete. |
| `EC_B(q)` | `evidence_coverage()` | Best fraction covered among the query's nonempty alternatives. Report the mean over answerable queries. |
| `FPR_B`, Eq. 2 | `RouteMetrics.unsupported_return_rate` | Verified negative queries. Count asserted evidence support. Merely inspecting a candidate does not increase the count. |
| `RegressionRate(Pnew, Pold)` | `RouteComparison.positive_regression` | Baseline discoveries that were complete. Count those that become incomplete. |
| `τ_D`, `δ` | `RepairConfig.minimum_discovery_rate`, `regression_tolerance` | Qualification threshold and allowed regression or increase in unsupported returns, respectively. |

`Rate` retains the numerator and denominator. A zero denominator yields
`None`. An empty baseline pass set means no observed positive loss for the
gate, with the rate still undefined. A required empty positive or negative
gate subset makes its criterion unevaluable.

## Where Algorithm 2 uses the scores

- **Repair set.** Check the positive regression and the increase in negative
  unsupported returns against the initial artifact and the last accepted
  candidate. A repair can pass without increasing overall discoverability
  if it fixes its targeted defect and satisfies the other checks.
- **Gate set.** Compare the frozen candidate with the initial artifact.
  Apply the minimum complete-discovery threshold, the regression tolerance,
  residual-defect checks, and hard invariants.
- **Test set.** Compute paired scores on the frozen artifacts for reporting
  after the qualification decision.

Artifact conformance and target-specific progress depend on annotations and
repository checks supplied by the adapters. Navigation cost is recorded per
trace as nodes, tokens, calls and latency. Localization precision, false
alarms on defect-free artifacts, multi-label scores, and the lifecycle cost
of construction, audit, repair and updates belong to the §7 evaluation
protocol. They require additional benchmark annotations or instrumentation.
Artifact-level false alarms and query-level `FPR_B` use different units.
