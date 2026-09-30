import {
  CATEGORIES,
  PAGE_SIZE,
  readState,
  filterNews,
  safeUrl,
} from "./news-view.mjs";

const text = {
  zh: {
    skip: "跳转到新闻",
    archiveNav: "新闻档案",
    heroTitle: ["看见", "下一步。"],
    heroDescription: [
      "追踪智能体、具身智能与世界模型的进展。",
      "从一手证据出发，读懂正在发生的未来。",
    ],
    explore: "阅读新闻档案",
    evidenceFirst: "证据优先 · 双语呈现",
    loading: "正在加载新闻…",
    agents: "智能体",
    "embodied-ai": "具身智能",
    "world-models": "世界模型",
    archiveTitle: "前沿观察",
    all: "全部",
    searchLabel: "搜索新闻",
    searchPlaceholder: "搜索标题、技术或项目…",
    sortLabel: "排序方式",
    latest: "最新发布",
    scoreSort: "评分优先",
    reset: "清除筛选",
    loadMore: "继续阅读",
    loadError: "新闻暂时未能加载，请稍后重试。",
    retry: "重新加载",
    aboutTitle: ["信息很多，", "值得关注的更少。"],
    aboutDescription:
      "精选有技术实质的进展。每条新闻保留原始来源、技术要点和评分，方便你继续追问。",
    statLabel: "条已核验新闻",
    updated: "最近收录",
    readingTitle: "关于这份档案",
    readingDescription:
      "评分衡量主题相关性、证据、创新、技术深度与关注度。它是编辑判断，不是模型排行榜。",
    openData: "开放数据",
    footerNote: "保持好奇，也保持求证。",
    viewRepository: "在 GitHub 上查看 ↗",
    technical: "技术要点",
    why: "为什么值得关注",
    source: "阅读原文 ↗",
    evidence: "补充证据",
    discussion: "社区讨论",
    high: "高置信",
    medium: "中等置信",
    low: "低置信",
    score: "评分",
    count: (n) => `${n} 条新闻 · 持续记录`,
    results: (n, shown) => `${n} 条符合条件，已显示 ${shown} 条`,
    noResults: "没有找到匹配的新闻。试试其他关键词或分类。",
    noNews: "档案还没有新闻，欢迎稍后再来。",
  },
  en: {
    skip: "Skip to news",
    archiveNav: "The archive",
    heroTitle: ["See what’s", " next."],
    heroDescription: [
      "Following agents, embodied AI and world models.",
      "Primary sources. Clear context. A future in focus.",
    ],
    explore: "Explore the archive",
    evidenceFirst: "Evidence first · Bilingual by design",
    loading: "Loading the latest news…",
    agents: "Agents",
    "embodied-ai": "Embodied AI",
    "world-models": "World models",
    archiveTitle: "Frontier dispatches",
    all: "All",
    searchLabel: "Search news",
    searchPlaceholder: "Search ideas, projects, or technologies…",
    sortLabel: "Sort news",
    latest: "Newest first",
    scoreSort: "Highest score",
    reset: "Clear filters",
    loadMore: "Keep reading",
    loadError: "News couldn’t load. Please try again in a moment.",
    retry: "Try again",
    aboutTitle: ["More signal.", "Less noise."],
    aboutDescription:
      "A considered collection of technical progress. Every entry includes its original source, technical details and an editorial score.",
    statLabel: "verified entries",
    updated: "Last collected",
    readingTitle: "About the archive",
    readingDescription:
      "Scores reflect relevance, evidence, novelty, technical depth and attention. They are editorial assessments, not model rankings.",
    openData: "Open data",
    footerNote: "Stay curious. Check the evidence.",
    viewRepository: "View on GitHub ↗",
    technical: "Technical points",
    why: "Why it matters",
    source: "Read the source ↗",
    evidence: "More evidence",
    discussion: "Discussion",
    high: "High confidence",
    medium: "Medium confidence",
    low: "Low confidence",
    score: "Score",
    count: (n) => `${n} dispatches · An ongoing record`,
    results: (n, shown) => `${n} matching entries · Showing ${shown}`,
    noResults: "No matching news. Try a different keyword or category.",
    noNews: "The archive is empty. Check back soon.",
  },
};

