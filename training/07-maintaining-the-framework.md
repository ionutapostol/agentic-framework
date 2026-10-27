# 07 — Maintaining the framework

**Why this comes last:** you only appreciate maintenance rules after you've built
something that can be broken by them. This module is about evolving the framework
without rotting the contract.

## Concepts

### The change rule

From `AGENTS.md` → Maintaining instructions: **"Change a canonical rule and its
action-point reminders together."** A rule edit is a commit-sized unit: home file,
reminders at decision points, and (if scope changed) router rows — all in one change.
The source repo's history shows this pattern (e.g. the commit that changed bug-reporting
severity/priority defaults updated the agent and the reference in one pass).

### Public-repo hygiene (this export is public)

- Placeholders, never real endpoints: `your-org`, `your-confluence.example.com`.
- `.env`/`.env.*` are gitignored; only `*.env.example` (placeholder values) is tracked.
- `training/` is gitignored — personal notes and exercises never leak into the artifact.
- Before every public push, re-run a sensitive-data grep over the tree:
  ```bash
  grep -riE 'your-real-org|real\.domain|p@ssw0rd' . --exclude-dir=.git
  ```

### Companion-project coupling

Agents reference the companion CLI project (`tools\pytools`) and Playwright project by
*convention*, not by tracked file links. When a pytools command signature changes:

1. Update the CLI project (its README owns the command table),
2. update any agent whose workflow quotes the old signature,
3. if behavior changed, update the affected skill's reference + its evals.

Breaking change in a companion project = a three-repo commit wave. Keep messages
conventional (`docs(ado-bug-report): ...`) so the wave is greppable.

### Evals as regression tests

`write-test-cases/evals/evals.json` asserts properties of outputs given prompts. When
you edit a skill's rules, re-run the affected evals mentally or via an assistant pass
and update expectations — a rule change that leaves stale evals is a future false
alarm (or worse, a silent miss).

### Growing without sprawling

- New workflow? Write the trigger contract first (negative scope included) so routing
  stays unambiguous.
- New detail? Ask "is this a reference?" before adding a line to a SKILL.md spine.
- New agent? It gets the module-05 discoverability checklist: router row, README line,
  read-before-action links instead of inlined detail.

## Code tour (short, by design)

1. `AGENTS.md` → Maintaining instructions + Git and secrets — the whole module's source.
2. `.gitignore` — map each entry to a leak it prevents.
3. `write-test-cases/evals/evals.json` — pick the eval closest to a rule you changed in
   module 06 and update (on paper) its expected properties.

## Exercises

1. Write the one-commit diff plan for this change: "plain `Bug` items no longer carry
   the component field; tag only." List every file (home, reminders, routers) it touches.
2. Invent a deprecation: you want to drop `ado-testcase-priority`'s dry-run default.
   Write the migration note you'd put in the agent, and decide whether router text
   changes.
3. Simulate a leak: someone committed a real org URL into a reference file. Write the
   remediation steps (fix, history check, placeholder convention note) and the grep
   line that proves the tree is clean.
4. Review your module-06 build against this module: which maintenance rules did you
   already satisfy, which did you miss?

## Self-check

- Why must a rule edit and its reminders land in the same change?
- What makes companion-project references safer than tracked cross-repo links here?
- Name the two automated-ish gates that catch regressions (hint: one runs per artifact,
  one asserts skill behavior).
- You add a skill that three agents now reference. What must stay true about its
  frontmatter description so routing doesn't degrade?

## Where you go next

- Rerun module 06's Phase D against the *real* assistant and iterate until drift is zero.
- Contribute one improvement back to this repo using the change rule from this module.
- Rebuild this learning path for the `playwright-ts` and `python-tools` repos and
  compare how their conventions differ — that contrast is the interview-ready part.
