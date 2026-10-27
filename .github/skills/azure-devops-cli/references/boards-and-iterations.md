# Work Items, Area Paths & Iterations

Before commands, apply [ADO prerequisites/authentication](ado-conventions.md).
Use a pytools CLI command first, then an existing `_common` helper; raw `az` examples
below cover operations not already owned by those tools. Named-sprint PBI discovery uses
`get_iteration_path` plus `get_sprint_committed_pbis`, not a copied WIQL query.

## Table of Contents
- [Work Items (Boards)](#work-items-boards)
- [Area Paths](#area-paths)
- [Iterations](#iterations)

---

## Work Items (Boards)

### Query Work Items

```bash
# WIQL query
az boards query \
  --wiql "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.State] = 'Active'"

# Query with output format
az boards query --wiql "SELECT * FROM WorkItems" --output table
```

### Show Work Item

```bash
az boards work-item show --id {work-item-id}
az boards work-item show --id {work-item-id} --open
```

> **Gotcha — `show` has no `--fields` filter for output.** `az boards work-item show` always expands the full work item (`ERROR: The expand parameter can not be used with the fields parameter.` if you try `--fields` here — that flag only exists on `work-item create`/`update` to *set* fields, not to select which ones to display). To get specific fields, fetch the full JSON and extract client-side:
>
> ```powershell
> # PowerShell: parse full JSON, pull out only what you need
> $wi = az boards work-item show --id 900102 --output json | ConvertFrom-Json
> $wi.fields.'System.Title'
> $wi.fields.'System.State'
> $wi.fields.'System.Description'
> ```
>
> ```bash
> # bash + jq equivalent
> az boards work-item show --id 900102 --output json | jq '.fields["System.Title"], .fields["System.State"]'
> ```
>
> **Broken in CLI 2.81.0 — `az devops invoke --resource workitems` batch lookup.** The
> previously-suggested batch pattern (`az devops invoke --area wit --resource workitems
> --route-parameters project={project} --query-parameters ids=... fields=... api-version=7.1`)
> fails with `ERROR: 'type' ... KeyError: 'type'` inside the extension's URL formatter — the
> `workitems` resource route needs a `type` route parameter this command doesn't expose. Don't
> use it. Loop `az boards work-item show --id {id} -o json` per ID instead; for a handful of IDs
> (a sprint's worth of tasks) the loop is fast enough and always works:
>
> ```powershell
> $ids = 900104, 900105, 900106
> foreach ($id in $ids) {
>   $wi = az boards work-item show --id $id -o json | ConvertFrom-Json
>   [pscustomobject]@{ Id = $id; Title = $wi.fields.'System.Title'; State = $wi.fields.'System.State' }
> }
> ```

### Query by Iteration Path

For sprint QA discovery, append these calls to the
[Python helper bootstrap](ado-conventions.md#python-helper-scripts) and run from `tools\pytools`:

```python
from pytools.devops._common import get_iteration_path, get_sprint_committed_pbis

iteration = get_iteration_path('<sprint-name>', organization, project, token)
pbis = get_sprint_committed_pbis(iteration, organization, project, token, area_path='<area-path>')
```

An empty sprint-phase result is `config_error`; do not mutate or hand off.
The helpers normalize the reserved `Iteration` root segment before WIQL matching.
The following raw query is for ad-hoc assigned-work lookup, not a replacement discovery flow.

`[System.IterationPath]` is an area-path-typed field — WIQL rejects `CONTAINS` on it
(`ERROR: The specified operator cannot be used with area path fields.`). Use `=` with the
**full resolved path**, not `UNDER` with a partial sprint name:

```powershell
# 1. Resolve the sprint name to its full path first
az boards iteration team list --team "Your Team" --project ShopApp --output json |
  ConvertFrom-Json | Where-Object { $_.name -like '*42*' } | Select-Object name, path
# → ShopApp\2026\Sprint 42

# 2. Use the exact path in WIQL with '='
az boards query --wiql "SELECT [System.Id], [System.Title], [System.State] FROM WorkItems WHERE [System.AssignedTo] = @Me AND [System.IterationPath] = 'ShopApp\2026\Sprint 42' AND [System.State] NOT IN ('New','Closed','Removed','Done')" --output table
```

### Create Work Item

For formal bugs, follow [bug-reporting.md](bug-reporting.md) rather than the generic examples:
required Component and ReproSteps fields are not supplied by a bare `--type Bug`.

```bash
# Basic work item
az boards work-item create \
  --title "Fix login bug" \
  --type Bug \
  --assigned-to user@example.com \
  --description "Users cannot login with SSO"

# With area and iteration
az boards work-item create \
  --title "New feature" \
  --type "User Story" \
  --area "Project\\Area1" \
  --iteration "Project\\Sprint 1"

# With custom fields
az boards work-item create \
  --title "Task" \
  --type Task \
  --fields "Priority=1" "Severity=2"

# With discussion comment
az boards work-item create \
  --title "Issue" \
  --type Bug \
  --discussion "Initial investigation completed"

# For a long --discussion body on Windows, see references/long-comments-on-windows.md.
# Select azps.ps1 or an --in-file request when quoting/length requires it;
# the wrapper is not required for every command.

# Open in browser after creation
az boards work-item create --title "Bug" --type Bug --open
```

### Update Work Item

```bash
# Update state, title, and assignee
az boards work-item update \
  --id {work-item-id} \
  --state "Active" \
  --title "Updated title" \
  --assigned-to user@example.com

# Move to different area
az boards work-item update \
  --id {work-item-id} \
  --area "{ProjectName}\\{Team}\\{Area}"

# Change iteration
az boards work-item update \
  --id {work-item-id} \
  --iteration "{ProjectName}\\Sprint 5"

# Add comment/discussion
az boards work-item update \
  --id {work-item-id} \
  --discussion "Work in progress"

# Long comment on Windows: read the body into a PowerShell variable and call
# azps.ps1 instead of az.cmd, or fall back to 'az devops invoke' with --in-file.
# Full guidance in references/long-comments-on-windows.md.
#
# PowerShell example:
#   $body = Get-Content -Raw .\comment.md
#   azps.ps1 boards work-item update --id 1234 --discussion $body

# Update with custom fields
az boards work-item update \
  --id {work-item-id} \
  --fields "Priority=1" "StoryPoints=5"
```

### Delete Work Item

```bash
# Soft delete (can be restored)
az boards work-item delete --id {work-item-id} --yes

# Permanent delete
az boards work-item delete --id {work-item-id} --destroy --yes
```

### Work Item Relations

```bash
# List relations
az boards work-item relation list --id {work-item-id}

# List supported relation types
az boards work-item relation list-type

# Add relation
az boards work-item relation add --id {work-item-id} --relation-type parent --target-id {parent-id}

# Remove relation
az boards work-item relation remove --id {work-item-id} --relation-id {relation-id}
```

### Resolve a Work Item's Parent (PowerShell)

`az boards work-item relation list` doesn't return the parent's fields directly. Fetch the full
item with `-o json`, filter its `relations[]` for the reverse-hierarchy link, extract the ID from
the URL, then look that item up too:

```powershell
$item = az boards work-item show --id 900103 -o json | ConvertFrom-Json
$parentUrl = ($item.relations | Where-Object { $_.rel -eq 'System.LinkTypes.Hierarchy-Reverse' } |
  Select-Object -First 1).url
$parentWorkItemId = $parentUrl -replace '.*/', ''
$parent = az boards work-item show --id $parentWorkItemId -o json | ConvertFrom-Json
$parent.fields.'System.Title'
```

Do not name the loop/temp variable `$pid` — it's PowerShell's reserved automatic variable for
the current process ID and assignment fails with `ParserError: Cannot overwrite variable PID`.

## Area Paths

### List Areas for Project

```bash
az boards area project list --project {project}
az boards area project show --path "Project\\Area1" --project {project}
```

### Create Area

```bash
az boards area project create --path "Project\\NewArea" --project {project}
```

### Update Area

```bash
az boards area project update \
  --path "Project\\OldArea" \
  --new-path "Project\\UpdatedArea" \
  --project {project}
```

### Delete Area

```bash
az boards area project delete --path "Project\\AreaToDelete" --project {project} --yes
```

### Area Team Management

```bash
# List areas for team
az boards area team list --team {team-name} --project {project}

# Add area to team
az boards area team add \
  --team {team-name} \
  --path "Project\\NewArea" \
  --project {project}

# Remove area from team
az boards area team remove \
  --team {team-name} \
  --path "Project\\AreaToRemove" \
  --project {project}

# Update team area
az boards area team update \
  --team {team-name} \
  --path "Project\\Area" \
  --project {project} \
  --include-sub-areas true
```

## Iterations

### List Iterations for Project

Sprints can be nested as `Project\Year\Sprint N`; use
`az boards iteration project list --depth 2` to include those nodes.
For named-sprint pipeline discovery, use the helper above instead.

```bash
az boards iteration project list --project {project}
az boards iteration project show --path "Project\\Sprint 1" --project {project}
```

### Create Iteration

```bash
az boards iteration project create --path "Project\\Sprint 1" --project {project}
```

### Update Iteration

```bash
az boards iteration project update \
  --path "Project\\OldSprint" \
  --new-path "Project\\NewSprint" \
  --project {project}
```

### Delete Iteration

```bash
az boards iteration project delete --path "Project\\OldSprint" --project {project} --yes
```

### Team Iterations

```bash
# List iterations for team
az boards iteration team list --team {team-name} --project {project}

# Add iteration to team
az boards iteration team add \
  --team {team-name} \
  --path "Project\\Sprint 1" \
  --project {project}

# Remove iteration from team
az boards iteration team remove \
  --team {team-name} \
  --path "Project\\Sprint 1" \
  --project {project}

# List work items in iteration
az boards iteration team list-work-items \
  --team {team-name} \
  --path "Project\\Sprint 1" \
  --project {project}
```

### Default & Backlog Iterations

```bash
# Set default iteration for team
az boards iteration team set-default-iteration \
  --team {team-name} \
  --path "Project\\Sprint 1" \
  --project {project}

# Show default iteration
az boards iteration team show-default-iteration \
  --team {team-name} \
  --project {project}

# Set backlog iteration for team
az boards iteration team set-backlog-iteration \
  --team {team-name} \
  --path "Project\\Sprint 1" \
  --project {project}

# Show backlog iteration
az boards iteration team show-backlog-iteration \
  --team {team-name} \
  --project {project}

# Show current iteration ('show' with --timeframe does not exist in this az devops
# extension version — use 'list' with --timeframe instead)
az boards iteration team list --team {team-name} --project {project} --timeframe current
```

## Read all work-item comments

Prefer `uv run read_pbi <pbi-id>` for PBI fields and every comment. Raw `az` (only if pytools lacks the operation) needs the root `.env` loaded first with `. tools\pytools\scripts\load-env.ps1` (sets `ADO_PAT` and `AZURE_DEVOPS_EXT_PAT` without printing them).

For requirement-source collection use `uv run read_pbi` (run from `tools\pytools`). It follows `continuationToken` until exhausted and fails on a repeated token or failed page; that leaves the requirement inventory incomplete, so stop rather than generating from a partial set.

```powershell
cd tools\pytools
uv run read_pbi <pbi-id> [<pbi-id> ...]
```

Fallback only if `read_pbi` is unavailable: `az devops invoke --area wit --resource comments --route-parameters project="<project>" workItemId=<pbi-id> --api-version 7.0-preview.3 --output json`, following `--query-parameters continuationToken="<token>"`. Some Azure CLI versions fail it with `could not convert string to float: '7.0.3'`. Retain only the required comment content and dates, not raw JSON dumps.
