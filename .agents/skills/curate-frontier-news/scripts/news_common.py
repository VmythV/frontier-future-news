#!/usr/bin/env python3
"""Shared, dependency-free helpers for the frontier news skill."""

from __future__ import annotations

import json
import os
import re
import tempfile
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit


CATEGORIES = ("agents", "embodied-ai", "world-models")
CATEGORY_LABELS = {
    "agents": "Agents / 智能体",
    "embodied-ai": "Embodied AI / 具身智能",
    "world-models": "World models / 世界模型",
}
SOURCE_TYPES = ("primary", "research", "media", "community", "aggregator")
LANGUAGES = ("en", "zh", "other")
CONFIDENCE_LEVELS = ("high", "medium", "low")
SCORE_LIMITS = {
    "relevance": 30,
    "evidence": 25,
    "novelty": 20,
    "technical_depth": 15,
    "traction": 10,
}

TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "ref_src",
    "source",
}


def find_repo_root(start: Path | None = None) -> Path:
    """Find the closest repository root from a file or directory."""
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "data" / "news.json").is_file() or (candidate / ".git").is_dir():
            return candidate
    raise RuntimeError("Could not find the frontier-future-news repository root")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_items(path: Path) -> list[dict[str, Any]]:
    """Load canonical database, candidate wrapper, or a bare candidate array."""
    payload = load_json(path)
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
        items = payload["items"]
    else:
        raise ValueError(f"{path}: expected a JSON array or an object with an items array")
    if not all(isinstance(item, dict) for item in items):
        raise ValueError(f"{path}: every item must be a JSON object")
    return items


def atomic_write_text(path: Path, content: str) -> bool:
    """Atomically update text and return whether the file changed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return False
    handle, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise
    return True


def atomic_write_json(path: Path, payload: Any) -> bool:
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return atomic_write_text(path, content)


def parse_iso_datetime(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone is required")
    return parsed


def is_http_url(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = urlsplit(value)
        _ = parsed.port
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.hostname)


def normalize_url(value: str) -> str:
    """Return a comparison key with tracking parameters and fragments removed."""
    try:
        parsed = urlsplit(value.strip())
        hostname = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError:
        return value.strip().casefold()
    if hostname.startswith("www."):
        hostname = hostname[4:]
    if port and not ((parsed.scheme == "http" and port == 80) or (parsed.scheme == "https" and port == 443)):
        hostname = f"{hostname}:{port}"
    path = re.sub(r"/{2,}", "/", parsed.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query = []
    for key, item_value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered.startswith("utm_") or lowered in TRACKING_QUERY_KEYS:
            continue
        query.append((key, item_value))
    query.sort()
    suffix = f"?{urlencode(query, doseq=True)}" if query else ""
    return f"{hostname}{path}{suffix}"


def normalize_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower()
    normalized = re.sub(r"^(show|ask|launch)\s+hn\s*:\s*", "", normalized)
    normalized = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", " ", normalized)
    return " ".join(normalized.split())


def title_similarity(left: str, right: str) -> float:
    left_normalized = normalize_title(left)
    right_normalized = normalize_title(right)
    if not left_normalized or not right_normalized:
        return 0.0
    sequence_score = SequenceMatcher(None, left_normalized, right_normalized).ratio()
    left_tokens = set(left_normalized.split())
    right_tokens = set(right_normalized.split())
    union = left_tokens | right_tokens
    token_score = len(left_tokens & right_tokens) / len(union) if union else 0.0
    return max(sequence_score, token_score)


def candidate_title(item: dict[str, Any]) -> str:
    return str(item.get("title_en") or item.get("title") or "").strip()


def candidate_url(item: dict[str, Any]) -> str:
    direct = item.get("url")
    if isinstance(direct, str):
        return direct.strip()
    source = item.get("source")
    if isinstance(source, dict) and isinstance(source.get("url"), str):
        return source["url"].strip()
    return ""


def markdown_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
