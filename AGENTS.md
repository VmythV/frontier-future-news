# Repository guidance

## Purpose

Maintain a verified bilingual archive about AI agents, embodied AI, and world models.

## Canonical and generated files

- Treat `data/news.json` as the only canonical news database.
- Treat `data/news.jsonl`, `LATEST.md`, `news/**/*.md`, and `topics/*.md` as generated files.
- Rebuild generated files with `.agents/skills/curate-frontier-news/scripts/rebuild_index.py`; do not edit them manually.
- Keep records compatible with `schema/news.schema.json` and the stricter publication validator.

## Editorial requirements

- Verify every record against a primary source or two credible independent sources.
- Keep discovery services, aggregators, HN posts, and Reddit posts as leads or discussion links rather than sole proof.
- Publish concise original Chinese and English summaries; do not reproduce source text.
- Deduplicate by canonical URL and underlying event.
- Use only the primary categories `agents`, `embodied-ai`, and `world-models`.
- Do not publish low-confidence items or scores below 65 unless the user explicitly changes the editorial policy.

## Required checks

Run these after changing news data or curation tooling:

```bash
python3 .agents/skills/curate-frontier-news/scripts/validate_news.py --strict
python3 .agents/skills/curate-frontier-news/scripts/rebuild_index.py --check
python3 -m unittest discover -s tests
git diff --check
```

## Git safety

- Preserve unrelated user changes.
- Commit only when requested or when the task explicitly includes publication through Git.
- Push only with explicit authorization and only after inspecting the configured remote and current branch.
