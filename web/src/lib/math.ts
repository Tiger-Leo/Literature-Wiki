/**
 * LaTeX/KaTeX helpers shared by the chat renderer (`markdown-text.tsx`) and the
 * wiki page viewer (`wiki/[slug]/page.tsx`).
 *
 * Math is parsed by `remark-math` (`$...$` inline, `$$...$$` display) and
 * rendered by `rehype-katex`. KaTeX's stylesheet is imported once globally in
 * `app/layout.tsx`.
 *
 * `normalizeCustomMathTags` rewrites the alternative delimiters that language
 * models sometimes emit into the `$`/`$$` forms `remark-math` understands:
 *   - `[/math]…[/math]`     → `$$…$$`   (display)
 *   - `[/inline]…[/inline]` → `$…$`     (inline)
 *   - `\(…\)` / `\\(…\\)`   → `$…$`     (inline)
 *   - `\[…\]` / `\\[…\\]`   → `$$…$$`   (display)
 *
 * Taken from the official assistant-ui LaTeX guide
 * (https://www.assistant-ui.com/docs/guides/latex).
 *
 * Currency caveat: some corpora contain dollar AMOUNTS such as `$5,500/day` and
 * `$3,500`. With single-dollar inline math enabled (the `remark-math` default,
 * required for `$\overline{X}_j$`-style inline equations), a run of text
 * bracketed by two such amounts can be mis-parsed as math. `remark-math` only
 * opens math on a `$` that is NOT followed by whitespace and closes on a `$` not
 * preceded by whitespace, and a `$` directly followed by a digit is treated as
 * text — so `$3,500` and `$5,500/day` are generally safe in isolation. The
 * residual risk is two amounts on the same line with no intervening `$` (e.g.
 * "from $3,500 to $5,500"): the span between them may render as math. Equations
 * are the priority, so single-dollar math stays on.
 */
export function normalizeCustomMathTags(input: string): string {
  const converted = input
    .replace(/\[\/math\]([\s\S]*?)\[\/math\]/g, (_, c) => `$$${c.trim()}$$`)
    .replace(/\[\/inline\]([\s\S]*?)\[\/inline\]/g, (_, c) => `$${c.trim()}$`)
    .replace(/\\{1,2}\(([\s\S]*?)\\{1,2}\)/g, (_, c) => `$${c.trim()}$`)
    .replace(/\\{1,2}\[([\s\S]*?)\\{1,2}\]/g, (_, c) => `$$${c.trim()}$$`);
  // A `$$…$$` whose content sits directly against the fences on a single line is
  // parsed by `remark-math` as INLINE math (wrapped in a `<p>`), not display.
  // Re-emit any `$$…$$` that occupies its own line in fenced block form
  // (`$$\n…\n$$`) so it reliably renders as a display equation (`.katex-display`).
  // The line-anchored pattern + non-newline first char leaves already-fenced
  // blocks and genuinely inline `$$x$$` (mid-paragraph) untouched.
  return converted.replace(
    /^[ \t]*\$\$[ \t]*([^\n][\s\S]*?)[ \t]*\$\$[ \t]*$/gm,
    (_, c) => `$$\n${c.trim()}\n$$`,
  );
}
