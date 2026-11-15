"""RSIC orchestration from Algorithm 1 (paper §5.1).

The builder owns traversal and the artifact handoff. Source access, semantic
extraction and sibling-aware composition are supplied by an adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from contracts import (
    Cue, Dependency, Directory, Document, EvidenceUnit, Index, RepositorySnapshot,
)


@dataclass(frozen=True)
class SubtreeDescription:
    """Child-to-parent contract, including support for discriminative cues."""

    node_id: str
    cues: tuple[Cue, ...]
    evidence_ids: frozenset[str]


@dataclass(frozen=True)
class ExtractedDocument:
    description: SubtreeDescription
    evidence: tuple[EvidenceUnit, ...]


@dataclass(frozen=True)
class ComposedDirectory:
    index: Index
    description: SubtreeDescription
    dependencies: tuple[Dependency, ...] = ()


class RSICOperations(Protocol):
    """Semantic and conformance operations required by the builder."""

    def extract(self, document: Document, source_snapshot_id: str) -> ExtractedDocument:
        """Extract evidence and cues from a pinned source, with context locators."""
        ...

    def compose(
        self, directory: Directory, children: tuple[SubtreeDescription, ...]
    ) -> ComposedDirectory:
        """Compose against all siblings and attach evidence and context links."""
        ...

    def check_artifact_contract(self, candidate: RepositorySnapshot) -> None:
        """Check references and record semantic conformance via the adapter.

        Raise for malformed build output. Assurance may subsequently inspect
        compatible artifacts with repairable repository defects.
        """
        ...


class RSICBuilder:
    """Build a versioned index bottom-up and return the assurance input."""

    def __init__(self, operations: RSICOperations) -> None:
        self.operations = operations

    def build(
        self, tree: Directory, *, snapshot_id: str, source_snapshot_id: str
    ) -> RepositorySnapshot:
        """Visit each directory after its children (Algorithm 1, lines 3–14)."""
        indexes: list[Index] = []
        evidence: list[EvidenceUnit] = []
        dependencies: list[Dependency] = []

        def visit(node: Directory | Document) -> SubtreeDescription:
            if isinstance(node, Document):
                extracted = self.operations.extract(node, source_snapshot_id)
                evidence.extend(extracted.evidence)
                return extracted.description

            children = tuple(visit(child) for child in node.children)
            composed = self.operations.compose(node, children)
            indexes.append(composed.index)
            dependencies.extend(composed.dependencies)
            return composed.description

        visit(tree)
        candidate = RepositorySnapshot(
            id=snapshot_id,
            source_snapshot_id=source_snapshot_id,
            tree=tree,
            indexes=tuple(indexes),
            evidence=tuple(evidence),
            dependencies=tuple(dependencies),
        )
        self.operations.check_artifact_contract(candidate)
        return candidate
