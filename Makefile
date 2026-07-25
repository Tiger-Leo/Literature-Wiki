# literature-wiki — dev/build orchestration
# Targets are domain-agnostic and read config from `.env` (see .env.example).
# Run `make help` for a summary.

# Load .env if present (export vars to recipe sub-shells).
ifneq (,$(wildcard .env))
include .env
export
endif

RAG_PORT ?= 8000
PY ?= python

# Resolve tools, with a clear error if missing.
PNPM := $(shell command -v pnpm 2>/dev/null)
UVICORN_OK := $(shell $(PY) -c "import uvicorn" 2>/dev/null && echo yes)

.DEFAULT_GOAL := help
.PHONY: help install search-index api web-dev web-build web-start serve build-serve clean

# Pass-through args for build-serve, e.g. `make build-serve ARGS="--mode dev"`.
ARGS ?=

help: ## Show this help
	@echo "literature-wiki targets:"
	@echo "  install       Install python (rag/requirements.txt) + web (pnpm) deps"
	@echo "  search-index  Rebuild the frontend search index (export_wiki)"
	@echo "  api           Run the agentic FastAPI backend (uvicorn, 0.0.0.0:$(RAG_PORT))"
	@echo "  web-dev       Run the Next.js dev server (web/)"
	@echo "  web-build     Production build of the frontend (web/)"
	@echo "  web-start     Serve the production build (web/)"
	@echo "  serve         Run api (background) + web together via scripts/serve.sh"
	@echo "  build-serve   One-shot deterministic build+serve (scripts/build_and_serve.py)"
	@echo "                  e.g. make build-serve ARGS=\"--mode dev --verify-only\""
	@echo "  clean         Remove web/.next"
	@echo ""
	@echo "Note: the backend is agentic-search only — there is NO embedding index"
	@echo "      build step (no 'make index' / build_index)."

install: ## Install backend + frontend dependencies
	@echo ">> Installing Python deps (rag/requirements.txt)..."
	$(PY) -m pip install -r rag/requirements.txt
ifeq ($(PNPM),)
	@echo "!! pnpm not found — skipping frontend deps. Install pnpm: https://pnpm.io/installation"
else
	@echo ">> Installing frontend deps (web/)..."
	cd web && pnpm install
endif

search-index: ## Rebuild the frontend search index
	@echo ">> Exporting wiki search index (scripts/export_wiki.py)..."
	$(PY) scripts/export_wiki.py

api: ## Run the agentic FastAPI backend
ifeq ($(UVICORN_OK),yes)
	@echo ">> Starting API on 0.0.0.0:$(RAG_PORT) (uvicorn rag.server:app)..."
	$(PY) -m uvicorn rag.server:app --host 0.0.0.0 --port $(RAG_PORT)
else
	@echo "!! uvicorn not importable under '$(PY)'. Run 'make install' or activate your env."; exit 1
endif

web-dev: ## Run the Next.js dev server
ifeq ($(PNPM),)
	@echo "!! pnpm not found. Install pnpm: https://pnpm.io/installation"; exit 1
else
	@echo ">> Starting Next.js dev server (web/)..."
	cd web && pnpm dev
endif

web-build: ## Production build of the frontend
ifeq ($(PNPM),)
	@echo "!! pnpm not found. Install pnpm: https://pnpm.io/installation"; exit 1
else
	@echo ">> Building frontend (web/)..."
	cd web && NODE_OPTIONS="" pnpm build
endif

web-start: ## Serve the production build
ifeq ($(PNPM),)
	@echo "!! pnpm not found. Install pnpm: https://pnpm.io/installation"; exit 1
else
	@echo ">> Serving production build (web/)..."
	cd web && pnpm start
endif

serve: ## Run api + web together (api in background, web in foreground)
	@echo ">> Launching api + web via scripts/serve.sh..."
	bash scripts/serve.sh

build-serve: ## One-shot deterministic build+serve (scripts/build_and_serve.py)
	@echo ">> Running scripts/build_and_serve.py $(ARGS)..."
	$(PY) scripts/build_and_serve.py $(ARGS)

clean: ## Remove build artifacts
	@echo ">> Removing web/.next..."
	rm -rf web/.next
