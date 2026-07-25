"use client";

import { useAuiState } from "@assistant-ui/react";
import { Download } from "lucide-react";
import { API_URL } from "@/lib/api";

/**
 * Downloads the current thread's conversation as Markdown via
 * `GET /api/threads/{id}/export?format=md`. Disabled until the active thread
 * has a backend `remoteId` (i.e. it has been persisted at least once).
 */
export function ExportButton() {
  const remoteId = useAuiState((s) => s.threadListItem?.remoteId) as
    | string
    | undefined;

  const onExport = async () => {
    if (!remoteId) return;
    const res = await fetch(
      `${API_URL}/api/threads/${remoteId}/export?format=md`,
    );
    if (!res.ok) {
      console.error(`Export failed: ${res.status} ${res.statusText}`);
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `thread-${remoteId}.md`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  return (
    <button
      type="button"
      onClick={onExport}
      disabled={!remoteId}
      title={remoteId ? "Export conversation as Markdown" : "Nothing to export yet"}
      className="flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm text-zinc-600 transition-colors hover:bg-zinc-200/70 disabled:cursor-not-allowed disabled:opacity-40 dark:text-zinc-300 dark:hover:bg-white/10"
    >
      <Download className="h-4 w-4" />
      Export
    </button>
  );
}
