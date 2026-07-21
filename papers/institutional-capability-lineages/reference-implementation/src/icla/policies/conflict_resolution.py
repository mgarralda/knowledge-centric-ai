"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""


def resolve_obligation_conflicts(
    obligations: list[dict],
) -> tuple[list[dict], list[str], list[dict]]:
    """Resolve comparable constraints and expose incompatible obligations."""
    selected: dict[str, dict] = {}
    rationale: list[str] = []
    unresolved: list[dict] = []
    for item in obligations:
        key = str(item.get("id") or item.get("name") or f"anonymous-{len(selected)}")
        current = selected.get(key)
        if current is None:
            selected[key] = item
        elif item == current:
            rationale.append(f"{key}: equivalent obligations merged")
        elif "maximum" in item and "maximum" in current:
            if item["maximum"] < current["maximum"]:
                selected[key] = item
            rationale.append(f"{key}: selected stricter maximum {selected[key]['maximum']}")
        elif "minimum" in item and "minimum" in current:
            if item["minimum"] > current["minimum"]:
                selected[key] = item
            rationale.append(f"{key}: selected stricter minimum {selected[key]['minimum']}")
        else:
            unresolved.append({"obligation": key, "left": current, "right": item})
            rationale.append(f"{key}: incompatible obligations require governance review")
    return list(selected.values()), rationale, unresolved
