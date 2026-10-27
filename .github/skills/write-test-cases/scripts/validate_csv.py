#!/usr/bin/env python3
"""
validate_csv.py — Automated CSV format validator for write-test-cases skill output.

Checks a generated test-case CSV against the blocking rules defined in evals.json.
All checks correspond to csv_format and navigation_paths evaluations.

Usage:
    python validate_csv.py <path-to-csv>

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
"""

import csv
import re
import sys
from pathlib import Path


REQUIRED_HEADER = 'ID,Work Item Type,Title,Test Step,Step Action,Step Expected,Area Path,Assigned To,State,Component'
REPO_ROOT = Path(__file__).resolve().parents[4]

CHECKS = []

VERIFICATION_ACTION = re.compile(
    r'\b(?:assert|validate|inspect|verify|check|confirm|search|query|open|locate|view|'
    r'call|use)\b',
    re.IGNORECASE,
)
BACKEND_SURFACE = re.compile(
    r'\b(?:kibana|elasticsearch|ledger|shpm02|database|api|endpoint|queue|topic|'
    r'log|trace|response body|output file)\b',
    re.IGNORECASE,
)
PORTAL_SURFACE = re.compile(r'\b(?:shp01|ord01|portal|screen)\b', re.IGNORECASE)
TABLE_SURFACE = re.compile(r'\btable\b', re.IGNORECASE)
PORTAL_UI_ARTIFACT = re.compile(
    r'\b(?:results?\s+table|confirmation message|dialog|button|field|tab)\b',
    re.IGNORECASE,
)
BACKEND_ARTIFACT = re.compile(
    r'\b(?:[A-Za-z][A-Za-z0-9]*Command|request|response|command|message|'
    r'processing record|principal determination|output file)\b',
    re.IGNORECASE,
)


def is_backend_assertion(step_action):
    if not VERIFICATION_ACTION.search(step_action):
        return False
    if (
        PORTAL_SURFACE.search(step_action)
        and PORTAL_UI_ARTIFACT.search(step_action)
        and not BACKEND_SURFACE.search(step_action)
    ):
        return False
    return bool(
        BACKEND_SURFACE.search(step_action)
        or TABLE_SURFACE.search(step_action)
        or BACKEND_ARTIFACT.search(step_action)
    )


def check(eval_id, description):
    def decorator(fn):
        CHECKS.append((eval_id, description, fn))
        return fn
    return decorator


@check('EVAL-FORMAT-004', 'CSV must use the correct column headers')
def check_header(rows):
    if not rows:
        return ['File is empty — no rows found.']
    actual = ','.join(rows[0])
    if actual != REQUIRED_HEADER:
        return [f'Header mismatch.\n  Expected: {REQUIRED_HEADER}\n  Got:      {actual}']
    return []


@check('EVAL-FORMAT-006', 'Every non-empty CSV row must have exactly 10 columns')
def check_row_width(rows):
    errors = []
    for i, row in enumerate(rows, start=1):
        if row and len(row) != len(REQUIRED_HEADER.split(',')):
            errors.append(f'Row {i}: Found {len(row)} columns; expected 10.')
    return errors


@check('EVAL-FORMAT-001', 'Test Case header row has correct Work Item Type')
def check_test_case_work_item_type(rows):
    errors = []
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 3 and row[2].strip():  # Title column is populated
            if row[1] != 'Test Case':
                errors.append(f'Row {i}: Title "{row[2]}" has Work Item Type "{row[1]}" — expected "Test Case".')
    return errors


@check('EVAL-FORMAT-002', 'Shared Steps row must have a real numeric ID, never empty ID')
def check_shared_steps_id(rows):
    errors = []
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 2 and row[1] == 'Shared Steps' and not row[0].strip():
            errors.append(
                f'Row {i}: Found "Shared Steps" with empty ID. '
                'Use bare ,, for plain step rows — "Shared Steps" requires a real numeric ID.'
            )
    return errors


@check('EVAL-FORMAT-007', 'Test Case header ID must always be empty')
def check_test_case_id_empty(rows):
    errors = []
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 2 and row[1] == 'Test Case' and row[0].strip():
            title = row[2] if len(row) >= 3 else '<missing title>'
            errors.append(
                f'Row {i}: Test Case "{title}" has ID "{row[0]}". '
                'Leave the ID empty so Azure DevOps creates or imports the test case.'
            )
    return errors


@check('EVAL-FORMAT-003', 'Test case titles must not contain TC-F-XXX: or TC-E-XXX: prefixes')
def check_no_tc_prefix(rows):
    prefix_pattern = re.compile(r'^TC-[A-Z]+-\d+:')
    errors = []
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 3 and row[2].strip():
            if prefix_pattern.match(row[2]):
                errors.append(f'Row {i}: Title has a TC-prefix: "{row[2]}". Strip the prefix.')
    return errors


