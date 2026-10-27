---
name: write-test-cases
description: 'Author manual QA test cases from feature requirements as Azure DevOps CSVs. Use for requests to write test cases, create scenarios, plan feature QA, or document test coverage. Explicit test checklist or Test execution Description requests produce plain-text checklists. Fixed sprint QA runs enter through ado-test-case-author, which uses this workflow internally. Not for automated test code.'
---

# Write Test Cases

Transforms product requirements into structured, traceable test cases with complete coverage across functional, edge case, error, and state transition scenarios.

## When to Use This Skill

- User asks to "create test cases", "write test cases", "create test scenarios", or "generate test cases"
- User asks to "plan QA", "write test documentation", or "cover this feature with tests"
- User provides a PRD or requirement file and wants test coverage derived from it
- User describes feature requirements verbally and needs structured QA test cases
- User asks "what tests should I write?" for a feature
- User explicitly requests a test checklist (keywords: "test checklist", "checklist for test execution") or asks for content to "paste into Test execution Description" — this opt-in request generates an optional plain-text list for Test execution tasks

> **Not for code tests** — this skill produces human-executed QA test documentation (CSV for Azure DevOps). For Playwright specs, unit tests, or pytest, do not use this skill.

For fixed sprint QA planning, enter through `@ado-test-case-author`; it applies this
workflow with its pipeline-specific scope and manifest contract.

## Workflow

### Step 1: Gather Requirements

Identify the source of requirements:

1. If the user provides a file path to a PRD, read it
2. If the user provides a Confluence URL, read the page using the confluence-assistant skill, then apply the **classify-before-fetch** rule below to every embedded reference link before extracting any scenarios. Code values in requirement mapping tables (e.g. Attribution type, Business type, Portfolio transaction type) may differ from the authoritative reference page — always prefer the value from the reference page and flag any discrepancy to the user.
2a. If the requirement source is an Azure DevOps work item (fetched directly via `az boards work-item show` or the azure-devops-cli skill, not just through the sprint QA pipeline agent), treat its `System.Description`, `Microsoft.VSTS.Common.AcceptanceCriteria`, and **every comment** the same as a Confluence page: scan each for embedded `your-confluence.example.com` links and apply the classify-before-fetch rule to each. This applies whether the work item was given to you as a URL, an ID, or fetched incidentally while answering another request — an ADO description or acceptance-criteria field is never a complete requirement on its own if it contains reference links or unread comments. Never treat linked "Related Work" items as a requirement source. Recurse into links found on fetched pages too, applying the same discrepancy-flagging rule as item 2.
3. If the user describes requirements verbally, capture them
4. If requirements are unclear, follow **Clarify before assuming** below (do not ask generic questions that the sources already answer).

**Classify before fetching:** for each embedded reference link, judge from its link text, surrounding sentence, and page title — without opening it — whether it is **relevant** (defines, maps, or constrains behavior for this requirement) or **unrelated** (navigation, space home, glossary/reference for a different feature). Fetch only relevant links; note unrelated ones as excluded without opening them. This keeps a wiki's cross-linking from turning a handful of true requirement references into an unbounded crawl. When a source's link count or recursion depth makes manual stopping-point judgment unclear, apply the same 25-page cap and 2-hop recursion limit the sprint pipeline uses (`.github/agents/ado-test-case-author.agent.md` Step 3b) rather than inventing a different limit.

**Record precedence and out-of-scope:** when two sources disagree (spelling, value, or described behavior), note both with their source and date; a canonical reference/spec page overrides a comment, and between two sources of the same kind the later revision wins — flag anything still ambiguous to the user instead of silently choosing. Record every explicit out-of-scope or excluded-behavior statement and never generate a scenario for it in Step 2 or Step 6b.

**Clarify before assuming:** after the sources are read, list every open item: an unresolved conflict, a missing observation point or discriminator, an unknown value or option code, an unclear flow, stale requirement text. Resolve each with this ladder, in order:

1. **Sources first** — answer it from the read sources and precedence rules; no question needed.
2. **Ask the user** — for every item still open, invoke the `ask_user` tool (a single form per PBI, at most 5 questions). Each question names the PBI and the conflicting or missing source, offers the plausible options from the sources as a suggested-value list (recommended option as the default) plus the freeform answer, and one question per item. Treat the answers as a requirement source: log them in the Source Log as "User clarification (<date>)" and apply them as final.
3. **No clue, or the user declines/does not know** — do not guess. Write the item as a PO question (Step 6c) and still generate the test case, linking each step that relies on the open item with `[Assumption: PO-Q<n>]` (see Step 6c).

