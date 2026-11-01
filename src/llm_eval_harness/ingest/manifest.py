"""Corpus hashing.

`corpus_hash` answers the question "which documents produced this number?".
It is computed from the *set of (path, content_hash) pairs*, sorted, so it is
stable across machines and file-read order.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from datetime import UTC, date, datetime

from llm_eval_harness.models import Document, Manifest, ManifestEntry


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def aggregate_hash(entries: Sequence[ManifestEntry]) -> str:
    payload = "\n".join(
        f"{entry.path}:{entry.content_hash}" for entry in sorted(entries, key=lambda e: e.path)
    )
    return sha256_text(payload)


def build_manifest(
    documents: Sequence[Document],
    *,
    corpus_name: str,
    snapshot: date,
    schema_version: int = 1,
) -> Manifest:
    entries = [
        ManifestEntry(
            doc_id=doc.doc_id,
            path=doc.source,
            content_hash=doc.content_hash,
            char_count=doc.char_count,
        )
        for doc in documents
    ]
    return Manifest(
        schema_version=schema_version,
        corpus_name=corpus_name,
        snapshot=snapshot,
        created_at=datetime.now(UTC),
        corpus_hash=aggregate_hash(entries),
        total_documents=len(entries),
        total_chars=sum(entry.char_count for entry in entries),
        entries=sorted(entries, key=lambda e: e.path),
    )
