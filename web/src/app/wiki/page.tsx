import type { Metadata } from "next";
import Link from "next/link";
import { listPages } from "@/lib/wiki-fs";
import { layerDescription, layerLabel, layerRank } from "@/lib/wiki-ui";
import { siteConfig } from "@/lib/site-config";

export const metadata: Metadata = {
  title: `Browse — ${siteConfig.title}`,
};

/**
 * Browse landing — the RIGHT pane of the `/wiki` two-pane shell. The heavy
 * per-page navigation lives in the persistent sidebar (see `layout.tsx`); this
 * surface is a clean overview: a title, the corpus size, and a compact grid of
 * layer sections, each linking to its first page. A SERVER component reading the
 * filesystem via `listPages()`, so it works with NO RAG backend.
 */
export default function BrowsePage() {
  const pages = listPages();

  const groups = new Map<string, typeof pages>();
  for (const p of pages) {
    const key = p.layer || "";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(p);
  }
  const ordered = [...groups.entries()].sort(
    ([a], [b]) => layerRank(a) - layerRank(b) || a.localeCompare(b),
  );

  return (
    <div className="mx-auto w-full max-w-[820px] px-6 py-9 pt-14 lg:px-10 lg:pt-9">
      <header className="mb-7 border-b border-zinc-200/70 pb-5 dark:border-white/10">
        <h1 className="text-[33px] font-bold leading-tight tracking-tight text-[#1f1f1f] dark:text-zinc-50">
          Browse
        </h1>
        <p className="mt-2 text-[14px] text-zinc-500 dark:text-zinc-400">
          {pages.length} page{pages.length === 1 ? "" : "s"} across{" "}
          {ordered.length} section{ordered.length === 1 ? "" : "s"}. Pick a
          section below, use the sidebar, or{" "}
          <Link
            href="/search"
            className="text-[#0b57d0] hover:underline dark:text-[#a8c7fa]"
          >
            search the wiki
          </Link>
          .
        </p>
      </header>

      {pages.length === 0 ? (
        <div className="rounded-xl border border-zinc-200 bg-zinc-50 px-4 py-6 text-sm text-zinc-600 dark:border-white/10 dark:bg-white/5 dark:text-zinc-300">
          <p className="font-medium">No wiki pages found.</p>
          <p className="mt-1 opacity-80">
            Point{" "}
            <code className="rounded bg-zinc-100 px-1 dark:bg-zinc-800">
              WIKI_DIR
            </code>{" "}
            at a wiki directory (default{" "}
            <code className="rounded bg-zinc-100 px-1 dark:bg-zinc-800">
              ../wiki
            </code>
            ).
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {ordered.map(([layer, items]) => {
            const first = items[0];
            const desc = layerDescription(layer);
            return (
              <Link
                key={layer || "other"}
                href={first ? `/wiki/${encodeURIComponent(first.slug)}` : "/wiki"}
                className="group flex flex-col rounded-xl border border-zinc-200/80 bg-[#f7f8fa] p-4 shadow-[0_1px_2px_rgba(0,0,0,.04)] transition-colors hover:border-[#4285f4]/40 hover:bg-[#eef3fe] dark:border-white/10 dark:bg-[#1c1e22] dark:hover:border-[#5c9aff]/40 dark:hover:bg-white/5"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[15px] font-semibold text-[#1f1f1f] group-hover:text-[#0b57d0] dark:text-zinc-100 dark:group-hover:text-[#a8c7fa]">
                    {layerLabel(layer)}
                  </span>
                  <span className="rounded-full border border-zinc-200 bg-[#fdfcfc] px-2 py-0.5 text-[11.5px] font-medium text-zinc-500 dark:border-white/10 dark:bg-[#16171a] dark:text-zinc-400">
                    {items.length}
                  </span>
                </div>
                {desc && (
                  <p className="mt-1.5 text-[13px] leading-snug text-zinc-500 dark:text-zinc-400">
                    {desc}
                  </p>
                )}
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
