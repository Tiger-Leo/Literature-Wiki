"use client";

import { useCallback } from "react";
import {
  RuntimeAdapterProvider,
  useAui,
  ExportedMessageRepository,
  type RemoteThreadListAdapter,
  type ThreadHistoryAdapter,
  type ExportedMessageRepositoryItem,
  type MessageFormatAdapter,
  type MessageFormatItem,
  type ThreadMessage,
  type ThreadMessageLike,
} from "@assistant-ui/react";
import { createAssistantStream } from "assistant-stream";
import {
  API_URL,
  apiDelete,
  apiGet,
  apiPatch,
  apiPost,
  type RemoteThread,
  type StoredMessageRow,
} from "./api";

/**
 * Storage format ("aui/v0"-compatible) for a single persisted message. This is
 * the JSON object stored in the backend's `content` column and returned as-is
 * (decoded) by `GET /api/threads/{id}/messages` (PROTOCOL §3).
 *
 * It mirrors the shape produced by assistant-ui's internal `auiV0Encode`
 * (role + content parts + optional status/metadata), minus the server-owned
 * `id`/`createdAt` fields.
 */
type StoredMessageContent = {
  role: ThreadMessage["role"];
  content: unknown[];
  status?: unknown;
  metadata?: unknown;
};

/**
 * Encode a runtime `ThreadMessage` into the JSON object we persist.
 *
 * The legacy local runtime hands us a fully-formed `ThreadMessage`. We keep the
 * JSON-serialisable parts (text / reasoning / source / tool-call / image /
 * file) and drop transient fields. A `running` status is normalised to
 * `incomplete` so a reload never resurrects a half-streamed message.
 */
function encodeMessage(message: ThreadMessage): StoredMessageContent {
  const status =
    message.status?.type === "running"
      ? { type: "incomplete", reason: "cancelled" }
      : message.status;

  const content = (message.content ?? [])
    .map((part): unknown | null => {
      switch (part.type) {
        case "text":
          return { type: "text", text: part.text };
        case "reasoning":
          return { type: "reasoning", text: part.text };
        case "tool-call":
          return {
            type: "tool-call",
            toolCallId: part.toolCallId,
            toolName: part.toolName,
            ...(part.argsText !== undefined
              ? { argsText: part.argsText }
              : { args: part.args }),
            ...(part.result !== undefined ? { result: part.result } : undefined),
            ...(part.isError ? { isError: true } : undefined),
          };
        case "source":
          return part;
        case "image":
          return { type: "image", image: part.image };
        case "file":
          return {
            type: "file",
            data: part.data,
            mimeType: part.mimeType,
            ...(part.filename ? { filename: part.filename } : undefined),
          };
        default:
          // Unknown / non-serialisable part types are dropped.
          return null;
      }
    })
    .filter((p): p is NonNullable<typeof p> => p !== null);

  return {
    role: message.role,
    content,
    ...(status ? { status } : undefined),
    ...(message.metadata ? { metadata: message.metadata } : undefined),
  };
}

/**
 * Decode one stored row back into a `ThreadMessageLike` (the loose shape the
 * runtime accepts). `ExportedMessageRepository.fromBranchableArray` then turns
 * the array of these into the `ExportedMessageRepository` that `load()` returns.
 */
function decodeRow(row: StoredMessageRow): {
  message: ThreadMessageLike;
  parentId: string | null;
} {
  const content = (row.content ?? {}) as Partial<StoredMessageContent>;
  const message = {
    id: row.id,
    role: (content.role ?? (row.role as ThreadMessage["role"]) ?? "assistant"),
    content: Array.isArray(content.content) ? content.content : [],
    ...(content.status ? { status: content.status } : undefined),
    ...(content.metadata ? { metadata: content.metadata } : undefined),
  } as ThreadMessageLike;

  return { message, parentId: row.parent_id ?? null };
}

const HISTORY_FORMAT = "aui/v0";

/** Low-level REST calls shared by both the bare and format-aware adapters. */
async function fetchRows(remoteId: string): Promise<StoredMessageRow[]> {
  return apiGet<StoredMessageRow[]>(`/api/threads/${remoteId}/messages`);
}

async function postRow(
  remoteId: string,
  row: {
    id: string;
    parent_id: string | null;
    role?: string;
    content: unknown;
  },
): Promise<void> {
  await apiPost(`/api/threads/${remoteId}/messages`, {
    id: row.id,
    parent_id: row.parent_id,
    format: HISTORY_FORMAT,
    ...(row.role ? { role: row.role } : undefined),
    content: row.content,
  });
}

