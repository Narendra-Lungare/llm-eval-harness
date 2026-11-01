"""Core data types shared across the harness.

Dependency-light on purpose: these models are the contract between ingest,
chunking, retrieval and reporting. Nothing here imports a model provider.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class CorpusConfig(BaseModel):
    """Contents of configs/corpus.yaml."""

    name: str
    snapshot: date
    raw_dir: Path = Path("data/raw")
    include: list[str] = Field(default_factory=lambda: ["*.md", "*.txt", "*.html"])
    exclude: list[str] = Field(default_factory=list)
    min_chars: int = 200


class Document(BaseModel):
    """One source document after parsing and normalisation."""

    doc_id: str
    source: str
    title: str
    text: str
    content_hash: str

    @property
    def char_count(self) -> int:
        return len(self.text)


class ManifestEntry(BaseModel):
    """A single document's fingerprint inside a corpus snapshot."""

    doc_id: str
    path: str
    content_hash: str
    char_count: int
    source_url: str | None = None


class Manifest(BaseModel):
    """Fingerprint of the whole corpus.

    `corpus_hash` is what makes a run reproducible: every metrics report is
    tied to exactly one snapshot of documents.
    """

    schema_version: int = 1
    corpus_name: str
    snapshot: date
    created_at: datetime
    corpus_hash: str
    total_documents: int
    total_chars: int
    entries: list[ManifestEntry]

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Manifest:
        return cls.model_validate_json(path.read_text(encoding="utf-8"))
