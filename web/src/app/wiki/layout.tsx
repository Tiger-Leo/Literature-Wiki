import { listPages } from "@/lib/wiki-fs";
import { layerLabel, layerRank } from "@/lib/wiki-ui";
import {
  WikiSidebar,
  type SidebarGroup,
} from "@/components/wiki-sidebar";

/**
 * Persistent two-pane shell for the whole `/wiki` segment (browse landing AND
 * `/wiki/[slug]`). A SERVER component: it reads every page from the filesystem
 * via `listPages()`, groups them by layer, and hands the lightweight group data
 * to the client {@link WikiSidebar}. The right-pane content (`children`) renders
 * either the Browse overview or an article + its own TOC.
 */
export default function WikiLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pages = listPages();

  const byLayer = new Map<string, SidebarGroup>();
  for (const p of pages) {
    const layer = p.layer || "";
    let g = byLayer.get(layer);
    if (!g) {
      g = { layer, label: layerLabel(layer), count: 0, pages: [] };
      byLayer.set(layer, g);
    }
    g.count += 1;
    g.pages.push({
      slug: p.slug,
      title: p.title,
      type: p.type,
      status: p.status,
    });
  }

  const groups = [...byLayer.values()].sort(
    (a, b) => layerRank(a.layer) - layerRank(b.layer) || a.layer.localeCompare(b.layer),
  );

  return (
    <div className="flex h-full min-h-0 bg-[#fdfcfc] text-zinc-800 dark:bg-[#131314] dark:text-zinc-100">
      <WikiSidebar groups={groups} />
      <main className="min-w-0 flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