/**
 * Per-thread history adapter wired to the backend message-persistence routes.
 *
 * THE PERSISTENCE PATH (read the installed source, not the docs):
 *
 * In assistant-ui 0.14.7 the **legacy `useLocalRuntime`** drives history through
 * the adapter's *bare* `load()` / `append()` methods — see
 * `local-thread-runtime-core`'s `__internal_load` (`this.adapters.history?.load()`)
 * and `append` (`this._options.adapters.history?.append(...)`). It never calls
 * `withFormat` (that path is reserved for the cloud / AI-SDK runtimes). So the
 * real persistence logic MUST live on the **bare** methods.
 *
 * - Bare `load()` runs on thread-open. When a persisted thread becomes active,
 *   the framework mounts a fresh per-thread local runtime inside the correct
 *   `ThreadListItemRuntimeProvider`, so `aui.threadListItem().getState().remoteId`
 *   already holds the real id. We `GET /api/threads/{remoteId}/messages` and
 *   rebuild the repository. NOTE: `__internal_load` is single-shot (memoised via
 *   `_loadPromise`), so the `history` adapter MUST be present on the runtime's
 *   first render — hence we let the `RuntimeAdapterProvider` context-merge own
 *   `history` (see runtime-provider.tsx) instead of passing a possibly-undefined
 *   `history` explicitly, which would clobber it and cache an empty load.
 *
 * We ALSO implement `withFormat` (mirroring the official cloud custom-adapter
 * example) so the format-aware load/append path works for any consumer that
 * uses it; it reuses the same backend calls and maps rows via `fmt.decode`.
 */
function useBackendHistoryAdapter(): ThreadHistoryAdapter {
  const aui = useAui();

  return {
    // --- Bare path: the one the legacy local runtime actually drives. ---
    async load() {
      // Resolve the remote id robustly. `__internal_load` is single-shot
      // (memoised on `_loadPromise`) and fires on the per-thread runtime's
      // FIRST render. On a fresh page reload the thread-list `list()` may not
      // have propagated `remoteId` into this item's state yet, so a synchronous
      // `getState().remoteId` read can be `undefined` for the first thread
      // opened — which previously cached an empty `{messages:[]}` forever (you
      // had to switch away and back to remount the runtime and reload).
      //
      // Fix: when `remoteId` is missing but the item is an EXISTING persisted
      // thread (status !== "new"/"deleted"), await `initialize()`. For an
      // existing item this resolves the already-pending `initializeTask` and
      // returns the real `{ remoteId }` WITHOUT creating anything remotely
      // (only genuinely-new threads hit the adapter's `initialize`). This makes
      // `__internal_load`'s single promise await the real id before resolving,
      // so the first open after reload reliably fetches its messages.
      //
      // The resolution is INLINED here (not extracted to a module-level helper)
      // deliberately: an earlier extracted helper symbol failed to resolve at
      // runtime under Turbopack (`ReferenceError` inside `load`), breaking
      // history loading entirely. Keeping the logic inside the closure avoids
      // any cross-symbol reference.
      let remoteId: string | null;
      {
        const item = aui.threadListItem();
        const state = item.getState();
        if (state.remoteId) {
          remoteId = state.remoteId;
        } else if (state.status === "new" || state.status === "deleted") {
          // Nothing persisted to load; must NOT call `initialize()` (would
          // create a remote thread just by opening an empty composer).
          remoteId = null;
        } else {
          try {
            const { remoteId: resolved } = await item.initialize();
            remoteId = resolved ?? null;
          } catch {
            // Initialization failed (e.g. backend down) — re-read state once.
            remoteId = null;
          }
          if (!remoteId) {
            remoteId = aui.threadListItem().getState().remoteId ?? null;
          }
        }
      }
      if (!remoteId) return { messages: [] };
      const rows = await fetchRows(remoteId);
      const items = rows.map(decodeRow);
      // `fromBranchableArray` requires every item to carry an `id`; our decoded
      // messages always do (the server row id).
      return ExportedMessageRepository.fromBranchableArray(items);
    },

    async append(item: ExportedMessageRepositoryItem) {
      // Ensure the thread exists remotely before persisting messages.
      const { remoteId } = await aui.threadListItem().initialize();
      await postRow(remoteId, {
        id: item.message.id,
        parent_id: item.parentId,
        role: item.message.role,
        content: encodeMessage(item.message),
      });
    },

    // --- Format-aware path (cloud/AI-SDK style); safety net + spec parity. ---
    withFormat<TMessage, TStorageFormat extends Record<string, unknown>>(
      fmt: MessageFormatAdapter<TMessage, TStorageFormat>,
    ) {
      return {
        async load() {
          // Inlined remote-id resolution (see bare `load()` above for why it is
          // not extracted to a module-level helper).
          let remoteId: string | null;
          {
            const item = aui.threadListItem();
            const state = item.getState();
            if (state.remoteId) {
              remoteId = state.remoteId;
            } else if (state.status === "new" || state.status === "deleted") {
              remoteId = null;
            } else {
              try {
                const { remoteId: resolved } = await item.initialize();
                remoteId = resolved ?? null;
              } catch {
                remoteId = null;
              }
              if (!remoteId) {
                remoteId = aui.threadListItem().getState().remoteId ?? null;
              }
            }
          }
          if (!remoteId) return { messages: [] };
          const rows = await fetchRows(remoteId);
          const messages = rows
            .filter((r) => r.format === fmt.format)
            .map((r) =>
              fmt.decode({
                id: r.id,
                parent_id: r.parent_id,
                format: r.format,
                // Backend returns `content` already decoded to a JSON object.
                content: r.content as TStorageFormat,
              }),
            );
          return { messages };
        },

        async append(item: MessageFormatItem<TMessage>) {
          const { remoteId } = await aui.threadListItem().initialize();
          await postRow(remoteId, {
            id: fmt.getId(item.message),
            parent_id: item.parentId,
            content: fmt.encode(item),
          });
        },
      };
    },
  };
}

