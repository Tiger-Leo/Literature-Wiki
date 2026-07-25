"use client";

import type { AnchorHTMLAttributes } from "react";
import Link from "next/link";

/**
 * Custom `a` renderer for react-markdown / MarkdownTextPrimitive.
 *
 * Internal hrefs (starting with "/") — including wikilinks to `/wiki/{slug}` —
 * render as a Next `<Link>` so navigation stays **client-side**. This keeps the
 * root `MyRuntimeProvider` (chat runtime + thread list) mounted across the
 * chat → /wiki → Back round-trip, instead of doing a full-page load that resets
 * the client router (which previously left Back on a blank page).
 *
 * External/other hrefs (http/https, mailto, anchors, …) render as a plain `<a>`;
 * http(s) links open in a new tab with safe rel.
 */
export function MarkdownLink({
  href,
  children,
  ...rest
}: AnchorHTMLAttributes<HTMLAnchorElement> & { node?: unknown }) {
  // react-markdown passes the mdast/hast `node`; strip it so it never reaches
  // the DOM.
  const props = { ...rest };
  delete (props as { node?: unknown }).node;
  const target = typeof href === "string" ? href : "";

  // Internal app route → client-side navigation.
  if (target.startsWith("/")) {
    return (
      <Link href={target} {...props}>
        {children}
      </Link>
    );
  }

  const isExternal = /^https?:\/\//i.test(target);
  return (
    <a
      href={target}
      {...(isExternal
        ? { target: "_blank", rel: "noopener noreferrer" }
        : undefined)}
      {...props}
    >
      {children}
    </a>
  );
}
