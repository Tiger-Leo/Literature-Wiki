"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ChevronRight, BookOpen } from "lucide-react";
import { useAuiState } from "@assistant-ui/react";

/**
 * Provenance of one retrieved passage, as streamed by the backend's NDJSON
 * `sources` event (PROTOCOL §1) and carried on the assistant message via
 * `metadata.custom.sources` (set by the chat adapter).
 */
export type SourceRef = {
  slug: string;
  citekey?: string;
  layer?: string;
  tier?: string;
  heading_path?: string;
};

function isSourceRef(v: unknown): v is SourceRef {
  return (
    typeof v === "object" &&
    v !== null &&
    typeof (v as { slug?: unknown }).slug === "string"
  );
}

/**
 * Collapsible "Sources (N)" panel rendered under an assistant message.
 *
 * Reads the retrieved-passage provenance the chat adapter stored on the current
 * message's `metadata.custom.sources` (and, via the persistence round-trip, the
 * same field on reloaded messages). Each source is a `next/link` to
 * `/wiki/{slug}` so it browses client-side, showing the slug plus a small
 * layer/tier chip and citekey when present. Collapsed by default.
 *
 * Renders nothing when the message has no sources (e.g. user messages, errored
 * runs, or messages predating the sources feature).
 */
export function SourcesPanel() {
  const [open, setOpen] = useState(false);

  // Select the RAW stored reference only — no `.filter`/`.map`/literals — so
  // `useAuiState`'s `Object.is` comparison stays stable across store updates
  // (a fresh array literal here would trip "getSnapshot should be cached" and
  // loop forever). The same array instance that the chat adapter stored on
  // `metadata.custom.sources` is returned unchanged; `undefined` stays a stable
  // primitive when there are none.
  const raw = useAuiState((s): unknown =>
    s.message.role === "assistant"
      ? (s.message.metadata?.custom as { sources?: unknown } | undefined)
          ?.sources
      : undefined,
  );

  // Validate/narrow OUTSIDE the selector, memoised on the raw reference so the
  // derived array is itself stable while `raw` is unchanged.
  const sources = useMemo<SourceRef[] | undefined>(() => {
    if (!Array.isArray(raw)) return undefined;
    const filtered = raw.filter(isSourceRef);
    return filtered.length > 0 ? filtered : undefined;
  }, [raw]);

  if (!sources) return null;

  return (
    <div className="mt-2 w-full">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[13px] text-zinc-500 transition-colors hover:bg-zinc-200/60 hover:text-zinc-700 dark:text-zinc-400 dark:hover:bg-white/10 dark:hover:text-zinc-200"
      >
        <ChevronRight
          className={`h-3.5 w-3.5 transition-transform ${
            open ? "rotate-90" : ""
          }`}
        />
        <BookOpen className="h-3.5 w-3.5" />
        Sources ({sources.length})
      </button>

      {open && (
        <ul className="mt-1.5 flex flex-col gap-1 border-l-2 border-zinc-200 pl-3 dark:border-white/10">
          {sources.map((src, i) => (
            <li key={`${src.slug}-${i}`}>
              <Link
                href={`/wiki/${encodeURIComponent(src.slug)}`}
                className="group/src flex items-center gap-2 rounded-lg px-2 py-1.5 text-[13px] no-underline transition-colors hover:bg-zinc-100 dark:hover:bg-white/5"
              >
                <span className="truncate font-medium text-zinc-700 group-hover/src:text-[#0b57d0] dark:text-zinc-200 dark:group-hover/src:text-[#a8c7fa]">
                  {src.slug}
                </span>
                {src.layer && (
                  <span className="flex-shrink-0 rounded-full bg-zinc-100 px-1.5 py-0.5 text-[11px] uppercase tracking-wide text-zinc-500 dark:bg-white/10 dark:text-zinc-400">
                    {src.layer}
                    {src.tier ? ` · ${src.tier}` : ""}
                  </span>
                )}
                {src.citekey && (
                  <span className="flex-shrink-0 truncate font-mono text-[11px] text-zinc-400 dark:text-zinc-500">
                    {src.citekey}
                  </span>
                )}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
