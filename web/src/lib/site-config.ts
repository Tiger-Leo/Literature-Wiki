/**
 * Domain-agnostic site identity. Every user-facing brand string flows from
 * here, driven by `NEXT_PUBLIC_*` env vars (build-time) with generic defaults so
 * the template runs out of the box. Override these in `.env.local` (see
 * `.env.example`) to brand the wiki for your own research domain.
 */
export const siteConfig = {
  title: process.env.NEXT_PUBLIC_SITE_TITLE ?? "Literature Wiki",
  description:
    process.env.NEXT_PUBLIC_SITE_DESCRIPTION ??
    "Browse, search, and chat with a research-literature wiki.",
  greeting:
    process.env.NEXT_PUBLIC_SITE_GREETING ?? "How can I help you today?",
  composerPlaceholder:
    process.env.NEXT_PUBLIC_SITE_PLACEHOLDER ?? "Ask the literature wiki…",
};
