# raw_markdown

Machine-readable conversions of source PDFs.

## Subdirectories

| Directory | Contents |
|---|---|
| `papers/` | One `.md` file per PDF, converted via markitdown |
| `metadata/` | One `.json` sidecar per paper (slug, word count, sha256, conversion notes) |
| `assets/` | Images and attachments extracted from PDFs |

## Usage

This layer is for faithful extraction only — no academic judgment is applied here.

- Agents read this layer when a wiki source page lacks sufficient detail.
- Do not edit converted markdown unless fixing obvious extraction failures.
- To convert a new PDF: `python scripts/convert_pdf_to_markdown.py raw_pdfs/your-paper.pdf`
