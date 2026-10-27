# 02 — Anatomy of an agent

**Why this comes now:** agents are the smallest complete unit of the framework. Once you
can read one cold, skills (module 03) are just the reference shelves the agent reaches for.

We dissect `.github/agents/ado-standup.agent.md` — deliberately the simplest agent:
read-only, no pytools dependency, one skill reference.

## Concepts

### The agent-file contract (as used in this repo)

Per the "Maintaining instructions" section of `AGENTS.md`, an agent file contains:

1. **Frontmatter** — `name`, `description` (trigger phrases included), `tools`.
2. **Persona + invocation** — one line of role, then exact invocation syntax and examples:
   `**Invocation:** ... **Example:** ...`
3. **Scope/limitations** — what it will NOT do ("This agent never mutates work items.").
4. **Step 0 — prerequisites** — toolchain and auth, with a read-before-action link to the
   canonical conventions (the agent does not restate them: one link, one home).
5. **Ordered workflow** — numbered steps, each with exact commands and **completion
   criteria** embedded ("take the first/only entry", "use the returned `path` as ...").
6. **Error behavior** — a table mapping step → failure behavior (here: all fatal, print
   the exact error; never mask a missing-auth failure as an empty result).
7. **Final-output contract** — an exact output template, so the assistant can't drift.
8. **Gotchas** — environment-specific landmines learned the hard way (`--timeframe current`
   needs `list` not `show`; `$PID` is reserved in PowerShell; `@Me` resolves to the PAT
   owner, not the human).

### Design tension to notice

An agent is **prose about commands** — but the prose exists to make execution
*deterministic*: exact CLI calls, exact fallbacks, exact output shape. When you write
agents, you are writing a runbook a model can execute reliably, not documentation a
human skims.

## Code tour

Read `ado-standup.agent.md` in full with these questions beside you:

- Lines 1–5: which trigger phrases in `description` would route "what am I working on?"
- "Scope": how does `--all` change behavior, and why is unbounded history made *explicit*?
- Step 0: why "read and apply" a linked doc instead of repeating the auth commands?
- Workflow step 1: find the exact fallback (`list` instead of `show`).
- Workflow step 4: which link relation identifies a parent PBI?
  (`System.LinkTypes.Hierarchy-Reverse`, parent ID from the last URL segment)
- Gotchas: which two would have cost you 10–30 minutes each in real usage?

Then skim a heavier agent for contrast: `.github/agents/ado-bug-report.agent.md`
(write operations, field contracts, verification loops). Don't study it yet — note how the
same section skeleton scales up.

## Exercises

1. Add (on paper or in `notes/`) a `--blocked-only` filter flag to ado-standup:
   write the Scope change, the WIQL change, and the Summary change it requires.
2. Intentionally break one thing (e.g. remove the iteration filter) and predict which
   Error Handling row would fire. Is it fatal or masked?
3. The final summary template uses emoji buckets. Find the workflow step that decides
   bucketing and list every tag/state that lands in each bucket.
4. Compare `ado-standup`'s Step 0 with `ado-testcase-priority.agent.md`'s prerequisites.
   What's identical? That's the canonical-rule-home pattern in action.

## Self-check

- Why does the output contract show a literal template instead of describing it in prose?
- What makes an error "fatal" vs reportable, in this agent's terms?
- Why does `@Me` deserve a gotcha? (Whose board do you actually read with a shared PAT?)
- If you had to cut one section from an agent file without losing reliability, which
  could survive removal — and which absolutely could not?
