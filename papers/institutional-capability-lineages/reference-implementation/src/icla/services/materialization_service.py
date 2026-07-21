"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Substrate adapters that preserve the logical assembly hash.

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import yaml

from ..models.assembly import Assembly, Materialization
from ..models.common import utc_now


def _canonical(assembly: Assembly) -> bytes:
    return json.dumps(
        assembly.model_dump(mode="json", by_alias=True, exclude_none=True),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()


class YamlBundleMaterializer:
    substrate = "yaml-bundle"

    def materialize(self, assembly: Assembly, target: str | Path) -> Materialization:
        content_hash = hashlib.sha256(_canonical(assembly)).hexdigest()
        path = Path(target)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(
                assembly.model_dump(mode="json", by_alias=True, exclude_none=True), sort_keys=False
            ),
            encoding="utf-8",
        )
        return Materialization(
            id=f"MAT-{str(uuid5(NAMESPACE_URL, assembly.id + self.substrate)).upper()}",
            assembly_ref=assembly.id,
            substrate=self.substrate,
            uri=path.resolve().as_uri(),
            content_hash=content_hash,
            created_at=utc_now(),
        )


class WorkspaceMaterializer(YamlBundleMaterializer):
    substrate = "workspace"

    def materialize(self, assembly: Assembly, target: str | Path) -> Materialization:
        directory = Path(target)
        directory.mkdir(parents=True, exist_ok=True)
        return super().materialize(assembly, directory / "assembly.yaml")
