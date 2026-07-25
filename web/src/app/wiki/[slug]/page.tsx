import Link from "next/link";
import { WikiMarkdown, WIKI_PROSE_CLASS } from "@/components/wiki-markdown";
import { WikiToc } from "@/components/wiki-toc";
import { getPage, listPages, type WikiPageFull } from "@/lib/wiki-fs";
import { layerLabel } from "@/lib/wiki-ui";

/**
 * Wiki page viewer — a SERVER component that reads the page from the filesystem
 * (`getPage`), so browsing works with NO RAG backend running. If the slug is not
 * found on disk AND an API base is configured (`NEXT_PUBLIC_API_URL` or
 * `NEXT_PUBLIC_BACKEND_PORT`), it falls back to fetching `/api/page/{slug}` so a
 * deployed instance can still resolve backend-only pages.
 *
 * The markdown is rendered through the shared client renderer ({@link WikiMarkdown}),
 * so `[[wikilinks]]`, callouts, and LaTeX all work and internal links keep the
 * chat runtime mounted across navigation.
 */

/** Resolve a configured backend base URL for server-side fallback, or null. */
function configuredApiBase(): string | null {
  const explicit = process.env.NEXT_PUBLIC_API_URL;
  if (explicit) return explicit.replace(/\/$/, "");
  const port = process.env.NEXT_PUBLIC_BACKEND_PORT;
  if (port) return `http://localhost:${port}`;
  return null;
}

async function fetchFromApi(slug: string): Promise<WikiPageFull | null> {
  const base = configuredApiBase();
  if (!base) return null;
  try {
    // Use a cached fetch: an uncached (`no-store`) fetch flips this statically
    // generated route to dynamic at runtime, which Next 16 rejects with a 500.
    // `force-cache` keeps the on-demand render static-compatible while still
    // resolving backend-only slugs (e.g. raw papers) when the API is reachable.
    const res = await fetch(`${base}/api/page/${encodeURIComponent(slug)}`, {
      cache: "force-cache",
    });
    if (!res.ok) return null;
    const page = (await res.json()) as Partial<WikiPageFull>;
    return {
      slug,
      path: page.path ?? "",
      layer: page.layer ?? "",
      title: page.title ?? slug,
      type: page.type ?? "",
      status: page.status ?? "",
      markdown: page.markdown ?? "",
      found: page.found ?? Boolean(page.markdown),
    };
  } catch {
    return null;
  }
}

/** Prerender every filesystem page so wiki views are static. */
export function generateStaticParams() {
  return listPages().map((p) => ({ slug: p.slug }));
}

export default async function WikiPageView({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;

  let page = getPage(slug);
  if (!page.found) {
    const fromApi = await fetchFromApi(slug);
    if (fromApi) page = fromApi;
  }

  if (!page.found) {
    return (
      <div className="mx-auto w-full max-w-[760px] px-6 py-12 pt-16 lg:px-10 lg:pt-12">
        <h1 className="text-2xl font-semibold">Page not found</h1>
        <p className="mt-3 text-zinc-600 dark:text-zinc-400">
          No wiki page matches the slug{" "}
          <code className="rounded bg-zinc-100 px-1.5 py-0.5 text-[13px] dark:bg-zinc-800">
            {slug}
          </code>
          .
        </p>
        <p className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">
          <Link
            href="/wiki"
            className="text-[#0b57d0] underline dark:text-[#a8c7fa]"
          >
            Browse all pages
          </Link>
        </p>
      </div>
    );
  }

  const layer = page.layer;

  return (
    // Center reading column (~720px measure) + right slim "On this page" TOC
    // (~200px, desktop only). Both live inside the persistent `/wiki` shell.
    <div className="mx-auto flex w-full max-w-[1000px] gap-8 px-6 pt-14 lg:px-10 lg:pt-0">
      <article
        id="wiki-article"
        className="min-w-0 max-w-[720px] flex-1 py-8 lg:py-9"
      >
        <nav className="mb-4 flex flex-wrap items-center gap-1.5 text-[12.5px] text-zinc-500 dark:text-zinc-400">
          <Link href="/wiki" className="hover:text-[#0b57d0] dark:hover:text-[#a8c7fa]">
            Browse
          </Link>
          {layer && (
            <>
              <span className="opacity-55">/</span>
              <Link
                href={`/wiki/${encodeURIComponent(slug)}`}
                className="hover:text-[#0b57d0] dark:hover:text-[#a8c7fa]"
              >
                {layerLabel(layer)}
              </Link>
            </>
          )}
          <span className="opacity-55">/</span>
          <span className="font-medium text-zinc-700 dark:text-zinc-200">
            {page.title || slug}
          </span>
        </nav>

        <h1 className="mb-3.5 text-[33px] font-bold leading-[1.18] tracking-tight text-[#1f1f1f] dark:text-zinc-50">
          {page.title || slug}
        </h1>

        <div className="mb-7 flex flex-wrap items-center gap-2">
          {layer && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-200 bg-[#f7f8fa] px-2.5 py-0.5 text-[12px] font-medium text-zinc-700 dark:border-white/10 dark:bg-[#1c1e22] dark:text-zinc-200">
              <span className="h-1.5 w-1.5 rounded-full bg-[#4285f4]" />
              {layerLabel(layer)}
            </span>
          )}
          {page.type && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-zinc-200 bg-[#f7f8fa] px-2.5 py-0.5 text-[12px] font-medium text-zinc-700 dark:border-white/10 dark:bg-[#1c1e22] dark:text-zinc-200">
              <span className="h-1.5 w-1.5 rounded-full bg-[#a855f7]" />
              {page.type}
            </span>
          )}
          {page.status && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-[#1a7f37]/25 bg-[#1a7f37]/[.07] px-2.5 py-0.5 text-[12px] font-medium text-[#1a7f37] dark:border-[#5fd089]/25 dark:bg-[#5fd089]/10 dark:text-[#5fd089]">
              <span className="h-1.5 w-1.5 rounded-full bg-current" />
              {page.status}
            </span>
          )}
        </div>

        <div className={WIKI_PROSE_CLASS}>
          <WikiMarkdown>{page.markdown}</WikiMarkdown>
        </div>
      </article>

      <aside className="sticky top-0 hidden h-[calc(100vh-3rem)] w-[200px] shrink-0 self-start overflow-y-auto py-9 xl:block">
        <WikiToc />
      </aside>
    </div>
  );
}
