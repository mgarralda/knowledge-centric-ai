"""Run a self-contained claim ingestion pipeline on Python 3.11+."""

import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory


async def extract_claim(text: str) -> tuple[str, str]:
    """Simulate network latency and return a claim and quote for a sample document."""
    await asyncio.sleep(0.1)
    return text, text


async def ingest_documents(
    documents: list[tuple[Path, int]],
) -> dict[tuple[str, int], tuple[str, str]]:
    """Ingest a small batch and return claims keyed by document stem and version."""
    # TaskGroup starts a task for each document. The shared semaphore lets
    # only two tasks enter the extractor at once, modeling a service with
    # limited capacity for simultaneous requests. Waiting tasks yield control.
    # Use a separate rate limiter for quotas measured per minute.
    extraction_slots = asyncio.Semaphore(2)
    index: dict[tuple[str, int], tuple[str, str]] = {}

    async def ingest_one(path: Path, version: int) -> None:
        """Read, extract, validate and index one version in dependency order."""
        # Path.read_text blocks its calling thread. Move it to a worker
        # thread so the event loop can keep advancing other documents.
        source = await asyncio.to_thread(path.read_text, encoding="utf-8")
        # Trimming a short string is cheap enough to do on the event loop.
        text = source.strip()

        # Hold the slot only during extraction. The context manager releases
        # it on completion, failure or cancellation.
        # Trace the wait separately from extraction so the limit is visible.
        print(f"{path.stem}: waiting for extraction")
        async with extraction_slots:
            print(f"{path.stem}: extraction started")
            claim, quote = await extract_claim(text)
            print(f"{path.stem}: extraction finished")

        # Check that the quote occurs verbatim in the original source.
        if not quote or quote not in source:
            raise ValueError(f"Missing source evidence for {path.name} v{version}")

        index[path.stem, version] = (claim, quote)

    # The group waits for the batch. If one task raises, it cancels
    # the remaining tasks and propagates the error.
    async with asyncio.TaskGroup() as group:
        for path, version in documents:
            group.create_task(ingest_one(path, version))

    return index


def main() -> None:
    """Create sample documents, run the async batch and print the index."""
    sources = {
        "ingestion": "The ingestion service accepts Markdown documents.",
        "provenance": "Each claim records the version of its source document.",
        "retrieval": "The retrieval service returns matching claims.",
    }

    with TemporaryDirectory() as directory:
        documents = []
        for document_id, text in sources.items():
            path = Path(directory) / f"{document_id}.txt"
            path.write_text(text + "\n", encoding="utf-8")
            documents.append((path, 1))

        index = asyncio.run(ingest_documents(documents))

    for (document_id, version), (claim, quote) in sorted(index.items()):
        print(f"{document_id} v{version}: {claim} [evidence: {quote!r}]")


if __name__ == "__main__":
    main()
