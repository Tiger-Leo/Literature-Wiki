/** Presentation helpers shared by Browse and Search (layer order, chip styles). */

/** Canonical layer display order; unknown layers sort after these, alphabetically. */
export const LAYER_ORDER = [
  "concepts",
  "mechanisms",
  "debates",
  "methods",
  "measures",
  "synthesis",
  "sources",
];

export function layerRank(layer: string): number {
  const i = LAYER_ORDER.indexOf(layer);
  return i === -1 ? LAYER_ORDER.length : i;
}

/** Human label for a layer dir ("concepts" → "Concepts"; "" → "Other"). */
export function layerLabel(layer: string): string {
  if (!layer) return "Other";
  if (layer === "pipeline-notes") return "Pipeline notes";
  return layer.charAt(0).toUpperCase() + layer.slice(1);
}

/** One-line description per layer for the Browse landing overview. */
const LAYER_DESCRIPTIONS: Record<string, string> = {
  concepts: "Core ideas, definitions, and constructs.",
  mechanisms: "Causal pathways and how-it-works explanations.",
  debates: "Open questions and competing positions.",
  methods: "Empirical and theoretical approaches.",
  measures: "Operational metrics and variables.",
  synthesis: "Cross-cutting overviews of the collection.",
  sources: "Individual papers in the collection.",
  "pipeline-notes": "Build logs and maintenance notes.",
};

export function layerDescription(layer: string): string {
  return LAYER_DESCRIPTIONS[layer] ?? "";
}

/**
 * Layers collapsed by default in the sidebar (large/low-traffic groups).
 * Sources is large (hundreds of pages); pipeline notes are rarely browsed.
 */
export const DEFAULT_COLLAPSED_LAYERS = new Set(["sources", "pipeline-notes"]);

/** Layers always expanded by default (in addition to the active page's group). */
export const DEFAULT_EXPANDED_LAYERS = new Set(["concepts", "mechanisms"]);

/** Small neutral chip class used for type/status/layer tags. */
export const CHIP_CLASS =
  "inline-flex items-center rounded-full bg-zinc-100 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-zinc-500 dark:bg-white/10 dark:text-zinc-400";