Skip `ask_user` when it is not in your available tools or no interactive user exists: go straight to step 3 and report the open items and PO questions in the summary.

**Do not proceed to Step 2 until every relevant reference link found in every requirement source (PRD, Confluence page, ADO work item field, or comment) has been read, and any conflicts or out-of-scope statements have been noted.**

### Step 2: Extract Test Scenarios

For ShopApp navigation, Component selection, EVENTBUS triggers, or SHP/carrier-message behavior, read
[shopapp-domain.md](references/shopapp-domain.md) before choosing steps or expectations.

Analyze requirements and extract:

1. **Functional** — Normal use cases from requirements
2. **Edge case** — Boundary conditions, empty states, maximum limits
3. **Error** — Invalid inputs, permission failures, network errors
4. **State transition** — All valid and invalid state changes (if stateful)

For each scenario identify: preconditions, test steps, expected results, postconditions.

**When requirements describe multiple flows** (e.g., New + Modify + Authorize), treat each flow as a separate group. Cover each flow's happy path before diving into edge cases for any single flow — breadth of coverage across all flows matters more than depth on one flow.

### Step 3: Plan Coverage (internal — not the output format)

Before generating CSV, build a mental coverage matrix mapping each requirement to its test scenarios. For each scenario note: category, preconditions, steps, expected result.

Use these category prefixes to organise your thinking:

| Prefix | Category |
|--------|----------|
| TC-F | Functional (happy path) |
| TC-E | Edge case |
| TC-ERR | Error handling |
| TC-ST | State transition |

> **These prefixes stay in your head (or a coverage matrix) — they are never written into the CSV Title column.** Titles in the CSV must be plain descriptive sentences (see CSV Format Rules below).

**How many test cases?** Aim for 5–15 per feature. Simple features (single CRUD form, one service call) need fewer; complex stateful features (maker/checker workflows, multi-step wizards) need more. Prioritise breadth across all requirements before adding depth to any single requirement.

**Example coverage matrix (internal only):**

| Requirement | Category | Scenario |
|---|---|---|
| Order saves with valid data | TC-F | Fill all mandatory fields, click Save, verify status = Placed |
| OrderTotal below minimum | TC-E | Enter amount < min, expect validation error on Save |
| Concurrent save conflict | TC-ERR | Two users modify same order, second save fails |
| Placed → PendingReview when DiscountRate > 0 | TC-ST | Enter order with DiscountRate, verify status after save |

Test-case output is CSV (Step 6). An explicit checklist-only request uses Step 6b without
requiring a CSV; unresolved gaps use the plain-text PO questions file in Step 6c.

### Step 4: Generate Test Cases

For each scenario create a detailed test case. Ensure:

| Rule | Detail |
|------|--------|
| Unique IDs | Use TC-F, TC-E, TC-ERR, TC-ST prefixes **in your planning only** — strip them from the CSV Title column before writing |
| Requirement traceability | Every test links to a specific requirement |
| Executable steps | Clear enough for any QA engineer |
| Measurable results | Expected results must be verifiable |

#### Step granularity

Each step should represent one user action or one verification. Combine setup actions (e.g., "fill Client, Currency, and Amount fields") into a single step when they don't need individual assertions. Split verification steps so each checks exactly one thing — this makes failures easy to diagnose.

Good: `"Navigate to ORD00, Orders → ORD01, Order Portal and locate an order with Status = Placed"` (one navigation action)
Bad: `"Navigate to portal, find order, click Modify, and verify all fields are prefilled"` (mixes action + verification)

**Step concreteness rules:**

- **Never use "Prepare preconditions" as a step action** — always describe the specific user action the QA engineer should take. "Prepare preconditions: ensure a Store stock record exists" tells the tester nothing; "Go to Shipment Portal and create a new shipment (eg: split shipment)" tells them exactly what to do.
- **Include a concrete example in parentheses** when the action type can vary (e.g., "create a new CA (eg: stock dividend)"). This anchors the step to a specific scenario without over-constraining it.
- Steps must be immediately executable by any QA engineer who has never seen the spec. If a step requires domain knowledge to interpret, rewrite it as a specific action.

**Backend observation contract:**

Every service or integration assertion must contain these three parts:

