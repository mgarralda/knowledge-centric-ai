"""Check the manuscript fixture and its regression and budget controls."""

from dataclasses import replace
import unittest

from assurance import AssurancePipeline, Query, QuerySplits, RouteOutcome, RouteTrace, Status
from demo_tls import (
    CONTROL_EVIDENCE, LIMIT, OPERATIONS, ROOT, TLS_EVIDENCE, TRANSPORT,
    CONFIG, SPLITS, FixtureAssurance, LexicalNavigator, build_fixture, fixture_invariants, repair_root, run_fixture,
)

from metrics import evidence_coverage, score_routes


class TLSExampleTest(unittest.TestCase):
    def test_paper_route_and_held_out_evidence(self) -> None:
        report = run_fixture()
        self.assertEqual(report.qualification.status, Status.PASS)
        self.assertEqual(len(report.attempts), 1)
        self.assertTrue(report.attempts[0].accepted)
        diagnostic, = report.attempts[0].targets
        probe, = diagnostic.replays
        self.assertEqual(probe.budget, report.budget)
        self.assertEqual(probe.policy_id, report.policy_id)
        self.assertFalse(report.repair.before[0].complete_discovery)
        self.assertTrue(probe.outcome.complete_discovery)
        self.assertEqual(report.gate_scores.before.discoverability.value, 0)
        self.assertEqual(report.gate_scores.after.discoverability.value, 1)
        self.assertEqual(report.test_scores.after.unsupported_return_rate.value, 0)
        held_out = report.test.after[0].trace
        self.assertEqual(held_out.visited_nodes, (ROOT, OPERATIONS, TRANSPORT))
        self.assertEqual(held_out.reached_evidence, TLS_EVIDENCE)
        self.assertEqual(report.attempts[0].routes[1].trace.reached_evidence, CONTROL_EVIDENCE)

    def test_regressive_edit_is_rejected(self) -> None:
        report = run_fixture(try_regressive_control=True)
        rejected, accepted = report.attempts
        self.assertEqual(rejected.progress.status, Status.PASS)
        self.assertEqual(rejected.regression.status, Status.FAIL)
        self.assertEqual(rejected.regression_scores[0].positive_regression.value, 1)
        self.assertTrue(accepted.accepted)
        self.assertEqual(accepted.base_id, report.initial_id)

    def test_budget_failure_does_not_edit_repository(self) -> None:
        healthy = repair_root(build_fixture(), preserve_security=True)
        report = run_fixture(replace(LIMIT, nodes=2), initial=healthy)
        self.assertFalse(report.attempts)
        self.assertEqual(report.final, healthy)
        self.assertEqual(report.qualification.status, Status.FAIL)
        diagnosis, = report.diagnostics
        self.assertEqual(diagnosis.label, "budget insufficiency")
        probe, = diagnosis.replays
        self.assertEqual(probe.snapshot_id, report.initial_id)
        self.assertEqual(probe.policy_id, report.policy_id)
        self.assertTrue(probe.outcome.complete_discovery)

    def test_mixed_failure_requires_both_interventions(self) -> None:
        initial = build_fixture()
        report = run_fixture(replace(LIMIT, nodes=2), initial=initial)
        self.assertEqual(report.final, initial)
        self.assertFalse(report.attempts)
        diagnosis, = report.diagnostics
        self.assertEqual(diagnosis.label, "mixed cue and budget failure")
        self.assertEqual(
            [probe.outcome.complete_discovery for probe in diagnosis.replays],
            [False, False, True],
        )
        self.assertFalse(report.repair.before[0].complete_discovery)

    def test_navigator_cannot_score_an_over_budget_trace(self) -> None:
        class Overrun(LexicalNavigator):
            def navigate(self, snapshot, question, budget) -> RouteTrace:
                return RouteTrace((), TLS_EVIDENCE, replace(budget, nodes=budget.nodes + 1))

        navigator = Overrun()
        operations = FixtureAssurance(navigator, LIMIT, try_regressive_control=False)
        with self.assertRaisesRegex(ValueError, "exceeds the budget"):
            AssurancePipeline(navigator, operations).run(build_fixture(), SPLITS, LIMIT, CONFIG)

    def test_same_question_with_a_different_id_cannot_cross_splits(self) -> None:
        first = Query("r", "TLS 1.3", (TLS_EVIDENCE,))
        duplicate = replace(first, id="g", text=" tls   1.3 ")
        with self.assertRaisesRegex(ValueError, "text must not repeat"):
            QuerySplits((first,), (duplicate,), ())


class FixtureContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = build_fixture()

    def edit_entries(self, node_id, edit):
        return replace(self.snapshot, indexes=tuple(
            replace(index, entries=edit(index.entries)) if index.node_id == node_id else index
            for index in self.snapshot.indexes
        ))

    def test_required_evidence_must_be_reachable(self) -> None:
        result = fixture_invariants(self.edit_entries(OPERATIONS, lambda entries: ()))
        self.assertEqual(result.status, Status.FAIL)
        self.assertIn("No root route", result.detail)

    def test_hierarchy_rejects_root_to_grandchild_link(self) -> None:
        def skip_directory(entries):
            return (*entries, replace(entries[-1], target_id=TRANSPORT, cues=()))

        result = fixture_invariants(self.edit_entries(ROOT, skip_directory))
        self.assertEqual(result.status, Status.FAIL)
        self.assertIn("immediate child", result.detail)

    def test_resolving_evidence_id_does_not_make_cue_supported(self) -> None:
        def change_cue(entries):
            first, *others = entries
            unsupported = replace(first.cues[0], text="TLS certificate latency limit")
            return (replace(first, cues=(unsupported,)), *others)

        result = fixture_invariants(self.edit_entries(ROOT, change_cue))
        self.assertEqual(result.status, Status.FAIL)
        self.assertIn("Unsupported cue", result.detail)

    def test_retrieved_candidate_does_not_increase_fpr(self) -> None:
        query = Query("negative", "TLS certificate review latency", ())
        trace = LexicalNavigator().navigate(self.snapshot, query.text, LIMIT)
        self.assertEqual(trace.reached_evidence, CONTROL_EVIDENCE)
        self.assertEqual(score_routes((RouteOutcome(query, trace),)).unsupported_return_rate.value, 0)
        asserted = replace(trace, unsupported_return=True)
        self.assertEqual(score_routes((RouteOutcome(query, asserted),)).unsupported_return_rate.value, 1)

    def test_evidence_alternatives_require_their_own_context(self) -> None:
        query = Query("positive", "TLS constraint", (
            TLS_EVIDENCE, frozenset({"alternate", "alternate-context"}),
        ))
        trace = RouteTrace((), frozenset({"E-17", "alternate-context"}), LIMIT)
        partial = RouteOutcome(query, trace)
        self.assertFalse(partial.complete_discovery)
        self.assertEqual(evidence_coverage(partial), 0.5)

        complete = RouteOutcome(query, replace(trace, reached_evidence=query.sufficient_sets[1]))
        self.assertTrue(complete.complete_discovery)
        self.assertEqual(evidence_coverage(complete), 1.0)


if __name__ == "__main__":
    unittest.main()
