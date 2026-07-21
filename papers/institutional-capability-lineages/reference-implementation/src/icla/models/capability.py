"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Stable institutional capability identity.

from pydantic import Field

from .common import ExtensibleModel, LifecycleStatus, SpecificationMetadata


class ActiveCKC(ExtensibleModel):
    id: str
    version: int = Field(ge=1)


class Capability(ExtensibleModel):
    id: str
    name: str
    outcome: str
    owner: str
    domain: str
    lifecycle: LifecycleStatus
    active_ckc: ActiveCKC
    risk: str | None = None
    maturity: str | None = None
    policy_refs: list[str] = Field(default_factory=list)
    conditions: dict[str, str] = Field(default_factory=dict)


class InstitutionalCapability(SpecificationMetadata):
    """Standalone form of the stable capability identity."""

    document_type: str = "institutional-capability"
    name: str
    outcome: str
    owner: str
    domain: str
    lifecycle: LifecycleStatus
    active_ckc: ActiveCKC
    risk: str | None = None
    maturity: str | None = None
    policy_refs: list[str] = Field(default_factory=list)
    conditions: dict[str, str] = Field(default_factory=dict)
