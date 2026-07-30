#!/usr/bin/env python3
"""Fetch Hacker News and AIHot discovery leads as normalized JSON."""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from news_common import normalize_url


USER_AGENT = "frontier-future-news/0.1 (bilingual news curation)"
HN_API = "https://hacker-news.firebaseio.com/v0"
AIHOT_FEEDS = {
    "curated": "https://aihot.tech/feed.xml",
    "all": "https://aihot.tech/feed/all.xml",
    "daily": "https://aihot.tech/feed/daily.xml",
}


def fetch_bytes(url: str, timeout: float) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.1"})
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def fetch_json(url: str, timeout: float) -> Any:
    return json.loads(fetch_bytes(url, timeout).decode("utf-8"))


def clean_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", html.unescape(value or ""))
    return " ".join(without_tags.split())


def utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_rss(payload: bytes, feed_url: str) -> list[dict[str, Any]]:
    root = ElementTree.fromstring(payload)
    items: list[dict[str, Any]] = []
    for node in root.findall(".//item"):
        title = clean_html(node.findtext("title", default=""))
        link = (node.findtext("link", default="") or "").strip()
        description = clean_html(node.findtext("description", default=""))
        published_raw = (node.findtext("pubDate", default="") or "").strip()
        if not title or not link:
            continue
        try:
            published_at = utc_iso(parsedate_to_datetime(published_raw))
        except (TypeError, ValueError):
            published_at = None
        items.append(
            {
                "discovered_via": "aihot",
                "title": title,
                "url": link,
                "summary": description,
                "published_at": published_at,
                "feed_url": feed_url,
            }
        )
    return items


def fetch_aihot(feed_name: str, timeout: float) -> list[dict[str, Any]]:
    feed_url = AIHOT_FEEDS[feed_name]
    return parse_rss(fetch_bytes(feed_url, timeout), feed_url)


def fetch_hn_story(story_id: int, timeout: float) -> dict[str, Any] | None:
    item = fetch_json(f"{HN_API}/item/{story_id}.json", timeout)
    if not isinstance(item, dict) or item.get("type") != "story" or item.get("dead") or item.get("deleted"):
        return None
    discussion_url = f"https://news.ycombinator.com/item?id={story_id}"
    url = item.get("url") or discussion_url
    title = clean_html(str(item.get("title") or ""))
    if not title:
        return None
    timestamp = item.get("time")
    published_at = utc_iso(datetime.fromtimestamp(timestamp, tz=timezone.utc)) if isinstance(timestamp, int) else None
    return {
        "discovered_via": "hacker-news",
        "title": title,
        "url": url,
        "discussion_url": discussion_url,
        "published_at": published_at,
        "metrics": {
            "score": item.get("score", 0),
            "comments": item.get("descendants", 0),
        },
    }


def fetch_hn(list_name: str, limit: int, timeout: float) -> list[dict[str, Any]]:
    story_ids = fetch_json(f"{HN_API}/{list_name}.json", timeout)
    if not isinstance(story_ids, list):
        raise ValueError(f"Unexpected Hacker News {list_name} response")
    selected_ids = [story_id for story_id in story_ids[:limit] if isinstance(story_id, int)]
    stories: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch_hn_story, story_id, timeout) for story_id in selected_ids]
        for future in concurrent.futures.as_completed(futures):
            story = future.result()
            if story:
                stories.append(story)
    return stories


def item_datetime(item: dict[str, Any]) -> datetime | None:
    value = item.get("published_at")
    if not isinstance(value, str):
        return None
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def filter_items(
    items: list[dict[str, Any]],
    since_hours: int,
    queries: list[str],
    now: datetime,
) -> list[dict[str, Any]]:
    cutoff = now - timedelta(hours=since_hours)
    lowered_queries = [query.casefold() for query in queries if query.strip()]
    selected: list[dict[str, Any]] = []
    for item in items:
        published = item_datetime(item)
        if published and published < cutoff:
            continue
        haystack = f"{item.get('title', '')} {item.get('summary', '')}".casefold()
        if lowered_queries and not any(query in haystack for query in lowered_queries):
            continue
        selected.append(item)
    return selected


def deduplicate_discovery(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for item in items:
        url = str(item.get("url") or "")
        key = normalize_url(url) if url else str(item.get("title") or "").casefold()
        current = selected.get(key)
        if current is None:
            selected[key] = item
            continue
        discovery = set(str(current.get("discovered_via", "")).split(","))
        discovery.add(str(item.get("discovered_via", "")))
        current["discovered_via"] = ",".join(sorted(value for value in discovery if value))
        if item.get("discussion_url") and not current.get("discussion_url"):
            current["discussion_url"] = item["discussion_url"]
    return list(selected.values())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=("hn", "aihot", "all"), default="all")
    parser.add_argument("--hn-list", choices=("newstories", "topstories", "beststories"), default="newstories")
    parser.add_argument("--aihot-feed", choices=tuple(AIHOT_FEEDS), default="all")
    parser.add_argument("--since-hours", type=int, default=48)
    parser.add_argument("--limit", type=int, default=60, help="Maximum HN IDs fetched and final items returned")
    parser.add_argument("--query", action="append", default=[], help="Keep items containing this text; repeat as needed")
    parser.add_argument("--timeout", type=float, default=15.0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.since_hours <= 0 or args.limit <= 0 or args.timeout <= 0:
        print("ERROR: --since-hours, --limit, and --timeout must be positive", file=sys.stderr)
        return 2

    now = datetime.now(timezone.utc)
    items: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    operations = []
    if args.source in {"hn", "all"}:
        operations.append(("hacker-news", lambda: fetch_hn(args.hn_list, args.limit, args.timeout)))
    if args.source in {"aihot", "all"}:
        operations.append(("aihot", lambda: fetch_aihot(args.aihot_feed, args.timeout)))

    for name, operation in operations:
        try:
            items.extend(operation())
        except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError, ElementTree.ParseError) as exc:
            errors.append({"source": name, "error": str(exc)})

    items = filter_items(items, args.since_hours, args.query, now)
    items = deduplicate_discovery(items)
    items.sort(key=lambda item: item_datetime(item) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    items = items[: args.limit]
    payload = {
        "fetched_at": utc_iso(now),
        "lookback_hours": args.since_hours,
        "counts": {"items": len(items), "source_errors": len(errors)},
        "errors": errors,
        "items": items,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 1 if errors and not items else 0


if __name__ == "__main__":
    raise SystemExit(main())
