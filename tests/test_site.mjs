import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { filterNews, readState, safeUrl } from "../site/news-view.mjs";

const { items } = JSON.parse(
  await readFile(new URL("../data/news.json", import.meta.url), "utf8"),
);

test("archive filters use real bilingual data and include secondary categories", () => {
  const all = filterNews(items, readState(""));
  assert.equal(all.length, items.length);
  assert.ok(
    all.every(
      (item, i) => i === 0 || all[i - 1].published_at >= item.published_at,
    ),
  );
  const embodied = filterNews(items, readState("?category=embodied-ai"));
  assert.ok(embodied.length > 0);
  assert.ok(embodied.every((item) => item.categories.includes("embodied-ai")));
  const chinese = filterNews(
    items,
    readState("?q=" + encodeURIComponent("触觉")),
  );
  assert.ok(
    chinese.some((item) => item.id.endsWith("dexterous-tactile-world-model")),
  );
  assert.ok(filterNews(items, readState("?q=DTWM")).length > 0);
  assert.equal(
    filterNews(items, readState("?q=no-such-project-1234567890")).length,
    0,
  );
});

test("score sorting and shareable filters are deterministic", () => {
  const state = readState("?lang=en&category=agents&sort=score&q=agent");
  assert.equal(state.lang, "en");
  const filtered = filterNews(items, state);
  assert.ok(filtered.length > 0);
  assert.ok(
    filtered.every((item, i) => i === 0 || filtered[i - 1].score >= item.score),
  );
  assert.deepEqual(
    readState("?category=invalid&lang=invalid&sort=invalid"),
    readState(""),
  );
});

test("source links reject executable or malformed URLs", () => {
  assert.equal(safeUrl("javascript:alert(1)"), null);
  assert.equal(safeUrl("data:text/html,test"), null);
  assert.equal(safeUrl("/relative-url"), null);
  assert.equal(
    safeUrl("https://arxiv.org/abs/2609.35750"),
    "https://arxiv.org/abs/2609.35750",
  );
});
