"""
Institutional Capability Lineage Architecture (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: CEE-side substrate adapters that preserve assembly semantics and authority.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, uuid5

import yaml

from ..models.assembly import Assembly, Materialization
from ..models.common import utc_now


def _versioned_binding(values: dict[str, Any], label: str) -> dict[str, Any]:
    if not values.get("id") or values.get("version") is None:
        raise ValueError(f"The assembly requires a versioned {label}")
    return {"id": values["id"], "version": values["version"]}


def _materialization_context(
    assembly: Assembly, transformation: dict[str, Any]
) -> dict[str, Any]:
    cee_ref = assembly.lineage.get("cee_ref")
    if not cee_ref:
        raise ValueError("The assembly requires a CEE lineage reference")
    local_transformation = _versioned_binding(transformation, "CEE-side transformation")
    return {
        "cee_ref": cee_ref,
        "transformation": local_transformation,
        "evaluation_binding": _versioned_binding(
            assembly.evaluation_contract, "evaluation binding"
        ),
        "evidence_binding": _versioned_binding(assembly.evidence_contract, "evidence binding"),
        "generated_from": {
            "assembly": assembly.id,
            "cee": cee_ref,
            "transformation": local_transformation,
        },
    }


class YamlBundleMaterializer:
    substrate = {"id": "yaml-bundle", "version": 1}
    representation_kind = "bundle"

    def materialize(
        self,
        assembly: Assembly,
        target: str | Path,
        transformation: dict[str, Any],
    ) -> Materialization:
        representation = yaml.safe_dump(
            assembly.model_dump(mode="json", by_alias=True, exclude_none=True), sort_keys=False
        )
        content_hash = hashlib.sha256(representation.encode()).hexdigest()
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(representation, encoding="utf-8")
        transformation_seed = json.dumps(transformation, sort_keys=True, separators=(",", ":"))
        identifier_seed = assembly.id + self.substrate["id"] + transformation_seed
        return Materialization(
            id=f"MAT-{str(uuid5(NAMESPACE_URL, identifier_seed)).upper()}",
            schema_ref="schemas/materialization.schema.yaml",
            assembly_ref=assembly.id,
            substrate=self.substrate,
            representation={
                "kind": self.representation_kind,
                "local_reference": path.resolve().as_uri(),
            },
            content_hash=content_hash,
            created_at=utc_now(),
            access={
                "mode": "local-reference",
                "policy_ref": assembly.access_policy_ref or "POL-ICLA-LOCAL-ACCESS",
            },
            **_materialization_context(assembly, transformation),
        )


class WorkspaceMaterializer(YamlBundleMaterializer):
    substrate = {"id": "workspace", "version": 1}
    representation_kind = "workspace"

    def materialize(
        self,
        assembly: Assembly,
        target: str | Path,
        transformation: dict[str, Any],
    ) -> Materialization:
        directory = Path(target)
        directory.mkdir(parents=True, exist_ok=True)
        return super().materialize(assembly, directory / "assembly.yaml", transformation)


class AccessHandleMaterializer:
    """Materialize governed references without copying their source payloads."""

    substrate = {"id": "governed-access-handles", "version": 1}

    def materialize(
        self,
        assembly: Assembly,
        handles: list[dict[str, Any]],
        transformation: dict[str, Any],
    ) -> Materialization:
        if not handles:
            raise ValueError("At least one governed access handle is required")
        required = {"id", "uri", "authority"}
        if any(required - handle.keys() for handle in handles):
            raise ValueError("Each access handle requires id, uri, and authority")
        descriptor = json.dumps(handles, sort_keys=True, separators=(",", ":")).encode()
        content_hash = hashlib.sha256(descriptor).hexdigest()
        transformation_seed = json.dumps(transformation, sort_keys=True, separators=(",", ":"))
        identifier_seed = assembly.id + self.substrate["id"] + transformation_seed + content_hash
        return Materialization(
            id=f"MAT-{str(uuid5(NAMESPACE_URL, identifier_seed)).upper()}",
            schema_ref="schemas/materialization.schema.yaml",
            assembly_ref=assembly.id,
            substrate=self.substrate,
            representation={"kind": "access-handles"},
            content_hash=content_hash,
            created_at=utc_now(),
            access={
                "mode": "governed-access-handles",
                "policy_ref": assembly.access_policy_ref or "POL-ICLA-LOCAL-ACCESS",
                "handles": handles,
            },
            **_materialization_context(assembly, transformation),
        )
