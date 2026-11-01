from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from llm_eval_harness.clean import normalize, title_from
from llm_eval_harness.ingest.loaders import doc_id_for, iter_documents
from llm_eval_harness.ingest.manifest import aggregate_hash, build_manifest, sha256_text
from llm_eval_harness.models import CorpusConfig, Document, Manifest, ManifestEntry


def make_document(doc_id: str, text: str) -> Document:
    return Document(
        doc_id=doc_id,
        source=f"{doc_id}.md",
        title=doc_id,
        text=text,
        content_hash=sha256_text(text),
    )


def test_sha256_is_deterministic() -> None:
    assert sha256_text("hello") == sha256_text("hello")
    assert sha256_text("hello") != sha256_text("hello ")


def test_aggregate_hash_ignores_order() -> None:
    a = ManifestEntry(doc_id="a", path="a.md", content_hash="111", char_count=1)
    b = ManifestEntry(doc_id="b", path="b.md", content_hash="222", char_count=1)
    assert aggregate_hash([a, b]) == aggregate_hash([b, a])


def test_aggregate_hash_changes_when_a_document_changes() -> None:
    before = [ManifestEntry(doc_id="a", path="a.md", content_hash="111", char_count=1)]
    after = [ManifestEntry(doc_id="a", path="a.md", content_hash="999", char_count=1)]
    assert aggregate_hash(before) != aggregate_hash(after)


def test_build_manifest_totals() -> None:
    docs = [make_document("a", "abc"), make_document("b", "de")]
    manifest = build_manifest(docs, corpus_name="test", snapshot=date(2026, 11, 1))
    assert manifest.total_documents == 2
    assert manifest.total_chars == 5
    assert [entry.path for entry in manifest.entries] == ["a.md", "b.md"]


def test_manifest_roundtrip(tmp_path: Path) -> None:
    docs = [make_document("a", "abc")]
    manifest = build_manifest(docs, corpus_name="test", snapshot=date(2026, 11, 1))
    path = tmp_path / "manifest.json"
    manifest.save(path)
    assert Manifest.load(path).corpus_hash == manifest.corpus_hash


def test_normalize_collapses_blank_lines_and_line_endings() -> None:
    raw = "title\r\n\r\n\r\n\r\nbody   with   spaces  \r\n"
    assert normalize(raw) == "title\n\nbody with spaces"


def test_title_from_prefers_markdown_heading() -> None:
    assert title_from("## Queue behaviour\n\nbody", fallback="x") == "Queue behaviour"
    assert title_from("", fallback="fallback") == "fallback"


def test_doc_id_is_stable_slug(tmp_path: Path) -> None:
    root = tmp_path
    path = root / "Guide To Queues.md"
    assert doc_id_for(path, root) == "guide-to-queues"


def test_iter_documents_skips_short_files(tmp_path: Path) -> None:
    (tmp_path / "long.md").write_text("# Long\n\n" + "word " * 200, encoding="utf-8")
    (tmp_path / "short.md").write_text("too short", encoding="utf-8")

    config = CorpusConfig(
        name="test",
        snapshot=date(2026, 11, 1),
        raw_dir=tmp_path,
        include=["*.md"],
        min_chars=100,
    )

    documents = iter_documents(config, tmp_path)
    assert [document.doc_id for document in documents] == ["long"]


def test_iter_documents_missing_directory_raises(tmp_path: Path) -> None:
    config = CorpusConfig(name="test", snapshot=date(2026, 11, 1), raw_dir=tmp_path / "nope")
    with pytest.raises(FileNotFoundError):
        iter_documents(config)
