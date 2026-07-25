# Frontend implementation notes

Domain-agnostic Next.js (App Router) frontend for the literature wiki, built on
**assistant-ui 0.14.7** / **@assistant-ui/core 0.2.4**. It exposes **three
surfaces** — Chat (`/`, RAG backend), Search (`/search`, client-side), Browse
(`/wiki`, `/wiki/[slug]`, filesystem) — behind a persistent top nav. The Chat
backend contract is in `INTEGRATION.md`.

## Route inventory

| Route | Component | Backend? | Notes |
|---|---|---|---|
| `/` | `app/page.tsx` | Yes | Chat. Thread-history sidebar + chat column; mobile hamburger → slide-in drawer (scrim). |
| `/search` | `app/search/page.tsx` | No | Client-side MiniSearch over `public/wiki-index.json`. Reads `?q=`. |
| `/wiki` | `app/wiki/page.tsx` (+ `wiki/layout.tsx`) | No | Two-pane shell; right pane = section-card overview. |
| `/wiki/[slug]` | `app/wiki/[slug]/page.tsx` | No* | Server component; reading column + right "On this page" TOC. `*`cached `/api/page/{slug}` fallback only when an API base is configured. |

The whole `/wiki` segment is wrapped by `wiki/layout.tsx` (server component): it
reads pages via `wiki-fs.ts`, groups by layer, and renders the persistent
two-pane shell (left `WikiSidebar`, right `children`).

## Files

| File | Role |
|---|---|
| `src/lib/site-config.ts` | Single source of branding strings from `NEXT_PUBLIC_*` (build-time). |
| `src/lib/api.ts` | `API_URL` resolution + `apiGet/apiPost/apiPatch/apiDelete` JSON helpers + `RemoteThread` / `StoredMessageRow` types. |
| `src/lib/chat-adapter.ts` | Streaming `ChatModelAdapter`. POSTs `{messages, deep, mode}` to `/api/chat`, reads `response.body` with a reader + `TextDecoder`, parses **NDJSON** lines (status/sources/delta/done/error), accumulates `delta.text`, yields `{content:[{type:"text",text:accumulated}], metadata:{custom:{sources}}}`. Exports `deepRead` / `agentMode` toggle flags. Errors degrade to a clean inline message (no throw). |
| `src/lib/chat-status.ts` | Module-level store for the pipeline-stage status pill shown while the answer is still empty. |
| `src/lib/thread-list-adapter.tsx` | `useBackendThreadListAdapter()` returning a `RemoteThreadListAdapter` (list/initialize/rename/archive/unarchive/delete/fetch/generateTitle) + `unstable_Provider` injecting a `ThreadHistoryAdapter` via `withFormat`. |
| `src/lib/runtime-provider.tsx` | `MyRuntimeProvider` = `useRemoteThreadListRuntime({ runtimeHook: () => useLocalRuntime(chatAdapter), adapter })` wrapped in `AssistantRuntimeProvider`. |
| `src/lib/wiki-fs.ts` | Server-only filesystem reader for `WIKI_DIR` — `listPages()` / `getPage(slug)`, frontmatter parsing. |
| `src/lib/wiki-ui.ts` | Layer label/rank/description helpers + default expanded/collapsed layer sets + shared chip class. |
| `src/lib/wikilinks.ts`, `callouts.ts`, `math.ts` | remark/rehype plugins for `[[wikilinks]]`, Obsidian callouts, and KaTeX. |
| `src/components/nav.tsx` | Persistent top nav (Search / Browse / Chat) using Next `<Link>`; lives inside the runtime provider so navigation keeps the runtime mounted. |
| `src/components/wiki-sidebar.tsx` | Client left nav for `/wiki`: collapsible groups by layer + counts + active-page highlight (via `usePathname`), search box → `/search`, mobile slide-in drawer (hamburger + scrim). |
| `src/components/wiki-toc.tsx` | Client "On this page" TOC: scans `#wiki-article` `h2/h3`, assigns ids, smooth-scroll + IntersectionObserver active highlight. Desktop only. |
| `src/components/wiki-markdown.tsx` | Shared client markdown renderer (`[[wikilinks]]`, callouts, GFM, KaTeX) + `WIKI_PROSE_CLASS`. |
| `src/components/wiki-back-nav.tsx`, `markdown-link.tsx` | Wiki nav/link helpers. |
| `src/components/assistant-ui/markdown-text.tsx` | `MarkdownText` using `MarkdownTextPrimitive` + `remark-gfm`, Tailwind-styled. |
| `src/components/assistant-ui/thread.tsx` | Gemini-styled `Thread` (greeting + radial glow, pill composer, deep/agentic toggles, status pill, full-width markdown replies, hover copy ActionBar). |
| `src/components/assistant-ui/thread-list.tsx` | Thread-history sidebar (`ThreadListPrimitive` + `ThreadListItemPrimitive`) with New + rename (window.prompt) + delete; optional `onNavigate` prop fires on new-chat/selection (mobile drawer close). |
| `src/components/sources-panel.tsx` | Renders the `sources` provenance carried in chat message metadata. |
| `src/components/export-button.tsx` | Downloads `/api/threads/{id}/export?format=md` as a Blob; disabled until the active thread has a `remoteId`. |
| `src/app/layout.tsx` | Wraps children in `MyRuntimeProvider` + top `Nav`. |
| `src/app/page.tsx` | `"use client"` Chat layout: persistent thread-list sidebar (desktop) / hamburger + slide-in drawer with scrim (mobile), main column (header w/ ExportButton + Thread). |

