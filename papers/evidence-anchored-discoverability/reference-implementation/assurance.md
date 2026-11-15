# Evidence-anchored assurance and evaluation

Typed algorithmic scaffold for Algorithm 2 (§5.2). The assurance loop audits a
candidate repository, repairs attributable repository defects, and qualifies
a frozen version. The research evaluation (§7) compares frozen artifacts and
reports the outcomes on held-out queries.

## Interfaces

| Input | Role |
| --- | --- |
| Initial snapshot | Frozen tree, indexes, source versions, and evidence links. |
| Evidence contract | Independently annotated sufficient evidence sets per query. Any complete alternative suffices, including required context. |
| Repair, gate, and test queries | Disjoint sets for diagnosis and repair, one-time qualification, and final evaluation, respectively. |
| Navigation policy and budget | Fixed for paired runs. Record the policy configuration and resource consumption in each route trace. |
| Repair configuration | Attempt cap, preregistered defect measures and thresholds, and regression tolerance. |

See [`AssurancePipeline.run()`](assurance.py) for the control flow and the `Navigator` and `AssuranceOperations` protocols for the replaceable policies.

The [metrics mapping](metrics.md) ties the route scores and thresholds used
by the pipeline to the paper's equations and notation.

## Diagnostic evidence

The TLS fixture retains counterfactual routes as `DiagnosticReplay` records.
A cue-only replay uses the original policy and budget. A budget-only replay
uses the original snapshot and policy. If only a combined replay succeeds,
the fixture reports a mixed attribution and declines repair. These probes
support attribution on repair queries. Qualification and final measurement
continue to use the declared policy and budget.

## Decision rules

- **Attribute before editing.** Keep multi-label diagnoses and their
  supporting traces. A missing cue and sibling ambiguity can coexist.
  Record policy, budget, downstream reasoning, and unresolved failures
  separately from repository repair targets. Where appropriate, replay a
  minimal cue change under the same policy and budget to test attribution.
- **Accept selectively.** Require invariant preservation and strict progress
  on at least one targeted defect measure, with no worsening of any other
  targeted measure. On the repair split, bound positive-query regression and
  increases in negative-query unsupported returns against both the initial
  artifact and the current accepted state. Log rejected
  candidates with their checks and leave the accepted state intact.
- **Qualify once.** On the frozen candidate, apply the residual-defect,
  hard-invariant, and gate-split checks from §5.2. Require the final complete
  discovery rate to meet the declared threshold and keep positive regression
  and negative unsupported returns within the declared tolerance. Compute
  positive regression over previously successful answerable queries. Report
  zero denominators as not applicable and required empty gate subsets as
  unevaluable.
- **Evaluate separately.** Follow §7 for benchmark splits, baselines, and
  ablations. Report artifact conformance, complete and partial discovery,
  negative-query behavior, failure localization, navigation efficiency, and
  lifecycle cost separately. The main controlled-repair contrast compares
  variants E and D on the locked test set. The paired initial/final traces in the report are one input to that evaluation.
