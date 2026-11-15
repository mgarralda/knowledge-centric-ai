"""Shared repository artifact contract (paper §§4.2–4.3, 5 and 6)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceRef:
    """Identify an immutable source version."""

    document_id: str
    version: str


@dataclass(frozen=True)
class EvidenceUnit:
    """Identify a passage and the context units required to interpret it."""

    id: str
    source: SourceRef
    locator: str
    context_ids: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Cue:
    """Preserve a discriminative assertion and its traceable support."""

    kind: str
    text: str
    evidence_ids: frozenset[str]
    critical_fields: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Document:
    id: str
    source: SourceRef


@dataclass(frozen=True)
class Directory:
    id: str
    children: tuple[Directory | Document, ...]


@dataclass(frozen=True)
class IndexEntry:
    """One navigable link and the cues available before following it."""

    target_id: str
    cues: tuple[Cue, ...]


@dataclass(frozen=True)
class Index:
    node_id: str
    entries: tuple[IndexEntry, ...]


@dataclass(frozen=True)
class Dependency:
    """A typed maintenance relation, independent of navigable index entries."""

    source_id: str
    dependent_id: str
    kind: str


@dataclass(frozen=True)
class RepositorySnapshot:
    """Immutable handoff accepted from RSIC or a compatible index builder."""

    id: str
    source_snapshot_id: str
    tree: Directory
    indexes: tuple[Index, ...]
    evidence: tuple[EvidenceUnit, ...]
    dependencies: tuple[Dependency, ...] = ()