## Verified assistant-ui exports / signatures (0.14.7 / core 0.2.4)

Verified by reading the installed `.d.ts` files (not docs):

- **Runtime**: `useLocalRuntime(chatModel, options?)`, `useRemoteThreadListRuntime({ runtimeHook, adapter })`, `AssistantRuntimeProvider` — all from `@assistant-ui/react`.
- **Adapters/types**: `ChatModelAdapter` (`run({messages, abortSignal, ...})` returns Promise **or** `AsyncGenerator<ChatModelRunResult, void>`), `RemoteThreadListAdapter` (fields exactly: `list/rename/archive/unarchive/delete/initialize/generateTitle/fetch/unstable_Provider`; `generateTitle` returns `Promise<AssistantStream>`; `list` returns `{threads:[{status,remoteId,title,externalId?}]}`), `ThreadHistoryAdapter` (has `load/append/withFormat?`), `MessageFormatAdapter<TMessage,TStorageFormat>` (`format/encode/decode/getId`), `MessageFormatItem` (`{parentId, message}`).
- **Context injection**: `RuntimeAdapterProvider` (`adapters={{ history }}`) — confirmed export from `@assistant-ui/react`.
- **Store**: `useAui()` returns the augmented `AssistantClient`; `aui.threadListItem()` returns a `ThreadListItemRuntime` with `initialize(): Promise<{remoteId}>`, `getState(): ThreadListItemState` (`.remoteId`, `.title`), `rename(title)`. `useAuiState((s) => s.threadListItem?.remoteId)` reads the active thread's remoteId reactively.
- **Streaming**: `createAssistantStream(cb)` from `assistant-stream`; controller has `appendText(delta)`.
- **Primitives** (namespace members confirmed): `ThreadPrimitive.{Root,Viewport,Messages,If,Empty}`, `ComposerPrimitive.{Root,Input,Send,Cancel}`, `MessagePrimitive.{Root,Parts,If}`, `ActionBarPrimitive.{Root,Copy}`, `ThreadListPrimitive.{Root,New,Items}`, `ThreadListItemPrimitive.{Root,Trigger,Title,Delete}`.
- **Markdown**: `@assistant-ui/react-markdown` exports **`MarkdownTextPrimitive`** (there is **no** `makeMarkdownText` helper in 0.14.0). Props are spread `react-markdown` `Options` minus `components/children` plus `className`, `smooth`, `components.{SyntaxHighlighter,CodeHeader}`.

## Deviations / decisions forced by 0.14.7

1. **No `makeMarkdownText`** — used `MarkdownTextPrimitive` directly inside a `MarkdownText` component, wired as `MessagePrimitive.Parts components={{ Text: MarkdownText }}`.
2. **`AuiIf` exists** but the simpler `ThreadPrimitive.If` / `MessagePrimitive.If` (marked `@deprecated`, still functional) were used for empty/running/copied conditional rendering — they type-check and build clean.
3. **`ThreadListItemPrimitive.Title` accepts only `fallback`, not `className`** — wrapped it in a styled `<span>` for truncation.
4. **`unstable_Provider`'s children prop must be optional** (`children?: ReactNode`) to satisfy `ComponentType<PropsWithChildren>`.
5. **Rename** has no built-in primitive button → implemented with `window.prompt` + `aui.threadListItem().rename()` (the modern `useAui` path; avoids the deprecated `useThreadListItemRuntime`).
6. **History persistence** uses the `withFormat` path (the official cloud-adapter shape). The bare `ThreadHistoryAdapter.load/append` are safe no-ops since the local runtime always calls `withFormat`.
7. **No global assistant-ui stylesheet ships** (only `react-markdown/styles/dot.css`); styling is 100% Tailwind 4 utility classes. Nothing imported beyond the existing `globals.css`.

## Validation

- `pnpm exec tsc --noEmit` → **clean** (0 errors).
- `pnpm build` → **succeeds**; Search and every `/wiki/[slug]` are prerendered as static content (Chat is client-rendered).
  - Note: the build worker crashes if `NODE_OPTIONS` contains `-r <preload>` (an environment-level OpenClaw proxy preload, unrelated to this code). Run with `NODE_OPTIONS="" pnpm build` if you hit `ERR_WORKER_INVALID_EXEC_ARGV`. `pnpm dev` is unaffected.
  - **Restart after every rebuild.** A `pnpm start` server holds the previous `.next`; serving it against a fresh build manifest 404s the hashed CSS chunks (→ unstyled pages). Stop, rebuild, then start again.

## How to run

```bash
# backend (sci env, from literature-wiki/) — only needed for the Chat surface:
uvicorn rag.server:app --port 8000
# frontend (Search + Browse work with no backend):
cd web && WIKI_DIR=../wiki pnpm dev    # http://localhost:3000
#   Demo wiki:  WIKI_DIR=../examples/demo-wiki/wiki pnpm dev
```

Set the backend URL with `NEXT_PUBLIC_API_URL` / `NEXT_PUBLIC_BACKEND_PORT`, the
wiki directory with `WIKI_DIR`, and branding via `NEXT_PUBLIC_SITE_*`. All
`NEXT_PUBLIC_*` vars are baked in at build time — set them before `pnpm build`.
