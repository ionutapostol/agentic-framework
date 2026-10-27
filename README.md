# agentic-framework

An AI-agent workflow framework for QA automation: fixed workflow entrypoints (agents)
backed by on-demand procedures, references, and validators (skills), with a central
routing guide ([AGENTS.md](AGENTS.md)) that owns the sprint pipeline contract.

Originally extracted from a larger QA automation monorepo. Two companion projects
complete the setup: a Python CLI (`tools\pytools` layout, see the `python-tools` repo)
and Playwright suites (see the `playwright-ts` repo).

## Layout

```
├── AGENTS.md              # Routing guide and pipeline run contract (start here)
└── .github/
    ├── agents/            # Fixed workflow entrypoints (@agent invocations)
    │   ├── ado-board-tasks.agent.md
    │   ├── ado-bug-report.agent.md
    │   ├── ado-standup.agent.md
    │   ├── ado-test-case-author.agent.md
    │   ├── ado-test-plan-setup.agent.md
    │   ├── ado-testcase-priority.agent.md
    │   ├── ui-automation.agent.md
    │   └── postman-runner.agent.md
    └── skills/            # On-demand procedures, references, validators
        ├── agent-architecture/    # Contract/design/audit references for agent systems
        ├── azure-devops-cli/      # ADO conventions, bug reporting, boards/iterations
        ├── confluence-assistant/  # Confluence read/export scripts (skill-local uv project)
        ├── postman-ops/           # Postman forks/merges/exports, Newman
        └── write-test-cases/      # CSV test-case authoring rules + stdlib validators
```

## Sprint QA pipeline

Four agent-driven phases — add tasks → create suites → generate CSVs → import — each
with reuse-first, zero-work-is-`config_error`, and bounded-evidence constraints.
See [AGENTS.md](AGENTS.md) for the full pipeline table and run contract; see
[.github/skills/README.md](.github/skills/README.md) for per-workflow prerequisites.

## Entry points

| Agent | Purpose |
|-------|---------|
| `@ado-board-tasks` | Add standard testing tasks to PBIs or sprint PBIs |
| `@ado-test-plan-setup` | Create sprint suites and import manifest-backed CSVs |
| `@ado-test-case-author` | Generate validated happy-path CSVs for sprint PBIs |
| `@ado-bug-report` | File formal Bug work items from QA/security findings |
| `@ado-standup` | Read-only standup reporting |
| `@ado-testcase-priority` | Bulk test-case priority updates (dry-run by default) |
| `@postman-runner` | Postman collection fork/merge/export management |
| `@ui-automation` | Playwright specialist for the companion UI test suite |

| Skill | Trigger |
|-------|---------|
| `write-test-cases` | "generate test cases", "create test scenarios" |
| `azure-devops-cli` | ad-hoc Boards/iterations/Test Plans work |
| `confluence-assistant` | "read this Confluence page", "export requirements" |
| `postman-ops` | "create a fork", "merge fork", "export collection" |
| `agent-architecture` | designing or auditing agent systems |

## Configuration

Credentials live in gitignored `.env` files or the process environment — never in this
repo. Each skill's README/configuration section (e.g. `confluence-assistant/.env.example`,
the ADO conventions reference) documents which variables it needs. All example URLs use
placeholders (`your-org`, `your-confluence.example.com`); substitute your own organization.

> The `training/` folder is gitignored on purpose — it holds a personal learning path
> and is not part of the public artifact.
