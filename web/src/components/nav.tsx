"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, Search, Library } from "lucide-react";
import { siteConfig } from "@/lib/site-config";

const LINKS = [
  { href: "/search", label: "Search", icon: Search },
  { href: "/wiki", label: "Browse", icon: Library },
  { href: "/", label: "Chat", icon: MessageSquare },
];

/**
 * Persistent top navigation. Lives inside the global runtime provider so
 * client-side navigation between Chat / Browse / Search keeps the assistant-ui
 * runtime mounted. Uses Next `<Link>` (no full reloads).
 */
export function Nav() {
  const pathname = usePathname();

  return (
    <header className="relative z-50 flex h-12 flex-shrink-0 items-center gap-1 border-b border-zinc-200/70 bg-[#f7f8fa] px-3 dark:border-white/10 dark:bg-[#1b1c1d]">
      <Link
        href="/"
        className="mr-2 min-w-0 max-w-[45vw] truncate px-2 text-sm font-semibold text-zinc-800 sm:max-w-none dark:text-zinc-100"
      >
        {siteConfig.title}
      </Link>
      <nav className="flex flex-shrink-0 items-center gap-1">
        {LINKS.map(({ href, label, icon: Icon }) => {
          const active =
            href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={
                "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-[13px] font-medium transition-colors " +
                (active
                  ? "bg-[#d3e3fd] text-[#0b57d0] dark:bg-[#3b4a63] dark:text-[#a8c7fa]"
                  : "text-zinc-600 hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10")
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