1. **Observation point** — name the interface used to inspect the result, such as a specific
   portal screen, API response, database table, Kibana service trace, LEDGER posting,
   queue, topic, or output file.
2. **Correlation key** — state how the tester finds the same transaction, such as
   `<CorrelationId>`, `<SenderReference>`, `<AccountNumber>`, or `<PostingId>`.
3. **Exact expectation** — list requirement-backed field names and values or formulas. Phrases
   such as "values mapped", "source data mapped", "correct fields", and "expected values" are
   not measurable results.

If requirements do not identify an observation point or field-level mapping, do not invent one.
Use a confirmed user-visible outcome, or flag the missing testability detail instead of writing a
vague assertion.

**Navigating to a portal and opening a record's Details screen are always two separate steps**, each with its own Expected result:

- Step N: Navigate to `[portal]` and locate/search for the record. Expected: `"[Screen name] screen opens."` (e.g. `"SHP01, Shipment Portal screen opens."`)
- Step N+1: Open/click the record to view its Details. Expected: `"The [Module] Details screen opens."`

Never combine navigation + opening details into a single step.

### Step 5: Validate Coverage

Before finalising, verify:

1. Every requirement has at least one test case
2. Happy path is covered for all user flows
3. Edge cases address boundary conditions
4. Error scenarios cover failure modes
5. State transitions are tested if the feature is stateful

Generate additional requirement-backed cases for coverage gaps. Missing specified behavior
is a requirement gap: record it in Step 6c rather than inventing an expectation.

### Step 6: Write Output

Write standalone test cases to `qa-output/test-cases/<name>-test-cases.csv` where `<name>` is the requirement file name (without `.md`) converted to kebab-case. Sprint pipeline runs write to `qa-output/test-cases/sprint-<slug>/<name>-test-cases.csv`. For example, a requirement file `Orders - Get translation of order description.md` produces `orders-get-translation-of-order-description-test-cases.csv`.

