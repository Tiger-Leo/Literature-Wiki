"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Search as SearchIcon } from "lucide-react";
import MiniSearch from "minisearch";
import { CHIP_CLASS, layerLabel } from "@/lib/wiki-ui";
import { siteConfig } from "@/lib/site-config";

/** One page record in `/wiki-index.json` (built by `scripts/export_wiki.py`). */
type IndexPage = {
  slug: string;
  path: string;
  layer: string;
  title: string;
  type: string;
  status: string;
  tags?: string[];
  papers?: string[];
  headings?: string[];
  wikilinks_out?: string[];
  excerpt?: string;
  text?: string;
};

type WikiIndex = {
  generated_at?: string;
  wiki_title?: string;
  count?: number;
  pages: IndexPage[];
};

type LoadState =
  | { kind: "loading" }
  | { kind: "missing" }
  | { kind: "error"; message: string }
  | { kind: "ready"; pages: Map<string, IndexPage>; mini: MiniSearch };

/** Build an excerpt snippet, highlighting matched query terms. */
function snippet(page: IndexPage, query: string): React.ReactNode {
  const source = page.excerpt || page.text || "";
  if (!source) return null;
  const terms = query
    .toLowerCase()
    .split(/\s+/)
    .map((t) => t.replace(/[^\p{L}\p{N}]/gu, ""))
    .filter((t) => t.length > 1);

  // Center the snippet on the first matched term when possible.
  let text = source;
  if (terms.length) {
    const lower = source.toLowerCase();
    const hit = terms
      .map((t) => lower.indexOf(t))
      .filter((i) => i >= 0)
      .sort((a, b) => a - b)[0];
    if (hit !== undefined && hit > 80) {
      text = "…" + source.slice(hit - 60);
    }
  }
  text = text.slice(0, 260);
  if (text.length >= 260) text = text + "…";

  if (!terms.length) return <span>{text}</span>;
  const re = new RegExp(
    `(${terms.map((t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`,
    "gi",
  );
  const parts = text.split(re);
  return (
    <span>
      {parts.map((part, i) =>
        terms.includes(part.toLowerCase()) ? (
          <mark
            key={i}
            className="rounded bg-yellow-100 px-0.5 text-inherit dark:bg-yellow-500/30"
          >
            {part}
          </mark>
        ) : (
          <span key={i}>{part}</span>
        ),
      )}
    </span>
  );
}

