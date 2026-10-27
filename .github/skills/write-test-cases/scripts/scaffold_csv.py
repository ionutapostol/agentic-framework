"""Generate a valid Azure DevOps test-case CSV from a compact JSON spec.

Usage (from repository root):
    uv run python .github\\skills\\write-test-cases\\scripts\\scaffold_csv.py <spec.json> [--out <csv>] [--no-validate]

Spec format:
{
  "area_path": "ShopApp\\\\Your Team",      // required
  "component": "SHP",                          // required
  "state": "Design",                           // optional
  "tests": [
    {
      "title": "Plain sentence, no TC- prefix",
      "portal": true,                          // true -> shared Login step first (ID from env SHARED_LOGIN_STEP_ID)
      "steps": [
        {"action": "...", "expected": "..."},
        {"action": "...", "expected": "...", "assumption": 2}   // appends [Assumption: PO-Q2]
      ]
    }
  ]
}

The Test Case ID is always empty. The output is validated with validate_csv.py unless
--no-validate is given; its exit code is returned.
"""

import argparse
import csv
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HEADER = [
    'ID', 'Work Item Type', 'Title', 'Test Step', 'Step Action', 'Step Expected',
    'Area Path', 'Assigned To', 'State', 'Component',
]
LOGIN_SHARED_STEP_ID = os.environ.get('SHARED_LOGIN_STEP_ID', '<SHARED_LOGIN_STEP_ID>')


def build_rows(spec: dict[str, Any]) -> list[list[str]]:
    component = spec.get('component')
    if not component:
        raise ValueError('spec.component is required')
    area = spec.get('area_path')
    if not area:
        raise ValueError('spec.area_path is required (the team area path)')
    state = spec.get('state', 'Design')
    tests = spec.get('tests') or []
    if not tests:
        raise ValueError('spec.tests must contain at least one test')

    rows = [HEADER]
    for t_index, test in enumerate(tests, start=1):
        title = (test.get('title') or '').strip()
        steps = test.get('steps') or []
        if not title or not steps:
            raise ValueError(f'tests[{t_index}] needs a title and at least one step')
        rows.append(['', 'Test Case', title, '', '', '', area, '', state, component])
        number = 1
        if test.get('portal'):
            if not LOGIN_SHARED_STEP_ID.isdigit():
                raise ValueError(
                    'portal tests need the numeric Login Shared Steps ID: '
                    'set env SHARED_LOGIN_STEP_ID'
                )
            rows.append([LOGIN_SHARED_STEP_ID, 'Shared Steps', '', '1', 'Login', '', '', '', '', ''])
            number = 2
        for s_index, step in enumerate(steps, start=1):
            action = (step.get('action') or '').strip()
            expected = (step.get('expected') or '').strip()
            if not action or not expected:
                raise ValueError(f'tests[{t_index}].steps[{s_index}] needs action and expected')
            if 'assumption' in step:
                n = step['assumption']
                if not isinstance(n, int) or isinstance(n, bool) or n < 1:
                    raise ValueError(
                        f'tests[{t_index}].steps[{s_index}].assumption must be a positive integer'
                    )
                action = f'{action} [Assumption: PO-Q{n}]'
            rows.append(['', '', '', str(number), action, expected, '', '', '', ''])
            number += 1
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('spec', help='Path to the JSON spec')
    parser.add_argument('--out', help='Output CSV path (default: <spec stem>-test-cases.csv)')
    parser.add_argument('--no-validate', action='store_true')
    args = parser.parse_args()

    spec_path = Path(args.spec).resolve()
    try:
        spec = json.loads(spec_path.read_text(encoding='utf-8-sig'))
        rows = build_rows(spec)
    except (OSError, ValueError) as e:
        print(f'ERROR: {e}', file=sys.stderr, flush=True)
        return 1

    out = Path(args.out).resolve() if args.out else spec_path.with_name(
        f'{spec_path.stem.removesuffix("-spec")}-test-cases.csv'
    )
    with open(out, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(rows)
    print(f'Wrote {out} ({len(rows) - 1} rows)', flush=True)

    if args.no_validate:
        return 0
    validator = Path(__file__).with_name('validate_csv.py')
    return subprocess.run([sys.executable, str(validator), str(out)]).returncode


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
