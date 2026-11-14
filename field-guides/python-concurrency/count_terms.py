"""Build per-document term counts with a process pool on Python 3.11+."""

from collections import Counter
from concurrent.futures import ProcessPoolExecutor


def count_terms(text: str) -> Counter[str]:
    """Normalize tokens and count them for one document."""
    counts: Counter[str] = Counter()
    for token in text.split():
        # This Python loop models local text processing for indexing.
        counts[token.strip(".,;:!?").casefold()] += 1
    return counts


def main() -> None:
    """Run independent CPU work on two synthetic documents."""
    documents = {
        "ingestion": "Read, normalize, and index the source. " * 50_000,
        "retrieval": "Search the index and return evidence. " * 50_000,
    }

    # Each worker can execute Python code on a separate core. Reuse the
    # pool across documents to amortize worker startup. Text and counters
    # cross a process boundary, so profile against direct calls first.
    with ProcessPoolExecutor(max_workers=2) as pool:
        # map returns results in input order, preserving document association.
        for document_id, counts in zip(documents, pool.map(count_terms, documents.values())):
            print(f"{document_id}: {counts.most_common(3)}")


if __name__ == "__main__":
    # Spawned workers import this module. The guard keeps them from
    # launching another pool while importing count_terms.
    main()
