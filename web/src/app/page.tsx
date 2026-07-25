"use client";

import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { Thread } from "@/components/assistant-ui/thread";
import { ThreadList } from "@/components/assistant-ui/thread-list";
import { ExportButton } from "@/components/export-button";
import { siteConfig } from "@/lib/site-config";

export default function Home() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const closeDrawer = () => setDrawerOpen(false);

  // Lock background scroll while the mobile drawer is open so the page behind
  // it cannot rubber-band/drift. Scoped to drawer-open only (the app shell never
  // sets a global body overflow, which would clip the document-scrolled /search).
  useEffect(() => {
    if (!drawerOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [drawerOpen]);

  return (
    <div className="flex h-full w-full overflow-hidden bg-[#fdfcfc] dark:bg-[#131314]">
      {/* Scrim (mobile only, when open). */}
      {drawerOpen && (
        <div
          onClick={closeDrawer}
          aria-hidden
          className="fixed inset-x-0 bottom-0 top-12 z-40 bg-black/30 md:hidden"
        />
      )}

      {/* Sidebar — persistent column on md+, fixed slide-in drawer below md.
          Mobile drawer sits below the global 48px top nav (top-12), mirroring
          wiki-sidebar's offset so it never covers the nav. */}
      <aside
        className={
          "z-50 flex w-[280px] flex-shrink-0 flex-col border-r border-zinc-200/80 bg-[#f7f8fa] dark:border-white/10 dark:bg-[#1b1c1d] " +
          "max-md:fixed max-md:inset-y-0 max-md:left-0 max-md:top-12 max-md:w-[84%] max-md:max-w-[320px] max-md:shadow-2xl max-md:transition-transform " +
          (drawerOpen ? "max-md:translate-x-0" : "max-md:-translate-x-[105%]")
        }
      >
        <div className="flex h-14 flex-shrink-0 items-center justify-between px-4">
          <span className="truncate text-sm font-medium text-zinc-700 dark:text-zinc-200">
            {siteConfig.title}
          </span>
          {/* Close affordance inside the drawer (mobile only). */}
          <button
            type="button"
            onClick={closeDrawer}
            aria-label="Close chat history"
            className="-mr-2 inline-flex h-11 w-11 items-center justify-center rounded-lg text-zinc-500 hover:bg-black/[.04] md:hidden dark:text-zinc-400 dark:hover:bg-white/5"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <ThreadList onNavigate={closeDrawer} />
        </div>
      </aside>

      {/* Main column */}
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 flex-shrink-0 items-center justify-between gap-2 border-b border-zinc-200/80 px-4 dark:border-white/10">
          <button
            type="button"
            onClick={() => setDrawerOpen((v) => !v)}
            aria-label={drawerOpen ? "Close chat history" : "Open chat history"}
            aria-expanded={drawerOpen}
            className="-ml-2 inline-flex h-11 w-11 items-center justify-center rounded-lg text-zinc-700 hover:bg-black/[.04] md:hidden dark:text-zinc-200 dark:hover:bg-white/5"
          >
            {drawerOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
          </button>
          <div className="ml-auto flex items-center gap-2">
            <ExportButton />
          </div>
        </header>
        <div className="min-h-0 flex-1">
          <Thread />
        </div>
      </main>
    </div>
  );
}
