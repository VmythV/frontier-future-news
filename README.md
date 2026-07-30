# Frontier Future News / 前沿未来技术新闻

A small, evidence-led, bilingual news archive focused on AI agents, embodied AI, and world models.

一个重视一手证据、中英双语呈现的前沿技术新闻集合，聚焦智能体、具身智能与世界模型。

## Focus / 关注方向

- **Agents / 智能体** — planning, reasoning, memory, tool use, computer use, multi-agent systems, evaluation, and safety.
- **Embodied AI / 具身智能** — robot learning, vision-language-action models, manipulation, locomotion, tactile sensing, sim-to-real, and physical AI.
- **World models / 世界模型** — learned dynamics, interactive simulation, predictive control, model-based RL, and spatial-temporal environment generation.

Adjacent ideas such as spatial intelligence, multimodality, robotics hardware, benchmarks, and datasets are represented as tags instead of additional top-level categories.

空间智能、多模态、机器人硬件、评测和数据集等相邻方向使用标签表达，暂不扩展为新的主分类。

## Read the news / 阅读新闻

- [Latest news / 最新新闻](LATEST.md)
- [News archive / 新闻归档](news/index.md)
- [Agents / 智能体](topics/agents.md)
- [Embodied AI / 具身智能](topics/embodied-ai.md)
- [World models / 世界模型](topics/world-models.md)
- [Machine-readable JSON](data/news.json)
- [Machine-readable JSONL](data/news.jsonl)

The collection contains only reviewed entries that pass evidence, duplicate, bilingual-content, and schema checks.

项目只收录经过来源核验、事件去重、双语内容检查和结构校验的新闻，不使用示例假新闻填充归档。

## Use with Codex CLI / 使用 Codex CLI

Start Codex from this repository. Codex discovers the repository-level `curate-frontier-news` Skill under `.agents/skills`.

在本仓库目录中启动 Codex，它会发现 `.agents/skills` 中的 `curate-frontier-news` Skill。

Collect a review-only digest without changing the repository:

```text
$curate-frontier-news 搜索过去 48 小时的 Agent、具身智能和世界模型新闻，先给我候选清单，不要发布。
```

After presenting the digest, the Skill offers four explicit next actions: keep it in the conversation, save it, save and commit it, or save, commit, and push it. No repository files are changed until one of those actions is authorized.

候选清单展示完毕后，Skill 会明确提供四种后续动作：仅保留在对话中、写入保存、保存并提交，或保存、提交并推送。获得对应授权前不会修改仓库文件。

Publish selected items after review:

```text
$curate-frontier-news 将我确认的第 1、3、5 条写入正式新闻库，重建索引并校验，不要推送。
```

Commit and push only when intended:

```text
$curate-frontier-news 校验本次新闻更新，提交并推送到当前远程分支。
```

The Skill defaults to collection-only, does not publish low-confidence leads, and never pushes unless the request explicitly authorizes it.

Skill 默认只收集和预览；低可信度线索不会直接发布，未明确授权时也不会执行推送。

## Deterministic tools / 确定性工具

The bundled scripts use the Python standard library and require no package installation.

内置脚本仅使用 Python 标准库，无需安装第三方依赖。

```bash
# Fetch discovery leads from Hacker News and AIHot.
python3 .agents/skills/curate-frontier-news/scripts/fetch_feeds.py \
  --source all --since-hours 48 --limit 60

# Compare a saved candidate batch with published records.
python3 .agents/skills/curate-frontier-news/scripts/deduplicate.py \
  /path/to/candidates.json

# Validate canonical records and publication thresholds.
python3 .agents/skills/curate-frontier-news/scripts/validate_news.py --strict

# Regenerate JSONL, latest, archive, daily, and topic views.
python3 .agents/skills/curate-frontier-news/scripts/rebuild_index.py

# Check that generated files are current without changing them.
python3 .agents/skills/curate-frontier-news/scripts/rebuild_index.py --check

# Run local tests.
python3 -m unittest discover -s tests
```

## Repository structure / 仓库结构

```text
.
├── .agents/skills/curate-frontier-news/  # Codex curation workflow
├── .github/workflows/validate.yml        # CI validation
├── data/news.json                        # canonical database
├── data/news.jsonl                       # generated agent-friendly feed
├── news/                                 # generated date archive
├── schema/news.schema.json               # public JSON Schema
├── topics/                               # generated topic views
├── LATEST.md                             # generated latest view
└── tests/                                # deterministic tool tests
```

Edit only `data/news.json` when publishing records. The JSONL and Markdown views are generated and carry a warning marker.

发布新闻时只编辑 `data/news.json`。JSONL 与 Markdown 页面均由脚本生成，并包含自动生成标记。

## Editorial rules / 编辑原则

- Discovery feeds are leads, not proof. Prefer official announcements, papers, repositories, model cards, and benchmark pages.
- Merge multiple reports about the same event into one record; preserve community threads as discussion links.
- Store original publication time separately from collection time.
- Write original short summaries in both languages; do not copy article bodies, paper abstracts, or paywalled passages.
- Popularity is only 10% of the score. Evidence and topic relevance have greater weight.

- 聚合源只负责发现线索，不能代替证据；优先核对官方公告、论文、代码仓库、模型卡和评测页面。
- 同一事件的多篇报道合并为一条，社区讨论保留为讨论链接。
- 原始发布时间和采集时间分别记录。
- 中英文摘要均需原创且简短，不复制文章正文、论文摘要或付费内容。
- 热度只占评分的 10%，证据质量和主题相关性权重更高。

## Publish to GitHub / 发布到 GitHub

After creating an empty GitHub repository, configure its remote and push the local `main` branch:

```bash
git remote add origin https://github.com/OWNER/frontier-future-news.git
git push -u origin main
```

The validation workflow runs on pushes and pull requests. A static GitHub Pages site can be added later without changing the canonical news format.

推送和拉取请求会自动运行校验。后续可以在不改变新闻数据格式的前提下增加 GitHub Pages 静态站点。
