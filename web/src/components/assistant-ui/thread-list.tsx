"use client";

import type { FC } from "react";
import {
  ThreadListItemPrimitive,
  ThreadListPrimitive,
  useAui,
} from "@assistant-ui/react";
import { Pencil, Plus, Trash2 } from "lucide-react";

/**
 * Gemini-style sidebar: a "New chat" button plus the list of past threads.
 * Each item exposes a rename and a delete affordance on hover.
 *
 * `onNavigate` (optional) fires whenever the user starts a new chat or selects
 * an existing thread. On mobile the page passes its drawer-close callback so a
 * selection also dismisses the slide-in drawer. It is composed *alongside* the
 * primitive's own click handling (never replacing it), so thread selection and
 * new-chat creation continue to work normally.
 */
export const ThreadList: FC<{ onNavigate?: () => void }> = ({ onNavigate }) => {
  return (
    <ThreadListPrimitive.Root className="flex h-full flex-col gap-2 p-2">
      <ThreadListNew onNavigate={onNavigate} />
      <div className="mt-1 flex flex-col gap-0.5 overflow-y-auto">
        <ThreadListPrimitive.Items
          components={{
            ThreadListItem: () => <ThreadListItem onNavigate={onNavigate} />,
          }}
        />
      </div>
    </ThreadListPrimitive.Root>
  );
};

const ThreadListNew: FC<{ onNavigate?: () => void }> = ({ onNavigate }) => {
  return (
    <ThreadListPrimitive.New asChild>
      <button
        type="button"
        onClick={() => onNavigate?.()}
        className="flex min-h-11 items-center gap-2 rounded-full bg-[#dde3ea] px-4 py-2.5 text-sm font-medium text-zinc-700 transition-colors hover:bg-[#d2d9e2] dark:bg-[#1e1f20] dark:text-zinc-200 dark:hover:bg-[#2a2b2d]"
      >
        <Plus className="h-4 w-4" />
        New chat
      </button>
    </ThreadListPrimitive.New>
  );
};

const ThreadListItem: FC<{ onNavigate?: () => void }> = ({ onNavigate }) => {
  return (
    <ThreadListItemPrimitive.Root className="group flex items-center gap-1 rounded-full px-1 transition-colors hover:bg-zinc-200/70 data-[active]:bg-[#d3e3fd] dark:hover:bg-white/5 dark:data-[active]:bg-[#3b4a63]">
      <ThreadListItemPrimitive.Trigger
        onClick={() => onNavigate?.()}
        className="flex min-h-11 flex-1 items-center overflow-hidden px-3 py-2 text-left"
      >
        <span className="truncate text-sm text-zinc-700 dark:text-zinc-200">
          <ThreadListItemPrimitive.Title fallback="New chat" />
        </span>
      </ThreadListItemPrimitive.Trigger>

      <div className="flex items-center pr-1 opacity-0 transition-opacity group-hover:opacity-100">
        <ThreadListItemRename />
        <ThreadListItemPrimitive.Delete asChild>
          <button
            type="button"
            aria-label="Delete thread"
            className="flex h-7 w-7 items-center justify-center rounded-full text-zinc-500 transition-colors hover:bg-zinc-300/70 hover:text-red-600 dark:text-zinc-400 dark:hover:bg-white/10"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </ThreadListItemPrimitive.Delete>
      </div>
    </ThreadListItemPrimitive.Root>
  );
};

/**
 * Rename uses a window prompt to collect the new title, then delegates to the
 * current thread-list item runtime's `rename` action (via `useAui`).
 */
const ThreadListItemRename: FC = () => {
  const aui = useAui();
  return (
    <button
      type="button"
      aria-label="Rename thread"
      onClick={() => {
        const item = aui.threadListItem();
        const current = item.getState().title ?? "";
        const next = window.prompt("Rename chat", current);
        if (next != null && next.trim() !== "") {
          void item.rename(next.trim());
        }
      }}
      className="flex h-7 w-7 items-center justify-center rounded-full text-zinc-500 transition-colors hover:bg-zinc-300/70 hover:text-zinc-800 dark:text-zinc-400 dark:hover:bg-white/10 dark:hover:text-zinc-100"
    >
      <Pencil className="h-3.5 w-3.5" />
    </button>
  );
};