export default function SearchPage() {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  const [raw, setRaw] = useState("");
  const [query, setQuery] = useState("");
  const [layerFilter, setLayerFilter] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load + index the wiki index on mount.
  useEffect(() => {
    let cancelled = false;
    fetch("/wiki-index.json", { cache: "no-store" })
      .then(async (res) => {
        if (res.status === 404) throw new Error("__MISSING__");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return (await res.json()) as WikiIndex;
      })
      .then((data) => {
        if (cancelled) return;
        const pages = new Map(data.pages.map((p) => [p.slug, p]));
        const mini = new MiniSearch<IndexPage>({
          idField: "slug",
          fields: ["title", "text", "headings", "tags"],
          storeFields: ["slug"],
          extractField: (doc, field) => {
            const v = (doc as unknown as Record<string, unknown>)[field];
            return Array.isArray(v) ? v.join(" ") : ((v as string) ?? "");
          },
          searchOptions: {
            boost: { title: 3, headings: 1.5, tags: 1.5 },
            fuzzy: 0.2,
            prefix: true,
          },
        });
        mini.addAll(data.pages);
        setState({ kind: "ready", pages, mini });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof Error && err.message === "__MISSING__") {
          setState({ kind: "missing" });
        } else {
          setState({
            kind: "error",
            message: err instanceof Error ? err.message : "Failed to load index",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // Debounce the query input (120ms).
  useEffect(() => {
    const t = setTimeout(() => setQuery(raw.trim()), 120);
    return () => clearTimeout(t);
  }, [raw]);

  // Available filter values (from the loaded pages).
  const { layers, types } = useMemo(() => {
    if (state.kind !== "ready") return { layers: [], types: [] };
    const ls = new Set<string>();
    const ts = new Set<string>();
    for (const p of state.pages.values()) {
      if (p.layer) ls.add(p.layer);
      if (p.type) ts.add(p.type);
    }
    return { layers: [...ls].sort(), types: [...ts].sort() };
  }, [state]);

  // Compute results: search hits when a query is present, else all pages.
  const results = useMemo(() => {
    if (state.kind !== "ready") return [] as IndexPage[];
    let pages: IndexPage[];
    if (query) {
      pages = state.mini
        .search(query)
        .map((r) => state.pages.get(r.id as string))
        .filter((p): p is IndexPage => Boolean(p));
    } else {
      pages = [...state.pages.values()].sort((a, b) =>
        a.title.localeCompare(b.title),
      );
    }
    if (layerFilter) pages = pages.filter((p) => p.layer === layerFilter);
    if (typeFilter) pages = pages.filter((p) => p.type === typeFilter);
    return pages;
  }, [state, query, layerFilter, typeFilter]);

  return (
    <div className="min-h-full bg-[#fdfcfc] text-zinc-800 dark:bg-[#131314] dark:text-zinc-100">
      <div className="mx-auto w-full max-w-3xl px-5 py-8">
        <h1 className="mb-4 text-2xl font-semibold tracking-tight">
          Search {siteConfig.title}
        </h1>

        <div className="relative">
          <SearchIcon className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-zinc-400" />
          <input
            ref={inputRef}
            autoFocus
            type="search"
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            placeholder="Search titles, headings, tags, and full text…"
            className="w-full rounded-[28px] border border-zinc-200/80 bg-white py-3 pl-12 pr-4 text-[15px] text-zinc-900 shadow-sm outline-none transition-colors focus:border-zinc-300 dark:border-white/10 dark:bg-[#1e1f20] dark:text-zinc-100 dark:focus:border-white/20"
          />
        </div>

        {/* Filter chips */}
        {state.kind === "ready" && (layers.length > 0 || types.length > 0) && (
          <div className="mt-3 flex flex-wrap items-center gap-1.5">
            {layers.map((l) => (
              <FilterChip
                key={`layer-${l}`}
                label={layerLabel(l)}
                active={layerFilter === l}
                onClick={() =>
                  setLayerFilter((cur) => (cur === l ? null : l))
                }
              />
            ))}
            {types.map((t) => (
              <FilterChip
                key={`type-${t}`}
                label={t}
                active={typeFilter === t}
                onClick={() => setTypeFilter((cur) => (cur === t ? null : t))}
              />
            ))}
            {(layerFilter || typeFilter) && (
              <button
                type="button"
                onClick={() => {
                  setLayerFilter(null);
                  setTypeFilter(null);
                }}
                className="rounded-full px-3 py-1 text-[13px] text-zinc-500 underline-offset-2 hover:underline dark:text-zinc-400"
              >
                Clear
              </button>
            )}
          </div>
        )}

        {/* States */}
        {state.kind === "loading" && (
          <p className="mt-8 text-sm text-zinc-500 dark:text-zinc-400">
            Loading search index…
          </p>
        )}

        {state.kind === "missing" && (
          <div className="mt-8 rounded-xl border border-amber-200 bg-amber-50 px-4 py-6 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/30 dark:text-amber-300">
            <p className="font-medium">No search index found.</p>
            <p className="mt-1 opacity-90">
              Build it with{" "}
              <code className="rounded bg-amber-100 px-1.5 py-0.5 dark:bg-amber-900/40">
                python scripts/export_wiki.py
              </code>{" "}
              (writes <code>web/public/wiki-index.json</code>).
            </p>
          </div>
        )}

        {state.kind === "error" && (
          <div className="mt-8 rounded-xl border border-red-200 bg-red-50 px-4 py-6 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
            <p className="font-medium">Could not load the search index.</p>
            <p className="mt-1 opacity-80">{state.message}</p>
          </div>
        )}

        {state.kind === "ready" && (
          <>
            <p className="mt-5 text-sm text-zinc-500 dark:text-zinc-400">
              {results.length} result{results.length === 1 ? "" : "s"}
              {query ? (
                <>
                  {" "}
                  for{" "}
                  <span className="font-medium text-zinc-700 dark:text-zinc-200">
                    &ldquo;{query}&rdquo;
                  </span>
                </>
              ) : null}
            </p>

            {results.length === 0 ? (
              <p className="mt-8 text-sm text-zinc-500 dark:text-zinc-400">
                No pages match your search. Try a shorter or different term.
              </p>
            ) : (
              <ul className="mt-3 divide-y divide-zinc-200/70 dark:divide-white/10">
                {results.map((p) => (
                  <li key={p.slug} className="py-3">
                    <Link
                      href={`/wiki/${encodeURIComponent(p.slug)}`}
                      className="group block"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[15px] font-medium text-zinc-800 group-hover:text-blue-600 group-hover:underline dark:text-zinc-100 dark:group-hover:text-blue-400">
                          {p.title}
                        </span>
                        {p.layer && (
                          <span className={CHIP_CLASS}>{p.layer}</span>
                        )}
                        {p.type && <span className={CHIP_CLASS}>{p.type}</span>}
                        {p.status && (
                          <span className={CHIP_CLASS}>{p.status}</span>
                        )}
                      </div>
                      <p className="mt-1 text-[13px] leading-6 text-zinc-600 dark:text-zinc-400">
                        {snippet(p, query)}
                      </p>
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
    </div>
  );
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={
        "rounded-full border px-3 py-1 text-[13px] font-medium capitalize transition-colors " +
        (active
          ? "border-[#0b57d0]/30 bg-[#d3e3fd] text-[#0b57d0] dark:border-[#a8c7fa]/30 dark:bg-[#3b4a63] dark:text-[#a8c7fa]"
          : "border-zinc-200 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-700 dark:border-white/10 dark:text-zinc-400 dark:hover:bg-white/5 dark:hover:text-zinc-200")
      }
    >
      {label}
    </button>
  );
}
