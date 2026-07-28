# raw_markdown

Machine-readable conversions of source PDFs.

## Subdirectories

| Directory | Contents |
|---|---|
| `papers/` | One `.md` file per PDF，converted via MinerU (default) or markitdown |
| `metadata/` | One `.json` sidecar per paper (slug, word count, sha256, conversion notes) |
| `assets/` | 预留目录（MinerU 图片为临时文件，转化后自动清理，不保留） |

## Conversion

统一入口：`scripts/convert_pdf_to_markdown.py`。默认使用 MinerU API，一行命令完成转化 + 元数据生成 + 临时文件清理 + 清单标记。

```bash
# 中文文献（默认 language=ch）
python scripts/convert_pdf_to_markdown.py "Author - YYYY - Title.pdf" --update-manifest

# 英文文献
python scripts/convert_pdf_to_markdown.py "Author - YYYY - Title.pdf" --language en --update-manifest

# 批量（从 pdf_sources.json 读 unconverted 条目）
python scripts/batch_convert.py 10
```

**参数：**
| 参数 | 默认值 | 说明 |
|---|---|---|
| `--converter` | `mineru` | 转化引擎：`mineru`（推荐）或 `markitdown` |
| `--language` | `ch` | MinerU 文档语言（中文 `ch`、英文 `en`） |
| `--update-manifest` | 关闭 | 转化成功后自动标记 `converted: true` |
| `--overwrite` | 关闭 | 覆盖已存在的输出 |

**配额：** MinerU 免费额度 2000 页/天。全库约 9 万页，全部转完需 ~45 天。优先转化核心文献。

## Usage

This layer is for faithful extraction only — no academic judgment is applied here.

- Agents read this layer when a wiki source page lacks sufficient detail.
- Do not edit converted markdown unless fixing obvious extraction failures.
- MinerU 转化的临时图片在转化完成后自动清理，不占用仓库空间。raw_markdown 层只服务 LLM 阅读，不需要渲染图片。
