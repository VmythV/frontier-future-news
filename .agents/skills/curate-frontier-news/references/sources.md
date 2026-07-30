# Source and verification policy

Discovery answers "what may have happened." Evidence answers "what can be published." Never treat those as the same step.

## Source priority

1. **Primary evidence**: official laboratory or company posts, papers, repositories, release notes, model cards, project pages, benchmark pages, and recorded technical demonstrations.
2. **Independent reporting**: technically credible reporting that identifies sources and adds verifiable context.
3. **Research indexes**: arXiv, conference proceedings, Semantic Scholar, Papers with Code, and institutional publication pages. Prefer the paper or project page as the final URL.
4. **Community discovery**: Hacker News and Reddit. Preserve valuable discussions, but do not use votes or comments as proof.
5. **Aggregators**: AIHot and similar feeds. Use them to find leads only, because duplicates, stale entries, classification errors, or truncated summaries can occur.

## Web search

Search a rolling time window and use queries specific enough to avoid generic AI coverage. Combine topic terms with words such as `release`, `paper`, `benchmark`, `model`, `dataset`, `robot`, `demo`, or `open source`. Search for the named organization or project again to find its primary page.

When search results conflict, prefer the primary source for what was released and use independent reporting only for clearly attributed context.

## Hacker News

Use the official Firebase API for current lists and item metadata:

- `https://hacker-news.firebaseio.com/v0/newstories.json`
- `https://hacker-news.firebaseio.com/v0/topstories.json`
- `https://hacker-news.firebaseio.com/v0/beststories.json`
- `https://hacker-news.firebaseio.com/v0/item/<id>.json`

Use the story's external URL as the candidate source and `https://news.ycombinator.com/item?id=<id>` as a discussion URL. Scores and comment counts are time-sensitive discovery metrics, not evidence-quality scores.

## Reddit

Search only focused communities, initially:

- `r/MachineLearning`
- `r/LocalLLaMA`
- `r/robotics`
- `r/singularity` only for discovery, with a high verification threshold

Prefer web search with `site:reddit.com/r/<community>` when no authorized Reddit integration exists. Respect current Reddit access rules and rate limits. Do not scrape around authentication, blocks, or robots controls. A post linking to a paper or release should resolve to that primary source; retain the Reddit URL only in `discussion_urls`.

## AIHot

Use the public feeds as discovery inputs:

- curated: `https://aihot.tech/feed.xml`
- all items: `https://aihot.tech/feed/all.xml`
- daily: `https://aihot.tech/feed/daily.xml`

Expect duplicated URLs, multiple versions of the same HN story, and occasional off-topic items. Always deduplicate and open the original link.

## Publication evidence rules

- Accept a direct primary source on its own when it clearly supports the record.
- Otherwise require two credible, independent sources that agree on the material facts.
- Use `confidence: high` for clear primary evidence, `medium` for well-corroborated secondary evidence, and `low` only in candidate digests. Do not publish low-confidence records by default.
- Keep summaries original and short. Do not copy article paragraphs, paywalled text, paper abstracts, or social posts.
- Distinguish an announcement date, paper submission date, repository release date, and reporting date. Store the date associated with the event described by the record and explain ambiguity in the summary when material.
