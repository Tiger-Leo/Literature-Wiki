// Backend base URL, resolved in priority order:
//   1. NEXT_PUBLIC_API_URL — explicit absolute override (build-time).
//   2. Runtime: the same host the page was served from, on the backend port. This
//      lets the app work from localhost, LAN, or ZeroTier WITHOUT baking an IP — the
//      browser talks to <its-own-host>:<backend-port>, and the backend's CORS is open.
//      The backend port comes from NEXT_PUBLIC_BACKEND_PORT (default 8000 for dev;
//      the deployment build sets it to 31491).
//   3. SSR / no-window fallback.
const BACKEND_PORT = process.env.NEXT_PUBLIC_BACKEND_PORT ?? "8000";

function resolveApiUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_API_URL;
  if (explicit) return explicit;
  if (typeof window !== "undefined" && window.location?.hostname) {
    return `${window.location.protocol}//${window.location.hostname}:${BACKEND_PORT}`;
  }
  return `http://localhost:${BACKEND_PORT}`;
}

export const API_URL = resolveApiUrl();

/** Thread metadata as returned by the backend. */
export type RemoteThread = {
  id: string;
  title: string;
  status: "regular" | "archived";
};

/** Stored message row as returned by `GET /api/threads/{id}/messages`. */
export type StoredMessageRow = {
  id: string;
  parent_id: string | null;
  role?: string;
  format: string;
  content: unknown;
};

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(
      `API ${res.status} ${res.statusText} for ${res.url}${body ? `: ${body}` : ""}`,
    );
  }
  return (await res.json()) as T;
}

export const apiGet = async <T>(path: string, init?: RequestInit): Promise<T> =>
  handle<T>(await fetch(`${API_URL}${path}`, { ...init, method: "GET" }));

export const apiPost = async <T>(
  path: string,
  body?: unknown,
  init?: RequestInit,
): Promise<T> =>
  handle<T>(
    await fetch(`${API_URL}${path}`, {
      ...init,
      method: "POST",
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  );

export const apiPatch = async <T>(
  path: string,
  body?: unknown,
  init?: RequestInit,
): Promise<T> =>
  handle<T>(
    await fetch(`${API_URL}${path}`, {
      ...init,
      method: "PATCH",
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
      body: body === undefined ? undefined : JSON.stringify(body),
    }),
  );

export const apiDelete = async <T>(
  path: string,
  init?: RequestInit,
): Promise<T> =>
  handle<T>(await fetch(`${API_URL}${path}`, { ...init, method: "DELETE" }));
