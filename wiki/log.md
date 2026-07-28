# Wiki Log

Append-only log of all wiki operations.

## Format

```
## [YYYY-MM-DD] ingest | Author et al. (Year) — Short Title
## [YYYY-MM-DD] synthesis | Synthesis Title
## [YYYY-MM-DD] lint | Full lint pass — N issues found, N fixed
## [YYYY-MM-DD] query | Query title (saved to wiki/synthesis/...)
```

---

## 2026-07-28 | config | 将 raw_pdfs/ 整体加入 .gitignore（含 pdf_sources.json）
## 2026-07-28 | config | 调整 pdf_sources.json PDF 来源映射（13 篇论文，manifest → PDF → markdown → metadata 全链路一致）
