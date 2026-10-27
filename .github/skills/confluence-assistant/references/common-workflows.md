# Common Workflows

---

## Extract a Confluence Page to Markdown

### 1. Setup

From repository root, enter the skill directory and provision dependencies with `uv`.
For credential locations and precedence, read [Configuration](../SKILL.md#configuration).

```powershell
cd .github\skills\confluence-assistant
uv sync
```

### 2. Extract a Single Page by URL

```powershell
uv run python scripts\confluence_to_md.py "<confluence-page-url>"
```

### 3. Extract a Single Page by ID

```powershell
uv run python scripts\confluence_to_md.py 12345
```

### 4. Extract with a Custom Output Path

```powershell
uv run python scripts\confluence_to_md.py 12345 --output C:\path\to\output
```

### 5. Batch Extract Multiple Pages

```powershell
$pages = @('12345', '23456', '34567')
foreach ($pageId in $pages) {
    uv run python scripts\confluence_to_md.py $pageId
}
```

### 6. Output Produced by the Script

For each extracted page, the script should produce:

- `<page-title>.md`
- `assets/<page-slug>/` folder containing downloaded attachments

With no `--output` or `DEFAULT_OUTPUT_PATH`, the repository-root layout is:

```text
qa-output\
└── requirements\
    ├── page-title.md
    └── assets\
        └── page-title\
            ├── diagram.png
            └── screenshot.jpg
```

`--output` overrides `DEFAULT_OUTPUT_PATH`; both accept a directory or explicit Markdown
file. Relative overrides remain relative to the command's working directory. Image paths
remain relative to the Markdown file, including for explicit output overrides.

## Search Pages with CQL

Use this procedure when a page must be discovered by title, URL-derived key, label, or
batch query. The read/export scripts accept a page URL or numeric ID, not a title.
Place any temporary search script directly in `.github\skills\confluence-assistant`,
run `uv run python <script-name>.py` from that directory, and remove it after use.
Reuse the read script's credential loading and header helpers:

```http
GET /rest/api/content/search?cql=...&limit=25&start=0
```

```python
import requests
from scripts.read_page import build_headers, load_credentials

base_url, pat = load_credentials()
response = requests.get(
    f'{base_url}/rest/api/content/search',
    headers=build_headers(pat),
    params={
        'cql': 'type=page AND space="DOC" AND title="Example page"',
        'limit': 25,
        'start': 0,
    },
    timeout=30,
)
response.raise_for_status()
results = response.json()
```

For a space-wide query, omit the title clause (`type=page AND space="DOC"`). Follow
pagination before treating search results as complete. Resolve a unique page ID before
calling the read/export script; ask the user to disambiguate multiple title matches.

## Troubleshooting

- `401` → check `.env` credentials.
- `404` → the page ID is wrong or the user lacks read permission.
- Images not downloading → check attachment permissions.
- Tables not rendering → check GFM table syntax (pipes + header separator).
