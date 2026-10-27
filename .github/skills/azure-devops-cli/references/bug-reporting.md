# Filing Formal Bugs (Repro Steps, Component, References)

Conventions for logging a formal Bug work item — e.g. from fuzzing/security findings, manual
QA, or automated test failures — with proper repro steps, a component tag (plus a required
custom field on plain `Bug`), and a
documentation reference link.

## Bugs under a PBI → type `Bug in PBI`

When the user names a parent PBI (id or URL), create the item as type **`Bug in PBI`**
(reference name `YourOrg.BuginPBI`), never `Bug`: only this type lists under the PBI's
child items. Do not create `Bug` and retype it afterwards. Use plain `Bug` only when no PBI
is given.

Field differences vs `Bug` (from the work item type field definitions; 900107/900108 were
created as `Bug` and retyped, so their leftover `YourOrg.Component`/`ReproSteps`/`ValueArea`
values are not evidence of what `Bug in PBI` accepts):

| Concept | `Bug` | `Bug in PBI` |
|---|---|---|
| Repro/actual/expected text | `Microsoft.VSTS.TCM.ReproSteps` | `System.Description` (same HTML template) |
| Component | `YourOrg.Component` field (required, TF401320) + tag | Tag only: `System.Tags` (component === tag). `YourOrg.Component` is not defined on this type; never a "Component:" line in the Description |
| Severity / Priority | `Microsoft.VSTS.Common.Severity` / `Priority` | Same fields, set on create |
| Initial state | `New` | `To Do` (states: To Do, In Progress, Done, Removed). Never pass `--state`; `New` is invalid |
| Value Area | present (required) | absent |

The CLI cannot set a parent on create. Right after create (separate call), link the PBI, then
attach the reference Hyperlink as usual. A work item has one parent: on retry, `show` first and
add only missing relations; never create a new bug for an ID you already hold. If the
`Bug in PBI` create is rejected, report the exact error; do not fall back to create-then-retype.

```powershell
az boards work-item relation add --id <bug-id> --relation-type "parent" --target-id <pbi-id>
```

Read Area and Iteration from the PBI (`az boards work-item show --id <pbi-id>`; accept an id or
a `_workitems/edit/<id>` URL; fatal if it is not a Product Backlog Item) and pass them to create;
don't ask. Verify type, parent link (`System.LinkTypes.Hierarchy-Reverse`), and that the item
appears in the PBI's child links.

## Severity and Priority defaults

Use **Severity `3 - Medium`** and **Priority `3`** unless the user states other values in
their first prompt (or via `--severity` / `--priority`). Do not ask about them and do not infer them from
the finding's perceived impact. State the values used in the summary.

## Pre-flight: ask once, up front

Collect everything missing in a single prompt before creating anything: Component (always
required if not supplied), the exact wrong/actual text per bug, and whether the bugs belong
under a parent PBI (id/URL, or "none" → plain `Bug`). Do not
ask about Environment: omit that section when not supplied. If the user cites a wiki or
spec for the expected result, read it first (ADO wiki: `az devops wiki page show --wiki <wiki>
--path "<path>" --include-content`; Confluence: confluence-assistant skill), including
dialog/screenshot text, since exact message wording is often only in images. Quote it in
Expected Result; if the doc is silent on wording, or the wording exists only in an image you
cannot read, say so rather than inventing it.

## Bug work item field mapping — `System.Description` is a dead end (plain `Bug` only)

This section applies to plain `Bug` only. For `Bug in PBI`, `System.Description` is the correct
body field; never clear it.

The Bug work item type in this project does **not** surface `System.Description` on its form.
Repro steps, actual/expected result, and root-cause text must go in
**`Microsoft.VSTS.TCM.ReproSteps`** instead:

```powershell
azps.ps1 boards work-item update --id 1234 --fields "Microsoft.VSTS.TCM.ReproSteps=<html>"
```

If content was accidentally written to `System.Description`, clear it rather than leaving it —
but only clear it if you wrote it; don't blank a field you didn't touch, since that field may
carry other data on an item you didn't create:

```powershell
azps.ps1 boards work-item update --id 1234 --fields "System.Description="
```

`ReproSteps` (like `System.Description`) is an HTML rich-text field. Build the whole value as
**one single-line string with no embedded newlines** — see
`references/long-comments-on-windows.md` for why multi-line values are risky even with
`azps.ps1`, and always HTML-escape `&` as `&amp;` in generated text (never strip it — stripping
corrupts real query strings and other data you're trying to document).

## Component === tag (`System.Tags`)

The component is conveyed by a tag whose text is the exact `YourOrg.Component` allowed value
(e.g. `SHP`, `ORD`, `ShopApp`, `Cloud - CI/CD` as-is; never a friendly name like "Orders module").
Map the user's wording to an allowed value and confirm it. Set `System.Tags=<component>` at
create time on every bug, plus `YourOrg.Component=<component>` on plain `Bug` only (required
there; not defined on `Bug in PBI`). Do not put the component in the description/ReproSteps
text. `System.Tags` is a `;`-separated list, so on update never set it blindly (it replaces all
tags): read the existing tags and write `<existing>; <component>` only if missing. Verify on
re-fetch (ADO tags are case-insensitive; other tags may be present):

```powershell
$tags = @(($f.fields.'System.Tags' -split ';') | ForEach-Object { $_.Trim() } | Where-Object { $_ })
if ($tags -notcontains $component) { 'TAG MISMATCH' }
if ($f.fields.'System.WorkItemType' -eq 'Bug' -and $f.fields.'YourOrg.Component' -ne $component) { 'FIELD MISMATCH' }
```

## `YourOrg.Component` is required on plain `Bug`

Plain `Bug` creation fails with `TF401320: Rule Error for field Component` if this is omitted
(`Bug in PBI` does not define the field; it uses the tag only). Its
allowed values are **project-specific and may change** — don't hardcode a list.

**Always prompt the user for the component value when it wasn't supplied by them** (e.g. no
`--component` argument and no explicit value stated in the request). Do not silently infer it
from an existing bug in the same Area Path and proceed — that risks tagging the wrong feature
component on a functionally unrelated bug. Inspecting an existing bug is fine as a *suggested
default* to show the user when asking, not as a substitute for asking:

