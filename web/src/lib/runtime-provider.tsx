"use client";

import type { ReactNode } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  useRemoteThreadListRuntime,
} from "@assistant-ui/react";
import { chatAdapter } from "./chat-adapter";
import { useBackendThreadListAdapter } from "./thread-list-adapter";

/**
 * Composes the local (per-thread) chat runtime with the remote thread-list
 * runtime.
 *
 *   useRemoteThreadListRuntime({
 *     runtimeHook: () => useLocalRuntime(chatAdapter),
 *     adapter: threadListAdapter,   // unstable_Provider injects `history`
 *   })
 *
 * Persistence wiring: the thread-list adapter's `unstable_Provider` mounts a
 * `RuntimeAdapterProvider adapters={{ history }}` *above* the per-thread
 * `runtimeHook`. Inside `useLocalRuntime`, the legacy runtime
 * (`useLocalThreadRuntime`) reads that context via `useRuntimeAdapters()` and
 * merges the injected `history` adapter into its options automatically.
 *
 * IMPORTANT: do NOT pass `{ adapters: { history } }` explicitly here. The merge
 * inside `useLocalThreadRuntime` is `{ ...contextAdapters, ...options.adapters }`,
 * so an explicit `history` (which can be `undefined` on the first render, before
 * the provider context resolves) clobbers the correctly-injected one and the
 * runtime ends up with no history adapter — meaning `history.load()` never runs
 * on thread-open. Letting the context-merge own `history` is the reliable path.
 */
function RuntimeHook() {
  return useLocalRuntime(chatAdapter);
}

export function MyRuntimeProvider({ children }: { children: ReactNode }) {
  const adapter = useBackendThreadListAdapter();
  const runtime = useRemoteThreadListRuntime({
    runtimeHook: RuntimeHook,
    adapter,
  });

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}
