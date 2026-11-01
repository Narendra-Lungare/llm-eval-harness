"""Fetch a public documentation corpus into data/raw.

Usage:
    uv run python scripts/fetch_corpus.py                  # all URLs in configs/sources.txt
    uv run python scripts/fetch_corpus.py --limit 3        # smoke test
    uv run python scripts/fetch_corpus.py --force          # refetch existing files

Design notes:
    * existing files are skipped by default, so re-running is cheap and the
      corpus does not drift between runs;
    * failures are reported at the end instead of aborting, so one dead URL
      does not cost you the whole fetch;
    * the URL -> file mapping is written to data/raw/sources.json, which is what
      lets you trace a chunk back to the page it came from.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
import trafilatura

USER_AGENT = (
    "llm-eval-harness/0.1 (+https://github.com/; educational retrieval evaluation corpus)"
)
DEFAULT_SOURCES = Path("configs/sources.txt")
DEFAULT_OUT = Path("data/raw")


def read_sources(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        urls.append(stripped)
    return urls


def slug_for(url: str) -> str:
    """Stable filename for a URL, unique enough that two pages cannot collide.

    Uses the last two path segments: many doc sites have several pages named
    `overview`, and a collision silently overwrites a document -- which then
    quietly changes every metric downstream.
    """
    parts = [part for part in urlparse(url).path.split("/") if part]
    if not parts:
        return "document"
    raw = "-".join(parts[-2:]) if len(parts) > 1 else parts[-1]
    cleaned = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in raw.lower())
    return cleaned.strip("-") or "document"


def fetch_one(client: httpx.Client, url: str) -> str:
    response = client.get(url)
    response.raise_for_status()
    extracted = trafilatura.extract(
        response.text,
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    )
    if not extracted:
        raise ValueError("no main content extracted")
    return extracted


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--limit", type=int, default=0, help="fetch at most N URLs (0 = all)")
    parser.add_argument("--delay", type=float, default=0.6, help="seconds between requests")
    parser.add_argument("--force", action="store_true", help="refetch existing files")
    args = parser.parse_args()

    urls = read_sources(args.sources)
    if args.limit:
        urls = urls[: args.limit]

    args.out.mkdir(parents=True, exist_ok=True)
    mapping_path = args.out / "sources.json"
    mapping: dict[str, str] = {}
    if mapping_path.exists():
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))

    fetched = skipped = 0
    failures: list[tuple[str, str]] = []

    with httpx.Client(
        follow_redirects=True,
        timeout=30.0,
        headers={"User-Agent": USER_AGENT},
    ) as client:
        for index, url in enumerate(urls, start=1):
            slug = slug_for(url)
            target = args.out / f"{slug}.md"
            if target.exists() and not args.force:
                skipped += 1
                print(f"[{index}/{len(urls)}] skip   {slug}.md")
                continue

            try:
                text = fetch_one(client, url)
            except (httpx.HTTPError, ValueError) as exc:
                failures.append((url, str(exc)))
                print(f"[{index}/{len(urls)}] FAIL   {url} -> {exc}")
                continue

            target.write_text(text.strip() + "\n", encoding="utf-8")
            mapping[slug] = url
            fetched += 1
            print(f"[{index}/{len(urls)}] ok     {slug}.md ({len(text):,} chars)")
            time.sleep(args.delay)

    mapping_path.write_text(json.dumps(mapping, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\nfetched={fetched} skipped={skipped} failed={len(failures)}")
    if failures:
        print("\nfailed URLs (fix or remove these in the sources file):")
        for url, reason in failures:
            print(f"  - {url}\n    {reason}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