let state = readState(location.search);
let items = [];
let ready = false;
let hasError = false;
const $ = (id) => document.getElementById(id);
const t = (key) => text[state.lang][key];
const field = (item, key) => item[`${key}_${state.lang}`];

function el(tag, className, value) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (value !== undefined) node.textContent = value;
  return node;
}

function externalLink(url, label) {
  const safe = safeUrl(url);
  if (!safe) return null;
  const link = el("a", "", label);
  link.href = safe;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  return link;
}

function dateLabel(value) {
  return new Intl.DateTimeFormat(state.lang === "zh" ? "zh-CN" : "en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "UTC",
  }).format(new Date(value));
}

function translate() {
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : "en";
  document.title =
    state.lang === "zh"
      ? "Frontier Future — 前沿 AI 新闻"
      : "Frontier Future — An evidence-led AI news archive";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const value = t(node.dataset.i18n);
    if (!Array.isArray(value)) {
      node.textContent = value;
      return;
    }
    node.replaceChildren(document.createTextNode(value[0]));
    if (node.id === "hero-title") node.append(el("span", "", value[1]));
    else
      node.append(
        document.createElement("br"),
        document.createTextNode(value[1]),
      );
  });
  $("language-toggle").textContent = state.lang === "zh" ? "EN ↔" : "中文 ↔";
  $("language-toggle").setAttribute(
    "aria-label",
    state.lang === "zh" ? "Switch to English" : "切换到中文",
  );
  $("search").placeholder = t("searchPlaceholder");
}

function syncUrl() {
  const params = new URLSearchParams();
  if (state.lang === "en") params.set("lang", "en");
  if (state.category !== "all") params.set("category", state.category);
  if (state.query) params.set("q", state.query);
  if (state.sort !== "latest") params.set("sort", state.sort);
  const query = params.toString();
  history.replaceState(
    null,
    "",
    location.pathname + (query ? `?${query}` : "") + location.hash,
  );
}

function renderEntry(item) {
  const entry = el("details", "news-entry");
  entry.id = item.id;
  const summary = el("summary");
  const meta = el("div", "news-meta");
  meta.append(
    el(
      "span",
      "category-label",
      item.categories.map((category) => t(category)).join(" / "),
    ),
  );
  meta.append(el("span", "meta-divider"));
  const date = el("time", "news-date", dateLabel(item.published_at));
  date.dateTime = item.published_at;
  meta.append(
    date,
    el("span", "meta-divider"),
    el("span", "source-name", item.source.name),
  );
  const heading = el("div", "news-heading");
  const title = el("h3", "", field(item, "title"));
  const icon = el("span", "expand-icon", "+");
  icon.setAttribute("aria-hidden", "true");
  heading.append(title, icon);
  summary.append(meta, heading);
  const synopsis = el("p", "news-summary", field(item, "summary"));
  const bottom = el("div", "entry-bottom");
  const tags = el("div", "entry-tags");
  item.tags.slice(0, 3).forEach((tag) => tags.append(el("span", "", tag)));
  const score = el("div", "entry-score");
  score.append(
    el("span", "", t("score")),
    document.createTextNode(`${item.score} / 100`),
  );
  bottom.append(tags, score);
  const more = el("div", "entry-details");
  more.append(el("h4", "detail-title", t("technical")));
  const points = el("ul");
  field(item, "tech_points").forEach((point) =>
    points.append(el("li", "", point)),
  );
  more.append(
    points,
    el("h4", "detail-title", t("why")),
    el("p", "detail-why", field(item, "why_it_matters")),
  );
  const links = el("div", "entry-links");
  const original = externalLink(item.source.url, t("source"));
  if (original) links.append(original);
  item.evidence_urls.forEach((url, index) => {
    const link = externalLink(url, `${t("evidence")} ${index + 1} ↗`);
    if (link) links.append(link);
  });
  item.discussion_urls.forEach((url, index) => {
    const link = externalLink(url, `${t("discussion")} ${index + 1} ↗`);
    if (link) links.append(link);
  });
  links.append(el("span", "confidence", t(item.confidence)));
  more.append(links);
  // Details contents are intentionally hidden until expanded; the synopsis stays visible.
  entry.append(summary, more);
  const article = el("article", "news-article");
  article.append(entry);
  summary.append(synopsis, bottom);
  return article;
}

