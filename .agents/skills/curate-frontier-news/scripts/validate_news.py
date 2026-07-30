#!/usr/bin/env python3
"""Validate the canonical bilingual frontier news database."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from news_common import (
    CATEGORIES,
    CONFIDENCE_LEVELS,
    LANGUAGES,
    SCORE_LIMITS,
    SOURCE_TYPES,
    find_repo_root,
    is_http_url,
    load_json,
    normalize_url,
    parse_iso_datetime,
    title_similarity,
)


REQUIRED_FIELDS = {
    "id",
    "published_at",
    "collected_at",
    "categories",
    "tags",
    "title_en",
    "title_zh",
    "summary_en",
    "summary_zh",
    "tech_points_en",
    "tech_points_zh",
    "why_it_matters_en",
    "why_it_matters_zh",
    "source",
    "discussion_urls",
    "evidence_urls",
    "confidence",
    "score",
    "score_breakdown",
}
ID_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*$")
TAG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _issue(bucket: list[str], location: str, message: str) -> None:
    bucket.append(f"{location}: {message}")


def _validate_string(item: dict[str, Any], field: str, location: str, errors: list[str]) -> None:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        _issue(errors, f"{location}.{field}", "must be a non-empty string")


def _validate_url_list(
    item: dict[str, Any], field: str, location: str, errors: list[str]
) -> None:
    value = item.get(field)
    if not isinstance(value, list):
        _issue(errors, f"{location}.{field}", "must be an array")
        return
    if all(isinstance(entry, str) for entry in value) and len(value) != len(set(value)):
        _issue(errors, f"{location}.{field}", "must not contain duplicate URLs")
    for index, url in enumerate(value):
        if not is_http_url(url):
            _issue(errors, f"{location}.{field}[{index}]", "must be an absolute HTTP(S) URL")


def validate_items(items: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    seen_ids: dict[str, int] = {}
    seen_urls: dict[str, tuple[int, str]] = {}
    seen_titles: list[tuple[int, str, str]] = []

    for index, item in enumerate(items):
        location = f"items[{index}]"
        if not isinstance(item, dict):
            _issue(errors, location, "must be an object")
            continue

        missing = sorted(REQUIRED_FIELDS - item.keys())
        extra = sorted(item.keys() - REQUIRED_FIELDS)
        if missing:
            _issue(errors, location, f"missing fields: {', '.join(missing)}")
        if extra:
            _issue(errors, location, f"unexpected fields: {', '.join(extra)}")

        item_id = item.get("id")
        if not isinstance(item_id, str) or not ID_PATTERN.fullmatch(item_id):
            _issue(errors, f"{location}.id", "must match YYYY-MM-DD-short-english-slug")
            item_id = f"index-{index}"
        elif item_id in seen_ids:
            _issue(errors, f"{location}.id", f"duplicates items[{seen_ids[item_id]}].id")
        else:
            seen_ids[item_id] = index

        parsed_times = {}
        for field in ("published_at", "collected_at"):
            value = item.get(field)
            if not isinstance(value, str):
                _issue(errors, f"{location}.{field}", "must be an ISO 8601 string with timezone")
                continue
            try:
                parsed_times[field] = parse_iso_datetime(value)
            except (TypeError, ValueError) as exc:
                _issue(errors, f"{location}.{field}", f"invalid ISO 8601 timestamp ({exc})")
        if set(parsed_times) == {"published_at", "collected_at"}:
            if parsed_times["collected_at"] < parsed_times["published_at"]:
                _issue(errors, location, "collected_at must not be earlier than published_at")
            if isinstance(item.get("id"), str) and item["id"][:10] != item["published_at"][:10]:
                _issue(warnings, f"{location}.id", "date prefix differs from published_at date")

        categories = item.get("categories")
        if not isinstance(categories, list) or not categories:
            _issue(errors, f"{location}.categories", "must contain at least one category")
        else:
            if all(isinstance(value, str) for value in categories) and len(categories) != len(set(categories)):
                _issue(errors, f"{location}.categories", "must not contain duplicates")
            for category in categories:
                if category not in CATEGORIES:
                    _issue(errors, f"{location}.categories", f"unsupported category: {category!r}")

        tags = item.get("tags")
        if not isinstance(tags, list):
            _issue(errors, f"{location}.tags", "must be an array")
        else:
            if all(isinstance(value, str) for value in tags) and len(tags) != len(set(tags)):
                _issue(errors, f"{location}.tags", "must not contain duplicates")
            for tag in tags:
                if not isinstance(tag, str) or not TAG_PATTERN.fullmatch(tag):
                    _issue(errors, f"{location}.tags", f"invalid lowercase hyphenated tag: {tag!r}")

        for field in (
            "title_en",
            "title_zh",
            "summary_en",
            "summary_zh",
            "why_it_matters_en",
            "why_it_matters_zh",
        ):
            _validate_string(item, field, location, errors)

        for field in ("tech_points_en", "tech_points_zh"):
            points = item.get(field)
            if not isinstance(points, list) or not 1 <= len(points) <= 5:
                _issue(errors, f"{location}.{field}", "must contain one to five strings")
            elif any(not isinstance(point, str) or not point.strip() for point in points):
                _issue(errors, f"{location}.{field}", "must contain only non-empty strings")
        if isinstance(item.get("tech_points_en"), list) and isinstance(item.get("tech_points_zh"), list):
            if len(item["tech_points_en"]) != len(item["tech_points_zh"]):
                _issue(errors, location, "English and Chinese technical-point arrays must have equal length")

        source = item.get("source")
        if not isinstance(source, dict):
            _issue(errors, f"{location}.source", "must be an object")
        else:
            required_source = {"name", "type", "url", "language"}
            missing_source = sorted(required_source - source.keys())
            extra_source = sorted(source.keys() - required_source)
            if missing_source:
                _issue(errors, f"{location}.source", f"missing fields: {', '.join(missing_source)}")
            if extra_source:
                _issue(errors, f"{location}.source", f"unexpected fields: {', '.join(extra_source)}")
            if not isinstance(source.get("name"), str) or not source.get("name", "").strip():
                _issue(errors, f"{location}.source.name", "must be a non-empty string")
            if source.get("type") not in SOURCE_TYPES:
                _issue(errors, f"{location}.source.type", f"must be one of {', '.join(SOURCE_TYPES)}")
            elif source.get("type") in {"community", "aggregator"}:
                _issue(warnings, f"{location}.source.type", "publish against the original source, not a discovery source")
            source_url = source.get("url")
            if not is_http_url(source_url):
                _issue(errors, f"{location}.source.url", "must be an absolute HTTP(S) URL")
            else:
                normalized = normalize_url(source_url)
                if normalized in seen_urls:
                    other_index, other_id = seen_urls[normalized]
                    _issue(errors, f"{location}.source.url", f"duplicates items[{other_index}] ({other_id})")
                else:
                    seen_urls[normalized] = (index, str(item_id))
            if source.get("language") not in LANGUAGES:
                _issue(errors, f"{location}.source.language", f"must be one of {', '.join(LANGUAGES)}")

        _validate_url_list(item, "discussion_urls", location, errors)
        _validate_url_list(item, "evidence_urls", location, errors)

        confidence = item.get("confidence")
        if confidence not in CONFIDENCE_LEVELS:
            _issue(errors, f"{location}.confidence", f"must be one of {', '.join(CONFIDENCE_LEVELS)}")
        elif confidence == "low":
            _issue(warnings, f"{location}.confidence", "low-confidence items should remain candidates")

        score = item.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
            _issue(errors, f"{location}.score", "must be an integer from 0 to 100")
        elif score < 65:
            _issue(warnings, f"{location}.score", "is below the default publication threshold of 65")

        breakdown = item.get("score_breakdown")
        if not isinstance(breakdown, dict):
            _issue(errors, f"{location}.score_breakdown", "must be an object")
        else:
            missing_scores = sorted(SCORE_LIMITS.keys() - breakdown.keys())
            extra_scores = sorted(breakdown.keys() - SCORE_LIMITS.keys())
            if missing_scores:
                _issue(errors, f"{location}.score_breakdown", f"missing fields: {', '.join(missing_scores)}")
            if extra_scores:
                _issue(errors, f"{location}.score_breakdown", f"unexpected fields: {', '.join(extra_scores)}")
            for field, maximum in SCORE_LIMITS.items():
                value = breakdown.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= maximum:
                    _issue(errors, f"{location}.score_breakdown.{field}", f"must be an integer from 0 to {maximum}")
            if all(isinstance(breakdown.get(field), int) and not isinstance(breakdown.get(field), bool) for field in SCORE_LIMITS):
                calculated = sum(breakdown[field] for field in SCORE_LIMITS)
                if isinstance(score, int) and calculated != score:
                    _issue(errors, f"{location}.score", f"must equal score_breakdown sum ({calculated})")

        title = item.get("title_en")
        if isinstance(title, str) and title.strip():
            for other_index, other_id, other_title in seen_titles:
                similarity = title_similarity(title, other_title)
                if similarity >= 0.94:
                    _issue(errors, f"{location}.title_en", f"near-duplicates items[{other_index}] ({other_id}); similarity={similarity:.2f}")
                elif similarity >= 0.88:
                    _issue(warnings, f"{location}.title_en", f"may duplicate items[{other_index}] ({other_id}); similarity={similarity:.2f}")
            seen_titles.append((index, str(item_id), title))

        for field in ("summary_en", "summary_zh"):
            value = item.get(field)
            if isinstance(value, str) and len(value) > 800:
                _issue(warnings, f"{location}.{field}", "is longer than 800 characters; keep news summaries concise")

    return errors, warnings


def validate_database(path: Path) -> tuple[list[str], list[str], int]:
    try:
        payload = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{path}: could not load JSON ({exc})"], [], 0
    if not isinstance(payload, dict):
        return [f"{path}: root must be an object"], [], 0
    errors: list[str] = []
    if set(payload) != {"schema_version", "items"}:
        errors.append(f"{path}: root fields must be exactly schema_version and items")
    if payload.get("schema_version") != 1:
        errors.append(f"{path}: schema_version must equal 1")
    items = payload.get("items")
    if not isinstance(items, list):
        errors.append(f"{path}: items must be an array")
        return errors, [], 0
    item_errors, warnings = validate_items(items)
    errors.extend(item_errors)
    return errors, warnings, len(items)


def build_parser() -> argparse.ArgumentParser:
    root = find_repo_root()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=root / "data" / "news.json",
        help="Canonical news database (default: data/news.json)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as validation failures for publication checks",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors, warnings, count = validate_database(args.input.resolve())
    for message in errors:
        print(f"ERROR: {message}", file=sys.stderr)
    for message in warnings:
        print(f"WARNING: {message}", file=sys.stderr)
    if errors or (args.strict and warnings):
        print(
            f"Validation failed: {len(errors)} error(s), {len(warnings)} warning(s), {count} item(s)",
            file=sys.stderr,
        )
        return 1
    print(f"Validated {count} news item(s): {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