/**
 * Remote thread-list adapter against `${API_URL}/api/threads*`.
 *
 * Archive/unarchive go through `PATCH {status}` (no `/archive` sub-route).
 * `generateTitle` returns an `AssistantStream` that appends the title produced
 * by `POST /api/threads/{id}/title`.
 */
export function useBackendThreadListAdapter(): RemoteThreadListAdapter {
  const HistoryProvider = useCallback(function HistoryProvider({
    children,
  }: {
    children?: React.ReactNode;
  }) {
    const history = useBackendHistoryAdapter();
    return (
      <RuntimeAdapterProvider adapters={{ history }}>
        {children}
      </RuntimeAdapterProvider>
    );
  }, []);

  return {
    async list() {
      // The thread-list runtime calls this on mount. If the backend is down,
      // throwing here strands the whole app on a blank/crashed page — so catch
      // and return a safe empty list. The sidebar renders empty (and a later
      // successful `list()` after the backend returns will repopulate it).
      try {
        const threads = await apiGet<RemoteThread[]>("/api/threads");
        return {
          threads: threads.map((t) => ({
            status: t.status,
            remoteId: t.id,
            title: t.title,
          })),
        };
      } catch (err) {
        console.warn(
          "[thread-list] Could not load threads (backend unreachable?). " +
            "Rendering an empty sidebar.",
          err,
        );
        return { threads: [] };
      }
    },

    async initialize(threadId) {
      const created = await apiPost<RemoteThread>("/api/threads", {
        localId: threadId,
      });
      return { remoteId: created.id, externalId: undefined };
    },

    async rename(remoteId, newTitle) {
      await apiPatch(`/api/threads/${remoteId}`, { title: newTitle });
    },

    async archive(remoteId) {
      await apiPatch(`/api/threads/${remoteId}`, { status: "archived" });
    },

    async unarchive(remoteId) {
      await apiPatch(`/api/threads/${remoteId}`, { status: "regular" });
    },

    async delete(remoteId) {
      await apiDelete(`/api/threads/${remoteId}`);
    },

    async fetch(threadId) {
      const t = await apiGet<RemoteThread>(`/api/threads/${threadId}`);
      return { status: t.status, remoteId: t.id, title: t.title };
    },

    async generateTitle(remoteId, unstable_messages) {
      const messages = unstable_messages.map((m) => ({
        role: m.role,
        content: m.content.filter(
          (p) => p.type === "text" || p.type === "tool-call",
        ),
      }));
      const { title } = await apiPost<{ title: string }>(
        `/api/threads/${remoteId}/title`,
        { messages },
      );
      return createAssistantStream(async (controller) => {
        controller.appendText(title);
      });
    },

    unstable_Provider: HistoryProvider,
  };
}

// Re-export the base URL for convenience.
export { API_URL };
