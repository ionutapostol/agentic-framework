# 03 — Anatomy of a skill

**Why this comes now:** you can already read an agent; now you learn the knowledge layer
agents lean on. Skills are where the framework's *rules, conventions, and objective
checks* actually live — get this structure right and everything you build in module 06
falls into place.

Main specimen: `.github/skills/write-test-cases/` (the richest skill).
Contrast specimen: `.github/skills/azure-devops-cli/` (compact, reference-only).
Odd one out: `.github/skills/confluence-assistant/` (ships runnable scripts + its own
`uv` project, `.env.example`, and credential rules).

## Concepts

### SKILL.md: the spine

- Frontmatter `description` doubles as the **trigger contract** — it enumerates the
  phrases that should route here, plus explicit *negative* scope ("Not for automated
  test code"). Negative scope prevents skill squatting: two skills must not both claim
  "tests".
- The body is the *procedure spine*: ordered steps, decision rules ("classify before
  fetching", "clarify before assuming"), and opt-in gates. It deliberately does **not**
  contain every detail.

### references/: progressive disclosure

Detail is loaded only when a step needs it: `shopapp-domain.md` (domain vocabulary),
`validator-rules.md`, templates, a golden-example CSV. This keeps context windows small
and gives each detail exactly one home (tie back to module 01's router principle).

### scripts/: objective validators

`validate_csv.py`, `validate_checklist.py`, `validate_manifest.py` — stdlib-only so they
run anywhere with `uv run python`. A validator turns "looks right to me" into
pass/fail output the agent must respect (note the `PYTHONIOENCODING` workaround in
`.github/skills/README.md` — platform reality leaks into skill docs, and that's correct).

### evals/: the skill tests itself

`evals/evals.json` holds prompts + expected properties. It's how you detect that an
edit to SKILL.md silently degraded output quality — the skill-level analog of unit tests.

### requirements/: sample inputs

Real (sanitized) requirement pages. They make evals repeatable and give you concrete
material for module 06 exercises.

## Code tour

1. `write-test-cases/SKILL.md` — read Step 1 (Gather Requirements) through the
   "classify before fetching" rule. Note the recursion cap (25 pages / 2 hops) and its
   cross-reference to the sprint agent — one rule, two homes linked.
2. `azure-devops-cli/SKILL.md` + `references/ado-conventions.md` — see how a skill can
   be mostly references: Smart Defaults, env vars (`ADO_PAT`, `ORGANIZATION`), and the
   placeholder org URL.
3. `confluence-assistant/SKILL.md` — configuration section, `.env.example`, and the
   rule "never `web_fetch` internal Confluence links — use the skill's scripts".
4. `write-test-cases/evals/evals.json` — read two entries: what does an eval assert?

## Exercises

1. Pick one rule from `write-test-cases/SKILL.md` (e.g. "keep every Test Case ID empty").
   Find which validator script enforces it and how. If no validator does, write down
   what a check would look like.
2. In `azure-devops-cli`, list every configuration value and its source-of-truth file.
   Which are secrets, which are defaults, which are placeholders here?
3. Describe, in bullet form, what would break if `references/shopapp-domain.md` were
   merged into SKILL.md. (Context size? discoverability? maintenance?)
4. Design one new eval entry for evals.json: a prompt, the skill it exercises, and two
   asserted properties of a correct output.

## Self-check

- What goes in SKILL.md vs references/? State the rule in one sentence.
- Why are validators stdlib-only?
- What's the difference between an eval and a validator?
- A user asks for "a quick automated API test". Which skill does the router NOT send
  them to, and why is that written in the skill itself?
