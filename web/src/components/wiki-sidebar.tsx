"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { ChevronDown, Search, Menu, X } from "lucide-react";
import {
  DEFAULT_COLLAPSED_LAYERS,
  DEFAULT_EXPANDED_LAYERS,
} from "@/lib/wiki-ui";

export type SidebarPage = {
  slug: string;
  title: string;
  type: string;
  status: string;
};

export type SidebarGroup = {
  layer: string;
  label: string;
  count: number;
  pages: SidebarPage[];
};

/**
 * Left category navigation for the `/wiki` two-pane layout.
 * - Collapsible groups by layer with counts.
 * - Active page highlighted (blue pill + left accent) via `usePathname()`.
 * - Default-expands Concepts + Mechanisms and the group containing the active
 *   page; large groups (Sources, pipeline notes) start collapsed.
 * - A search box that routes to `/search?q=` on Enter.
 * - On mobile (<1024px) it lives behind a hamburger as a slide-in drawer.
 */
export function WikiSidebar({ groups }: { groups: SidebarGroup[] }) {
  const pathname = usePathname();
  const router = useRouter();

  // Active slug from the URL (/wiki/<slug>).
  const activeSlug = useMemo(() => {
    const m = /^\/wiki\/([^/?#]+)/.exec(pathname);
    return m ? decodeURIComponent(m[1]) : null;
  }, [pathname]);

  const activeLayer = useMemo(() => {
    if (!activeSlug) return null;
    for (const g of groups) {
      if (g.pages.some((p) => p.slug === activeSlug)) return g.layer;
    }
    return null;
  }, [activeSlug, groups]);

  // Which groups are open. Initialise from defaults + active group.
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [initialised, setInitialised] = useState(false);

  useEffect(() => {
    if (initialised) return;
    const next: Record<string, boolean> = {};
    for (const g of groups) {
      let isOpen = DEFAULT_EXPANDED_LAYERS.has(g.layer);
      if (DEFAULT_COLLAPSED_LAYERS.has(g.layer)) isOpen = false;
      if (g.layer === activeLayer) isOpen = true;
      next[g.layer] = isOpen;
    }
    setOpen(next);
    setInitialised(true);
  }, [groups, activeLayer, initialised]);

  // Make sure the active group opens when navigating between pages.
  useEffect(() => {
    if (activeLayer) {
      setOpen((prev) =>
        prev[activeLayer] ? prev : { ...prev, [activeLayer]: true },
      );
    }
  }, [activeLayer]);

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [query, setQuery] = useState("");

  const toggle = (layer: string) =>
    setOpen((prev) => ({ ...prev, [layer]: !prev[layer] }));

  const closeDrawer = () => setDrawerOpen(false);

  // Lock background scroll while the mobile drawer is open so the page behind it
  // cannot rubber-band/drift (matches the Chat shell).
  useEffect(() => {
    if (!drawerOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [drawerOpen]);

  const submitSearch = () => {
    const q = query.trim();
    router.push(q ? `/search?q=${encodeURIComponent(q)}` : "/search");
    closeDrawer();
  };

  return (
    <>
      {/* Mobile hamburger — shown only below lg. */}
      <button
        type="button"
        onClick={() => setDrawerOpen((v) => !v)}
        aria-label="Toggle navigation"
        className="fixed left-3 top-[58px] z-40 inline-flex h-11 w-11 items-center justify-center rounded-lg border border-zinc-200 bg-[#f7f8fa] text-zinc-700 shadow-sm lg:hidden dark:border-white/10 dark:bg-[#1c1e22] dark:text-zinc-200"
      >
        {drawerOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
      </button>

      {/* Scrim (mobile only, when open). */}
      {drawerOpen && (
        <div
          onClick={closeDrawer}
          aria-hidden
          className="fixed inset-x-0 bottom-0 top-12 z-40 bg-black/30 lg:hidden"
        />
      )}

      <aside
        className={
          "z-50 w-[280px] shrink-0 overflow-y-auto border-r border-zinc-200/80 bg-[#f7f8fa] px-3 pb-12 pt-4 dark:border-white/10 dark:bg-[#1c1e22] " +
          // Desktop: in-flow column. Mobile: fixed slide-in drawer.
          "max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:top-12 max-lg:w-[84%] max-lg:max-w-[320px] max-lg:shadow-2xl max-lg:transition-transform " +
          (drawerOpen ? "max-lg:translate-x-0" : "max-lg:-translate-x-[105%]")
        }
      >
        {/* Search box */}
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-zinc-300/70 bg-[#fdfcfc] px-2.5 py-2 dark:border-white/15 dark:bg-[#16171a]">
          <Search className="h-4 w-4 shrink-0 text-zinc-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submitSearch();
            }}
            placeholder="Search the wiki…"
            aria-label="Search the wiki"
            className="min-w-0 flex-1 bg-transparent text-[13.5px] text-zinc-700 outline-none placeholder:text-zinc-400 dark:text-zinc-200"
          />
        </div>

        <nav>
          {groups.map((g) => {
            const isOpen = open[g.layer] ?? false;
            return (
              <div key={g.layer || "other"} className="mb-0.5">
                <button
                  type="button"
                  onClick={() => toggle(g.layer)}
                  aria-expanded={isOpen}
                  className="flex min-h-11 w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-[13px] font-semibold text-zinc-800 hover:bg-black/[.035] dark:text-zinc-100 dark:hover:bg-white/5"
                >
                  <ChevronDown
                    className={
                      "h-3.5 w-3.5 shrink-0 text-zinc-400 transition-transform " +
                      (isOpen ? "" : "-rotate-90")
                    }
                  />
                  <span className="flex-1">{g.label}</span>
                  <span className="rounded-full border border-zinc-200 bg-[#fdfcfc] px-2 py-0.5 text-[11.5px] font-medium text-zinc-500 dark:border-white/10 dark:bg-[#16171a] dark:text-zinc-400">
                    {g.count}
                  </span>
                </button>

                {isOpen && (
                  <ul className="mb-2 mt-0.5 list-none pl-2">
                    {g.pages.map((p) => {
                      const active = p.slug === activeSlug;
                      return (
                        <li key={p.slug}>
                          <Link
                            href={`/wiki/${encodeURIComponent(p.slug)}`}
                            onClick={closeDrawer}
                            aria-current={active ? "page" : undefined}
                            className={
                              "flex min-h-11 items-center rounded-md border-l-2 px-3 py-1.5 text-[13px] leading-snug transition-colors lg:min-h-0 " +
                              (active
                                ? "border-[#0b57d0] bg-[#d3e3fd] font-semibold text-[#0b57d0] dark:border-[#a8c7fa] dark:bg-[#1f3b66] dark:text-[#a8c7fa]"
                                : "border-transparent text-zinc-500 hover:bg-black/[.035] hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-white/5 dark:hover:text-zinc-100")
                            }
                          >
                            {p.title}
                          </Link>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            );
          })}
        </nav>
      </aside>
    </>
  );
}
