import re
from pathlib import Path

MATRIX = Path(__file__).parents[3] / "specification" / "conformance-matrix.md"


def test_conformance_matrix_maps_every_invariant_without_certification_columns():
    text = MATRIX.read_text(encoding="utf-8")

    for invariant in range(1, 12):
        assert f"**ICLA-{invariant} -" in text

    header = next(line for line in text.splitlines() if line.startswith("| Invariant |"))
    assert header == (
        "| Invariant | Machine-checkable clauses | Supporting artifacts | "
        "Executable tests | Governed-judgment remainder |"
    )
    for excluded_column in ("Profile", "Status", "Pass/fail", "Score"):
        assert excluded_column not in header


def test_conformance_matrix_local_links_resolve():
    text = MATRIX.read_text(encoding="utf-8")
    targets = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)

    assert targets
    for target in targets:
        assert (MATRIX.parent / target).resolve().exists(), target
