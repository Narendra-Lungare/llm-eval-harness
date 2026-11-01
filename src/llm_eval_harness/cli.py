"""Command line interface.

Session 1 implements `ingest` only. The remaining commands are declared now so
the shape of the tool is visible from the first commit -- and so each later
session has an obvious slot to fill.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from llm_eval_harness.config import load_corpus_config
from llm_eval_harness.ingest.loaders import iter_documents
from llm_eval_harness.ingest.manifest import build_manifest

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Evaluate chunking, embedding and reranking choices against a golden set.",
)
console = Console()


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )


@app.command()
def ingest(
    config: Annotated[
        Path, typer.Option("--config", "-c", help="Corpus config file.")
    ] = Path("configs/corpus.yaml"),
    raw_dir: Annotated[
        Path | None, typer.Option("--raw-dir", help="Override corpus.raw_dir (smoke tests).")
    ] = None,
    out: Annotated[
        Path, typer.Option("--out", help="Manifest output path.")
    ] = Path("data/manifest.json"),
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Read the corpus, normalise it, and write a reproducible manifest."""
    _configure_logging(verbose)

    try:
        corpus = load_corpus_config(config)
    except (FileNotFoundError, ValueError) as exc:
        console.print(f"[red]config error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    root = raw_dir or corpus.raw_dir
    try:
        documents = iter_documents(corpus, root)
    except FileNotFoundError as exc:
        console.print(f"[red]corpus error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    if not documents:
        console.print(
            f"[red]no documents found[/red] in {root} matching {corpus.include} "
            f"with >= {corpus.min_chars} chars"
        )
        raise typer.Exit(code=1)

    manifest = build_manifest(documents, corpus_name=corpus.name, snapshot=corpus.snapshot)
    manifest.save(out)

    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_row("corpus", f"{manifest.corpus_name} ({manifest.snapshot})")
    table.add_row("documents", str(manifest.total_documents))
    table.add_row("characters", f"{manifest.total_chars:,}")
    table.add_row("corpus_hash", manifest.corpus_hash)
    table.add_row("manifest", str(out))

    console.print(table)
    console.print(
        "\n[dim]Record this hash whenever you publish metrics: it identifies "
        "the exact documents the numbers came from.[/dim]"
    )


@app.command()
def index() -> None:
    """Build an index for one chunking + embedding config. (session 3)"""
    console.print("[yellow]not implemented yet[/yellow] - lands in session 3")
    raise typer.Exit(code=2)


@app.command()
def run() -> None:
    """Run the golden set against one retrieval config. (session 6)"""
    console.print("[yellow]not implemented yet[/yellow] - lands in session 6")
    raise typer.Exit(code=2)


@app.command()
def report(
    runs: Annotated[Path, typer.Option("--runs")] = Path("runs"),
    fmt: Annotated[str, typer.Option("--format")] = "md,csv",
) -> None:
    """Render metrics for stored runs. (session 6)"""
    console.print(f"[yellow]not implemented yet[/yellow] - will read {runs} as {fmt}")
    raise typer.Exit(code=2)


@app.command()
def check(
    baseline: Annotated[Path, typer.Option("--baseline")] = Path("runs/baseline.json"),
    tolerance: Annotated[float, typer.Option("--tolerance")] = 0.02,
) -> None:
    """CI gate: fail when metrics regress past tolerance. (session 8)"""
    console.print(f"[yellow]not implemented yet[/yellow] - {baseline} +/- {tolerance}")
    raise typer.Exit(code=2)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
