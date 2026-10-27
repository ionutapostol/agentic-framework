---
name: postman-ops
description: 'Manage Postman collections via pytools CLI: create forks, delete one or more forks, merge a fork back into its parent collection, and export a parent collection to JSON. Use when asked to "create a fork", "delete a fork", "merge fork", "export collection", or any Postman collection workflow using uv run commands.'
---

# Postman Ops

CLI operations for Postman collection management via `uv run` commands in `tools/pytools`.

## When to Use This Skill

- User asks to "create a fork", "fork a collection", or "make a fork"
- User asks to "delete a fork", "remove fork", or "clean up forks"
- User asks to "merge fork", "merge back", or "push fork to parent"
- User asks to "export collection", "download collection", or "save collection as JSON"
- Any Postman collection management workflow

## Smart Defaults (no prompting)

When arguments are missing, resolve them silently — **never ask the user**:

| Missing argument | Resolution |
|-----------------|------------|
| **Fork name** | Generate: `"<acronym>-$(Get-Date -Format 'yyyyMMddHHmmssfff')"` where acronym = first segment of collection key, lowercased (e.g. `shp-20260430152512345` for `SHIPMENTS`) |
| **Workspace** | Re-use last workspace from this session; if none, default to `PRIMARY` |

Always confirm what name/workspace was used in your response.

## Operations

| Operation | Command |
|-----------|---------|
| Create fork | `uv run create_fork <name> <collection> [--workspace WORKSPACE]` |
| Delete fork(s) | `uv run delete_fork <name>` — repeat per fork |
| Merge fork → parent | `uv run merge_fork <fork-name> <collection>` |
| Export parent collection | `uv run export_collection <collection> [-o path]` |
| Export fork | `uv run export_fork <label>` |

> **Export default**: files go to `qa-output/exports/` at the repo root. Use `-o` to override.

### Valid Arguments

**Workspaces** (case-insensitive): `TEAM` · `PRIMARY` · `SECONDARY` · `LOCAL`

**Collections** (fuzzy-matched): `ORDERS_PART1` · `ORDERS_PART2` · `PAYMENTS_A` · `SHIPMENTS` · `INVOICES_B` · `ANALYTICS` · `TEST_HELPER`

> **Name resolution**: the CLI normalises user input — `payments-a`, `payments_a`, and `PAYMENTS_A` all resolve to `PAYMENTS_A`. Pass the user's exact words.

## Execution

1. Identify the operation from the user's request
2. Resolve any missing parameters using Smart Defaults — never ask
3. Execute from `tools/pytools/` using the appropriate command
4. Report: result + resolved fork name + workspace + output paths

## Prerequisites and configuration

Requires `uv`; run `uv sync` from `tools\pytools` to provision Python/dependencies.
Root `.env` holds `POSTMAN_API_KEY`, workspace IDs, and collection IDs. Never copy credentials
into exports or instructions. Newman execution is optional and additionally needs Node.js/npm.

## Collection domains

| Key | Domain |
|---|---|
| `ORDERS_PART1`, `ORDERS_PART2` | Order management, parts 1 and 2 |
| `PAYMENTS_A` | Payments |
| `SHIPMENTS` | Shipments |
| `INVOICES_B` | Invoices |
| `ANALYTICS` | Analytics |
| `TEST_HELPER` | Helper utilities |

Collection keys are configured in the companion CLI project
(`src\pytools\postman\constants.py`); extend that table and this one together.

## Workspaces

| Workspace | Purpose |
|---|---|
| `TEAM` | Production forks; the team's active work |
| `PRIMARY` | Testing/experimentation; default |
| `SECONDARY` | Testing/experimentation |
| `LOCAL` | Scratch/personal experiments |

## Fork lifecycle and destructive operations

Create a fork, edit it manually in Postman, merge into its parent, then delete the fork
only after the merge succeeds. Fork arguments are labels, not IDs: use the exact label
created. Deletion searches across workspaces.

Merge uses `updateSourceWithDestination` and overwrites the parent; delete executes
immediately. Neither CLI operation prompts. Confirm the user's intended destructive
target before invoking it; the request for a specific merge/delete supplies that intent.
Report failures rather than assuming a merge or cleanup succeeded.

## Exports and optional Newman execution

Parent exports default to `qa-output\exports\<KEY>.postman_collection.json` at repo root.
`-o` overrides the output. From `tools\pytools`:

```powershell
uv run export_collection <KEY>
```

For optional execution, supply an exported collection and an existing environment JSON
outside source control. From repository root, with Node.js/npm installed:

```powershell
npx newman run "qa-output\exports\<KEY>.postman_collection.json" -e "<environment-json-path>"
```

This portable workflow needs no `postman\` directory. Console results are the baseline
report; Allure and repository-specific preset suites are not portable prerequisites.