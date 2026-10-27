# 04 — Sprint pipeline & run contract

**Why this comes now:** you understand single agents and single skills. The sprint
pipeline is where they're *composed* — four agents chained with a strict run contract.
This is the framework's flagship workflow and the best model for composing your own.

## Concepts

### The four phases (AGENTS.md → Sprint QA pipeline)

| Phase | Agent | Produces |
|---|---|---|
| Add tasks | `@ado-board-tasks` | Testing tasks on sprint PBIs |
| Create suites | `@ado-test-plan-setup --mode suites` | Sprint/team/requirement test suites |
| Generate CSVs | `@ado-test-case-author` | Requirement files, happy-path CSVs, PO questions, manifest |
| Import reviewed CSVs | `@ado-test-plan-setup --mode import --manifest ...` | Test cases in ADO, linked to suites |

Two properties make this a pipeline rather than four unrelated commands:

- **Hand-offs are explicit.** Each phase's Final Summary prints the *next paste-ready
  prompt* (see `ado-board-tasks.agent.md` → "Pipeline Handoff"). The human copy-pastes;
  the agents don't call each other.
- **A human review gate sits between generate and import.** CSVs are reviewed before
  `--mode import` runs. The pipeline encodes where judgment is required.

### The run contract (the four rules)

From `AGENTS.md` → Pipeline run contract:

1. **Reuse first** — prefer existing pytools commands, `_common` helpers, or skills over
   temporary scripts. Prevents five private variants of "create suite".
2. **Zero work is `config_error`** — a run that finds zero PBIs/suites/cases is a
   *misconfiguration signal*, never success — even if a lower-level command exited 0.
   This is the single most important anti-quiet-failure rule in the framework.
3. **Bounded evidence** — no raw REST/JSON dumps, no repeated re-fetching of manifest
   data; fetch remote state only when verification/concurrency requires it. Keeps
   context windows and runtimes sane.
4. **Working directories** — pytools commands from the companion CLI project; validators
   from the repo root; resolve artifact paths *before* `cd`.

Plus the failure nuance in the footer: **suite failures retain confirmed mappings and
distinguish unknown outcomes** — a partial run must be resume-safe, and "unknown" is a
first-class result, not a guess.

### Where phases keep state

Requirement files, CSVs, and `manifest.json` under `qa-output\test-cases\<sprint-slug>\`
(consuming repo) are the connective tissue: `--mode import` consumes the manifest that
`ado-test-case-author` wrote (Step 5). Phase 2 and 4 share the suite-reuse contract from
the companion CLI project.

## Code tour

1. `AGENTS.md` pipeline table + run contract (reread now with fresh eyes).
2. `ado-board-tasks.agent.md` — Step 0, Mode 1 vs Mode 2, and the Pipeline Handoff section.
3. `ado-test-plan-setup.agent.md` — the two modes (suites/import), Steps 1–3 idempotent
   suite creation, Step 4 manifest import + verification, and its Error Handling table.
4. `ado-test-case-author.agent.md` — Step 3 sub-steps (3a–3f) for requirement collection
   and Step 5 manifest writing. Note the 25-page/2-hop crawl cap shared with the skill.

## Exercises

1. Simulate a config error: mentally run phase 1 against a sprint name that doesn't
   exist. Which rule turns "0 PBIs found" into `config_error`, and what must the agent
   NOT emit afterwards? (Answer to find: no next-phase handoff.)
2. Trace the manifest: find where it's written (author Step 5) and where it's consumed
   (setup Step 4). What fields would a broken manifest need for the import to skip
   re-verification? Check with `validate_manifest.py`.
3. Phase 2 is described as idempotent. Find the suite-reuse behavior that makes re-running
   it safe, and state in one sentence why "reuse is sequential only" matters.
4. Draft a fifth phase ("report sprint QA status") as one paragraph: its inputs (manifest
   + ADO state), its read-only guarantee, and its contract-compliant evidence bounds.

## Self-check

- Why is zero-work-success dangerous in a pipeline, and how does the framework outlaw it?
- Which rule would you cite to reject a patch that dumps full JSON responses into context?
- Where exactly does human judgment enter the pipeline, and why is it not automated?
- What makes a suite re-run safe, and what concurrency promise does the framework
  explicitly NOT make?
