"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

from ..models.assembly import Assembly
from ..storage import AppendOnlyStore


class AssemblyRepository:
    def __init__(self, store: AppendOnlyStore) -> None:
        self.store = store

    def append(self, assembly: Assembly) -> None:
        self.store.append(
            "assemblies",
            assembly.id,
            assembly.model_dump(mode="json", by_alias=True, exclude_none=True),
        )

    def get(self, assembly_id: str) -> Assembly:
        return Assembly.model_validate(self.store.read("assemblies", assembly_id))
