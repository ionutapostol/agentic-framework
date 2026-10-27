# Validator cheat-sheet (`validate_csv.py`)

Read this before drafting. Sprint pipeline files must be named
`<pbi-id>-<pbi-slug>-test-cases.csv` (sprint naming contract; the validator itself accepts any
`<name>-test-cases.csv`). Write the CSV to pass these checks the first time. The script is the authority; this page
only summarizes the rules that caused rewrites. Run from repository root:

```powershell
uv run python .github\skills\write-test-cases\scripts\validate_csv.py "<csv-path>"
```

## Backend steps (EVAL-QUALITY-006 and 007)

A step is a **backend assertion** when its action contains a verb (assert, validate, inspect,
verify, check, confirm, search, query, open, locate, view, call, use) **and** a backend word
(LEDGER, SHPM02, database, API, endpoint, queue, log, response body, `table`, a `…Command`,
request/response/message). Portal-only UI steps (SHP01/ORD01 buttons, fields, dialogs) are exempt.

For each backend assertion:

| Rule | Passes | Fails |
|---|---|---|
| Name an observation point (kibana, elasticsearch, ledger, shpm02, shp01, ord01, portal, database, table, api, endpoint, queue, topic, log, trace, response body, output file, screen) | `table [CarrierExt].[ShipmentMessageXml]`, `LEDGER` | "in the system" |
| Name a correlation key: placeholder `<…ID\|Id\|Identifier\|Number\|Reference>` or `Xxx(Id\|Number\|Reference) =` | `<InvoiceNumber>`, `ExternalReference = <…Number>` | `<InvoiceNbr>`, `<Sku>` |
| Expected result states an exact value: `Field = value`, `exactly N <records\|messages\|rows>`, `HTTP 200`, `status is X`, `N rows` | `exactly 1 message with invoiceNumber = <…Number>` | "screen opens and lists the message", "values are correctly mapped", "is correct" |

Shortcut: end every placeholder that identifies a transaction with `Number`, `Id`, or
`Reference`, and put an exact count or `Field = value` in every backend Expected cell.

## Format rules that bite

- Header row exactly `ID,Work Item Type,Title,Test Step,Step Action,Step Expected,Area Path,Assigned To,State,Component`, 10 columns on every row.
- Test Case ID empty (`"","Test Case"`); Shared Steps need a real numeric ID.
- No `TC-F-001:` title prefixes; no old paths (`SHP02`, `PAY02`, `ORDER02`); no "Prepare preconditions".
- File path `qa-output/test-cases/[sprint-<slug>/]<name>-test-cases.csv`.
- Every test case has an Area Path and at least one step.

## Assumptions (EVAL-QUALITY-008)

When a step depends on something no source confirms, link it to a PO question instead of
hiding the guess: append `[Assumption: PO-Q<n>]` to that step's Action or Expected text, where
`<n>` is the numbered question in the PBI's PO questions file. The marker must reference an
existing question; any other use of the word "assumption" in a step fails the check. Remove
the marker once the question is answered and the step is updated.
