"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""


def can_consume(consumer: dict, capability, scope: dict | None = None) -> tuple[bool, str]:
    allowed = set(getattr(capability, "allowed_consumers", []) or [])
    identity = consumer.get("configuration_id")
    permitted = not allowed or identity in allowed or consumer.get("type") in allowed
    return (
        permitted,
        "consumer authorized" if permitted else f"consumer {identity!r} is not authorized",
    )


def can_submit_evidence(producer: str, assembly) -> tuple[bool, str]:
    allowed = assembly.evidence_contract.get("authorized_producers", [])
    permitted = not allowed or producer in allowed
    return (
        permitted,
        "producer authorized" if permitted else f"producer {producer!r} is not authorized",
    )


def can_activate(reviewer: str, capability) -> tuple[bool, str]:
    permitted = reviewer == capability.owner or reviewer in capability.policy_refs
    return (
        permitted,
        "reviewer authorized"
        if permitted
        else "reviewer is not capability owner or delegated authority",
    )
