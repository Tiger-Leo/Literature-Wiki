import type { ChatModelAdapter } from "@assistant-ui/react";
import { API_URL } from "./api";
import { setChatStatus, clearChatStatus } from "./chat-status";

/**
 * One line of the backend's NDJSON `POST /api/chat` stream (PROTOCOL §1).
 * Response `Content-Type: application/x-ndjson`; each line is one JSON object.
 */
type NdjsonEvent =
  | { type: "status"; label: string }
  | { type: "sources"; sources: SourceRef[] }
  | { type: "delta"; text: string }
  | { type: "done" }
  | { type: "error"; message?: string };

type SourceRef = {
  slug: string;
  citekey?: string;
  layer?: string;
  tier?: string;
  heading_path?: string;
};

/**
 * Inline message shown when the backend is unreachable or returns an error.
 * Yielded as a clean assistant message (with a settled `complete` status) so the
 * composer leaves the running state without throwing to the dev console overlay.
 */
const NETWORK_ERROR_TEXT =
  `⚠️ Could not reach the server at ${API_URL}. ` +
  "Is the backend running and reachable? Please try again.";

/** A user-pressed-Cancel abort — distinguish it from a network failure. */
function isUserAbort(signal: AbortSignal | undefined, err: unknown): boolean {
  if (signal?.aborted) return true;
  return err instanceof DOMException && err.name === "AbortError";
}

/**
 * Streaming chat adapter for the agentic-search backend.
 *
 * The backend answers ONLY by agentic filesystem navigation (no embeddings/RAG)
 * and streams **NDJSON** (newline-delimited JSON), one event per line.
 * We read `response.body`, buffer partial lines, `JSON.parse` each complete
 * line, and maintain two pieces of state:
 *   - `answer`: concatenation of every `delta.text` chunk (the message text).
 *   - `status`: the latest `status.label` (surfaced to the UI via the
 *     module-level chat-status store; the Thread shows a spinner pill while the
 *     answer is still empty).
 *
 * On each event we yield `{ content: [{ type: "text", text: answer }] }`. While
 * `answer` is empty the content stays empty and the UI shows the status pill;
 * once the first delta arrives the status is cleared and the answer streams in.
 */
export const chatAdapter: ChatModelAdapter = {
  async *run({ messages, abortSignal }) {
    let answer = "";
    let sources: SourceRef[] = [];
    let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages }),
        signal: abortSignal,
      });

      if (!res.ok) {
        // Non-OK HTTP response (e.g. 500/502/404). Surface a clean inline
        // message and settle, rather than throwing to the console overlay.
        const body = await res.text().catch(() => "");
        const detail = body ? ` (HTTP ${res.status}: ${body.slice(0, 300)})` : "";
        yield {
          content: [{ type: "text", text: NETWORK_ERROR_TEXT + detail }],
          status: { type: "complete", reason: "stop" },
        };
        return;
      }

      if (!res.body) {
        const text = await res.text().catch(() => "");
        yield {
          content: [{ type: "text", text: text || NETWORK_ERROR_TEXT }],
          status: { type: "complete", reason: "stop" },
        };
        return;
      }

      reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      // Set when the stream carried an explicit `{type:"error"}` event so we can
      // fall through to the graceful inline message after the loop.
      let backendError: string | null = null;

      const flushLine = (line: string): boolean => {
        const trimmed = line.trim();
        if (!trimmed) return false;
        let ev: NdjsonEvent;
        try {
          ev = JSON.parse(trimmed) as NdjsonEvent;
        } catch {
          // Tolerate a stray non-JSON line rather than aborting the stream.
          return false;
        }
        switch (ev.type) {
          case "status":
            // Only surface the stage label while no answer text has arrived.
            if (!answer) setChatStatus(ev.label);
            return false;
          case "sources":
            sources = ev.sources ?? [];
            return false;
          case "delta":
            if (ev.text) {
              answer += ev.text;
              clearChatStatus();
              return true;
            }
            return false;
          case "error":
            // Record the error and stop processing further lines; handled below
            // as a graceful inline message instead of a thrown exception.
            backendError = ev.message || "The backend reported an error.";
            return false;
          case "done":
          default:
            return false;
        }
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        let nl: number;
        let shouldYield = false;
        while ((nl = buffer.indexOf("\n")) !== -1) {
          const line = buffer.slice(0, nl);
          buffer = buffer.slice(nl + 1);
          if (flushLine(line)) shouldYield = true;
        }
        if (backendError) break;

        // Yield the growing answer (only matters once it's non-empty).
        if (shouldYield) {
          yield {
            content: [{ type: "text", text: answer }],
            metadata: { custom: { sources } },
          };
        }
      }

      // Flush any trailing partial line.
      if (!backendError) {
        buffer += decoder.decode();
        if (buffer.trim() && flushLine(buffer)) {
          yield {
            content: [{ type: "text", text: answer }],
            metadata: { custom: { sources } },
          };
        }
      }

      if (backendError) {
        // Append (or set) a graceful note so the user sees what happened and the
        // message settles cleanly — no throw, no console overlay.
        const text = answer
          ? `${answer}\n\n⚠️ ${backendError}`
          : `⚠️ ${backendError}`;
        yield {
          content: [{ type: "text", text }],
          metadata: { custom: { sources } },
          status: { type: "complete", reason: "stop" },
        };
        return;
      }

      // Final emit so the message settles even if the last line wasn't a delta.
      yield {
        content: [{ type: "text", text: answer }],
        metadata: { custom: { sources } },
      };
    } catch (err) {
      // User pressed Cancel / switched threads → let the framework treat it as a
      // cancellation (it inspects `abortSignal.aborted` per-yield and on throw).
      if (isUserAbort(abortSignal, err)) return;

      // Network failure / unexpected error. If we already streamed text, append
      // a note; otherwise show the standalone error message. Either way settle
      // cleanly and DO NOT rethrow (avoids the dev console error overlay).
      const text = answer
        ? `${answer}\n\n${NETWORK_ERROR_TEXT}`
        : NETWORK_ERROR_TEXT;
      yield {
        content: [{ type: "text", text }],
        ...(sources.length ? { metadata: { custom: { sources } } } : undefined),
        status: { type: "complete", reason: "stop" },
      };
      return;
    } finally {
      clearChatStatus();
      reader?.releaseLock();
    }
  },
};