function render() {
  translate();
  document
    .querySelectorAll(".category-filters [data-category]")
    .forEach((button) =>
      button.setAttribute(
        "aria-pressed",
        String(button.dataset.category === state.category),
      ),
    );
  $("search").value = state.query;
  $("sort").value = state.sort;
  $("error-state").hidden = !hasError;
  $("news-list").setAttribute("aria-busy", String(!ready && !hasError));
  if (!ready) {
    $("results-status").textContent = hasError ? "" : t("loading");
    return;
  }
  $("stat-total").textContent = items.length;
  $("archive-total").textContent = t("count")(items.length);
  const newest = filterNews(items, {
    category: "all",
    query: "",
    sort: "latest",
  })[0];
  if (newest) {
    $("featured-title").textContent = field(newest, "title");
    $("featured-summary").textContent = field(newest, "summary");
    $("featured-date").textContent = newest.published_at.slice(0, 10);
    $("featured-link").href = safeUrl(newest.source.url) || "#archive";
    $("featured-link").target = "_blank";
    $("featured-link").rel = "noopener noreferrer";
    const collected = items
      .map((item) => item.collected_at)
      .sort()
      .at(-1);
    $("updated-date").textContent = dateLabel(collected);
    $("updated-date").dateTime = collected;
  } else {
    $("featured-title").textContent = t("noNews");
    $("featured-summary").textContent = "";
  }
  const filtered = filterNews(items, state);
  const visible = filtered.slice(0, state.limit);
  $("news-list").replaceChildren(...visible.map(renderEntry));
  $("results-status").textContent = t("results")(
    filtered.length,
    visible.length,
  );
  $("empty-state").hidden = filtered.length !== 0;
  $("empty-message").textContent = items.length ? t("noResults") : t("noNews");
  $("load-more").hidden = visible.length >= filtered.length;
}

function update(change) {
  state = { ...state, ...change, limit: PAGE_SIZE };
  syncUrl();
  render();
}

async function loadNews() {
  hasError = false;
  render();
  try {
    const response = await fetch("./data/news.json");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (data.schema_version !== 1 || !Array.isArray(data.items))
      throw new Error("Invalid archive");
    items = data.items;
    ready = true;
  } catch (error) {
    hasError = true;
    console.error("News archive could not be loaded", error);
  }
  render();
}

document.querySelectorAll("[data-category]").forEach((button) =>
  button.addEventListener("click", () => {
    update({ category: button.dataset.category });
    if (button.closest(".topic-strip"))
      $("archive").scrollIntoView({
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
      });
  }),
);
$("language-toggle").addEventListener("click", () =>
  update({ lang: state.lang === "zh" ? "en" : "zh" }),
);
$("search").addEventListener("input", (event) =>
  update({ query: event.target.value }),
);
$("sort").addEventListener("change", (event) =>
  update({ sort: event.target.value }),
);
$("reset-filters").addEventListener("click", () =>
  update({ category: "all", query: "", sort: "latest" }),
);
$("load-more").addEventListener("click", () => {
  state.limit += PAGE_SIZE;
  render();
});
$("retry").addEventListener("click", loadNews);
window.addEventListener("popstate", () => {
  state = readState(location.search);
  render();
});
loadNews();
