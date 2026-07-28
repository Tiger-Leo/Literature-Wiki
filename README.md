# 📚 Literature Wiki · 文献维基

[![English](https://img.shields.io/badge/Readme-English-blue)](README_en.md)

一个**开箱即用的 AI 原生文献知识库模板**——将学术 PDF 合集自动构建为按主题组织的**维基百科式综合页面**，由 Claude Code 多代理流水线驱动。

> **灵感来源**：[karpathy/llm-wiki](https://github.com/karpathy/llm-wiki)：*"LLM 不只是查询时检索原始文档，而是增量构建和维护一个持久化的维基……知识一次编译，持续更新，而不是每次查询重新推导。"*

> **当前维护者**：刘岳虎（西安石油大学经济管理学院），研究方向：产业融合、数实融合、技术融合、文化产业。

---

## ⚡ 常用命令速查

> 这是日常使用最频繁的命令，放在最前面方便查阅。

### 首次配置（一次性）

```powershell
# 将你的 PDF 目录链接到项目。将 <你的PDF目录> 替换为实际路径即可。
# 例如：e:\Papers、D:\文献\期刊、/home/user/papers 等。
python scripts/link_pdfs.py "<你的PDF目录>" --mode manifest
```

### PDF 管理（外部 PDF，无需复制或移动源文件）

```powershell
# 将外部 PDF 目录链接到项目（生成 pdf_sources.json 路径映射表）
python scripts/link_pdfs.py "<你的PDF目录>" --mode manifest

# 排除某些子目录（可多次使用 --exclude）
python scripts/link_pdfs.py "<你的PDF目录>" --mode manifest --exclude "<你的PDF目录>\不想读的文件夹"
```

### PDF 转化（MinerU 云端 API，高质量）

> MinerU 免费额度 **2000 页/天**。全库 ~3500 篇、~9 万页，全部转完需约 45 天。
> 建议每日跑一批，由少到多，优先核心文献。

```powershell
# 批量转化：从 pdf_sources.json 读取 N 篇 unconverted 的 PDF（按页数从少到多排序）
python scripts/batch_convert.py           # 默认 20 篇
python scripts/batch_convert.py 10        # 10 篇
python scripts/batch_convert.py 5 --language en  # 5 篇英文文献

# 单篇转化：
python scripts/convert_pdf_to_markdown.py "Author - YYYY - Title.pdf" --update-manifest
python scripts/convert_pdf_to_markdown.py "Author - YYYY - Title.pdf" --language en --update-manifest

# 查看转化状态（converted: false = 待转化）
python -c "import json; d=json.load(open('raw_pdfs/pdf_sources.json','r',encoding='utf-8')); total=len(d['pdfs']); done=sum(1 for v in d['pdfs'].values() if v.get('converted')); print(f'{done}/{total} converted ({done/total*100:.1f}%)')"
```

**`convert_pdf_to_markdown.py` 参数：**

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--converter` | `mineru` | 转化引擎：`mineru`（推荐）或 `markitdown` |
| `--language` | `ch` | 文档语言：`ch`（中文）或 `en`（英文） |
| `--update-manifest` | 关闭 | 成功后自动标记 `converted: true` |
| `--overwrite` | 关闭 | 覆盖已有的 .md 和 metadata 输出 |

### Zotero 语义搜索

```powershell
# 增量更新语义搜索数据库（新增论文后运行；每周一晚上22:00后打开项目时自动执行，含全文提取）
zotero-mcp update-db --fulltext

# 查看数据库状态
zotero-mcp db-status

# 强制全量重建（更换嵌入模型或修复数据库时使用）
zotero-mcp update-db --force-rebuild

# 含全文提取的增量更新（更全面，但较慢）
zotero-mcp update-db --fulltext
```

#### 自动更新机制

> 语义搜索数据库的自动更新通过 **Claude Code SessionStart 钩子**实现。每次在该项目中启动 Claude Code 会话时，会自动检查是否是周一晚上 22:00 之后且本周尚未更新——若满足条件，则在后台自动运行 `zotero-mcp update-db --fulltext`。每周只运行一次（按 ISO 周编号记录）。

**工作流程：**

1. 打开本项目的 Claude Code 会话
2. `SessionStart` 钩子触发 → 运行 `scripts/auto-update-db.ps1`
3. 脚本检测：（a）是否周一？（b）≥ 22:00 北京时间？（c）本周已运行过？
4. 三项均满足 → 后台启动 `zotero-mcp update-db --fulltext`，写入 `.cache/zotero-db-update-week.txt` 标记
5. 更新在后台运行，不阻塞会话

**必要条件：**

| 条件 | 说明 |
|---|---|
| **Zotero 桌面版运行中** | 本地模式（`ZOTERO_LOCAL: true`）需要 Zotero 桌面端运行。建议将 Zotero 设为开机自启 |
| **网络畅通** | 嵌入 API（SiliconFlow `BAAI/bge-m3`）需要外网访问 |
| **钩子已配置** | 项目 `.claude/settings.local.json` 中已配置 `SessionStart` 钩子 |

**手动运行（覆盖自动机制）：**

```powershell
zotero-mcp update-db              # 增量更新
zotero-mcp update-db --fulltext   # 含全文提取
zotero-mcp update-db --force-rebuild  # 全量重建
```

**故障排查：**

- 自动更新未触发 → 检查是否为周一 22:00 后首次打开项目；查看 `.cache/zotero-db-update-week.txt` 中的周编号
- 钩子未执行 → 检查 `.claude/settings.local.json` 中 `hooks.SessionStart` 配置是否存在
- 更新失败 → 手动运行 `zotero-mcp update-db`；确保 Zotero 桌面端在运行
- 查看后台更新日志：`Get-Content .cache/zotero-db-update.log`

### 维基构建与维护

```bash
/wiki-build          # 默认 2 轮多代理构建
/wiki-build 3        # 3 轮（更深入的语料库）
/wiki-query          # 从维基层回答研究问题
/wiki-synthesis      # 保存一次性洞察为单独页面
/wiki-update-db      # 检查、验证、维护维基健康
/wiki-serve          # 构建搜索索引并启动 Web 界面
```

### 验证脚本

```bash
python -m py_compile scripts/*.py                         # 编译检查
python scripts/check_links.py wiki raw_markdown           # 断链检测
python scripts/check_orphans.py wiki                      # 孤立页面检测
python scripts/validate_frontmatter.py wiki               # Frontmatter 验证
python scripts/export_wiki.py --wiki-dir wiki             # 导出搜索索引
```

### 查看转换器来源

```bash
# 查看所有 Markdown 文件分别使用了哪个转换器（mineru / markitdown / pdftotext）
python -c "import json,glob;[print(f'{json.load(open(f))[\"canonical_slug\"]:55s} {json.load(open(f))[\"conversion_tool\"]}') for f in sorted(glob.glob('raw_markdown/metadata/*.json'))]"
```

---

## 🧭 这是什么？

一个 **AI 原生的文献维基**——将学术 PDF 合集转化为一组聚焦的**维基百科式综合页面**，每个页面围绕一个主题（概念、争论、机制、测量、方法或主题），从整个文献合集中整合证据。

**不是**单篇论文摘要。**不是**带注释的参考文献目录。**不是**「论文 X 说 A，论文 Y 说 B」的罗列。而是以主题组织、百科全书式的文献知识体系。

架构完全领域无关，适用于任何学术研究领域。**跨平台**——macOS、Linux、Windows（PowerShell）均支持。

---

## 🎯 核心理念：不是 RAG，不是摘要存档

大多数文献管理工具属于两类：

- **PDF 存档**——按文件夹存储，需要时搜索。
- **RAG 系统**——文档被切块和嵌入，查询时检索并生成回答。

**Literature Wiki 两者都不是。** 它是一个持久化、持续演进的维基，每次构建产出聚焦的综合页面，由多个代理并行编写和审查，在每个主题上整合整个合集。维基是主要界面——不是 PDF，不是嵌入索引。

当你问「不同论文如何概念化 X？」——回答已经以维基百科式页面预先组织在 `wiki/concepts/concept-x.md`，具有百科式引导段落、整合多篇论文的子主题章节和明确的当前评估标注。无需检索步骤。

---

## 🏗️ 三层架构

```
raw_pdfs/
    └── 不可变的源 PDF。永不编辑。事实来源。
        实际 PDF 可存放在外部目录，通过 pdf_sources.json 映射。

raw_markdown/
    ├── papers/      ← 忠实的 PDF→Markdown 转换（MinerU 云端 API）
    ├── metadata/    ← 转换时提取的结构化元数据
    └── assets/      ← 从 PDF 提取的图片和附件

wiki/
    ├── sources/     ← 每篇论文的文献记录（锚点，非交付物）
    ├── concepts/    ← 维基百科式概念页面（交付物）
    ├── mechanisms/  ← 维基百科式机制页面
    ├── methods/     ← 维基百科式方法页面
    ├── measures/    ← 维基百科式测量页面
    ├── debates/     ← 维基百科式争论页面
    ├── synthesis/   ← 更高层次的交叉页面
    ├── templates/   ← 页面模板
    ├── schema/      ← 命名规则、Frontmatter 规范、构建工作流
    └── log.md       ← 仅追加的构建/合成/检查历史
```

**各层职责：**

- `raw_pdfs/` — 仅保存。LLM 永远不在此写入。**支持外部 PDF 目录**：通过 `pdf_sources.json` 清单，PDF 可存放在任意位置（如按期刊分类的文件夹），无需移动或复制。
- `raw_markdown/` — 忠实的机器可读转换。所有综合页面的实质性声明以此为准。
- `wiki/` — 结构化知识。**综合页面**是查询的主要界面；**源页面**仅作为文献锚点。
- `scripts/` — 确定性工具（验证、索引、导出、规范化）。不做学术判断。

---

## ⚙️ 四大核心操作

| 操作 | 技能 | 功能 |
|---|---|---|
| **build** | `/wiki-build` | 多轮、多代理构建/重建。从语料库规划页面集，按集群并行编写、并行审查，反复修订直至达到质量标准，最后检查。 |
| **query** | `/wiki-query` | 从综合层优先回答研究问题；仅在需要时深入源页面或原始 Markdown。 |
| **synthesis** | `/wiki-synthesis` | 将一次性洞察保存为单个维基页面——逐页精准补充。 |
| **update-db** | `/wiki-update-db` | 检查和健康检查——断链检测、孤立页面检测、Frontmatter 验证、元数据导出。 |

**使用节奏：**

- 在 `raw_pdfs/` 中添加新 PDF 后 → `/wiki-build`
- 回答研究问题 → `/wiki-query`
- 讨论产生了非显而易见的洞察后 → `/wiki-synthesis`
- 每月一次，每次大型构建后 → `/wiki-update-db`

---

## 🔗 PDF 外部链接方案

### 设计思路

项目需要读取 PDF 才能运行 `/wiki-build` 流水线，但 PDF 通常存放在外部目录（如按期刊分类的文件夹），且**不应移动或重命名源文件**。

解决方案：**路径清单（Manifest）模式**——`raw_pdfs/pdf_sources.json` 记录每个标准化名称到真实文件路径的映射。所有读取 PDF 的脚本通过它解析实际路径，无需开发者模式或管理员权限。

### 工作流

```
                     ┌──────────────────────┐
                     │  <你的PDF目录>\       │  ← PDF 真实存放位置
                     │  ├── 期刊A/           │     （按期刊/主题分类，不动）
                     │  ├── 期刊B/           │
                     │  └── ...              │
                     └────────┬─────────────┘
                              │
                link_pdfs.py --mode manifest
                              │
                     ┌────────▼─────────────┐
                     │  raw_pdfs/            │
                     │  └── pdf_sources.json │  ← 名称 → 路径映射表
                     └────────┬─────────────┘
                              │
              convert_pdf_to_markdown.py
              （查询 manifest，解析真实路径）
                              │
                     ┌────────▼─────────────┐
                     │  raw_markdown/papers/ │  ← 转换后的 Markdown
                     └──────────────────────┘
```

### PDF 命名规范

源 PDF 文件名为 `Author1_Author2_YYYY_Title.pdf`（下划线分隔），脚本自动转换为项目规范 `Author1 Author2 - YYYY - Title.pdf`（` - ` 分隔）。中文「等」自动替换为「et al」。

### 排除目录

源目录下可能有不想纳入维基的文件夹（如草稿、临时归档等）。有两种方式排除：

**方式 A：`--exclude` 命令行参数（推荐，效果立即可见）**

```powershell
python scripts/link_pdfs.py "<你的PDF目录>" --mode manifest --exclude "<你的PDF目录>\20260726" --exclude "<你的PDF目录>\momo"
```

可多次使用 `--exclude`，每次指定一个目录。脚本扫描时跳过这些目录下的所有 PDF。

**方式 B：直接编辑 `pdf_sources.json`（持久化，后续扫描自动生效）**

在 `exclude_dirs` 数组中添加路径：

```json
{
  "source_dirs": ["E:\\Desktop\\Desktop\\test"],
  "exclude_dirs": [
    "E:\\Desktop\\Desktop\\test\\20260726",
    "E:\\Desktop\\Desktop\\test\\momo"
  ],
  "pdfs": { ... }
}
```

两种方式可配合使用——JSON 中保存常规排除项，命令行 `--exclude` 用于临时排除。重新运行 manifest 扫描时，JSON 中已有的 `exclude_dirs` 会自动保留并与新的 `--exclude` 合并。

### 增量更新

添加新 PDF 后，运行 `--convert --new-only` 自动检测并仅转换新文件：

```powershell
python scripts/link_pdfs.py "<你的PDF目录>" --mode manifest --convert --new-only
```

脚本对比 manifest 条目与 `raw_markdown/papers/<slug>.md` 的存在性，跳过已转换的 PDF。

---

## 🤖 多代理构建流水线

`/wiki-build` 是核心。它以轮次为基础、文件交接为机制运行：

```
Phase 0  扫描 & 工作区设置
Phase 1  PDF → raw_markdown（新论文）
Phase 2  源页面——并行编写，轻量审查
Phase 3  轮次计划——单个规划子代理产出页面列表与集群
Phase 4  轮次执行
           Stage A: 策展人（1 个子代理）——含大纲和抽查锚点的页面简报
           Stage B: 集群编写者（并行）——维基百科式页面草稿
           Stage C: 集群审查者（并行）——三镜头审查，附带裁决
           Stage D: 修订者（并行）——应用修复列表；PASS 页面直接通过
         根据需要重复第 2 轮和第 3 轮
Phase 5  决定是否开启下一轮
Phase 6  定稿——复制轮次输出到 wiki/，运行全面检查，更新索引
```

所有中间产物存放在 `agent_tasks/wikipedia-rewrite_<DATE><HHMM>/`。子代理通过写文件通信；编排器收集 ≤200 字的状态摘要。

---

## 🧠 核心设计原则

### 角色分离

> **LLM（编排器）** 规划、生成子代理、收集状态、决定修订/轮次继续。永不自己写维基内容。
>
> **LLM（子代理）** 策展简报、编写页面、审查页面、修订页面——仅文件交接，≤200 字状态返回。
>
> **脚本** 验证 Frontmatter、检查链接、检测孤立页面、导出元数据——仅确定性操作，不做学术判断。
>
> **研究者** 设定研究方向、挑选论文、在集群不合理时编辑轮次计划、校准最终页面的可信度。

### 维基百科式综合，而非论文罗列

每个综合页面必须满足以下硬性要求（详见 `.claude/skills/wiki-build/rubric.md`）：

- **百科式引导段落**——定义主题、说明重要性、预览页面。不使用项目符号。
- **主题骨干**——章节标题命名子主题、子问题、形式化模型组件——**而非论文**。没有「论文观点」章节。
- **整合引用**——观点趋同时使用多重引用；仅在论文的独特贡献重要时才在行文中指名。
- **三个知识层可见但不占主导**——论文声明通过行内 `[[slug]]`，跨论文模式通过斜体概括，当前评估通过简短标注块。

---

## 🗂️ 文档导航

| 文档 | 内容 |
|---|---|
| [docs/llm-wiki.md](docs/llm-wiki.md) | 原始灵感（Andrej Karpathy） |
| [docs/architecture.md](docs/architecture.md) | 设计原则、分层模型、理念 |
| [docs/quick-start.md](docs/quick-start.md) | 设置 + 首次构建指南 |
| [docs/pipeline.md](docs/pipeline.md) | 完整 PDF 到维基流水线 |
| [docs/wiki-structure.md](docs/wiki-structure.md) | 维基目录设计与页面类型 |
| [docs/skills-reference.md](docs/skills-reference.md) | 四大技能参考 |
| [docs/scripts-reference.md](docs/scripts-reference.md) | Python 工具脚本参考 |
| [docs/obsidian-integration.md](docs/obsidian-integration.md) | Obsidian 集成 |
| [docs/scale-up-guide.md](docs/scale-up-guide.md) | 规模化指南 |
| [docs/adaptation-guide.md](docs/adaptation-guide.md) | 领域适配指南 |
| [docs/search-and-browse.md](docs/search-and-browse.md) | 零后端搜索+浏览 Web 界面 |
| [docs/web-frontend.md](docs/web-frontend.md) | Next.js 前端配置与构建 |
| [docs/rag-backend.md](docs/rag-backend.md) | 可选的智能聊天后端 |
| [docs/deployment.md](docs/deployment.md) | Web UI 和 API 部署指南 |
| [.claude/skills/wiki-build/rubric.md](.claude/skills/wiki-build/rubric.md) | **维基百科式质量标准** |

---

## 🚀 快速开始

**新手上路：**

1. [docs/quick-start.md](docs/quick-start.md) — 环境设置与首次构建
2. [docs/architecture.md](docs/architecture.md) — 理解设计理念
3. [.claude/skills/wiki-build/rubric.md](.claude/skills/wiki-build/rubric.md) — 编写前必读质量标准

**添加论文并构建：**

- [docs/pipeline.md](docs/pipeline.md) — 完整构建流水线参考
- [docs/skills-reference.md](docs/skills-reference.md) — 四大技能

**维基维护：**

- [docs/scripts-reference.md](docs/scripts-reference.md) — 检查和验证脚本
- [docs/scale-up-guide.md](docs/scale-up-guide.md) — 维护节奏

**适配其他领域：**

- [docs/adaptation-guide.md](docs/adaptation-guide.md) — 改什么、留什么

---

## 🌐 Web 界面

构建完维基后，启动搜索 + 浏览界面（**无需 AI、无需后端**）：

```bash
make install
python scripts/export_wiki.py
make web-build
make web-start   # http://localhost:3000 （搜索 + 浏览）
```

加上聊天界面（可选，需要一个生成式端点）：

```bash
python scripts/build_and_serve.py   # API :8000 + Web :3000
```

在 `.env` 中配置品牌和生成端点（参考 `.env.example`）。

---

## 🔗 导航约定

当 LLM 代理进入此仓库，预期阅读顺序为：

1. `CLAUDE.md` — 项目规则与自动化边界
2. `/_index.md` — 全局仓库导航
3. 子目录 `_index.md` 文件 — 目录路由
4. `wiki/synthesis/` 和 `wiki/concepts/` — 主要查询目标
5. `wiki/sources/` — 论文文献细节
6. `raw_markdown/` — 权威转换文本
7. `raw_pdfs/` — 原始证据

---

## 📋 项目脚本清单

| 脚本 | 功能 |
|---|---|
| `scripts/link_pdfs.py` | 扫描外部 PDF 目录，生成 `pdf_sources.json` 路径映射表；支持 `--exclude` 排除子目录、`--convert` 批量转换和 `--new-only` 增量更新 |
| `scripts/convert_pdf_to_markdown.py` | PDF → Markdown 转换（支持 `--converter markitdown` 和 `--converter mineru`） |
| `scripts/pipeline_utils.py` | 共享工具函数（slug 生成、manifest 解析、路径解析、哈希计算） |
| `scripts/check_links.py` | 断链检测 |
| `scripts/check_orphans.py` | 孤立页面检测 |
| `scripts/validate_frontmatter.py` | YAML Frontmatter 验证 |
| `scripts/export_wiki.py` | 导出前端搜索索引 |
| `scripts/export_metadata.py` | 导出元数据 |

---

*本仓库是一个通用文献维基模板。原始项目描述见项目根目录的 `README.md`。*
