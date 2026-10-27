"""Fetch a Confluence page and print its content as Markdown to stdout.

Usage (from repo root):
    cd .github/skills/confluence-assistant
    uv run python scripts/read_page.py <confluence-url-or-page-id> [-o <output-file>]

Accepts a /pages/<id> URL, a viewpage.action?pageId=<id> URL, or a bare numeric
page ID. Use -o/--output to write large pages to a file instead of stdout.

Credentials are loaded from .env (same variables as confluence_to_md.py):
    CONFLUENCE_URL, CONFLUENCE_PAT
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from markdownify import markdownify as to_markdown

PAGE_ID_PATTERN = re.compile(r'/pages/(\d+)')
PAGE_ID_QUERY_PATTERN = re.compile(r'pageId=(\d+)')
SCRIPT_DIR = Path(__file__).resolve().parent


def load_credentials() -> tuple[str, str]:
	candidates = [
		SCRIPT_DIR / '.env',
		SCRIPT_DIR.parent / '.env',
		SCRIPT_DIR.parent.parent.parent.parent / '.env',
	]
	# Also try git root
	current = SCRIPT_DIR
	while current != current.parent:
		if (current / '.git').exists():
			candidates.append(current / '.env')
			break
		current = current.parent

	for path in candidates:
		if path.exists():
			load_dotenv(path)

	url = os.getenv('CONFLUENCE_URL', '').strip()
	pat = os.getenv('CONFLUENCE_PAT', '').strip()

	missing = [k for k, v in [('CONFLUENCE_URL', url), ('CONFLUENCE_PAT', pat)] if not v]
	if missing:
		print(f'Error: missing required env vars: {", ".join(missing)}', file=sys.stderr)
		print('Create .env in the skill or repo root with CONFLUENCE_URL, CONFLUENCE_PAT', file=sys.stderr)
		sys.exit(1)

	return url, pat


def extract_page_id(value: str) -> str:
	value = value.strip()
	if value.isdigit():
		return value
	match = PAGE_ID_PATTERN.search(value)
	if match:
		return match.group(1)
	match = PAGE_ID_QUERY_PATTERN.search(value)
	if match:
		return match.group(1)
	print(f'Error: could not extract page ID from: {value}', file=sys.stderr)
	print('Expected a Confluence URL with /pages/<id>/, a viewpage.action?pageId=<id> URL, or a bare numeric page ID.', file=sys.stderr)
	sys.exit(1)


def build_headers(pat: str) -> dict[str, str]:
	return {'Authorization': f'Bearer {pat}', 'Accept': 'application/json'}


def fetch_page(base_url: str, page_id: str, headers: dict[str, str]) -> dict:
	url = f'{base_url.rstrip("/")}/rest/api/content/{page_id}?expand=body.storage,title'
	try:
		response = requests.get(url, headers=headers, timeout=30)
	except requests.ConnectionError as exc:
		print(f'Connection error: {exc}', file=sys.stderr)
		sys.exit(1)

	if response.status_code == 401:
		print('Authentication failed — check CONFLUENCE_PAT in .env', file=sys.stderr)
		sys.exit(1)
	if response.status_code == 404:
		print('Page not found — check the page ID and your permissions', file=sys.stderr)
		sys.exit(1)

	try:
		response.raise_for_status()
	except requests.HTTPError as exc:
		print(f'Request failed: {exc}', file=sys.stderr)
		sys.exit(1)

	return response.json()


def storage_to_markdown(storage_html: str) -> str:
	"""Convert Confluence storage format to clean readable Markdown."""
	soup = BeautifulSoup(storage_html, 'html.parser')

	# Remove TOC macros (they add no value without rendered links)
	for macro in soup.find_all('ac:structured-macro'):
		name = macro.get('ac:name', '')
		if name == 'toc':
			macro.decompose()
			continue
		# For panel/expand/note macros, unwrap the rich-text body so the content survives
		body = macro.find('ac:rich-text-body')
		if body:
			macro.replace_with(body)
		else:
			macro.decompose()

	# Replace Confluence image tags with a short placeholder — images aren't needed in context
	for img in soup.find_all('ac:image'):
		alt = img.get('ac:alt', '')
		img.replace_with(f'[image: {alt}]' if alt else '[image]')

	markdown = to_markdown(str(soup), heading_style='ATX', bullets='-')
	# Collapse excessive blank lines
	markdown = re.sub(r'\n{3,}', '\n\n', markdown)
	return markdown.strip()


def main() -> None:
	parser = argparse.ArgumentParser(description='Read a Confluence page and print its content as Markdown.')
	parser.add_argument('page_url_or_id', help='Confluence page URL or bare numeric page ID')
	parser.add_argument(
		'--output',
		'-o',
		type=Path,
		help='Write Markdown to this file instead of stdout (useful for large pages that exceed stdout limits)',
	)
	args = parser.parse_args()

	base_url, pat = load_credentials()
	headers = build_headers(pat)
	page_id = extract_page_id(args.page_url_or_id)

	page = fetch_page(base_url, page_id, headers)
	title = str(page.get('title', f'Page {page_id}')).strip()
	storage = str(page.get('body', {}).get('storage', {}).get('value', ''))

	content = f'# {title}\n\n{storage_to_markdown(storage)}\n'

	if args.output:
		args.output.parent.mkdir(parents=True, exist_ok=True)
		args.output.write_text(content, encoding='utf-8')
		print(f'Output file: {args.output}')
	else:
		print(content)


if __name__ == '__main__':
	main()
