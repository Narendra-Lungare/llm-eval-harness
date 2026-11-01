"""Discover and read source documents from a directory tree."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import trafilatura

from llm_eval_harness.clean import normalize, title_from
from llm_eval_harness.ingest.manifest import sha256_text
from llm_eval_harness.models import CorpusConfig, Document

logger = logging.getLogger(__name__)

TEXT_SUFFIXES = frozenset({".md", ".markdown", ".txt", ".rst"})
HTML_SUFFIXES = frozenset({".html", ".htm"})

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    return _SLUG_STRIP.sub("-", value.lower()).strip("-")


def doc_id_for(path: Path, root: Path) -> str:
    relative = path.relative_to(root)
    return slugify(relative.with_suffix("").as_posix())


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_html_file(path: Path) -> str:
    html = path.read_text(encoding="utf-8", errors="replace")
    extracted = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    )
    if not extracted:
        logger.warning("no main content extracted from %s", path)
        return ""
    return extracted


def iter_source_paths(config: CorpusConfig, root: Path) -> list[Path]:
    paths: list[Path] = []
    for pattern in config.include:
        paths.extend(sorted(root.rglob(pattern)))

    excluded = [root / item for item in config.exclude]
    unique: dict[Path, None] = {}
    for path in paths:
        if not path.is_file():
            continue
        if any(path.is_relative_to(item) for item in excluded):
            continue
        unique[path] = None
    return sorted(unique)


def load_document(path: Path, root: Path) -> Document:
    suffix = path.suffix.lower()
    raw = read_html_file(path) if suffix in HTML_SUFFIXES else read_text_file(path)

    text = normalize(raw)
    if not text:
        return Document(
            doc_id=doc_id_for(path, root),
            source=path.relative_to(root).as_posix(),
            title=path.stem,
            text="",
            content_hash=sha256_text(""),
        )
    return Document(
        doc_id=doc_id_for(path, root),
        source=path.relative_to(root).as_posix(),
        title=title_from(text, fallback=path.stem),
        text=text,
        content_hash=sha256_text(text),
    )


def iter_documents(config: CorpusConfig, root: Path | None = None) -> list[Document]:
    """Read every matching file, dropping anything below `min_chars`.

    Skipped documents are logged rather than silently dropped: a corpus that
    quietly loses 30% of its files makes every later metric a lie.
    """
    base = root or config.raw_dir
    if not base.exists():
        raise FileNotFoundError(f"corpus directory not found: {base}")

    documents: list[Document] = []
    for path in iter_source_paths(config, base):
        document = load_document(path, base)
        if document.char_count < config.min_chars:
            logger.warning(
                "skipping %s (%d chars < min_chars=%d)",
                document.source,
                document.char_count,
                config.min_chars,
            )
            continue
        documents.append(document)

    return documents
