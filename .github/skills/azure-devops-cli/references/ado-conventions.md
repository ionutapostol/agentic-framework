# ADO project conventions (shared)

Canonical configuration and authentication for the ADO agents. Read before any ADO
command; action-point reminders may link here but must not redefine these rules.

## Prerequisites and authentication

Python CLI commands use `uv` from `tools\pytools`; `uv sync` provisions their dependencies.
Retained `az` operations additionally require Azure CLI and its Azure DevOps extension:
`az extension add --name azure-devops`. Bug reporting, standup, test-case priority,
and remaining PBI/comment lookups use `az`; installing pytools does not install it.

Store credentials in the root `.env`. Document `ORGANIZATION` as a full
`https://dev.azure.com/<org>` URL for interoperability: pytools accepts a slug or URL,
but raw `az` requires the URL. `ADO_PAT` is the raw PAT; `auth_header()` performs Basic
encoding internally. Never print the PAT or include it in command arguments.
Boards/Test Plans writes require the appropriate `vso.work_write` / `vso.test_write` scopes.

For raw `az`, run `. tools\pytools\scripts\load-env.ps1` from repository root. It loads the
root `.env` into the process without displaying values, keeps existing variables, sets
`AZURE_DEVOPS_EXT_PAT` from `ADO_PAT`, and throws if the PAT is missing. Then configure
defaults non-interactively:

```powershell
$env:AZURE_DEVOPS_EXT_PAT = $env:ADO_PAT
az devops configure --defaults organization="$env:ORGANIZATION" project="$env:ADO_PROJECT"
```

Resolve missing non-secret settings from Smart Defaults before this command; a missing PAT
is a configuration error. Stop on auth/configuration failure and preserve the exact error.
An agent must obtain the user's approval before live writes outside the requested scope;
scratch verification additionally requires explicit plan, parent suite, and PBI IDs.

### Python helper scripts

When no CLI command covers the operation, run a temporary script with `uv run python
<absolute-script-path>` from `tools\pytools` after `uv sync`. Start it with this bootstrap;
append the workflow's helper calls below it. `_common` does not load credentials itself.

```python
import os
import click
from dotenv import load_dotenv
from pytools.devops._common import auth_header, org_base

load_dotenv('../../.env', override=False)
organization = os.getenv('ORGANIZATION', 'https://dev.azure.com/your-org')
project = os.getenv('ADO_PROJECT', 'ShopApp')
token = os.getenv('ADO_PAT')
if not token:
    raise click.ClickException('Missing ADO_PAT in process environment or root .env.')
```

Keep environment values out of output. Resolve workflow-specific values (team, area,
plan ID) using the defaults below; do not duplicate credential-loading code in each agent.
For an HTTP call without an existing helper, use `org_base(organization)` and
`auth_header(token)`, a bounded timeout, and `raise_for_status()`.

### Suite ID lookup (read-only)

Use this to map PBIs to requirement suite IDs. Run it once per authoring run for all PBIs;
never probe per PBI. Start with the bootstrap above, then append:

```python
import re
from pytools.devops._common import list_plan_suites, resolve_suite_id

plan_id = int(os.getenv('ADO_TEST_PLAN_ID', '700100'))
pbi_ids = [1234, 1235]  # REPLACE with in-scope PBI IDs
suites = list_plan_suites(plan_id, organization, project, token)
team_suite_id = resolve_suite_id(
	'<Sprint suite> → <Team suite>', plan_id, organization, project, token, suites=suites
)
children = [s for s in suites if (s.get('parentSuite') or {}).get('id') == team_suite_id]
for pbi_id in pbi_ids:
	hits = [
		s for s in children
		if (m := re.match(r'^\s*(\d+)\s*:', str(s.get('name', '')))) and int(m.group(1)) == pbi_id
	]
	if len(hits) != 1:
		raise click.ClickException(f'{pbi_id}: expected 1 suite under team suite, found {len(hits)}.')
	print(pbi_id, '→', hits[0]['id'], hits[0]['name'])
```

The plan ID is not a suite ID. Match only direct children of the team suite, and fail on zero
or multiple matches instead of taking the first.

## Smart Defaults

| Variable | Purpose | Default |
|---|---|---|
| `ORGANIZATION` | ADO org URL — full URL required for raw `az`, pytools accepts a slug | `https://dev.azure.com/your-org/` |
| `ADO_PROJECT` | Project name | `ShopApp` |
| `ADO_TEAM` | Team name for sprint lookup | `Your Team` |
| `ADO_AREA_PATH` | Area path | `ShopApp\Your Team` |
| `ADO_PAT` | Raw PAT — `auth_header()` encodes it internally | — |
| `ADO_TEST_PLAN_ID` | Test plan ID | `700100` (Sprint testing plan) |
| `ADO_TEST_SUITE_ID` | Root suite for scoped lookups | `700101` |
| `ADO_ITERATION_PATH` | Optional explicit iteration; sprint commands can resolve it | — |

## Team resolution

Resolve team arguments case-insensitively:

| Argument | Suite name | Area path |
|---|---|---|
| `your-team` | `Your Team` | `ShopApp\Your Team` |
| `second-team` | `Second Team` | `ShopApp\Second Team` |

For another value, use it exactly as the suite name and derive `ShopApp\<Team name>`.
Explicit `--suite-name` and `--area-path` override those derived values. If zero PBIs are
found, report the sprint/team/area used and suggest an explicit area override where needed.
Sprint QA phases treat zero work as `config_error` and emit no next-phase handoff.

## Plan ID ≠ root suite ID

The plan ID and its root suite ID are different numbers (plan `700100` has
root suite `700101`). Passing the numeric plan ID as a suite parent 404s.
Use the plan/suite **name** (e.g. `"Sprint testing"`) instead — commands
resolve it to the correct suite ID automatically.

## Area path uses a backslash

Area paths use `\`, e.g. `"ShopApp\Your Team"`. Quote the whole value
as one string in PowerShell so the backslash is preserved.

## Support-bucket exclusion

Sprint-PBI commands (`add_sprint_tasks`, `add_requirement_suites`, and the
agents that query committed PBIs directly) exclude PBIs whose titles start
with or contain: `Technical improvements`, `Release support`,
`Implementation support`.
Explicit `add_requirement_suites --pbi-id` requests bypass these discovery filters.

## Default task set

When `--tasks` is omitted, task-creation commands fall back to:
`Create test cases`, `Review test cases`, `Test execution`,
`Postman tests`, `Review postman tests`.

## Bug work items: component tag (+ `YourOrg.Component` on plain `Bug`); `ReproSteps` on `Bug`, `Description` on `Bug in PBI` — see bug-reporting.md

Before creating a Bug, read [bug-reporting.md](bug-reporting.md). That reference owns
Component prompting, field mapping, HTML, reference relations, and content verification.
Keep the bug agent's `az` workflow: `create_bug` does not support all required fields yet.
