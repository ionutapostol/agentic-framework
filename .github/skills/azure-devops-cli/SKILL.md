---
name: azure-devops-cli
description: 'Use for ad-hoc Azure Boards work-item, iteration, area, and Test Plans lookups or one-off automation, and for shared ADO conventions. The fixed sprint QA pipeline uses its specialist agents; this skill provides their shared references.'
---

# Azure Boards and Test Plans

## Routing

Use `ado-board-tasks`, `ado-test-plan-setup`, and `ado-test-case-author` as the fixed sprint
QA entrypoints. For an ad-hoc task, use the first existing capability that owns the operation:

1. A pytools command, run with `uv run <command>` from `tools\pytools`.
2. An existing `pytools.devops._common` helper from that project.
3. A supported `az boards` / `az devops` command.
4. REST only when the preceding surfaces do not own the operation.

Preserve the bug agent's `az` workflow until `create_bug` supports its required fields.
This skill does not orchestrate CI/CD or maintain general pipeline/repository reference material.

## Preflight

Read [ado-conventions.md](references/ado-conventions.md) before executing commands:
it owns authentication, organization format, defaults, team resolution, and prerequisites.
Python workflows need `uv`; retained raw `az` workflows also need Azure CLI and its
Azure DevOps extension. Authenticate non-interactively; keep the raw PAT out of output.

## References

| Reference | Read before |
|---|---|
| [ado-conventions.md](references/ado-conventions.md) | Resolving auth, defaults, teams, plan/suite identities, support buckets or default tasks |
| [boards-and-iterations.md](references/boards-and-iterations.md) | Work-item queries/updates/comments, areas, iteration lookup |
| [long-comments-on-windows.md](references/long-comments-on-windows.md) | Passing long or quoted `--discussion`, `--description`, `--content`, or rich-text field values on Windows |
| [bug-reporting.md](references/bug-reporting.md) | Filing a Bug, selecting Component, constructing ReproSteps, adding references and verifying content |

## Completion

Report confirmed IDs and partial failures. An empty sprint-phase result is `config_error`,
not success, and suppresses handoff. Before live writes, confirm the requested scope;
read-only discovery does not authorize mutations.
