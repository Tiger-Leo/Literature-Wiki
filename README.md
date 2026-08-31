# 📚 Literature Wiki · 文献维基

[![English](https://img.shields.io/badge/Readme-English-blue)](README_en.md)

一个**开箱即用的 AI 原生文献知识库模板**——将学术 PDF 合集自动构建为按主题组织的**维基百科式综合页面**，由 Claude Code 多代理流水线驱动。

> **灵感来源**：[karpathy/llm-wiki](https://github.com/karpathy/llm-wiki)：*"LLM 不只是查询时检索原始文档，而是增量构建和维护一个持久化的维基……知识一次编译，持续更新，而不是每次查询重新推导。"*

> **当前维护者**：刘岳虎（西安石油大学经济管理学院），研究方向：产业融合、数实融合、技术融合、文化产业。

---

## 🚀 快速开始

```powershell
# 1. 链接你的 PDF 目录（一次性）
python scripts/link_pdfs.py "<你的PDF目录>" --mode manifest

# 2. 批量转化 PDF → Markdown（日常最常用）
python scripts/batch_convert.py 30 --skip dissertation,book

# 3. 构建维基
/wiki-build
```

> 详细指南：[docs/quick-start.md](docs/quick-start.md)

---

## 🏗️ 三层架构

```
raw_pdfs/              不可变源 PDF（外部存放，通过 pdf_sources.json 映射）
    └── pdf_sources.json    path → slug → type → pages → converted

raw_markdown/          机器可读的 Markdown 转换
    ├── papers/             .md 文件（MinerU 云端 API）
    ├── metadata/           .json 元数据（含 doc_type、页数、SHA256）
    └── assets/             预留（MinerU 临时图片自动清理）

wiki/                  结构化知识 · 维基百科式综合页面
    ├── concepts/           概念页面（交付物）
    ├── debates/            争论页面
    ├── mechanisms/         机制页面
    ├── methods/            方法页面
    ├── measures/           测量页面
    ├── synthesis/          跨主题综合页面
    ├── sources/            论文文献锚点
    ├── schema/             规范与模板
    └── log.md              仅追加的构建/检查历史
```

---

## ⚡ 日常操作

### PDF 管理

```powershell
# 生成 / 更新路径映射表（不移动源文件）
python scripts/link_pdfs.py "<你的PDF目录>" --mode manifest

# 排除某些子目录
python scripts/link_pdfs.py "<你的PDF目录>" --mode manifest --exclude "<路径>\草稿"
```

> 排除目录也可直接编辑 `pdf_sources.json` 中的 `exclude_dirs` 数组，下次扫描自动生效。

### PDF 转化

> MinerU 免费额度 **2000 页/天**。全库 ~3,500 篇、~9 万页。建议每日 `--skip dissertation,book`，优先期刊论文。

```powershell
# 批量转化（按页数由少到多排序）
python scripts/batch_convert.py                              # 默认 20 篇（全部类型）
python scripts/batch_convert.py 30 --skip dissertation,book  # 排除学位论文和图书（推荐日常）
python scripts/batch_convert.py 20 --only journal-article    # 只转化期刊论文
python scripts/batch_convert.py 5 --language en              # 英文文献

# 单篇转化
python scripts/convert_pdf_to_markdown.py "Author - YYYY - Title.pdf" --update-manifest --overwrite

# 查看进度
python -c "import json; d=json.load(open('raw_pdfs/pdf_sources.json','r',encoding='utf-8')); total=len(d['pdfs']); done=sum(1 for v in d['pdfs'].values() if v.get('converted')); print(f'{done}/{total} ({done/total*100:.1f}%)')"
```

**类型过滤：**

# 批量转化（按页数由少到多排序）

python scripts/batch_convert.py                              # 默认 20 篇（全部类型）
python scripts/batch_convert.py 30 --skip dissertation,book  # 排除学位论文和图书（推荐日常）
python scripts/batch_convert.py 20 --only journal-article    # 只转化期刊论文
python scripts/batch_convert.py 5 --language en              # 英文文献

# 单篇转化

python scripts/convert_pdf_to_markdown.py "Author - YYYY - Title.pdf" --update-manifest --overwrite

# 查看进度

python -c "import json; d=json.load(open('raw_pdfs/pdf_sources.json','r',encoding='utf-8')); total=len(d['pdfs']); done=sum(1 for v in d['pdfs'].values() if v.get('converted')); print(f'{done}/{total} ({done/total*100:.1f}%)')"

| 参数       | 示例                         | 效果                 |
| ---------- | ---------------------------- | -------------------- |
| `--skip` | `--skip dissertation,book` | 排除学位论文和图书   |
| `--only` | `--only journal-article`   | 只转化期刊论文       |
| `--only` | `--only dissertation,book` | 只转化学位论文和图书 |

`--only` 和 `--skip` 互斥，`--only` 优先。

| 脚本                           | 参数                              | 说明                          |
| ------------------------------ | --------------------------------- | ----------------------------- |
| `batch_convert.py`           | `N` (默认 20)                   | 转化篇数                      |
|                                | `--language ch\|en`              | 文档语言                      |
|                                | `--only type,…`                | 只转化指定类型                |
|                                | `--skip type,…`                | 跳过指定类型                  |
| `convert_pdf_to_markdown.py` | `--converter mineru\|markitdown` | 转化引擎                      |
|                                | `--language ch\|en`              | 文档语言                      |
|                                | `--update-manifest`             | 成功后标记`converted: true` |
|                                | `--overwrite`                   | 覆盖已有输出                  |

### 文档类型自动判别

每条 PDF 自动标注 `type` 字段（`path → slug → type → pages → converted`），判别逻辑在 `pipeline_utils.py` → `classify_doc_type()`：

| type                | 判别依据                                          | 数量   |
| ------------------- | ------------------------------------------------- | ------ |
| `journal-article` | 默认（期刊目录）                                  | ~3,300 |
| `dissertation`    | 100–200 页，非出版社目录                         | ~130   |
| `book`            | 出版社目录（Springer、Cambridge UP…）或 ≥200 页 | ~55    |
| `book-chapter`    | 出版社目录且 <60 页                               | ~18    |

所有入口（`link_pdfs.py`、`detect_new_pdfs.py`、`convert_pdf_to_markdown.py`）均自动调用。

### 维基构建与查询

```bash
/wiki-build          # 默认 2 轮多代理构建
/wiki-build 3        # 3 轮（更深覆盖）
/wiki-query          # 从维基层回答研究问题
/wiki-synthesis      # 保存一次性洞察为单独页面
/wiki-update-db      # 检查、验证、维护
/wiki-serve          # 构建搜索索引并启动 Web 界面
```

### 验证脚本

```bash
python -m py_compile scripts/*.py                         # 编译检查
python scripts/check_links.py wiki raw_markdown           # 断链检测
python scripts/check_orphans.py wiki                      # 孤立页面
python scripts/validate_frontmatter.py wiki               # Frontmatter
python scripts/export_wiki.py --wiki-dir wiki             # 搜索索引
```

### 定时任务（SessionStart 钩子）

项目内置**每周一次**的定时任务，由 Claude Code 的 `SessionStart` 钩子在「周一 ≥7:00（北京时间）」自动触发，并用 ISO 周戳去重（每周最多执行一次）。其中「检查本周任务是否已完成」的提醒**仅在本周第一次打开项目时打印**，同周后续打开保持静默：

| 任务                   | 脚本                               | 完成标记                             |
| ---------------------- | ---------------------------------- | ------------------------------------ |
| 扫描新 PDF 并更新清单  | `scripts/auto-sync-pdfs.ps1`     | `.cache/pdf-sync-week.txt`         |
| 更新 Zotero 语义搜索库 | `scripts/auto-update-db.ps1`     | `.cache/zotero-db-update-week.txt` |
| 检查本周任务是否已完成 | `scripts/check-weekly-tasks.ps1` | `.cache/weekly-check-week.txt`     |

**钩子配置**（写入 `.claude/settings.json` 或 `.claude/settings.local.json`）：

```json
{
  "hooks": {
    "SessionStart": [
      { "hooks": [{ "type": "command", "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"<项目路径>\\scripts\\auto-update-db.ps1\"" }] },
      { "hooks": [{ "type": "command", "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"<项目路径>\\scripts\\auto-sync-pdfs.ps1\"" }] },
      { "hooks": [{ "type": "command", "command": "powershell -NoProfile -ExecutionPolicy Bypass -File \"<项目路径>\\scripts\\check-weekly-tasks.ps1\"" }] }
    ]
  }
}
```

> ⚠️ `.claude/settings.local.json` 默认被 git 忽略（本机私有配置）；如需跨机器同步钩子，请写入被跟踪的 `.claude/settings.json`。

**手动检查本周任务是否已完成**：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\check-weekly-tasks.ps1
```

### Zotero 语义搜索

```powershell
zotero-mcp update-db                # 增量更新
zotero-mcp update-db --fulltext     # 含全文提取
zotero-mcp update-db --force-rebuild  # 全量重建
zotero-mcp db-status                # 查看状态
```

> 每周一 7:00 后打开项目时自动触发增量更新（`SessionStart` 钩子 → `auto-update-db.ps1`）。需 Zotero 桌面版运行中。

---

## 🎯 核心理念：不是 RAG，不是摘要存档

大多数文献管理工具属于两类：

- **PDF 存档**——按文件夹存储，需要时搜索。
- **RAG 系统**——文档被切块和嵌入，查询时检索并生成回答。

**Literature Wiki 两者都不是。** 它是一个持久化、持续演进的维基，每次构建产出聚焦的综合页面，由多个代理并行编写和审查，在每个主题上整合整个合集。维基是主要界面——不是 PDF，不是嵌入索引。

当你问「不同论文如何概念化 X？」——回答已经以维基百科式页面预先组织在 `wiki/concepts/concept-x.md`，具有百科式引导段落、整合多篇论文的子主题章节和明确的当前评估标注。无需检索步骤。

---

## 🤖 多代理构建流水线

`/wiki-build` 以轮次为基础、文件交接为机制运行：

```
Phase 0  扫描 & 工作区设置
Phase 1  PDF → raw_markdown（新论文）
Phase 2  源页面——并行编写，轻量审查
Phase 3  轮次计划——单个规划子代理产出页面列表与集群
Phase 4  轮次执行
           Stage A: 策展人——含大纲和抽查锚点的页面简报
           Stage B: 集群编写者（并行）——维基百科式页面草稿
           Stage C: 集群审查者（并行）——三镜头审查，附带裁决
           Stage D: 修订者（并行）——应用修复；PASS 页面直接通过
         根据需要重复第 2–3 轮
Phase 5  决定是否开启下一轮
Phase 6  定稿——复制轮次输出到 wiki/，运行全面检查，更新索引
```

所有中间产物存放在 `agent_tasks/wikipedia-rewrite_<DATE><HHMM>/`。子代理通过写文件通信；编排器收集 ≤200 字的状态摘要。

---

## 🧠 核心设计原则

### 角色分离

| 角色                    | 职责                                                   |
| ----------------------- | ------------------------------------------------------ |
| **LLM（编排器）** | 规划、生成子代理、收集状态、决定修订/轮次              |
| **LLM（子代理）** | 策展简报、编写/审查/修订页面——文件交接，≤200 字返回 |
| **脚本**          | 确定性操作：验证、检查、导出——不做学术判断           |
| **研究者**        | 研究方向、论文挑选、校准最终可信度                     |

### 维基百科式综合标准

详见 [`.claude/skills/wiki-build/rubric.md`](.claude/skills/wiki-build/rubric.md)：

- **百科式引导段落**——定义主题、说明重要性、预览页面。不使用项目符号。
- **主题骨干**——章节标题命名子主题，**而非论文**。没有「论文观点」章节。
- **整合引用**——观点趋同时使用多重引用；仅在独特贡献重要时才在行文中指名。
- **三个知识层可见但不占主导**——论文声明 `[[slug]]` / 跨论文模式（斜体） / 当前评估（标注块）。

---

## 🌐 Web 界面（可选）

构建完维基后，启动搜索 + 浏览界面（**无需 AI、无需后端**）：

```bash
make install
python scripts/export_wiki.py
make web-build
make web-start   # http://localhost:3000
```

加上聊天界面（需要生成式端点）：

```bash
python scripts/build_and_serve.py   # API :8000 + Web :3000
```

在 `.env` 中配置品牌和端点（参考 `.env.example`）。

---

## 📋 脚本清单

| 脚本                                   | 功能                                                   |
| -------------------------------------- | ------------------------------------------------------ |
| `scripts/link_pdfs.py`               | 扫描外部 PDF 目录，生成`pdf_sources.json` 路径映射表 |
| `scripts/detect_new_pdfs.py`         | 增量检测新 PDF（每周一自动运行）                       |
| `scripts/convert_pdf_to_markdown.py` | 单篇 PDF → Markdown（MinerU / markitdown）            |
| `scripts/batch_convert.py`           | 批量转化（按页数排序，支持`--skip` 过滤类型）        |
| `scripts/pipeline_utils.py`          | 共享工具：slug、页数、类型分类、manifest 规范化        |
| `scripts/check_links.py`             | 断链检测                                               |
| `scripts/check_orphans.py`           | 孤立页面检测                                           |
| `scripts/validate_frontmatter.py`    | YAML Frontmatter 验证                                  |
| `scripts/export_wiki.py`             | 导出前端搜索索引                                       |
| `scripts/export_metadata.py`         | 导出元数据                                             |

---

## 🗂️ 文档导航

| 文档                                                                      | 内容                         |
| ------------------------------------------------------------------------- | ---------------------------- |
| [docs/quick-start.md](docs/quick-start.md)                                 | 环境设置与首次构建           |
| [docs/architecture.md](docs/architecture.md)                               | 设计原则、分层模型           |
| [docs/pipeline.md](docs/pipeline.md)                                       | 完整 PDF→维基流水线         |
| [docs/wiki-structure.md](docs/wiki-structure.md)                           | 维基目录设计与页面类型       |
| [docs/skills-reference.md](docs/skills-reference.md)                       | 四大技能参考                 |
| [docs/scripts-reference.md](docs/scripts-reference.md)                     | Python 工具脚本参考          |
| [docs/obsidian-integration.md](docs/obsidian-integration.md)               | Obsidian 集成                |
| [docs/scale-up-guide.md](docs/scale-up-guide.md)                           | 规模化指南                   |
| [docs/adaptation-guide.md](docs/adaptation-guide.md)                       | 领域适配指南                 |
| [docs/search-and-browse.md](docs/search-and-browse.md)                     | 零后端搜索+浏览 Web 界面     |
| [docs/web-frontend.md](docs/web-frontend.md)                               | Next.js 前端配置             |
| [docs/rag-backend.md](docs/rag-backend.md)                                 | 可选的智能聊天后端           |
| [docs/deployment.md](docs/deployment.md)                                   | Web UI 和 API 部署           |
| [docs/llm-wiki.md](docs/llm-wiki.md)                                       | 原始灵感（Karpathy）         |
| [.claude/skills/wiki-build/rubric.md](.claude/skills/wiki-build/rubric.md) | **维基百科式质量标准** |

---

## 🔗 导航约定（写给 AI 代理）

1. `CLAUDE.md` — 项目规则与自动化边界
2. `/_index.md` — 全局仓库导航
3. 子目录 `_index.md` — 目录路由
4. `wiki/synthesis/`、`wiki/concepts/` — 主要查询目标
5. `wiki/sources/` — 论文文献细节
6. `raw_markdown/` — 权威转换文本
7. `raw_pdfs/` — 原始证据

---

*本仓库是一个通用文献维基模板。原始项目描述见项目根目录的 `README.md`。*
