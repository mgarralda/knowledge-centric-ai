"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Locate, load, cache, and resolve specification schemas.

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from referencing import Registry, Resource

from ..config import Settings
from ..exceptions import ArtifactNotFoundError


class SchemaLoader:
    def __init__(self, schema_dir: Path | None = None) -> None:
        self.schema_dir = (schema_dir or Settings().schema_dir).resolve()
        self._cache: dict[str, dict[str, Any]] = {}
        self._registry: Registry | None = None

    def available(self) -> tuple[str, ...]:
        if not self.schema_dir.is_dir():
            return ()
        return tuple(
            sorted(
                path.name.removesuffix(".schema.yaml")
                for path in self.schema_dir.glob("*.schema.yaml")
            )
        )

    def path_for(self, schema_name: str) -> Path:
        name = schema_name.removesuffix(".schema.yaml")
        path = self.schema_dir / f"{name}.schema.yaml"
        if not path.is_file():
            raise ArtifactNotFoundError(f"Schema not found: {path}")
        return path

    def load(self, schema_name: str) -> dict[str, Any]:
        name = schema_name.removesuffix(".schema.yaml")
        if name not in self._cache:
            with self.path_for(name).open(encoding="utf-8") as stream:
                value = yaml.safe_load(stream)
            if not isinstance(value, dict):
                raise ValueError(f"Schema {name!r} is not a mapping")
            self._cache[name] = value
        return self._cache[name]

    @property
    def registry(self) -> Registry:
        """Return a registry capable of resolving local schema references."""
        if self._registry is None:
            resources: list[tuple[str, Resource]] = []
            for name in self.available():
                path = self.path_for(name)
                resource = Resource.from_contents(self.load(name))
                resources.extend(
                    (
                        (path.as_uri(), resource),
                        (path.name, resource),
                        (f"./{path.name}", resource),
                    )
                )
            self._registry = Registry().with_resources(resources)
        return self._registry

    @property
    def specification_version(self) -> str | None:
        for name in self.available():
            schema = self.load(name)
            try:
                return schema["properties"]["specification_version"]["properties"]["icla-spec"][
                    "const"
                ]
            except KeyError:
                continue
        return None
