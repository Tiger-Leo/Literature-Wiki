"use client";

import { useEffect, useState } from "react";

type TocItem = { id: string; text: string; level: number };

function slugify(text: string): string {
  return (
    text
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-")
      .replace(/^-|-$/g, "") || "section"
  );
}

/**
 * Right-hand "On this page" table of contents. After mount, finds the rendered
 * `h2,h3` inside the article container (`#wiki-article`), assigns slug ids if
 * missing, and renders anchor links with smooth scroll + active-section
 * highlight driven by an IntersectionObserver. DOM-based — no extra deps.
 * Hidden on mobile/narrow viewports via the parent's responsive classes.
 */
export function WikiToc() {
  const [items, setItems] = useState<TocItem[]>([]);
  const [activeId, setActiveId] = useState<string>("");

  useEffect(() => {
    const container = document.getElementById("wiki-article");
    if (!container) return;

    const headings = Array.from(
      container.querySelectorAll<HTMLElement>("h2, h3"),
    );
    const seen = new Set<string>();
    const collected: TocItem[] = [];

    for (const h of headings) {
      const text = (h.textContent ?? "").trim();
      if (!text) continue;
      let id = h.id || slugify(text);
      let unique = id;
      let n = 2;
      while (seen.has(unique)) unique = `${id}-${n++}`;
      id = unique;
      seen.add(id);
      if (!h.id) h.id = id;
      h.style.scrollMarginTop = "72px";
      collected.push({ id, text, level: h.tagName === "H3" ? 3 : 2 });
    }

    setItems(collected);
    if (collected.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
        if (visible[0]) setActiveId(visible[0].target.id);
      },
      { rootMargin: "-72px 0px -70% 0px", threshold: 0 },
    );
    for (const h of headings) {
      if (h.id) observer.observe(h);
    }
    return () => observer.disconnect();
  }, []);

  if (items.length === 0) return null;

  return (
    <nav aria-label="On this page" className="text-[12.5px]">
      <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.06em] text-zinc-400 dark:text-zinc-500">
        On this page
      </div>
      <ul className="list-none">
        {items.map((it) => {
          const active = it.id === activeId;
          return (
            <li key={it.id}>
              <a
                href={`#${it.id}`}
                onClick={(e) => {
                  e.preventDefault();
                  const el = document.getElementById(it.id);
                  if (el) {
                    el.scrollIntoView({ behavior: "smooth", block: "start" });
                    history.replaceState(null, "", `#${it.id}`);
                    setActiveId(it.id);
                  }
                }}
                className={
                  "block border-l-2 py-1.5 leading-snug transition-colors " +
                  (it.level === 3 ? "pl-6 pr-2.5" : "pl-3 pr-2.5") +
                  " " +
                  (active
                    ? "border-[#0b57d0] font-semibold text-[#0b57d0] dark:border-[#a8c7fa] dark:text-[#a8c7fa]"
                    : "border-zinc-200 text-zinc-500 hover:text-zinc-900 dark:border-white/10 dark:text-zinc-400 dark:hover:text-zinc-100")
                }
              >
                {it.text}
              </a>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
