# llm-eval-harness

Measure retrieval quality instead of arguing about it.

`recall@k`, `MRR`, `nDCG`, groundedness, p95 latency and cost per 1k queries for
any combination of chunking, embedding and reranking — from one CLI run, tied to
a hashed corpus snapshot.

> Status: session 1 of 8. Ingestion and corpus fingerprinting work; chunking,
> indexing, metrics and the CI gate are stubs on purpose.

## Quickstart

```bash
uv sync

# smoke test on the three hand-written fixtures in data/sample
uv run harness ingest --raw-dir data/sample

# real corpus: fetch the pages listed in configs/sources.txt, then ingest
uv run python scripts/fetch_corpus.py
uv run harness ingest
```

`ingest` writes `data/manifest.json` and prints the `corpus_hash`:

```
corpus       azure-messaging-docs (2026-11-01)
documents    <n>
characters   <total>
corpus_hash  <sha256>
manifest     data/manifest.json
```

Every published number must cite that hash. Metrics without a corpus hash are
not reproducible and will not be compared across runs.

## Commands

| Command | Status | Purpose |
|---|---|---|
| `harness ingest` | working | read corpus, normalise, hash, write manifest |
| `harness index` | session 3 | chunk + embed + build index for one config |
| `harness run` | session 6 | run the golden set, store per-question results |
| `harness report` | session 6 | render markdown/CSV metrics table |
| `harness check` | session 8 | CI gate: fail on regression past tolerance |

## Layout

```
configs/          corpus.yaml + sources.txt (+ chunking/embedding/retrieval later)
data/raw/         fetched documents, gitignored
data/sample/      three fixtures used by the smoke test and the test suite
data/golden/      golden questions with character-level source spans (session 5)
scripts/          fetch_corpus.py
src/llm_eval_harness/
  cli.py          typer commands
  clean.py        normalisation (offsets depend on this being stable)
  config.py       config loading
  models.py       Document / Manifest / CorpusConfig
  ingest/         discovery, parsing, manifest hashing
tests/            manifest determinism, normalisation, CLI behaviour
```

## Design decisions

- **Manifest hash over file mtimes.** Two machines can rebuild the same corpus and
  prove it with one hash. Costs ~30 lines.
- **Normalise once, offset forever.** Golden spans and chunk spans are relative to
  `clean.normalize`. Changing it invalidates every stored span, so the manifest has
  a `schema_version`.
- **Skip, don't silently drop.** Documents below `min_chars` are logged. A corpus
  that quietly loses files makes every later metric a lie.
- **Stub the whole CLI on day one.** The tool shape is a design decision; leaving it
  undefined until session 6 would force a rewrite.

## Development

```bash
uv run ruff check .
uv run ruff format .
uv run mypy
uv run pytest
```

Sample fixtures in `data/sample/` are hand-written for smoke tests only. Real
metrics require a real corpus; do not publish numbers measured on samples.