@check('EVAL-FORMAT-005', 'Output file must be in qa-output/test-cases/')
def check_output_path(rows, filepath):
    try:
        path = Path(filepath).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        path = Path(filepath).resolve().as_posix()

    if not re.fullmatch(
        r'qa-output/test-cases/(?:sprint-[\w-]+/)?[\w-]+-test-cases\.csv$',
        path,
    ):
        return [
            f'File path "{path}" does not match qa-output/test-cases/'
            '[sprint-<slug>/]<name>-test-cases.csv.'
        ]
    return []


@check('EVAL-NAV-001', 'Old-style navigation paths must not appear')
def check_no_old_nav_paths(rows):
    old_paths = re.compile(r'ORDER02|OrderOrder02|PAY02|SHP02', re.IGNORECASE)
    errors = []
    for i, row in enumerate(rows[1:], start=2):
        step_action = row[4] if len(row) > 4 else ''
        if old_paths.search(step_action):
            errors.append(
                f'Row {i}: Old-style navigation path found in Step Action: "{step_action}". '
                'Use ORD00, Orders → ORD01, Order Portal (or PAY00/SHP00 equivalents).'
            )
    return errors


@check('EVAL-QUALITY-001', 'Every test case must have at least one step')
def check_test_cases_have_steps(rows):
    errors = []
    last_tc_row = None
    last_tc_index = None
    has_step = False

    for i, row in enumerate(rows[1:], start=2):
        is_tc_header = len(row) >= 3 and row[1] == 'Test Case' and row[2].strip()
        is_step = len(row) >= 5 and row[4].strip()

        if is_tc_header:
            if last_tc_row and not has_step:
                errors.append(
                    f'Row {last_tc_index}: Test case "{last_tc_row[2]}" has no steps.'
                )
            last_tc_row = row
            last_tc_index = i
            has_step = False
        elif is_step and last_tc_row:
            has_step = True

    if last_tc_row and not has_step:
        errors.append(f'Row {last_tc_index}: Test case "{last_tc_row[2]}" has no steps.')
    return errors


@check('EVAL-QUALITY-004', 'Area Path must be set on every test case header row')
def check_area_path(rows):
    errors = []
    for i, row in enumerate(rows[1:], start=2):
        if len(row) >= 7 and row[1] == 'Test Case' and row[2].strip():
            area_path = row[6].strip()
            if not area_path:
                errors.append(f'Row {i}: Test case "{row[2]}" has an empty Area Path.')
    return errors


@check('EVAL-QUALITY-005', 'Step actions must not use generic "Prepare preconditions" language')
def check_no_generic_preconditions(rows):
    pattern = re.compile(r'prepare preconditions', re.IGNORECASE)
    warnings = []
    for i, row in enumerate(rows[1:], start=2):
        step_action = row[4] if len(row) > 4 else ''
        if pattern.search(step_action):
            warnings.append(
                f'Row {i}: Step action uses generic "Prepare preconditions" language: "{step_action}". '
                'Replace with a specific user action (e.g. "Go to Shipment Portal and create a new shipment (eg: split shipment)").'
            )
    return warnings


@check('EVAL-QUALITY-006', 'Expected results must state exact observable values')
def check_no_vague_expected_results(rows):
    vague_pattern = re.compile(
        r'\b(?:source data|values?|fields?)\s+(?:are\s+)?(?:correctly\s+)?mapped\b'
        r'|\b(?:correct|expected)\s+(?:fields|values)\b'
        r'|\bis correct\b'
        r'|\bmatches\s+(?:expected(?:\s+values?)?|expectations)\b'
        r'|\b(?:result|status|response|request|fields?|values?)\s*(?:=|equals)\s*'
        r'(?:mapped|success(?:ful(?:ly)?)?|succeeded|ok)\b',
        re.IGNORECASE,
    )
    exact_result = re.compile(
        r'\b[A-Za-z][A-Za-z0-9_. -]*\s*(?:=|equals)'
        r'(?!\s*(?:expected\b|expectations\b|correct\b|mapped\b|'
        r'success(?:ful(?:ly)?)?\b|succeeded\b|ok\b))\s*[^,;\n]+'
        r'|\b[A-Za-z][A-Za-z0-9_. -]*\s+matches\s+'
        r'(?!expected\b|expectations\b)(?:<[^>]+>|["\']?[A-Za-z0-9_.+-]+)'
        r'|\bexactly\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b'
        r'|\bHTTP\s+\d{3}\b'
        r'|\b(?:record\s+)?status\s+is\s+'
        r'(?!(?:correct|expected)\b)[A-Za-z0-9_-]+\b'
        r'|\b(?:contains?|returns?|has)\s+\d+\s+'
        r'(?:records?|messages?|rows?|items?|files?|responses?|requests?|commands?)\b'
        r'|\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+'
        r'(?:records?|messages?|rows?|items?|files?|responses?|requests?|commands?)\b'
        r'|\bremains unchanged\b',
        re.IGNORECASE,
    )
    errors = []
    for i, row in enumerate(rows[1:], start=2):
        step_action = row[4] if len(row) > 4 else ''
        step_expected = row[5] if len(row) > 5 else ''
        has_exact_result = exact_result.search(step_expected)
        if (
            vague_pattern.search(step_expected) or is_backend_assertion(step_action)
        ) and not has_exact_result:
            errors.append(
                f'Row {i}: Step Expected is not measurable: "{step_expected}". '
                'List exact requirement-backed values, formulas, status codes, or counts.'
            )
    return errors


