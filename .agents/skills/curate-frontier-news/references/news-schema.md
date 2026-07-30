# News record schema

Treat `data/news.json` as the canonical database. It contains `schema_version: 1` and an `items` array. `data/news.jsonl`, `LATEST.md`, `news/`, and `topics/` are generated outputs.

## Required record

```json
{
  "id": "2026-07-30-example-release",
  "published_at": "2026-07-30T09:00:00Z",
  "collected_at": "2026-07-30T12:00:00Z",
  "categories": ["agents"],
  "tags": ["tool-use", "open-source"],
  "title_en": "Example technical release",
  "title_zh": "示例技术发布",
  "summary_en": "An original English summary grounded in the linked evidence.",
  "summary_zh": "基于所链接证据撰写的原创中文摘要。",
  "tech_points_en": ["One concrete technical point."],
  "tech_points_zh": ["一项具体技术点。"],
  "why_it_matters_en": "A concise explanation of the likely technical significance.",
  "why_it_matters_zh": "对其潜在技术意义的简要说明。",
  "source": {
    "name": "Example Lab",
    "type": "primary",
    "url": "https://example.com/release",
    "language": "en"
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
    "traction": 5
  }
}
```

The example shows structure only. Never publish it as news.

## Field rules

- `id`: stable lowercase ID in `YYYY-MM-DD-short-english-slug` form. Do not change it after publication.
- `published_at`, `collected_at`: ISO 8601 timestamps with a timezone. Prefer UTC with `Z`.
- `categories`: one or more values from `agents`, `embodied-ai`, and `world-models`.
- `tags`: unique lowercase hyphenated English terms.
- bilingual fields: original prose, non-empty, factually equivalent, and concise.
- `tech_points_en` and `tech_points_zh`: paired arrays of one to five items with equal length.
- `source.type`: one of `primary`, `research`, `media`, `community`, or `aggregator`.
- `source.language`: `en`, `zh`, or `other`.
- `discussion_urls`: HN, Reddit, forum, or social discussion links.
- `evidence_urls`: additional evidence beyond `source.url`; use an empty array when the primary source alone is sufficient.
- `confidence`: `high`, `medium`, or `low`. Default publication threshold excludes `low`.
- `score`: integer sum of all five score components.

## Scoring rubric

- `relevance` (0-30): directness and importance to the three primary topics.
- `evidence` (0-25): quality, directness, and corroboration of sources.
- `novelty` (0-20): new capability, result, method, dataset, benchmark, or deployment rather than recycled commentary.
- `technical_depth` (0-15): amount of inspectable technical substance.
- `traction` (0-10): credible adoption or expert/community attention. Keep this the smallest component.

Publish at 65 or above by default. A high total cannot compensate for missing evidence or no topical fit.

## Candidate files

Feed output and temporary candidate lists do not need to match the canonical schema. Before publication, transform each selected candidate into the complete record, verify every URL and timestamp, run duplicate detection, and validate the database.
