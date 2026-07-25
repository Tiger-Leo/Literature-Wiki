"use client";

import { useSyncExternalStore } from "react";

/**
 * Tiny module-level store for the *current* backend pipeline stage label
 * (e.g. "Searching the literature…", "Writing the answer…").
 *
 * The NDJSON chat adapter pushes the latest `status.label` here while a run is
 * in flight and clears it when the first answer text arrives (or the run ends).
 * The thread UI subscribes via `useChatStatus()` to show an animated spinner
 * pill while waiting for the first token.
 *
 * A module-level store (rather than per-message metadata) keeps the indicator
 * decoupled from assistant-ui's message-state typing and works reliably for the
 * single active run of a local runtime.
 */
let currentStatus: string | null = null;
const listeners = new Set<() => void>();

function emit() {
  for (const l of listeners) l();
}

export function setChatStatus(status: string | null) {
  if (currentStatus === status) return;
  currentStatus = status;
  emit();
}

export function clearChatStatus() {
  setChatStatus(null);
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

function getSnapshot() {
  return currentStatus;
}

/** Reactive read of the current backend stage label (or null when idle). */
export function useChatStatus(): string | null {
  return useSyncExternalStore(subscribe, getSnapshot, () => null);
}
