# Copilot skills

On-demand procedures and references for the QA workflows. For the fixed sprint pipeline,
start with the [agents](../agents/ado-board-tasks.agent.md), not a skill.

## Supported skills

| Skill | Read when |
|---|---|
| [azure-devops-cli](azure-devops-cli/SKILL.md) | Ad-hoc Boards, iterations, or Test Plans work; shared ADO conventions |
| [confluence-assistant](confluence-assistant/SKILL.md) | Reading or exporting a Confluence page, including relevant requirement references |
| [postman-ops](postman-ops/SKILL.md) | Creating, merging, deleting, or exporting collection forks; optional Newman execution |
| [write-test-cases](write-test-cases/SKILL.md) | Ad-hoc CSV test cases, explicitly requested checklists, requirement gaps and PO questions |

## Prerequisites by workflow

Commands assume Windows PowerShell. Install only what the selected workflow requires.

| Workflow | Prerequisites |
|---|---|
| Python CLI / Postman management | `uv`; from `tools\pytools`, run `uv sync` |
| Confluence scripts | `uv`; from `.github\skills\confluence-assistant`, run `uv sync` |
| CSV/checklist/manifest validation | `uv`; stdlib-only scripts run from repository root |
| Retained `az` operations | Azure CLI plus `az extension add --name azure-devops` |
| Optional Newman runs | Node.js/npm and `npx newman`; provide collection/environment paths |

`uv` provisions the project's supported Python and dependencies. It does not install Azure CLI,
ODBC drivers, or Node.js. Azure CLI is required for bug reporting, standup, priority updates,
and the retained PBI/comment lookups in sprint agents; pure pytools calls do not require it.
See the prerequisites section of the companion CLI project README for database, queue,
and pull-request utilities carried alongside the framework.

## Credentials and configuration

Keep credentials in gitignored files or process environment; never copy real values into a
portable payload. Read the relevant canonical configuration before connecting:

| Workflow | Configuration |
|---|---|
| ADO | Root `.env`; [ADO conventions](azure-devops-cli/references/ado-conventions.md) own raw `ADO_PAT`, organization URL, defaults, and non-interactive `az` auth |
| Postman | Root `.env`; [postman-ops](postman-ops/SKILL.md#prerequisites-and-configuration) owns API key, workspace/collection IDs and defaults |
| Confluence | [Skill configuration](confluence-assistant/SKILL.md#configuration); copy its `.env.example` to a gitignored `.env`, or use root `.env` |

Confluence keeps existing process values, then fills missing values from script-local,
skill-local, and root `.env` files in that order. `--output` overrides `DEFAULT_OUTPUT_PATH`;
with neither, exports go to `qa-output\requirements\<page-title>.md` and images to
`qa-output\requirements\assets\<page-slug>\`. Explicit relative output paths remain relative to the caller.

## Working directories

Run `uv run <command>` from `tools\pytools`. Run Confluence scripts from the skill directory.
Return to repository root before validators:

```powershell
uv run python .github\skills\write-test-cases\scripts\validate_csv.py "<csv-path>"
uv run python .github\skills\write-test-cases\scripts\validate_checklist.py "<checklist-path>"
uv run python .github\skills\write-test-cases\scripts\validate_manifest.py "<manifest-path>"
```

When capturing validator output under a legacy Windows code page (for example cp1252),
set `$env:PYTHONIOENCODING = 'utf-8'` in the calling PowerShell process before these commands.
The CSV validator's Unicode error markers otherwise raise `UnicodeEncodeError` while reporting
invalid input. This is an output-encoding workaround, not a change to validation rules.

Generated artifacts belong under qa-output (see the output layout guide in the companion CLI project), not skill directories.
The skill's workflow determines when an artifact is required; CSV generation alone does not
request a checklist.
