# 01 — Framework mental model

**Why this comes now:** every file in this repo only makes sense once you understand
the three roles — router, agent, skill — and how an AI assistant discovers and follows them.
Everything later assumes you can tell at a glance which role a file plays.

## Concepts

### The three roles

1. **Agents** (`.github/agents/*.agent.md`) — fixed workflow entrypoints. A user invokes
   one by name (`@ado-standup`). Each agent is an ordered procedure: steps with
   completion criteria, error behavior, and a final-output contract.
   Frontmatter:
   ```yaml
   ---
   name: 'ADO Standup'
   description: '...Use when asked for "standup summary"...'
   tools: ['read', 'execute']
   ---
   ```
   The `description` is not decoration — it's the trigger text a router matches against.

2. **Skills** (`.github/skills/<name>/`) — on-demand know-how. A `SKILL.md` holds the
   spine of a procedure; `references/` hold detail loaded only when needed
   (progressive disclosure); `scripts/` hold objective validators; `evals/` test the
   skill itself. Skills are pulled in by agents, by the router, or by direct request.

3. **Router** (`AGENTS.md` at the root) — the single guide that owns *routing*
   (request → entrypoint) and the *run contract* (rules every pipeline run obeys).
   It points at "canonical rule homes" instead of duplicating rules.

### Why the split exists

- An agent without skills would have to inline every table, convention, and template —
  unreadable in one context window and impossible to reuse across agents.
- Skills without agents would be a pile of knowledge with no guaranteed execution order.
- A router without both would have nothing to route to.

### Discovery flow

```
user request → AGENTS.md routing table → agent file → read-before-action links → skill → references/validators
```

Key idea: **nothing important is discovered by accident.** Every hop is an explicit link.

## Code tour

Open these in order:

1. `AGENTS.md` — read the Routing table and Canonical rule homes table. Note that every
   "Read" cell is a link into a skill, and that "Before doing this" phrasing is an
   action point, not a topic.
2. `.github/agents/ado-standup.agent.md` — just the frontmatter and headings for now;
   you'll dissect it fully in module 02.
3. `.github/skills/write-test-cases/SKILL.md` — frontmatter only: see how the
   `description` lists trigger phrases ("create test cases", "generate test cases").
4. `.github/skills/README.md` — the skills index: a second-level router for skills.

## Exercises

1. For each file under `.github/agents/`, write one line: which routing-table row in
   `AGENTS.md` points to it, or note that none does.
2. `ado-board-tasks.agent.md` and the `azure-devops-cli` skill both mention ADO.
   Explain in two sentences why the split is agent vs skill and not, say, two agents.
3. Trace one request by hand: "file a bug for a failing order flow". Write the hop
   sequence (router row → agent → skill reference files) you expect the assistant to follow.
4. Find a skill that no agent links to directly. How would a user reach it?

## Self-check

- What lives in an agent's `description`, and who reads it?
- Why does `AGENTS.md` say "detailed procedures and tables belong only in their home"?
- Name the three subfolders a skill can have beyond `SKILL.md` and what each is for.
- A teammate pastes a full ADO conventions table into an agent file. Which principle
  does that violate, and what's the fix?
