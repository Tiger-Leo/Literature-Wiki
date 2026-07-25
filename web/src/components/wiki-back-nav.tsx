"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, Home, List } from "lucide-react";

/** Client back/home/browse controls for the (server-rendered) wiki viewer. */
export function WikiBackNav() {
  const router = useRouter();
  return (
    <div className="mb-6 flex items-center gap-1">
      <button
        type="button"
        onClick={() => router.back()}
        className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm text-zinc-600 transition-colors hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>
      <Link
        href="/wiki"
        className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm text-zinc-600 transition-colors hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10"
      >
        <List className="h-4 w-4" />
        Browse
      </Link>
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm text-zinc-600 transition-colors hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-white/10"
      >
        <Home className="h-4 w-4" />
        Chat
      </Link>
    </div>
  );
}
