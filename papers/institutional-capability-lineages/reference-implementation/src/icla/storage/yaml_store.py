"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Small inspectable YAML object store.

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import yaml

from ..exceptions import ArtifactNotFoundError


class YamlStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def path_for(self, namespace: str, artifact_id: str) -> Path:
        safe_id = artifact_id.replace("/", "_").replace("\\", "_")
        return self.root / namespace / f"{safe_id}.yaml"

    def read(self, namespace: str, artifact_id: str) -> dict[str, Any]:
        path = self.path_for(namespace, artifact_id)
        if not path.is_file():
            raise ArtifactNotFoundError(f"Artifact not found: {namespace}/{artifact_id}")
        with path.open(encoding="utf-8") as stream:
            value = yaml.safe_load(stream)
        if not isinstance(value, dict):
            raise ValueError(f"Stored artifact is not a mapping: {path}")
        return value

    def write(self, namespace: str, artifact_id: str, value: dict[str, Any]) -> Path:
        path = self.path_for(namespace, artifact_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                yaml.safe_dump(value, stream, sort_keys=False, allow_unicode=True)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return path

    def list(self, namespace: str) -> list[dict[str, Any]]:
        directory = self.root / namespace
        if not directory.is_dir():
            return []
        return [self.read(namespace, path.stem) for path in sorted(directory.glob("*.yaml"))]
