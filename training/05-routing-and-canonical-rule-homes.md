# 05 — Routing & canonical rule homes

**Why this comes now:** before you *add* anything (module 06), you must know where rules
live and how discovery is wired — otherwise every new file makes the framework harder to
navigate instead of more capable.

## Concepts

### One rule, one home

Each detailed rule has exactly **one canonical home** (e.g. bug field/template rules live
only in `azure-devops-cli/references/bug-reporting.md`). Everything else holds either:

- a **pointer row** ("Before filing formal bugs → read X") in `AGENTS.md`, or
- an **action-point reminder** — a 1–2 line crib of the constraint *at the moment of
  decision* (e.g. the "Before CSV output, keep every Test Case ID empty" line right after
  the rule-homes table).

Reminders may repeat a constraint; procedures and tables may not be duplicated. This is
the framework's answer to doc drift.

### The three-layer routing system

1. **Root router** — `AGENTS.md`: request-shape → entrypoint (Routing table), and
   action → rule home (Canonical rule homes table).
2. **Section router** — `.github/skills/README.md`: picks a skill + states per-workflow
   prerequisites.
3. **Trigger text** — frontmatter `description` in each agent/skill: the last-mile match
   when a user phrase lands without going through a human reading the router.

### Bounded crawl as routing inside a skill

The "classify before fetching" rule (write-test-cases Step 1, mirrored in
`ado-test-case-author` Step 3b) is routing applied to *information*: judge a link from
its text/title *before* spending I/O on it; cap recursion (25 pages, 2 hops) so a wiki's
cross-linking can't turn one requirement into an unbounded crawl. Same pattern, new domain:
declare the route first, then travel.

### Discoverability checklist (from Maintaining instructions)

Any new/changed rule must be reachable from: **this guide** (AGENTS.md) →
**the relevant entrypoint** (agent/skill) → **file-scoped instructions** where they exist.
If any of the three wouldn't find it, the wiring is unfinished.

## Code tour

1. `AGENTS.md` — compare the Routing table with the Canonical rule homes table. Column
   one differs in kind: *requests* vs *actions*. Why?
2. `.github/skills/README.md` — "Supported skills" and "Prerequisites by workflow":
   second-level routing with setup constraints attached.
3. `write-test-cases/SKILL.md` Step 1 — read the classify-before-fetch paragraph and the
   precedence ladder ("Clarify before assuming").
4. `ado-bug-report.agent.md` Step 3 — an action-point reminder ("component === tag",
   `YourOrg.Component` only on plain `Bug`) pointing at its rule home in bug-reporting.md.

## Exercises

1. New rule arrives: "checklist attachments always target the Test execution task."
   Decide its canonical home, its action-point reminders, and whether a router row
   changes. Write the three edits you'd make (file + line intent).
2. Find one action-point reminder in the export that restates a home's constraint, and
   one place where a reminder *should* exist but doesn't (justify briefly).
3. You're adding a "sprint retro summary" agent. Write its one-line Routing-table row
   and its frontmatter `description`, keeping trigger phrases distinct from ado-standup's.
4. Audit: run a mental grep — is `bug-reporting.md`'s severity/priority default stated
   anywhere outside its home? What did the export's own history (see git commits in the
   source repo) say about keeping these in sync?

## Self-check

- State the difference between a pointer row and an action-point reminder.
- Why does classify-before-fetch belong in routing philosophy, not just web scraping?
- Which three places must discover a new rule before you call the change done?
- What breaks first when two files each hold their own copy of a detailed table?

