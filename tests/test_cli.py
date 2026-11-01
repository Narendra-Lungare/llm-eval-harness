from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from llm_eval_harness.cli import app

runner = CliRunner()


def write_corpus(root: Path) -> None:
    body = "# Queue behaviour\n\n" + ("A message moves to the dead-letter queue after delivery. " * 20)
    (root / "queues.md").write_text(body, encoding="utf-8")


def test_ingest_writes_manifest(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    write_corpus(raw)

    config = tmp_path / "corpus.yaml"
    config.write_text(
        "name: test-corpus\n"
        "snapshot: 2026-11-01\n"
        f'raw_dir: "{raw.as_posix()}"\n'
        'include: ["*.md"]\n'
        "min_chars: 50\n",
        encoding="utf-8",
    )
    out = tmp_path / "manifest.json"

    result = runner.invoke(app, ["ingest", "--config", str(config), "--out", str(out)])

    assert result.exit_code == 0, result.output
    assert out.exists()
    assert "corpus_hash" in out.read_text(encoding="utf-8")


def test_ingest_fails_without_documents(tmp_path: Path) -> None:
    raw = tmp_path / "empty"
    raw.mkdir()
    config = tmp_path / "corpus.yaml"
    config.write_text(
        "name: empty\n"
        "snapshot: 2026-11-01\n"
        f'raw_dir: "{raw.as_posix()}"\n'
        'include: ["*.md"]\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["ingest", "--config", str(config), "--out", str(tmp_path / "m.json")])

    assert result.exit_code == 1


def test_unimplemented_commands_exit_nonzero() -> None:
    assert runner.invoke(app, ["index"]).exit_code == 2
    assert runner.invoke(app, ["run"]).exit_code == 2
