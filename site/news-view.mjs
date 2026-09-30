export const CATEGORIES = ["agents", "embodied-ai", "world-models"];
export const PAGE_SIZE = 12;

export function readState(search) {
  const params = new URLSearchParams(search);
  return {
    lang: params.get("lang") === "en" ? "en" : "zh",
    category: CATEGORIES.includes(params.get("category"))
      ? params.get("category")
      : "all",
    query: params.get("q") || "",
    sort: params.get("sort") === "score" ? "score" : "latest",
    limit: PAGE_SIZE,
  };
}

export function filterNews(items, state) {
  const query = state.query.trim().toLocaleLowerCase();
  return items
    .filter(
      (item) =>
        (state.category === "all" ||
          item.categories.includes(state.category)) &&
        (!query ||
          [
            item.title_zh,
            item.title_en,
            item.summary_zh,
            item.summary_en,
            item.source.name,
            ...item.tags,
            ...item.tech_points_zh,
            ...item.tech_points_en,
          ]
            .join(" ")
            .toLocaleLowerCase()
            .includes(query)),
    )
    .sort(
      (a, b) =>
        (state.sort === "score" ? b.score - a.score : 0) ||
        b.published_at.localeCompare(a.published_at) ||
        b.id.localeCompare(a.id),
    );
}

export function safeUrl(value) {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : null;
  } catch {
    return null;
  }
}
