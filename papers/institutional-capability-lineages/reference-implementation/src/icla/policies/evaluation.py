"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricEvaluation:
    definition_conformity: bool
    threshold_passed: bool | None
    rationale: str


def evaluate_metric(measurement: dict) -> MetricEvaluation:
    required_definition = ("metric_id", "unit", "governed_definition", "threshold")
    missing = [key for key in required_definition if measurement.get(key) in (None, "")]
    declared_conformity = measurement.get("conformity")
    conforming = not missing and declared_conformity not in {False, "non-conforming"}
    if not conforming:
        return MetricEvaluation(
            definition_conformity=False,
            threshold_passed=None,
            rationale=f"metric definition is not conforming; missing={missing}",
        )

    value, threshold = measurement.get("value"), measurement.get("threshold", {})
    if isinstance(threshold, dict) and value is not None:
        operator, expected = threshold.get("operator"), threshold.get("value")
        operations = {
            "<=": lambda: value <= expected,
            "less-than-or-equal": lambda: value <= expected,
            ">=": lambda: value >= expected,
            "greater-than-or-equal": lambda: value >= expected,
            "==": lambda: value == expected,
            "equal": lambda: value == expected,
        }
        if operator in operations and expected is not None:
            result = operations[operator]()
            return MetricEvaluation(True, result, f"{value} {operator} {expected} is {result}")

    declared_result = str(measurement.get("result", "")).casefold()
    if declared_result in {"pass", "passed", "success"}:
        return MetricEvaluation(True, True, "declared threshold outcome: pass")
    if declared_result in {"fail", "failed", "failure"}:
        return MetricEvaluation(True, False, "declared threshold outcome: fail")
    return MetricEvaluation(True, None, "metric conforms; threshold outcome is not comparable")
