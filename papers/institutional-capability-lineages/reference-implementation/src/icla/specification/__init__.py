"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Integration with the normative sibling specification.

from .conformance import ConformanceChecker, ConformanceProfile
from .schema_loader import SchemaLoader
from .validator import ArtifactValidator

__all__ = ["ArtifactValidator", "ConformanceChecker", "ConformanceProfile", "SchemaLoader"]
