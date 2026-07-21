"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Domain-specific failures exposed by the public API.


class ICLAError(Exception):
    """Base error for expected ICLA failures."""


class ArtifactNotFoundError(ICLAError):
    pass


class DuplicateArtifactError(ICLAError):
    pass


class SpecificationValidationError(ICLAError):
    pass


class ConformanceError(ICLAError):
    pass


class AuthorizationError(ICLAError):
    pass


class AdmissionError(ICLAError):
    pass


class ActivationError(ICLAError):
    pass


class LineageError(ICLAError):
    pass