For inline requirements, derive the same kebab-case name from the PBI/feature title.
Before writing, apply [CSV Format Rules](#csv-format-rules): Test Case IDs are empty,
including when updating an exported CSV; only real Shared Steps references retain IDs.
Priority is managed separately with `@ado-testcase-priority`, not as a CSV column.

#### Step 6b: Optional — Generate a plain-text checklist for Test execution

- Only generate a plain-text checklist when the user explicitly requests it using the checklist trigger keywords (e.g., "test checklist", "checklist for test execution") or asks for content to "paste into Test execution Description", or otherwise specifies a "Test execution" task wording. This is opt-in only; plain requests to "write test cases" or "comprehensive test coverage" still produce CSV only.
- Read `references/testing-principles.md` → **Coverage Requirements** before creating the
  checklist. Evaluate Happy Path, Edge Case, Error Handling, and State Transition coverage for
  the specific requirement.
- Every checklist must contain at least one requirement-backed Happy Path, Edge Case, and Error
  Handling scenario. Include State Transition scenarios when applicable. Never publish or attach
  a checklist missing any mandatory category.
- If no in-scope requirement supports an Edge Case or Error Handling scenario, stop and ask the
  user for scope clarification. Never invent a scenario or restore behavior that the requirement
  explicitly marks out of scope.
  Write the open PO question from Step 6c, but do not write a checklist or place that question
  under an Error handling/Edge case checklist label yet. A request for all coverage categories
  is not consent to include inferred behavior. Await the user's explicit decision.
- If the user explicitly opts to include a scenario anyway despite no requirement backing it,
  label the item as inferred (e.g. "Inferred scenario, not explicit in the PBI text: ...") and
  phrase it as an **open question**, not an asserted specific outcome. Never assert a specific
  pass/fail expected result (e.g. "the entry must be rejected") for behavior no source
  describes — that risks a false bug report or a false pass. Write the same question, with a
  concrete example, to the PO questions file (Step 6c) so it can be confirmed before test
  execution.
- Source checklist items from the Step 3 coverage matrix. When the CSV was deliberately trimmed
  (for example, happy-path-only), include additional in-scope edge, error, and state scenarios
  from the coverage matrix even though they are absent from the CSV. Otherwise derive the
  checklist from the complete CSV set.
- Write one literal hyphen-list item per line using exactly one of these forms:
  `- Happy path:`, `- Edge case:`, `- Error handling:`, or `- State transition:`.
- Do not add a heading, numbering, checkboxes, bracketed category tags, blank separator sections,
  or formatting beyond the required `- ` list marker.
- If a scenario also exists as a CSV Test Case, the sentence after the coverage prefix must match
  the CSV title verbatim.
- For checklist-only requests (no CSV produced), derive `<name>` using the same requirement-file-name / PBI-title kebab-case rules as for CSV naming. If no CSV is generated, skip reconciliation.
- Standalone checklist output:
  `qa-output/test-cases/<name>-checklist.txt`.
- Sprint checklist output:
  `qa-output/test-cases/sprint-<slug>/checklists/<name>-checklist.txt`.
  Create the sprint's `checklists` directory when it does not exist. Never place a sprint
  checklist directly beside the sprint CSV files.
- From repository root, run `uv run python .github\skills\write-test-cases\scripts\validate_checklist.py <checklist-path>`
  before attaching the checklist. Structural validation does not replace the semantic review
  against all four Coverage Requirements and explicit exclusions.

#### Step 6c: PO questions file — for gaps and conflicts needing PO input

Whenever Step 1's conflict/out-of-scope recording, Step 6b's inferred-scenario labeling, or a
later review (e.g. a rubber-duck pass) surfaces a genuine, **unresolved** requirement gap or
conflict — not a wording nit, and not a conflict already settled by source precedence — write
one plain-text question file per PBI/requirement so the answers can later be confirmed and
attached as a PBI comment:

- `<name>` uses the same requirement-file-name / PBI-title kebab-case rule as Step 6's CSV
  naming and Step 6b's checklist naming.
- Standalone: `qa-output/test-cases/<name>-questions.txt`.
- Sprint pipeline: `qa-output/test-cases/sprint-<slug>/po-questions/<pbi-id>-questions.txt`.
- Format: numbered items, each with **the question**, a **"Why it matters"** line naming the
  specific source(s) involved — or stating plainly that no source describes the proposed
  behavior, when there is no conflicting source to cite — a **"Affects:"** line naming the test
  case title(s) and step number(s) that carry `[Assumption: PO-Q<n>]`, and a concrete
  **"Example"** grounding
  the ambiguity in real field/value names from the requirement. No markdown formatting — plain
  text only, since this is drafted for eventual copy-paste into an ADO comment.
- Include: unresolved Conflicts, missing discriminators that make a test case non-reproducible
  (e.g. two scenarios triggered by identical steps but asserting different outputs with no
  distinguishing field), inferred Edge/Error items from Step 6b, and any requirement text that
  is stale relative to a later decision (e.g. a Description not yet updated to match an agreed
  comment-thread change).
- Never guess an answer to include in the CSV/checklist in place of asking — only items still
  open after the Step 1 `ask_user` round reach this file. Ship the happy-path/labeled-inferred
  version and let the question file carry the ambiguity.
- **Link steps to questions.** Every CSV step whose Action or Expected text relies on an open
  question gets `[Assumption: PO-Q<n>]` appended (`<n>` = the item number in this file).
  Each question gets an `Affects:` line naming the test case title and step number(s) it
  touches, so the two files cross-reference. `validate_csv.py` (EVAL-QUALITY-008) fails a
  marker that points to a missing question. After the PO answers, update the steps and remove
  the marker.

The `qa-output/` directory is at the repository root. Use the templates in [templates/](./templates/) as a structural reference for CSV format.

#### Which template to use?

| Scenario | Template |
|---|---|
| Test involves navigating the ShopApp portal UI (entry screen, view screen, grid, buttons) | [`template-portal.csv`](./templates/template-portal.csv) |
| Test involves Shipments portal UI (SHP01, Shipment Portal — details screen pattern) | [`template-shipment-portal.csv`](./templates/template-shipment-portal.csv) |
| Test validates a backend service, integration, event, JSON payload, or DB state — no UI login needed | [`template-service.csv`](./templates/template-service.csv) |
| Test validates a **single** ledger posting sent from a module (ORD / PAY / SHP / INV) to LEDGER via `CreateSinglePostingCommand` — verifying header, order posting, and account line instances | [`template-ledger-posting.csv`](./templates/template-ledger-posting.csv) |
| Test validates a **bulk** ledger posting flow where a module sends `StartBulkCommand` + one or more `CreateBulkPostingCommand` + `EndBulkCommand` to LEDGER (e.g. PAY fee batch) | [`template-bulk-ledger-posting.csv`](./templates/template-bulk-ledger-posting.csv) |
| Need a real-world domain example showing a full order portal flow | [`template-order-portal.csv`](./templates/template-order-portal.csv) |

**Portal tests** always start with the Login shared step (`"1000","Shared Steps"`; use your project's real Login Shared Steps ID).  
**Service tests** start directly with a data-preparation step — no Login row.

> **Hybrid rule — backend change, portal testing**: The template is determined by **how you test**, not by what the spec describes. If the spec describes a backend or DB change to an SHP entity (e.g. `Shp.Parcel`, `Shp.Allocation`) but the only way to trigger and verify it is through the Shipment portal (create a shipment, trigger determine allocation, query the DB), use `template-shipment-portal.csv` — not `template-service.csv`. See also [references/golden-example-shipment-allocation.csv](./references/golden-example-shipment-allocation.csv) for a worked example of this pattern.

### Step 7: Summary

After generating, provide:
- Total test cases generated
- Coverage breakdown (functional / edge / error / state)
- Assumptions made or areas needing clarification
- File path where test cases were saved
- If a checklist was generated, the checklist file path (e.g. `qa-output/test-cases/<name>-checklist.txt`)
- If a PO questions file was generated, its file path and question count

## CSV Format Rules

These rules are **mandatory**. Violating them causes import failures in Azure DevOps.

### Row types

| Row | ID | Work Item Type | Notes |
|-----|----|----------------|-------|
| Test Case header | `""` | `"Test Case"` | Title, Area Path, Assigned To, State, Component filled here |
| Shared Step reference (existing) | `"<id>"` | `"Shared Steps"` | Only use when referencing an existing shared step by its real numeric ID (e.g. `"1000"`) |
| Step row (no shared step) | *(empty — no quotes)* | *(empty — no quotes)* | Use bare `,,` — **never** `"","Shared Steps"` with an empty ID |

**Test Case IDs must always be empty.** Write every Test Case header as `"","Test Case"`,
including when updating a CSV exported from Azure DevOps or preserving existing test cases.
Never copy or retain an existing Test Case work item ID; populated IDs cause manual import errors.
Only Shared Steps references may contain an ID.

Every non-empty row must contain exactly the 10 fields declared by the header. A normal step row
with Step Expected populated ends with four empty fields (`",,,,`); a Shared Steps row with an
empty Step Expected ends with five (`",,,,,`).

### Title format

- **Do NOT prefix test case titles with IDs** such as `TC-F-001:` or `TC-E-002:`.  
  Write titles as plain descriptive sentences: `"Payment account selection when ShouldBillFees = FALSE"`.
- TC-prefixes are for internal planning only (e.g. coverage matrices); they must be stripped before writing the CSV.

### Navigation paths

Read [domain navigation](references/shopapp-domain.md#navigation) when writing portal
steps. Apply Step 4's separate navigation/Details-step rule.

### Component field values

Before writing each Test Case header, select the value using
[domain Component rules](references/shopapp-domain.md#component). Clarify ambiguous
ownership rather than leaving the ADO-required value empty.

### Minimal correct example

```csv
ID,Work Item Type,Title,Test Step,Step Action,Step Expected,Area Path,Assigned To,State,Component
"","Test Case","Order saves successfully with valid data",,,,"ShopApp\Your Team","","Design",ORD
"1000","Shared Steps",,"1","Login",,,,,
,,,"2","Navigate to ORD00, Orders → ORD01, Order Portal → click New","The Order Entry screen opens in a new tab",,,,
,,,"3","Fill all mandatory fields","All fields are completed",,,,
,,,"4","Click Save","Order is saved with status Placed",,,,
```

## Gotchas

- **Revise CSVs in place** — create a CSV once, then change it only with the `edit` tool. Never
  use temp files, `Move-Item`, or delete-then-recreate for a rewrite.
- **Output goes to `qa-output/test-cases/` at repo root** — standalone files go directly in
  this directory; sprint pipeline files may use one `sprint-<slug>` child directory. Do not write
  inside the skill folder, `tests/`, or deeper nested directories.
- **Requirement images are stored in `assets/<page-slug>/` beside the markdown** and referenced as `assets/<slug>/filename.png`.
- **CSV format must match templates** — use `template-portal.csv` for UI tests and `template-service.csv` for service/integration tests in `templates/`.
- **One CSV per feature** — do not append to existing files; create a new file per generation run.
- **PRD images are not readable** — if the user provides a PRD with embedded images, ask them to describe the content or provide the text version.
- **Multi-line Step Expected values** — when an expected result spans multiple lines (e.g., a list of field values), the CSV cell must be wrapped in double quotes and any inner quotes must be escaped by doubling them (`""`). See the `template-order-portal.csv` template for examples.
- **Use placeholders for environment-specific data** — do not hardcode dates, IDs, or environment-specific URLs in test steps. Use descriptive placeholders like `<AccountNumber>`, `<BusinessDate>`, `<StoreNumber>` that the QA engineer fills in at execution time.
- **Step numbering restarts at 1 for each test case** — do not continue step numbering across test cases. Each test case's steps begin at `"1"` (or `"1"` for a Login shared step reference, then `"2"` for the next step).
- **Before writing scenarios**, confirm Step 1's source inventory is complete, precedence is
  recorded, and explicit exclusions remain excluded.
- **Checklists are opt-in, plain text, and coverage-driven** — generate one only when explicitly
  requested using checklist triggers or "Test execution" task wording. Read all four Coverage
  Requirements in `references/testing-principles.md`, include every applicable in-scope
  scenario, and keep explicit exclusions excluded. Output one `- ` list item per line in a
  `.txt` file under the correct standalone or sprint checklist directory.

### SHP allocation domain knowledge

Read [SHP allocation](references/shopapp-domain.md#shp-allocation) before choosing
the portal workflow and stock-source variants.

### SHP individual reversal — warehouse selection

Read [warehouse selection](references/shopapp-domain.md#shp-individual-reversal-warehouse-selection)
before authoring individual reversal and Closing exception cases.

## Quality Checklist

- [ ] Every requirement has corresponding test cases
- [ ] Happy path scenarios are covered
- [ ] Edge cases include boundary values, empty inputs, max limits
- [ ] Error handling covers invalid inputs and failure scenarios
- [ ] State transitions are tested if applicable
- [ ] Test case titles are plain descriptive sentences — no TC-F-XXX: prefix in the CSV Title column
- [ ] Every Test Case header has an empty ID (`"","Test Case"`); existing Test Case IDs are never retained
- [ ] Every non-empty CSV row contains exactly 10 columns
- [ ] Step rows with no shared step reference use bare `,,` — never `"","Shared Steps"` with an empty ID
- [ ] Shared Steps rows only appear when referencing a real existing shared step with its numeric ID
- [ ] Test steps are clear and executable
- [ ] Expected results are measurable and verifiable
- [ ] Backend assertions name an observation point and correlation key
- [ ] Backend expected results list exact requirement-backed fields and values
- [ ] Coverage matrix shows complete coverage
- [ ] Output written directly under `qa-output/test-cases/`, or under one `sprint-<slug>` child directory for sprint runs
- [ ] All relevant embedded Confluence reference links in requirements have been read — including ADO work item Description, Acceptance Criteria, and every comment, whether fetched via the sprint QA pipeline agent or ad hoc
- [ ] Links classified unrelated were excluded without fetching, and ADO "Related Work" items were never treated as a requirement source
- [ ] Code values from authoritative reference pages are used (not just values from the requirement mapping table)
- [ ] Any discrepancy between a mapping table value and an authoritative reference is flagged to the user, with precedence recorded
- [ ] Every explicit out-of-scope or excluded-behavior statement from a source is preserved and never resurfaced as a generated scenario
- [ ] Checklist evaluates Happy Path, Edge Case, Error Handling, and State Transition coverage
- [ ] Checklist contains at least one requirement-backed Happy Path, Edge Case, and Error Handling item
- [ ] Missing mandatory coverage blocks generation instead of inventing or restoring excluded scope
- [ ] Checklist is a `.txt` file with one literal `- ` list item per line and no checkbox syntax
- [ ] Every checklist line uses `- Happy path:`, `- Edge case:`, `- Error handling:`, or `- State transition:`
- [ ] Sprint checklist is under `qa-output/test-cases/sprint-<slug>/checklists/`
- [ ] For overlapping scenarios, text after the coverage prefix matches the CSV title verbatim
- [ ] Checklist generation only fires when explicitly requested (opt-in)
- [ ] Checklist-only naming follows the same kebab-case rules as CSV naming and is stable
- [ ] No two test cases share identical trigger steps while asserting different, undiscriminated outputs — if a variant (e.g. two values of the same InstructionType) can't be distinguished by a stated field, flag it in the PO questions file instead of guessing a discriminator
- [ ] An expected result that aggregates or nets multiple entries (e.g. "nets to zero", "sum equals X") names the specific offsetting entry/entries, not just the one visible transaction
- [ ] Any inferred Edge/Error item has explicit user opt-in, an inferred label, and an open
  question mirrored in the PO questions file; absent opt-in, checklist output remains blocked
- [ ] Test execution layer (UI vs. API/backend) is explicit per test case, especially for INV/ORD/PAY/SHP tests without a Login step
- [ ] Any asserted expected value is confirmed observable by a tester (UI field, DB column, payload) — not assumed from an internal implementation detail
- [ ] Before finalizing sprint-scale or high-stakes test artifacts, consider a rubber-duck (or equivalent critical) review pass against this checklist and the Conflicts section before attaching checklists or importing CSVs

## References

| File | Contents | When to consult |
|------|----------|-----------------|
| [references/testing-principles.md](./references/testing-principles.md) | Requirement-backed coverage and design patterns | When planning coverage |
| [references/shopapp-domain.md](./references/shopapp-domain.md) | Navigation, Component, EVENTBUS, carrier-message and SHP exceptions | Before choosing domain-specific steps or values |
| [templates/template-portal.csv](./templates/template-portal.csv) | Generic template for portal/UI tests (Login shared step included) | Every time you write a portal/UI test case |
| [templates/template-shipment-portal.csv](./templates/template-shipment-portal.csv) | SHP portal template — shows the two-step navigate→open-details pattern with correct SHP01 path; also includes an SHP allocation variant (Login → Create shipment → Trigger allocation → Query DB → Verify) | Every time you write an SHP Shipments portal test |
| [templates/template-service.csv](./templates/template-service.csv) | Generic template for backend/service/integration tests (no login) | Every time you write a service/integration test case |
| [templates/template-ledger-posting.csv](./templates/template-ledger-posting.csv) | Template for single ledger posting → LEDGER tests: verifies header, order posting, and all account line instances with their attributions | Every time you write a test for a module sending a `CreateSinglePostingCommand` to LEDGER |
| [templates/template-bulk-ledger-posting.csv](./templates/template-bulk-ledger-posting.csv) | Template for bulk ledger posting → LEDGER tests: covers `StartBulkCommand`, `CreateBulkPostingCommand` (header, order posting, account line), and `EndBulkCommand` | Every time you write a test for a module sending a bulk (`StartBulkCommand` / `CreateBulkPostingCommand` / `EndBulkCommand`) to LEDGER |
| [templates/template-order-portal.csv](./templates/template-order-portal.csv) | Domain reference: order portal test showing full portal flow with multi-line expected results | When you need to see a complete example |
| [references/golden-example-shipment-allocation.csv](./references/golden-example-shipment-allocation.csv) | Reviewed golden example for the SHP Allocation hybrid pattern — two test cases (LEDGER path + ERP path) | When writing test cases for any SHP Allocation backend change that is tested via the Shipment portal |
| [references/validator-rules.md](./references/validator-rules.md) | Cheat-sheet of the validator rules that cause rewrites (backend observation point, correlation key, exact expected values, assumption markers) | Before writing any CSV |
| [scripts/scaffold_csv.py](./scripts/scaffold_csv.py) | Generates a valid CSV from a compact JSON spec (header, empty IDs, Login shared step, quoting, `assumption` markers) and runs the validator | Preferred way to write any CSV: write the small spec, not hand-quoted CSV |
| [scripts/validate_csv.py](./scripts/validate_csv.py) | Automated CSV validator — run against any generated CSV to check blocking rules | After generating any CSV to catch format errors |
| [scripts/validate_checklist.py](./scripts/validate_checklist.py) | Plain-text checklist structural validator | Before attaching any checklist to a Test execution task |

Validators contain their blocking checks and require no external evaluation files.
Repository-only evaluation assets are outside the portable framework; they are not
prerequisites for authoring, validation, or changing this workflow. Use bounded synthetic
behavioral probes plus the validators when checking instruction changes.

### Running the validator

Run from repository root:

```powershell
uv run python .github\skills\write-test-cases\scripts\validate_csv.py qa-output\test-cases\<name>-test-cases.csv
```

Exit code `0` = all checks passed. Exit code `1` = one or more failures (output shows which eval IDs failed).
