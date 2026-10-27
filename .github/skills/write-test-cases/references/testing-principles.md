# Requirement-backed test design

Consult this reference to choose coverage and design techniques. Output rules, checklist
gates, and PO questions are defined in [SKILL.md](../SKILL.md), not here.

## Coverage Requirements

Evaluate each category against the requirement and its explicit exclusions. These categories
are prompts for analysis, not permission to invent expected behavior.

| Category | Look for in the sources |
|---|---|
| Happy path | Distinct user/service flows, accepted inputs, observable results |
| Edge case | Specified boundaries, empty states, limits, exceptional valid inputs |
| Error handling | Defined invalid inputs, permission/dependency failures and their responses |
| State transition | Defined initial states, allowed/forbidden transitions and observable results |

Cover every in-scope flow before adding depth to one flow. If a category has no requirement
backing, apply SKILL.md Step 6b's clarification gate rather than filling it with generic
network, permission, or validation expectations. Happy-path-only sprint CSVs retain that
scope; a separate requested checklist evaluates the broader requirement.

## Design patterns

### Arrange, act, assert

Identify concrete prerequisites, one executable action, and an observable expected result.
For example, given a requirement that Confirm displays an entered valid Amount unchanged:
open Order Entry, enter the specified Amount, click Confirm, inspect the confirmation value.
Split assertions when they verify different outputs.

### Equivalence partitions and boundaries

Group inputs only when the requirement says they share behavior. Test a representative value
and stated endpoints. If the accepted range is 0.01–100.00, those endpoints are valid
boundary cases; behavior at 0.00 or 100.01 needs its own requirement before assertion.

### State transition tables

For stateful features, map current state, trigger, expected next state and source. An
unspecified transition is a question, not an assumed rejection:

| Current state | Trigger | Expected next state | Source |
|---|---|---|---|
| Requirement-defined state | Requirement-defined action | Requirement-defined result | Section/revision |

## Coverage review

- Each scenario traces to a source and preserves exclusions and resolved precedence.
- Every assertion names an observation point and an exact value/formula; backend assertions
  also identify a correlation key.
- Cases are repeatable and independent; missing prerequisites are stated as gaps.
- Distinct expected outputs require distinct, source-backed trigger conditions.
- Update or remove cases as requirements change; record unresolved questions before delivery.

Risk can determine review order, but CSV columns remain those in SKILL.md. Test Case
Priority is set separately through `@ado-testcase-priority`, not an invented CSV field.
