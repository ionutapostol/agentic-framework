#!/usr/bin/env python3
"""
validate_manifest.py — Enforces the sprint QA pipeline run contract.

A run backed by an empty or malformed manifest is a config error, never a pass.

Usage:
    python validate_manifest.py <path-to-manifest.json>

Exit codes:
    0 — valid: well-formed envelope with >=1 item and no content failures
    1 — content failure: a "failed" row, or a "valid" row missing suite_id/csv_path
    2 — config_error: missing file, malformed JSON, missing keys, or zero items
"""

import json
import sys
from pathlib import Path

REQUIRED_TOP_KEYS = ('sprint', 'team', 'area_path', 'generated_at', 'items')
VALID_STATUSES = ('valid', 'failed', 'exempted')


def load_manifest(filepath):
	path = Path(filepath)
	if not path.is_file():
		print(f'config_error: file not found: {filepath}')
		sys.exit(2)
	try:
		data = json.loads(path.read_text(encoding='utf-8'))
	except json.JSONDecodeError as exc:
		print(f'config_error: invalid JSON: {exc}')
		sys.exit(2)
	if not isinstance(data, dict):
		print('config_error: manifest root must be a JSON object.')
		sys.exit(2)
	return data


def check_envelope(data):
	missing = [k for k in REQUIRED_TOP_KEYS if k not in data]
	if missing:
		print(f'config_error: missing top-level keys: {", ".join(missing)}')
		sys.exit(2)
	items = data.get('items')
	if not isinstance(items, list) or not items:
		print('config_error: "items" must be a non-empty list. Zero work is never a pass.')
		sys.exit(2)
	return items


def check_items(items):
	failures = []
	for i, item in enumerate(items, start=1):
		pbi = item.get('pbi_id', f'<row {i}>')
		status = item.get('status')
		if status not in VALID_STATUSES:
			failures.append(f'PBI {pbi}: invalid status {status!r}.')
			continue
		if status == 'failed':
			failures.append(f'PBI {pbi}: status "failed" — {item.get("error", "no error given")}.')
		elif status == 'valid':
			for key in ('suite_id', 'csv_path'):
				if not item.get(key):
					failures.append(f'PBI {pbi}: "valid" row missing {key}.')
	return failures


def run(filepath):
	data = load_manifest(filepath)
	items = check_envelope(data)
	failures = check_items(items)

	valid = sum(1 for it in items if it.get('status') == 'valid')
	exempted = sum(1 for it in items if it.get('status') == 'exempted')
	failed = sum(1 for it in items if it.get('status') == 'failed')
	print(f'Envelope OK: {len(items)} rows ({valid} valid, {exempted} exempted, {failed} failed).')

	# Zero valid rows is a config error even if every row is otherwise well-formed
	# (e.g. all exempted/failed) — checked before content failures per the pipeline
	# run contract's "zero work is a config error, never a pass" rule.
	if valid == 0:
		print('config_error: no valid rows to import. Zero work is never a pass.')
		sys.exit(2)
	if failures:
		print(f'{len(failures)} content failure(s):')
		for f in failures:
			print(f'  x {f}')
		sys.exit(1)
	print('Manifest valid.')
	sys.exit(0)


if __name__ == '__main__':
	if len(sys.argv) != 2:
		print('Usage: python validate_manifest.py <path-to-manifest.json>')
		sys.exit(2)
	run(sys.argv[1])
