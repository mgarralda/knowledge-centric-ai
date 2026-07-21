"""
Institutional Capability Lineages (ICLA)
Reference Implementation

Copyright (c) 2026 Mariano Garralda-Barrio

Licensed under the MIT License.
See the LICENSE file in the repository root for details.
"""

# Module purpose: Immutable named snapshots.

from .append_only_store import AppendOnlyStore


class SnapshotStore(AppendOnlyStore):
    pass
