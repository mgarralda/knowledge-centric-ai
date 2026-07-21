"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: YAML persistence that refuses mutation of an existing artifact ID.

from pathlib import Path
from typing import Any

from ..exceptions import DuplicateArtifactError
from .yaml_store import YamlStore


class AppendOnlyStore(YamlStore):
    def append(self, namespace: str, artifact_id: str, value: dict[str, Any]) -> Path:
        if self.path_for(namespace, artifact_id).exists():
            raise DuplicateArtifactError(
                f"Append-only artifact already exists: {namespace}/{artifact_id}"
            )
        return self.write(namespace, artifact_id, value)

    def write(self, namespace: str, artifact_id: str, value: dict[str, Any]) -> Path:
        if self.path_for(namespace, artifact_id).exists():
            raise DuplicateArtifactError(
                f"Append-only artifact already exists: {namespace}/{artifact_id}"
            )
        return super().write(namespace, artifact_id, value)
