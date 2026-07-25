"use client";

import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { remarkWikilinks } from "@/lib/wikilinks";
import { remarkCallouts } from "@/lib/callouts";
import { normalizeCustomMathTags } from "@/lib/math";
import { MarkdownLink } from "@/components/markdown-link";

/**
 * Shared prose-styling utility string for rendered wiki/markdown content. The
 * project does not ship the Tailwind Typography plugin, so the key elements are
 * styled directly. Kept in one place so the chat renderer and the wiki viewer
 * stay visually identical.
 */
export const WIKI_PROSE_CLASS =
  "aui-md text-[15px] leading-7 [&_a]:text-blue-600 [&_a]:underline [&_a]:underline-offset-2 dark:[&_a]:text-blue-400 [&_h1]:mt-7 [&_h1]:mb-3 [&_h1]:text-2xl [&_h1]:font-semibold [&_h2]:mt-6 [&_h2]:mb-2 [&_h2]:text-xl [&_h2]:font-semibold [&_h3]:mt-5 [&_h3]:mb-2 [&_h3]:text-lg [&_h3]:font-semibold [&_p]:my-3 [&_ul]:my-3 [&_ul]:list-disc [&_ul]:pl-6 [&_ol]:my-3 [&_ol]:list-decimal [&_ol]:pl-6 [&_li]:my-1 [&_blockquote]:my-3 [&_blockquote]:border-l-2 [&_blockquote]:border-zinc-300 [&_blockquote]:pl-4 [&_blockquote]:text-zinc-600 dark:[&_blockquote]:border-zinc-700 dark:[&_blockquote]:text-zinc-400 [&_code]:rounded [&_code]:bg-zinc-100 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:text-[13px] dark:[&_code]:bg-zinc-800 [&_pre]:my-4 [&_pre]:overflow-x-auto [&_pre]:rounded-xl [&_pre]:bg-zinc-100 [&_pre]:p-4 [&_pre]:text-[13px] dark:[&_pre]:bg-zinc-900 [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_table]:my-4 [&_table]:w-full [&_table]:border-collapse [&_th]:border [&_th]:border-zinc-300 [&_th]:px-3 [&_th]:py-1.5 [&_th]:text-left dark:[&_th]:border-zinc-700 [&_td]:border [&_td]:border-zinc-300 [&_td]:px-3 [&_td]:py-1.5 dark:[&_td]:border-zinc-700 [&_hr]:my-6 [&_hr]:border-zinc-200 dark:[&_hr]:border-zinc-800";

/**
 * Reusable client-side markdown renderer used by the wiki page viewer (and
 * available for any other surface). Runs the full custom pipeline:
 * `[[wikilinks]]`, Obsidian callouts, GFM, and LaTeX math (KaTeX). Internal
 * links route client-side via {@link MarkdownLink}, keeping the chat runtime
 * mounted across navigation. `normalizeCustomMathTags` rewrites alternative math
 * delimiters into the `$`/`$$` forms `remark-math` understands.
 */
export function WikiMarkdown({ children }: { children: string }) {
  return (
    <Markdown
      remarkPlugins={[remarkGfm, remarkMath, remarkWikilinks, remarkCallouts]}
      rehypePlugins={[rehypeKatex]}
      components={{ a: MarkdownLink }}
    >
      {normalizeCustomMathTags(children)}
    </Markdown>
  );
}