@check('EVAL-QUALITY-007', 'Backend assertions must name an observation point and correlation key')
def check_backend_observation_points(rows):
    observation_point = re.compile(
        r'\b(?:kibana|elasticsearch|ledger|shpm02|shp01|ord01|portal|database|table|api|'
        r'endpoint|queue|topic|log|trace|response body|output file|screen)\b',
        re.IGNORECASE,
    )
    correlation_key = re.compile(
        r'<[A-Za-z][A-Za-z0-9]*(?:ID|Id|Identifier|Number|Reference)>'
        r'|\b[A-Za-z][A-Za-z0-9]*(?:ID|Id|Identifier|Number|Reference)\s*='
        r'|(?i:\bcorrelation\s+(?:id|identifier|number|reference)\b)'
        r'|(?i:\bsender reference\b)',
    )
    errors = []
    for i, row in enumerate(rows[1:], start=2):
        step_action = row[4] if len(row) > 4 else ''
        step_expected = row[5] if len(row) > 5 else ''
        assertion = f'{step_action} {step_expected}'
        if not is_backend_assertion(step_action):
            continue

        missing = []
        if not observation_point.search(assertion):
            missing.append('observation point')
        if not correlation_key.search(assertion):
            missing.append('correlation key')
        if missing:
            errors.append(
                f'Row {i}: Backend assertion is missing {" and ".join(missing)}: '
                f'"{step_action}". Name where to observe it and how to locate the same transaction.'
            )
    return errors


def find_questions_file(filepath):
    """Locate the PO questions file belonging to a generated CSV, or None."""
    path = Path(filepath).resolve()
    stem = path.name.removesuffix('-test-cases.csv')
    candidates = [
        path.parent / 'po-questions' / f'{stem.split("-")[0]}-questions.txt',
        path.parent / f'{stem}-questions.txt',
    ]
    return next((c for c in candidates if c.is_file()), None)


@check('EVAL-QUALITY-008', 'Assumption markers must reference an existing PO question')
def check_assumption_markers(rows, filepath):
    marker = re.compile(r'\[Assumption:\s*PO-Q(\d+)\]')
    loose = re.compile(r'assumption', re.IGNORECASE)
    referenced = {}
    errors = []
    for i, row in enumerate(rows[1:], start=2):
        for col in (4, 5):
            text = row[col] if len(row) > col else ''
            found = marker.findall(text)
            for number in found:
                referenced.setdefault(int(number), []).append(i)
            if not found and loose.search(text):
                errors.append(
                    f'Row {i}: Unlinked assumption wording. Use "[Assumption: PO-Q<n>]" tied to '
                    'a PO question, or remove the assumption.'
                )
    if not referenced:
        return errors

    questions_file = find_questions_file(filepath)
    if questions_file is None:
        return errors + [
            f'Rows {sorted({r for v in referenced.values() for r in v})}: assumption markers '
            'found but no PO questions file exists (po-questions/<pbi-id>-questions.txt).'
        ]
    try:
        text = questions_file.read_text(encoding='utf-8-sig')
    except UnicodeDecodeError:
        return errors + [f'{questions_file.name} is not UTF-8; re-save it as UTF-8.']
    existing = {int(n) for n in re.findall(r'^\s*(\d+)[.)]\s', text, re.MULTILINE)}
    for number, row_numbers in sorted(referenced.items()):
        if number not in existing:
            errors.append(
                f'Rows {row_numbers}: PO-Q{number} is not a numbered question in '
                f'{questions_file.name}.'
            )
    return errors


def load_csv(filepath):
    with open(filepath, newline='', encoding='utf-8-sig') as f:
        return list(csv.reader(f))


def run(filepath):
    try:
        rows = load_csv(filepath)
    except FileNotFoundError:
        print(f'ERROR: File not found: {filepath}')
        sys.exit(1)

    total_failures = 0
    for eval_id, description, fn in CHECKS:
        if fn.__code__.co_varnames[:fn.__code__.co_argcount] == ('rows', 'filepath'):
            errors = fn(rows, filepath)
        else:
            errors = fn(rows)

        if errors:
            print(f'FAIL [{eval_id}] {description}')
            for err in errors:
                print(f'  ✗ {err}')
            total_failures += 1
        else:
            print(f'PASS [{eval_id}] {description}')

    print()
    if total_failures == 0:
        print(f'All {len(CHECKS)} checks passed.')
        sys.exit(0)
    else:
        print(f'{total_failures}/{len(CHECKS)} checks FAILED.')
        sys.exit(1)


if __name__ == '__main__':
    # Windows consoles default to cp1252 and crash on the "✗" marker.
    sys.stdout.reconfigure(encoding='utf-8')
    if len(sys.argv) != 2:
        print('Usage: python validate_csv.py <path-to-csv>')
        sys.exit(1)
    run(sys.argv[1])
