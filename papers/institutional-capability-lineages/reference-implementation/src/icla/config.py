"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Runtime paths for the file-based reference implementation.

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _default_specification_dir() -> Path:
    configured = os.getenv("ICLA_SPECIFICATION_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return (Path(__file__).resolve().parents[3] / "specification").resolve()


@dataclass(frozen=True, slots=True)
class Settings:
    specification_dir: Path = _default_specification_dir()
    data_dir: Path = Path(".icla-data")

    @property
    def schema_dir(self) -> Path:
        return self.specification_dir / "schemas"
