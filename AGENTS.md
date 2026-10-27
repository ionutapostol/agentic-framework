# Agent framework structure

Windows/PowerShell QA workflows backed by Python CLI utilities. This guide owns routing
and the sprint run contract; detailed rules live in the canonical homes below.

This repo contains the workflow definitions only. Two companion projects complete the
setup: a Python CLI project (`tools\pytools` layout, e.g. the `python-tools` repo) that
the ADO/suite agents shell out to, and Playwright suites (e.g. the `playwright-ts` repo).
Generated artifacts land in `qa-output\` under the consuming repo root.

## Repository map

| Path | Purpose |
|---|---|
| `.github\agents\` | Fixed workflow entrypoints |
| `.github\skills\` | On-demand procedures, references, templates, and validators |

## Setup and execution

Read [workflow prerequisites](.github/skills/README.md#prerequisites-by-workflow) before
running a workflow. `uv` provisions Python/project dependencies, not external tools.
The companion CLI project manages its own environment:

```powershell
cd <repo>\tools\pytools
uv sync
```

Use the pytools command guide in the companion CLI project for signatures and working
directories. Confluence has its own skill-local project. Retained `az` operations require
Azure CLI and its Azure DevOps extension; optional Newman execution requires Node.js/npm.

## Canonical rule homes

Read the indicated home before the corresponding decision or action. Critical reminders at
action points may repeat a constraint; detailed procedures and tables belong only in their home.

| Before doing this | Read |
|---|---|
| Gathering requirements or writing/updating CSV cases, checklists, or PO questions | [write-test-cases](.github/skills/write-test-cases/SKILL.md); for sprint collection also follow the author agent's Step 3 |
| Choosing ShopApp Component, menu paths, integration triggers, or domain-specific expectations | [ShopApp domain reference](.github/skills/write-test-cases/references/shopapp-domain.md) |
| Any ADO command: configuration, authentication, team/area, suite defaults | [ADO conventions](.github/skills/azure-devops-cli/references/ado-conventions.md) |
| Filing formal bugs | [Bug field/template rules](.github/skills/azure-devops-cli/references/bug-reporting.md) |
| Reading/exporting Confluence or following relevant requirement links | [confluence-assistant](.github/skills/confluence-assistant/SKILL.md) |
| Managing Postman collections/forks or running Newman | [postman-ops](.github/skills/postman-ops/SKILL.md) |
| Creating/reusing suites or selecting generated output paths | The suite reuse contract and output layout guide in the companion CLI project |

Before CSV output, keep every Test Case ID empty; Shared Steps IDs are the exception.
Before checklist output, require Happy path, Edge case, and Error handling backing;
missing backing means clarification and a PO question, not an invented pass/fail assertion.
Read the skill's opt-in gate before proposing inferred checklist items.

## Routing

| Request | Entrypoint |
|---|---|
| Sprint QA setup/authoring/import | The pipeline below, using agents |
| Ad-hoc test cases or an explicitly requested checklist | [write-test-cases](.github/skills/write-test-cases/SKILL.md) |
| Ad-hoc ADO lookup or operation | [azure-devops-cli](.github/skills/azure-devops-cli/SKILL.md): existing pytools command, then `_common` helper, then `az`, then REST |
| Child tasks or checklist attachment | [ado-board-tasks](.github/agents/ado-board-tasks.agent.md) |
| Formal bugs | [ado-bug-report](.github/agents/ado-bug-report.agent.md); retain `az` while the legacy CLI lacks required fields |
| Read-only standup | [ado-standup](.github/agents/ado-standup.agent.md) |
| Bulk test-case priority | [ado-testcase-priority](.github/agents/ado-testcase-priority.agent.md); dry-run by default |
| Postman operations | [postman-runner](.github/agents/postman-runner.agent.md) or its skill |
| Confluence read/export | [confluence-assistant](.github/skills/confluence-assistant/SKILL.md) |

## Sprint QA pipeline

Use agents as user entrypoints; they may internally follow skills. Read each agent before its phase.

| Phase | Invocation |
|---|---|
| Add tasks | [ado-board-tasks](.github/agents/ado-board-tasks.agent.md): `@ado-board-tasks --current` or `--sprint "<Sprint>" --team "<team>"` |
| Create suites | [ado-test-plan-setup](.github/agents/ado-test-plan-setup.agent.md): `@ado-test-plan-setup "<Sprint>" "<team>" --mode suites` |
| Generate CSVs | [ado-test-case-author](.github/agents/ado-test-case-author.agent.md): `@ado-test-case-author "<Sprint>" "<team>"` |
| Import reviewed CSVs | `@ado-test-plan-setup "<Sprint>" "<team>" --mode import --manifest qa-output\test-cases\<sprint-slug>\manifest.json` |

Review generated CSVs before import. Successful phases print the next paste-ready prompt.
Sprint CSVs are happy-path only; checklists require a separate explicit request.

### Pipeline run contract

1. **Reuse first:** use existing pytools commands, `_common` helpers, or skills before a
   temporary script. Do not reimplement owned discovery or suite lookups.
2. **Zero work is `config_error`:** zero PBIs, suites, or imported cases is not success,
   even when a lower-level command exits zero. Stop and emit no next-phase handoff.
3. **Bounded evidence:** avoid raw REST/JSON dumps and repeated fetches of manifest data.
   Fetch current remote state when verification or concurrency checks require it.
4. **Working directories:** pytools commands run from the companion CLI project
   (`tools\pytools` layout); stdlib skill
   validators run from repository root:
   `uv run python .github\skills\write-test-cases\scripts\<validator>.py <path>`.
   Resolve artifact paths before changing directories.

Suite failures retain confirmed mappings and distinguish unknown outcomes; read the linked
contract before retrying. Reuse is sequential only, not protection against concurrent runs.

## Maintaining instructions

Agent files use: invocation/examples, ordered steps with completion criteria, error behavior,
final-output contract, and workflow-specific gotchas. Put reusable setup/reference detail behind
explicit read-before-action links. Change a canonical rule and its action-point reminders together.
Check discoverability from this guide, the relevant entrypoint, and file-scoped instructions.

## Git and secrets

Use conventional commits and validate locally; there is no CI pipeline. Worktrees belong in
`.worktrees\`. Never stage secrets, virtual environments, or generated output.
Credentials belong in gitignored `.env` files or process environment; use placeholder-only
examples. For portable copies, retain the documented layout and ignore protections, not real
credentials or generated artifacts. Push only when requested.
