"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Stable institutional capability identity.

from pydantic import Field, model_validator

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
    active_ckc: ActiveCKC | None = None
    risk: str | None = None
    maturity: str | None = None
    policy_refs: list[str] = Field(default_factory=list)
    conditions: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_active_pointer(self):
        if self.lifecycle == LifecycleStatus.ACTIVE and self.active_ckc is None:
            raise ValueError("An active capability requires an active CKC pointer")
        return self


class InstitutionalCapability(SpecificationMetadata):
    """Standalone form of the stable capability identity."""

    document_type: str = "institutional-capability"
    name: str
    outcome: str
    owner: str
    domain: str
    lifecycle: LifecycleStatus
    active_ckc: ActiveCKC | None = None
    risk: str | None = None
    maturity: str | None = None
    policy_refs: list[str] = Field(default_factory=list)
    conditions: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_active_pointer(self):
        if self.lifecycle == LifecycleStatus.ACTIVE and self.active_ckc is None:
            raise ValueError("An active capability requires an active CKC pointer")
        return self
