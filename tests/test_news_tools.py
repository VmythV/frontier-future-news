from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / ".agents" / "skills" / "curate-frontier-news" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from deduplicate import deduplicate_candidates  # noqa: E402
from fetch_feeds import parse_rss  # noqa: E402
from news_common import is_http_url, normalize_url  # noqa: E402
from rebuild_index import build_outputs  # noqa: E402
from validate_news import validate_items  # noqa: E402


def sample_item(**updates):
    item = {
        "id": "2026-07-30-example-release",
        "published_at": "2026-07-30T09:00:00Z",
        "collected_at": "2026-07-30T12:00:00Z",
        "categories": ["agents"],
        "tags": ["tool-use", "open-source"],
        "title_en": "Example technical release",
        "title_zh": "示例技术发布",
        "summary_en": "An original English summary grounded in linked evidence.",
        "summary_zh": "基于所链接证据撰写的原创中文摘要。",
        "tech_points_en": ["One concrete technical point."],
        "tech_points_zh": ["一项具体技术点。"],
        "why_it_matters_en": "It demonstrates a material agent capability.",
        "why_it_matters_zh": "它展示了一项实质性的智能体能力。",
        "source": {
            "name": "Example Lab",
            "type": "primary",
            "url": "https://example.com/release",
            "language": "en",
        },
        "discussion_urls": [],
        "evidence_urls": ["https://example.com/paper"],
        "confidence": "high",
        "score": 82,
        "score_breakdown": {
            "relevance": 27,
            "evidence": 24,
            "novelty": 15,
            "technical_depth": 11,
            "traction": 5,
        },
    }
    item.update(updates)
    return item


class CommonTests(unittest.TestCase):
    def test_normalize_url_removes_tracking(self):
        self.assertEqual(
            normalize_url("https://www.Example.com/release/?utm_source=x&b=2&a=1#top"),
            "example.com/release?a=1&b=2",
        )

    def test_invalid_port_is_not_a_valid_url(self):
        self.assertFalse(is_http_url("https://example.com:not-a-port/item"))


class ValidationTests(unittest.TestCase):
    def test_valid_item(self):
        errors, warnings = validate_items([sample_item()])
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_duplicate_url_is_rejected(self):
        duplicate = sample_item(
            id="2026-07-30-another-release",
            title_en="A distinct title",
            source={
                "name": "Mirror",
                "type": "media",
                "url": "https://example.com/release/?utm_source=test",
                "language": "en",
            },
        )
        errors, _ = validate_items([sample_item(), duplicate])
        self.assertTrue(any("duplicates items[0]" in error for error in errors))


class DedupeTests(unittest.TestCase):
    def test_candidate_duplicate_and_unique(self):
        candidates = [
            {"title": "Example technical release", "url": "https://example.com/release?utm_campaign=x"},
            {"title": "Different robotics result", "url": "https://robot.example/result"},
        ]
        report = deduplicate_candidates(candidates, [sample_item()])
        self.assertEqual(report["counts"], {"input": 2, "unique": 1, "duplicates": 1, "invalid": 0})


class FeedTests(unittest.TestCase):
    def test_parse_rss(self):
        payload = b"""<?xml version="1.0"?><rss><channel><item>
        <title>Agent &amp; Robot</title><link>https://example.com/a</link>
        <description><![CDATA[<p>A short summary.</p>]]></description>
        <pubDate>Thu, 30 Jul 2026 09:00:00 GMT</pubDate>
        </item></channel></rss>"""
        items = parse_rss(payload, "https://feed.example/rss")
        self.assertEqual(items[0]["title"], "Agent & Robot")
        self.assertEqual(items[0]["published_at"], "2026-07-30T09:00:00Z")


class RenderTests(unittest.TestCase):
    def test_build_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = build_outputs(root, [sample_item()])
            daily = root / "news" / "2026" / "07" / "2026-07-30.md"
            self.assertIn(daily, outputs)
            self.assertIn("示例技术发布", outputs[daily])
            self.assertIn(root / "data" / "news.jsonl", outputs)


if __name__ == "__main__":
    unittest.main()
