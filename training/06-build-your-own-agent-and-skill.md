# 06 — Build your own agent + skill

**Why this comes now:** you've read the router (01), dissected an agent (02) and a
skill (03), seen composition (04), and learned where rules live (05). Time to extend
the framework yourself — a guided build, checked against the real conventions.

## The brief

Build a **"weekly release-notes digest"** workflow:

- Agent `release-digest`: given an iteration, lists PBIs completed this week, grouped
  by area path, read-only, with a fixed summary template.
- Skill `ado-query-playbook`: reusable reference for WIQL patterns (bucketing, date
  filters, hierarchy links) plus a small validator that checks a rendered digest.

Work in `training/notes/build/` (gitignored) first; only promote to `.github/` when the
exercise tell you to.

## Phase A — Design before writing (20 min)

1. Write the trigger contract: three user phrases that MUST route to `release-digest`,
   and two that must NOT (e.g. anything about test cases — that's `write-test-cases`).
2. Decide what's agent vs skill. The WIQL table format and bucketing rules are reused
   by future agents → skill. Invocation, step order, error behavior → agent.
3. Choose the canonical home for each rule you introduce. List them before writing.

## Phase B — Scaffold the skill (30 min)

Create `training/notes/build/ado-query-playbook/SKILL.md`:

```yaml
---
name: ado-query-playbook
description: '...trigger phrases + negative scope...'
---
```

Body spine: prerequisites → WIQL recipe index → bucketing rules → output expectations.
Add `references/wiql-patterns.md` with 3 copyable WIQL snippets, and
`scripts/validate_digest.py`: stdlib-only, exits non-zero unless the digest has
Scope/Assignee lines and at least one bucket heading (mirror the validators in
`.github/skills/write-test-cases/scripts/` — read `validate_checklist.py` first and
copy its CLI/reporting shape).

## Phase C — Scaffold the agent (25 min)

Create `training/notes/build/release-digest.agent.md` following the section skeleton
from module 02:

- Frontmatter (`name`, `description` with trigger phrases, `tools`).
- Persona + `**Invocation:**` + `**Example:**`.
- Step 0 — prerequisites with a **link** to `azure-devops-cli/references/ado-conventions.md`
  (do not restate the auth steps!).
- Workflow: resolve iteration → WIQL with a 7-day `ClosedDate` filter → bucket by area
  path → render per the Final Summary template.
- Error Handling table (fatal vs degraded — can a missing area path degrade to
  "Ungrouped" the way standup does for parents?).
- Gotchas: at least two real ones you learned from ado-standup (e.g. WIQL quoting).

Then wire it: a new row in the copy of `AGENTS.md` Routing table, and a line in
README's agent table — the three-layer discoverability check from module 05.

## Phase D — Exercise it dry (15 min)

No ADO access needed: hand the agent file to an AI assistant with "run release-digest
for iteration X; here's a fake WIQL JSON result" and check whether it: (a) asks for/
reads conventions before auth, (b) produces the exact template, (c) treats zero closed
items as config_error per the run contract. Fix the file where it drifts.

## Self-check

- Which of your rules ended up in the skill vs the agent, and does your AGENTS.md row
  survive the module-05 checklist (guide → entrypoint → scoped instructions)?
- Does your agent contain any table that belongs in a reference? Move it.
- What did the validator catch in Phase D that human review missed?
- If a teammate edits `wiql-patterns.md`, what else must they touch per the maintenance
  rule? (Peek at module 07.)
