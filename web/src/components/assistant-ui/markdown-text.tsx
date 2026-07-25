"use client";

import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { remarkWikilinks } from "@/lib/wikilinks";
import { remarkCallouts } from "@/lib/callouts";
import { normalizeCustomMathTags } from "@/lib/math";
import { MarkdownLink } from "@/components/markdown-link";
import { WIKI_PROSE_CLASS } from "@/components/wiki-markdown";

/**
 * Full-width markdown renderer for assistant replies. Styling leans on Tailwind
 * Typography-like utility classes applied directly (the project does not ship
 * the typography plugin, so we style the key elements ourselves).
 *
 * LaTeX: `remarkMath` parses `$...$` / `$$...$$`, `rehypeKatex` renders it with
 * KaTeX (CSS imported globally in `app/layout.tsx`). `preprocess` normalises the
 * alternative delimiters models sometimes emit (`\(…\)`, `\[…\]`, `[/math]…`).
 */
export function MarkdownText() {
  return (
    <MarkdownTextPrimitive
      remarkPlugins={[remarkGfm, remarkMath, remarkWikilinks, remarkCallouts]}
      rehypePlugins={[rehypeKatex]}
      preprocess={normalizeCustomMathTags}
      components={{ a: MarkdownLink }}
      smooth
      className={`${WIKI_PROSE_CLASS} text-zinc-800 dark:text-zinc-100`}
    />
  );
}
