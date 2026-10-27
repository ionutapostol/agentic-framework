#!/usr/bin/env python3
"""Validate plain-text Test execution checklists."""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
COVERAGE_PREFIXES = (
	'Happy path: ',
	'Edge case: ',
	'Error handling: ',
	'State transition: ',
)
REQUIRED_COVERAGE_PREFIXES = COVERAGE_PREFIXES[:3]
CHECKLIST_PATH = re.compile(
	r'(?:qa-output/test-cases|qa-output/test-cases/sprint-[\w-]+/checklists)/'
	r'[\w-]+-checklist\.txt'
)
MARKDOWN_PATTERN = re.compile(
	r'^\s*(?:#{1,6}(?:\s|$)|[-*+]\s|\d+[.)]\s|>|[|]|-{3,}\s*$|\*{3,}\s*$|_{3,}\s*$)'
	r'|\[[ xX]\]'
	r'|^\[[^\]]+\]\s'
	r'|\*\*|__|`'
	r'|~~'
	r'|(?<!\w)\*[^*\n]+\*(?!\w)'
	r'|(?<!\w)_[^_\n]+_(?!\w)'
	r'|\[[^\]]+\]\([^)]+\)'
	r'|\|'
	r'|<https?://[^>]+>'
	r'|</?(?:a|b|blockquote|br|code|del|details|div|em|h[1-6]|hr|i|img|li|mark|ol|'
	r'p|pre|s|section|span|strong|sub|summary|sup|table|td|th|tr|ul)'
	r'\b[^>]*>',
	re.IGNORECASE,
)


def validate_line(number: int, line: str) -> list[str]:
	"""Return structural violations for one checklist line."""
	errors: list[str] = []
	if not line:
		return [f'Line {number}: blank lines are not allowed.']
	if line != line.strip():
		errors.append(f'Line {number}: leading or trailing whitespace is not allowed.')
	if not line.startswith('- '):
		errors.append(f'Line {number}: checklist items must start with "- ".')
		return errors
	content = line.removeprefix('- ')
	prefix = next((value for value in COVERAGE_PREFIXES if content.startswith(value)), None)
	if prefix is None:
		errors.append(f'Line {number}: missing a valid coverage prefix.')
		return errors
	scenario = content.removeprefix(prefix)
	if not scenario:
		errors.append(f'Line {number}: scenario text is required after the prefix.')
	if MARKDOWN_PATTERN.search(scenario):
		errors.append(f'Line {number}: Markdown formatting is not allowed.')
	return errors


def validate_checklist(path: Path) -> list[str]:
	"""Return contract violations for one checklist file."""
	errors: list[str] = []
	if path.suffix.lower() != '.txt':
		errors.append(f'File extension must be .txt: {path.name}')
	try:
		relative_path = path.resolve().relative_to(REPO_ROOT).as_posix()
	except ValueError:
		relative_path = path.resolve().as_posix()
	if not CHECKLIST_PATH.fullmatch(relative_path):
		errors.append(f'Checklist path is outside an allowed checklist directory: {relative_path}')

	try:
		lines = path.read_text(encoding='utf-8').splitlines()
	except FileNotFoundError:
		return [f'Checklist not found: {path}']

	if not lines:
		errors.append('Checklist must contain at least one item.')
		return errors

	seen: set[str] = set()
	for number, line in enumerate(lines, start=1):
		errors.extend(validate_line(number, line))
		if line in seen:
			errors.append(f'Line {number}: duplicate checklist item.')
		seen.add(line)

	for prefix in REQUIRED_COVERAGE_PREFIXES:
		if not any(line.startswith(f'- {prefix}') for line in lines):
			errors.append(f'At least one {prefix.strip()} item is required.')
	return errors


def main() -> int:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('checklists', nargs='+', type=Path)
	args = parser.parse_args()

	failed = False
	for path in args.checklists:
		errors = validate_checklist(path)
		if errors:
			failed = True
			for error in errors:
				sys.stdout.write(f'FAIL {path}: {error}\n')
		else:
			sys.stdout.write(f'PASS {path}\n')
	return int(failed)


if __name__ == '__main__':
	raise SystemExit(main())
