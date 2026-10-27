---
name: confluence-assistant
description: Use this skill for anything involving a Confluence page — reading content, summarizing, exporting to a local markdown file, or using page content as context to create test cases. Triggers when a Confluence URL appears anywhere in the conversation (including embedded in Azure DevOps PBI descriptions, requirements docs, or user stories), or when the user says "read this Confluence link", "what does this wiki page say?", "export this page", "download page as markdown", "get page content", or "save wiki page". This skill fetches pages via REST API — no MCP required.
---

# Confluence Assistant

Two things, one skill: **read** a Confluence page into context, or **export** it as a local `.md` file.

## Configuration

Requires `uv`; from `.github\skills\confluence-assistant`, `uv sync` provisions Python
and this skill's dependencies. No Azure CLI or Node.js is needed for reading/exporting.

Load credentials from `.env` at the skill root or repo root. Existing process environment
values win; otherwise the scripts try script-local, then skill-local, then repository-root
`.env` files without overriding already loaded values. Keep both supported locations:

```env
CONFLUENCE_URL=https://your-confluence.example.com
CONFLUENCE_PAT=your_personal_access_token
```

The scripts authenticate with the PAT from these variables. For extraction setup, read
[common-workflows.md](references/common-workflows.md#extract-a-confluence-page-to-markdown).

## Workflow 1 — Read page into context

When the user wants to know what a page says, summarize it, or use it for test case generation:

```powershell
cd .github\skills\confluence-assistant
uv run python scripts\read_page.py "<confluence-url-or-page-id>"
```

The script prints the page as Markdown to stdout. Read the output and use it directly — summarize it, answer the user's question, or feed it into test case creation.

**Large pages:** if a page is big enough that stdout gets truncated, write it to a file with `-o` and then read the file:

```powershell
uv run python scripts\read_page.py "<confluence-url-or-page-id>" -o page.md
```

**Reading multiple pages (e.g. from an ADO PBI):** extract each URL from the description, run once per URL, combine the content.

## Workflow 2 — Export page to local `.md` file

When the user wants to save a page as a markdown file (e.g. as a requirements doc):

```powershell
cd .github\skills\confluence-assistant
uv run python scripts\confluence_to_md.py "<confluence-url-or-page-id>" [--output <path>]
```

When neither `--output` nor `DEFAULT_OUTPUT_PATH` is set, output goes to
`qa-output\requirements\<page-title>.md` at repository root (title normalized to a filename).
An explicit `--output` wins over `DEFAULT_OUTPUT_PATH`; a directory receives the generated
filename and a `.md` path is used directly. Images go to `assets\<page-slug>\` inside the Markdown directory, so default exports use
`qa-output\requirements\assets\<page-slug>\`.

## Page ID Resolution

Both scripts extract the page ID automatically from any of these forms:

- Modern URL: `https://your-confluence.example.com/pages/12345678/Page-Title`
- Legacy URL: `https://your-confluence.example.com/pages/viewpage.action?pageId=12345678&spaceKey=DOCS`
- A bare numeric page ID: `12345678`

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| `Authentication failed` | Wrong credentials | Check `.env` values |
| `Page not found` | Bad ID or no permission | Verify URL and access |
| `Missing required env vars` | `.env` not found or incomplete | Create/update `.env` at repo root |

**Never use `web_fetch` on `your-confluence.example.com` links** — it resolves to a private/internal address and is blocked (`resolves to blocked address`). Always use `scripts\read_page.py` (or `confluence_to_md.py`) instead, which authenticates with the PAT from `.env`.

## Reference files

| Topic | File | Load When |
|-------|------|-----------|
| Conversion implementation | [scripts/confluence_to_md.py](scripts/confluence_to_md.py) | Maintaining storage-format conversion or macro handling |
| Workflows | [references/common-workflows.md](references/common-workflows.md) | Extraction setup, batch extraction, CQL/title discovery |