```powershell
az boards query --wiql "SELECT [System.Id] FROM WorkItems WHERE [System.TeamProject]='ShopApp' AND [System.WorkItemType] IN ('Bug','Bug in PBI') AND [System.AreaPath]='ShopApp\<Team>' ORDER BY [System.ChangedDate] DESC"
az boards work-item show --id <returned-id> --output json | ConvertFrom-Json | Select-Object -ExpandProperty fields | Select-Object 'YourOrg.Component','System.Tags'
```

Treat the result as one example, not the full allowed set (`YourOrg.Component` is null on native `Bug in PBI` items; use the tag).

## Standard formal-bug template

Structure the body field (`Microsoft.VSTS.TCM.ReproSteps` for `Bug`, `System.Description` for `Bug in PBI`) with these sections (adapt headers to plain HTML
since the field renders HTML, not Markdown):

```html
<h3>Repro Steps</h3><ol><li>...</li><li>...</li></ol>
<h3>Actual Result</h3><p>...</p>
<h3>Expected Result</h3><p>...</p>
<h3>Root Cause / Classification</h3><p>...</p>
<h3>Environment</h3><p>...</p>
```

Only add a CWE/OWASP-style classification under "Root Cause" when the finding is genuinely
security-relevant and the mapping is well-supported (label it "suspected" if uncertain) — don't
force a security framing onto ordinary functional bugs.

## Reference links → Hyperlink relation, not inline text

Attach documentation/standard references (OWASP, RFC, internal runbook, etc.) as a proper
**Hyperlink relation** so it renders as a linked resource on the item, instead of just pasting
the URL into the text body:

```powershell
az boards work-item relation add --id 1234 --relation-type "Hyperlink" --target-url "https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/"
```

`az boards work-item relation list-type --output table` lists all supported relation types.

## Batch checklist (multiple bugs from one fuzzing/test run)

1. Resolve area path (team) and iteration path (sprint) — see `references/boards-and-iterations.md`
   for the `--depth 2` gotcha on nested sprint paths (`Project\Year\Sprint N`).
2. Prompt the user for the component (the exact `YourOrg.Component` allowed value, also the tag)
   if not already given — don't assume a fixed value or silently infer one from an existing bug.
3. Create each bug, recording the returned ID immediately (so a mid-batch failure doesn't lose
   track of what already succeeded). Plain `Bug`:
   ```powershell
   az boards work-item create --type Bug --title "..." --area "<area>" --iteration "<iteration>" --fields "Microsoft.VSTS.Common.Severity=3 - Medium" "Microsoft.VSTS.Common.Priority=3" "YourOrg.Component=<value>" "System.Tags=<value>"
   ```
   With a PBI, use the PBI's Area/Iteration and no `YourOrg.Component`:
   ```powershell
   az boards work-item create --type "Bug in PBI" --title "..." --area "<pbi-area>" --iteration "<pbi-iteration>" --fields "Microsoft.VSTS.Common.Severity=3 - Medium" "Microsoft.VSTS.Common.Priority=3" "System.Tags=<value>"
   ```
4. Populate the body per bug: `Microsoft.VSTS.TCM.ReproSteps` for `Bug`, `System.Description`
   for `Bug in PBI` (single-line HTML, `&` escaped). For `Bug in PBI`, also add the `parent` relation.
   Select the Windows-safe invocation from [long-comments-on-windows.md](long-comments-on-windows.md):
   use `azps.ps1` when quoting or length requires it, not as an unconditional dependency.
5. Add the Hyperlink relation per bug.
6. **Verify by content, not just length or exit code** — a same-length corruption would pass a
   length-only check:
   ```powershell
   $f = az boards work-item show --id 1234 --output json | ConvertFrom-Json
   $f.fields.'System.WorkItemType'
   $f.fields.'Microsoft.VSTS.TCM.ReproSteps'   # Bug; use System.Description for Bug in PBI
   $f.fields.'System.Tags'   # split on ';', trim, case-insensitive contains the component
   $f.fields.'YourOrg.Component'   # plain Bug only; null on Bug in PBI
   $f.relations | Where-Object { $_.rel -eq 'System.LinkTypes.Hierarchy-Reverse' } | Select-Object url
   $f.relations | Where-Object { $_.rel -eq 'Hyperlink' } | Select-Object url
   ```
7. Report any partial failures explicitly (which IDs succeeded/failed) rather than assuming
   all-or-nothing success on a batch.
