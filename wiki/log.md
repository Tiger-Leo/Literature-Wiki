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
## 2026-07-28 | manifest | 从真实文献库重新生成 pdf_sources.json
- 源目录: C:\Users\pc\OneDrive\【我的科研】\literature
- 旧条目: 13（全部指向 E:\Desktop\Desktop\test\ 测试目录）
- 新条目: 3,538（来自真实文献库，含中英文论文）
- 中文文件名处理: 添加 pypinyin 拼音转写，避免中文信息丢失
- 排除目录: .obsidian, 【Typora Notes】, 【笔记检索】, 【数据统计】
- 已有 markdown 协调: 12/13 篇 metadata 路径已更新至真实目录
- 未匹配: Miranda-Agrippino et al 2025（文献库仅有 2026 版）
- 转换: 未进行（仅 manifest）
