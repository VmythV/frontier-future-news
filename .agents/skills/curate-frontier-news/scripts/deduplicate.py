#!/usr/bin/env python3
"""Compare candidate news JSON with the canonical database without mutating it."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from news_common import (
    atomic_write_json,
    candidate_title,
    candidate_url,
    find_repo_root,
    load_items,
    normalize_url,
    title_similarity,
)


def item_label(item: dict[str, Any], fallback: str) -> str:
    value = item.get("id") or candidate_title(item)
    return str(value).strip() or fallback


def find_match(
    candidate: dict[str, Any],
    references: list[tuple[str, dict[str, Any]]],
    threshold: float,
) -> dict[str, Any] | None:
    title = candidate_title(candidate)
    url = candidate_url(candidate)
    normalized = normalize_url(url) if url else ""
    best_title_match: dict[str, Any] | None = None

    for label, reference in references:
        reference_url = candidate_url(reference)
        if normalized and reference_url and normalize_url(reference_url) == normalized:
            return {
                "duplicate_against": label,
                "reason": "canonical-url",
                "similarity": 1.0,
            }
        reference_title = candidate_title(reference)
        if title and reference_title:
            similarity = title_similarity(title, reference_title)
            if similarity >= threshold and (
                best_title_match is None or similarity > best_title_match["similarity"]
            ):
                best_title_match = {
                    "duplicate_against": label,
                    "reason": "near-title",
                    "similarity": round(similarity, 4),
                }
    return best_title_match


def deduplicate_candidates(
    candidates: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    threshold: float = 0.88,
) -> dict[str, Any]:
    references = [(item_label(item, f"existing-{index}"), item) for index, item in enumerate(existing)]
    unique: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []

    for index, candidate in enumerate(candidates):
        label = item_label(candidate, f"candidate-{index}")
        title = candidate_title(candidate)
        url = candidate_url(candidate)
        if not title or not url:
            invalid.append(
                {
                    "candidate": candidate,
                    "reason": "candidate requires a title/title_en and url/source.url",
                }
            )
            continue
        match = find_match(candidate, references, threshold)
        if match:
            duplicates.append({"candidate": candidate, **match})
            continue
        unique.append(candidate)
        references.append((label, candidate))

    return {
        "counts": {
            "input": len(candidates),
            "unique": len(unique),
            "duplicates": len(duplicates),
            "invalid": len(invalid),
        },
        "unique": unique,
        "duplicates": duplicates,
        "invalid": invalid,
    }


def build_parser() -> argparse.ArgumentParser:
    root = find_repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidates", type=Path, help="Candidate JSON array or object with an items array")
    parser.add_argument(
        "--existing",
        type=Path,
        default=root / "data" / "news.json",
        help="Existing canonical database (default: data/news.json)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.88,
        help="Near-title similarity threshold from 0.0 to 1.0 (default: 0.88)",
    )
    parser.add_argument("--output", type=Path, help="Write the JSON report to a file instead of stdout")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not 0.0 <= args.threshold <= 1.0:
        print("ERROR: --threshold must be between 0.0 and 1.0", file=sys.stderr)
        return 2
    try:
        candidates = load_items(args.candidates.resolve())
        existing = load_items(args.existing.resolve())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report = deduplicate_candidates(candidates, existing, args.threshold)
    if args.output:
        atomic_write_json(args.output.resolve(), report)
        print(json.dumps(report["counts"], ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
