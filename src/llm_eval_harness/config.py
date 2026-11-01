"""Load and validate configs/*.yaml."""

from __future__ import annotations

from pathlib import Path

import yaml

from llm_eval_harness.models import CorpusConfig


def load_corpus_config(path: Path) -> CorpusConfig:
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return CorpusConfig.model_validate(raw)
