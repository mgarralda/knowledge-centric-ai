"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Deterministic lexical normalization for outcome coverage.

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

_STOP_WORDS = {
    "a",
    "an",
    "and",
    "approved",
    "auditable",
    "compliant",
    "cross",
    "governed",
    "high",
    "of",
    "outcome",
    "platform",
    "service",
    "services",
    "sufficient",
    "the",
    "to",
    "within",
    "zero",
}

_CONCEPTS = {
    "identity": {
        "access",
        "authentication",
        "authorization",
        "iam",
        "identity",
        "oauth",
    },
    "interface": {
        "api",
        "client",
        "clients",
        "compatibility",
        "compatible",
        "endpoint",
        "endpoints",
        "interface",
        "profile",
        "protocol",
    },
    "verification": {
        "assurance",
        "finding",
        "findings",
        "latency",
        "security",
        "severity",
        "validation",
        "verification",
        "verify",
    },
    "release": {"production", "release", "reversible", "rollback", "rollout"},
    "change": {
        "change",
        "changes",
        "code",
        "evolution",
        "implementation",
        "introduce",
        "migration",
    },
    "architecture": {"architecture", "enterprise"},
    "data": {"data", "privacy", "retention"},
    "observability": {"alerting", "monitoring", "observability", "telemetry"},
}

_CANONICAL = {token: concept for concept, tokens in _CONCEPTS.items() for token in tokens}


def semantic_terms(*values: str) -> set[str]:
    terms = set()
    for value in values:
        for token in re.findall(r"[a-z0-9]+", value.casefold()):
            if token not in _STOP_WORDS:
                terms.add(_CANONICAL.get(token, token))
    return terms


def structured_text_values(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for item in value.values():
            yield from structured_text_values(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from structured_text_values(item)
    elif value not in (None, ""):
        yield str(value)


def outcome_matches(required: str, offered: str) -> bool:
    required_value = required.casefold()
    offered_value = offered.casefold()
    if (
        required_value == offered_value
        or required_value in offered_value
        or offered_value in required_value
    ):
        return True
    return bool(semantic_terms(required) & semantic_terms(offered))
