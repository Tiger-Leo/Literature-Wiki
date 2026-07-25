"use client";

import type { FC } from "react";
import {
  ActionBarPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useAuiState,
} from "@assistant-ui/react";
import {
  ArrowUp,
  CheckIcon,
  CopyIcon,
  RefreshCw,
  Square,
} from "lucide-react";
import { MarkdownText } from "./markdown-text";
import { SourcesPanel } from "@/components/sources-panel";
import { useChatStatus } from "@/lib/chat-status";
import { siteConfig } from "@/lib/site-config";

/**
 * Gemini-styled chat thread.
 * - Centered greeting + soft radial glow on the empty state.
 * - Single-row rounded "pill" composer.
 * - Avatar-free, full-width markdown assistant replies.
 * - Right-aligned rounded grey user bubble.
 * - Hover ActionBar (copy) on assistant replies.
 */
export const Thread: FC = () => {
  return (
    <ThreadPrimitive.Root
      className="flex h-full flex-col bg-[#fdfcfc] dark:bg-[#131314]"
      style={{ ["--thread-max-width" as string]: "46rem" }}
    >
      <ThreadPrimitive.Viewport className="relative flex flex-1 flex-col items-center overflow-y-auto scroll-smooth px-4">
        <ThreadWelcome />

        <ThreadPrimitive.Messages
          components={{
            UserMessage,
            AssistantMessage,
          }}
        />

        <StatusIndicator />

        <ThreadPrimitive.If empty={false}>
          <div className="min-h-6 flex-shrink-0" />
        </ThreadPrimitive.If>

        <div className="sticky bottom-0 mt-auto flex w-full max-w-[var(--thread-max-width)] flex-col items-center bg-gradient-to-t from-[#fdfcfc] via-[#fdfcfc] to-transparent pb-4 pt-2 dark:from-[#131314] dark:via-[#131314]">
          <Composer />
        </div>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
};

const ThreadWelcome: FC = () => {
  return (
    <ThreadPrimitive.If empty>
      <div className="flex w-full max-w-[var(--thread-max-width)] flex-1 flex-col items-center justify-center">
        <div className="relative flex flex-col items-center">
          <div
            aria-hidden
            className="pointer-events-none absolute -inset-24 -z-10 rounded-full opacity-70 blur-3xl"
            style={{
              background:
                "radial-gradient(closest-side, #a9d1fb 0%, rgba(169,209,251,0.25) 45%, transparent 75%)",
            }}
          />
          <h1 className="bg-gradient-to-r from-[#4285f4] via-[#9b72cb] to-[#d96570] bg-clip-text text-center text-3xl font-medium text-transparent sm:text-4xl">
            {siteConfig.greeting}
          </h1>
        </div>
      </div>
    </ThreadPrimitive.If>
  );
};

/**
 * Animated spinner pill showing the current backend stage
 * ("Searching the literature…", "Writing the answer…") while the thread is
 * running and no answer text has arrived yet. The label comes from the NDJSON
 * chat adapter via the module-level chat-status store; we only show it while the
 * run is in flight (`thread.isRunning`).
 */
const StatusIndicator: FC = () => {
  const isRunning = useAuiState((s) => s.thread.isRunning);
  const status = useChatStatus();

  if (!isRunning || !status) return null;

  return (
    <div className="flex w-full max-w-[var(--thread-max-width)] justify-start py-1.5">
      <div className="inline-flex items-center gap-2 rounded-full bg-zinc-100/80 px-3 py-1.5 text-[13px] text-zinc-600 dark:bg-white/5 dark:text-zinc-300">
        <span
          aria-hidden
          className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-zinc-300 border-t-[#4285f4] dark:border-zinc-600 dark:border-t-[#a8c7fa]"
        />
        <span className="animate-pulse">{status}</span>
      </div>
    </div>
  );
};

const Composer: FC = () => {
  return (
    <ComposerPrimitive.Root className="flex w-full flex-col gap-1.5 rounded-[28px] border border-zinc-200/80 bg-white px-4 py-2.5 shadow-sm transition-colors focus-within:border-zinc-300 dark:border-white/10 dark:bg-[#1e1f20] dark:focus-within:border-white/20">
      <ComposerPrimitive.Input
        autoFocus
        rows={1}
        placeholder={siteConfig.composerPlaceholder}
        className="max-h-40 w-full resize-none bg-transparent py-1.5 text-[15px] leading-6 text-zinc-900 outline-none placeholder:text-zinc-400 dark:text-zinc-100 dark:placeholder:text-zinc-500"
      />

      <div className="flex items-center justify-end gap-2">
        <ThreadPrimitive.If running={false}>
          <ComposerPrimitive.Send asChild>
            <button
              type="submit"
              aria-label="Send message"
              className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-[#d3e3fd] text-[#0b57d0] transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40 dark:bg-[#3b4a63] dark:text-[#a8c7fa]"
            >
              <ArrowUp className="h-5 w-5" />
            </button>
          </ComposerPrimitive.Send>
        </ThreadPrimitive.If>

        <ThreadPrimitive.If running>
          <ComposerPrimitive.Cancel asChild>
            <button
              type="button"
              aria-label="Stop generating"
              className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-zinc-900 text-white transition-opacity hover:opacity-90 dark:bg-white dark:text-zinc-900"
            >
              <Square className="h-4 w-4 fill-current" />
            </button>
          </ComposerPrimitive.Cancel>
        </ThreadPrimitive.If>
      </div>
    </ComposerPrimitive.Root>
  );
};

const UserMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="flex w-full max-w-[var(--thread-max-width)] justify-end py-2.5">
      <div className="max-w-[80%] whitespace-pre-wrap break-words rounded-3xl bg-[#f2f0f0] px-4 py-2.5 text-[15px] leading-7 text-zinc-900 dark:bg-[#333537] dark:text-zinc-100">
        <MessagePrimitive.Parts />
      </div>
    </MessagePrimitive.Root>
  );
};

const AssistantMessage: FC = () => {
  return (
    <MessagePrimitive.Root className="group flex w-full max-w-[var(--thread-max-width)] flex-col py-2.5">
      <div className="w-full">
        <MessagePrimitive.Parts components={{ Text: MarkdownText }} />
      </div>

      <SourcesPanel />

      <ActionBarPrimitive.Root
        hideWhenRunning
        autohide="not-last"
        autohideFloat="single-branch"
        className="mt-1 flex items-center gap-1 text-zinc-500 opacity-100 transition-opacity [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover:opacity-100 [@media(hover:hover)]:data-[floating]:opacity-100 dark:text-zinc-400"
      >
        <ActionBarPrimitive.Copy asChild>
          <button
            type="button"
            aria-label="Copy"
            className="flex h-8 w-8 items-center justify-center rounded-full transition-colors hover:bg-zinc-200/70 dark:hover:bg-white/10"
          >
            <MessagePrimitive.If copied>
              <CheckIcon className="h-4 w-4" />
            </MessagePrimitive.If>
            <MessagePrimitive.If copied={false}>
              <CopyIcon className="h-4 w-4" />
            </MessagePrimitive.If>
          </button>
        </ActionBarPrimitive.Copy>

        <ActionBarPrimitive.Reload asChild>
          <button
            type="button"
            aria-label="Regenerate"
            className="flex h-8 w-8 items-center justify-center rounded-full transition-colors hover:bg-zinc-200/70 dark:hover:bg-white/10"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </ActionBarPrimitive.Reload>
      </ActionBarPrimitive.Root>
    </MessagePrimitive.Root>
  );
};
