# Posting Long Comments and Bodies on Windows

On Windows, `az` normally resolves to `az.cmd`; its command line is capped at about 8191
characters. Short, simple values can use `az`. Prefer a native file argument for long bodies;
otherwise use `azps.ps1` for long values or values with quotes/ampersands. If the wrapper
is unavailable, use the supported `az devops invoke --in-file` shape below.

## Option 1: `azps.ps1` (PowerShell on Windows)

`azps.ps1` ships with the Azure CLI installer and invokes the Python entry point directly. No `cmd.exe` length cap.

```powershell
# For rich-text fields, construct single-line HTML and escape literal ampersands as &amp;.
$body = Get-Content -Raw .\comment.md
azps.ps1 boards work-item update --id 1234 --discussion $body
```

## Option 2: dedicated `--file-path` flag where Azure CLI offers one

Some commands have a native file flag and you should prefer it over any inline body:

- `az devops wiki page create` and `az devops wiki page update` take `--file-path` (with optional `--encoding`).
- Use it on any shell, including Windows.

```powershell
az devops wiki page create --path 'My page' --wiki myproject --file-path .\page.md --encoding utf-8
```

## Option 3: `az devops invoke` fallback

When no native file flag exists and the PowerShell wrapper is unavailable, use the supported
REST resource through `az devops invoke --in-file`. The body is read from a file, keeping
the command line short even when `az` still resolves through `cmd.exe`:

```powershell
# Post a long discussion comment to work item 1234.
# REST: POST /{project}/_apis/wit/workItems/{id}/comments?api-version=7.0-preview.3
az devops invoke --area wit --resource comments --route-parameters project=<project> workItemId=1234 --api-version 7.0-preview.3 --http-method POST --in-file .\comment.json
```

Where `comment.json` is `{ "text": "<long markdown body>" }`. This is the universal escape hatch when neither `azps.ps1` nor `--file-path` is available. `az devops invoke` itself accepts `--in-file` natively.

## Don't rely on `@<file>` for plain string args

The Azure CLI `@<file>` convention is documented for JSON parameters (see [the official quoting guide](https://learn.microsoft.com/en-us/cli/azure/use-azure-cli-successfully-quoting)). It is not guaranteed to expand plain string args like `--discussion` or `--description`, so don't reach for it as a substitute for the three options above.
