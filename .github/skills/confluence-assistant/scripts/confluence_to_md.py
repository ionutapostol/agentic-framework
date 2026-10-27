"""Extract a Confluence page to Markdown with local images."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, NavigableString, Tag
from dotenv import load_dotenv
from markdownify import markdownify as to_markdown

SCRIPT_DIR = Path(__file__).resolve().parent
_DEFAULT_OUTPUT = SCRIPT_DIR.parents[3] / 'qa-output' / 'requirements'

PAGE_ID_PATTERN = re.compile(r'/pages/(\d+)')
PAGE_ID_QUERY_PATTERN = re.compile(r'pageId=(\d+)')
INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
INVALID_SLUG_CHARS = re.compile(r'[^A-Za-z0-9\s-]')

__all__ = ['main']


class FatalError(Exception):
	"""Raised when the export cannot continue."""


class ConfluenceExporter:
	def __init__(self, base_url: str, pat: str) -> None:
		self.base_url = base_url.rstrip('/')
		self.session = requests.Session()
		self.session.headers.update(
			{
				'Authorization': f'Bearer {pat}',
				'Accept': 'application/json',
			}
		)

	def _request(self, path_or_url: str, *, stream: bool = False) -> requests.Response:
		url = path_or_url
		if not path_or_url.startswith(('http://', 'https://')):
			url = f'{self.base_url}{path_or_url}'

		try:
			response = self.session.get(url, timeout=30, stream=stream)
		except requests.ConnectionError as exc:
			raise FatalError(f'Connection error while accessing {url}: {exc}') from exc
		except requests.RequestException as exc:
			raise FatalError(f'Failed to access {url}: {exc}') from exc

		if response.status_code == 401:
			raise FatalError('Authentication failed — check CONFLUENCE_PAT in .env')
		if response.status_code == 404:
			raise FatalError('Page not found — check page ID and permissions')

		try:
			response.raise_for_status()
		except requests.HTTPError as exc:
			raise FatalError(f'Confluence request failed for {url}: {exc}') from exc

		return response

	def fetch_page(self, page_id: str) -> dict[str, object]:
		response = self._request(
			f'/rest/api/content/{page_id}?expand=body.storage,title,space,version'
		)
		return response.json()

	def fetch_attachments(self, page_id: str) -> list[dict[str, object]]:
		attachments: list[dict[str, object]] = []
		path = f'/rest/api/content/{page_id}/child/attachment?limit=100'

		while path:
			response = self._request(path)
			payload = response.json()
			attachments.extend(payload.get('results', []))
			next_link = payload.get('_links', {}).get('next')
			path = str(next_link) if next_link else ''

		return attachments

	def download_file(self, url: str, destination: Path) -> None:
		is_internal = url.startswith(self.base_url)
		response = self._request(url, stream=True) if is_internal else self._request_external(url)
		destination.parent.mkdir(parents=True, exist_ok=True)
		with destination.open('wb') as file_handle:
			for chunk in response.iter_content(chunk_size=8192):
				if chunk:
					file_handle.write(chunk)

	def _request_external(self, url: str) -> requests.Response:
		"""Fetch an external URL without Confluence auth headers."""
		try:
			response = requests.get(url, timeout=30, stream=True)
			response.raise_for_status()
			return response
		except requests.RequestException as exc:
			raise FatalError(f'Failed to download external image {url}: {exc}') from exc


class ImageTracker:
	def __init__(self, output_dir: Path, page_slug: str, exporter: ConfluenceExporter) -> None:
		self.output_dir = output_dir
		self.page_slug = page_slug
		self.exporter = exporter
		self.assets_dir = self.output_dir / 'assets' / page_slug
		self.relative_dir = Path('assets') / page_slug
		self.downloaded = 0
		self._seen_paths: set[Path] = set()
		self.attachment_paths: dict[str, str] = {}
		self._external_cache: dict[str, str] = {}

	def download_attachment_images(self, attachments: list[dict[str, object]]) -> None:
		for attachment in attachments:
			media_type = str(attachment.get('metadata', {}).get('mediaType', ''))
			if not media_type.startswith('image/'):
				continue

			original_name = str(attachment.get('title', '')).strip()
			if not original_name:
				continue

			filename = sanitize_attachment_filename(original_name)
			relative_path = (self.relative_dir / filename).as_posix()
			self.attachment_paths[original_name] = relative_path
			attachment_links = attachment.get('_links', {})
			download_link = str(attachment_links.get('download', ''))
			if not download_link:
				continue

			absolute_path = self.assets_dir / filename
			if absolute_path not in self._seen_paths:
				self.exporter.download_file(urljoin(f'{self.exporter.base_url}/', download_link), absolute_path)
				self._seen_paths.add(absolute_path)
				self.downloaded += 1

	def attachment_path(self, filename: str) -> str:
		safe_name = sanitize_attachment_filename(filename)
		return self.attachment_paths.get(filename, (self.relative_dir / safe_name).as_posix())

	def download_external_image(self, image_url: str) -> str:
		cached = self._external_cache.get(image_url)
		if cached:
			return cached

		filename = infer_remote_filename(image_url)
		absolute_path = self.assets_dir / filename
		unique_path = ensure_unique_path(absolute_path)
		try:
			self.exporter.download_file(image_url, unique_path)
			self._seen_paths.add(unique_path)
			self.downloaded += 1
			relative_path = (self.relative_dir / unique_path.name).as_posix()
		except FatalError:
			# External image inaccessible (e.g. requires different auth); keep original URL
			relative_path = image_url
		self._external_cache[image_url] = relative_path
		return relative_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description='Extract a Confluence page to a Markdown file with local images.'
	)
	parser.add_argument('page_url_or_id', help='Confluence page URL or bare numeric page ID')
	parser.add_argument(
		'--output',
		'-o',
		type=Path,
		help='Output Markdown file path or destination directory',
	)
	return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
	args = parse_args(argv)

	try:
		config = load_config()
		page_id = extract_page_id(args.page_url_or_id)
		exporter = ConfluenceExporter(
			config['CONFLUENCE_URL'],
			config['CONFLUENCE_PAT'],
		)

		page = exporter.fetch_page(page_id)
		page_title = str(page.get('title', '')).strip() or f'Confluence Page {page_id}'
		output_path = resolve_output_path(args.output, config.get('DEFAULT_OUTPUT_PATH', ''), page_title)
		output_dir = output_path.parent
		page_slug = slugify(page_title) or f'page-{page_id}'

		attachments = exporter.fetch_attachments(page_id)
		images = ImageTracker(output_dir, page_slug, exporter)
		images.download_attachment_images(attachments)

		storage_value = str(page.get('body', {}).get('storage', {}).get('value', ''))
		markdown_body = convert_storage_to_markdown(storage_value, images)
		content = f'# {page_title}\n\n{markdown_body.strip()}\n'

		output_path.parent.mkdir(parents=True, exist_ok=True)
		output_path.write_text(content, encoding='utf-8')

		print(f'Output file: {output_path}')
		print(f'Images downloaded: {images.downloaded}')
		return 0
	except FatalError as exc:
		print(str(exc), file=sys.stderr)
		return 1


def find_git_root(start: Path) -> Path | None:
	"""Walk up from *start* until a directory containing .git is found."""
	current = start.resolve()
	while True:
		if (current / '.git').exists():
			return current
		parent = current.parent
		if parent == current:
			return None
		current = parent


def load_config() -> dict[str, str]:
	# Candidate .env locations in priority order:
	# 1. Next to the script itself
	# 2. Skill root (scripts/ → confluence-assistant/)
	# 3. Repo root derived from script path (scripts/ → … → repo root)
	# 4. Git root found by traversing up from CWD — handles any invocation context
	REPO_ROOT_BY_PATH = SCRIPT_DIR.parent.parent.parent.parent
	GIT_ROOT = find_git_root(Path.cwd())
	candidates: list[Path] = [
		SCRIPT_DIR / '.env',
		SCRIPT_DIR.parent / '.env',
		REPO_ROOT_BY_PATH / '.env',
	]
	if GIT_ROOT and GIT_ROOT not in (REPO_ROOT_BY_PATH,):
		candidates.append(GIT_ROOT / '.env')
	for env_path in candidates:
		if env_path.exists():
			load_dotenv(env_path)

	config = {
		'CONFLUENCE_URL': os.getenv('CONFLUENCE_URL', '').strip(),
		'CONFLUENCE_PAT': os.getenv('CONFLUENCE_PAT', '').strip(),
		'DEFAULT_OUTPUT_PATH': os.getenv('DEFAULT_OUTPUT_PATH', '').strip() or str(_DEFAULT_OUTPUT),
	}

	missing = [
		key
		for key in ('CONFLUENCE_URL', 'CONFLUENCE_PAT')
		if not config[key]
	]
	if missing:
		raise FatalError(f'Missing required environment variables: {", ".join(missing)}')

	return config


def extract_page_id(page_url_or_id: str) -> str:
	value = page_url_or_id.strip()
	if value.isdigit():
		return value

	try:
		urlparse(value)
	except ValueError as exc:
		raise FatalError('Expected a Confluence page URL or bare numeric page ID.') from exc

	match = PAGE_ID_PATTERN.search(value)
	if match:
		return match.group(1)

	match = PAGE_ID_QUERY_PATTERN.search(value)
	if match:
		return match.group(1)

	raise FatalError('Expected a Confluence page URL containing /pages/<id>, a viewpage.action?pageId=<id> URL, or a bare page ID.')


def resolve_output_path(output: Path | None, default_output: str, page_title: str) -> Path:
	filename = f'{safe_markdown_stem(page_title)}.md'
	target = output or (Path(default_output) if default_output else _DEFAULT_OUTPUT)

	if target.exists() and target.is_dir():
		return target / filename
	if target.suffix.lower() == '.md':
		return target
	if not target.suffix:
		return target / filename
	return target


def safe_markdown_stem(title: str) -> str:
	return slugify(title) or 'confluence-page'


def slugify(title: str) -> str:
	cleaned = INVALID_SLUG_CHARS.sub('', title)
	cleaned = re.sub(r'\s+', '-', cleaned.strip())
	cleaned = re.sub(r'-+', '-', cleaned).strip('-').lower()
	return cleaned or 'confluence-page'


def sanitize_attachment_filename(filename: str) -> str:
	cleaned = INVALID_FILENAME_CHARS.sub('_', Path(filename).name).strip().rstrip('.')
	return cleaned or 'image'


def infer_remote_filename(image_url: str) -> str:
	parsed = urlparse(image_url)
	candidate = sanitize_attachment_filename(unquote(Path(parsed.path).name))
	if candidate == 'image' and parsed.query:
		candidate = sanitize_attachment_filename(parsed.query.split('&', 1)[0].split('=', 1)[-1])
	if Path(candidate).suffix:
		return candidate

	return f'{candidate}.png'


def ensure_unique_path(path: Path) -> Path:
	if not path.exists():
		return path

	stem = path.stem
	for index in range(1, 10_000):
		candidate = path.with_name(f'{stem}-{index}{path.suffix}')
		if not candidate.exists():
			return candidate
	return path.with_name(f'{stem}-{os.getpid()}{path.suffix}')


def convert_storage_to_markdown(storage_value: str, images: ImageTracker) -> str:
	soup = BeautifulSoup(storage_value, 'html.parser')
	preprocess_macros(soup)
	preprocess_images(soup, images)
	preprocess_tables(soup)
	markdown = to_markdown(str(soup), heading_style='ATX', bullets='-')
	markdown = re.sub(r'\n{3,}', '\n\n', markdown)
	return markdown.strip()


def preprocess_macros(soup: BeautifulSoup) -> None:
	for macro in list(soup.find_all('ac:structured-macro')):
		macro_name = macro.get('ac:name') or macro.get('name') or ''
		body_html = extract_rich_text_body(macro)
		title = extract_macro_parameter(macro, 'title')

		if macro_name == 'toc':
			macro.decompose()
			continue
		if macro_name == 'panel':
			replace_with_html(
				macro,
				build_panel_html(title or 'Panel', body_html),
			)
			continue
		if macro_name == 'expand':
			replace_with_html(
				macro,
				build_expand_html(title or 'Details', body_html),
			)
			continue
		if macro_name in {'note', 'warning', 'info'}:
			replace_with_html(
				macro,
				build_message_html(macro_name.capitalize(), body_html),
			)
			continue

		if body_html:
			replace_with_html(macro, body_html)
		else:
			macro.decompose()


def preprocess_images(soup: BeautifulSoup, images: ImageTracker) -> None:
	for image in list(soup.find_all('ac:image')):
		alt_text = image.get('ac:alt') or image.get('alt') or ''
		attachment = image.find('ri:attachment')
		url_tag = image.find('ri:url')

		if attachment is not None:
			filename = attachment.get('ri:filename') or attachment.get('filename') or 'image'
			local_path = images.attachment_path(str(filename))
			replace_with_html(image, f'<img alt="{escape_html(str(alt_text) or str(filename))}" src="{local_path}" />')
			continue

		if url_tag is not None:
			image_url = url_tag.get('ri:value') or url_tag.get('value')
			if image_url:
				local_path = images.download_external_image(str(image_url))
				filename = Path(urlparse(str(image_url)).path).name or 'image'
				replace_with_html(
					image,
					f'<img alt="{escape_html(str(alt_text) or filename)}" src="{local_path}" />',
				)
				continue

		image.decompose()


def preprocess_tables(soup: BeautifulSoup) -> None:
	for table in list(soup.find_all('table')):
		markdown_table = table_to_gfm(table)
		table.replace_with(NavigableString(f'\n\n{markdown_table}\n\n'))


def extract_macro_parameter(macro: Tag, parameter_name: str) -> str:
	for parameter in macro.find_all('ac:parameter'):
		name = parameter.get('ac:name') or parameter.get('name')
		if name == parameter_name:
			return parameter.get_text(' ', strip=True)
	return ''


def extract_rich_text_body(macro: Tag) -> str:
	body = macro.find('ac:rich-text-body')
	if body is None:
		return ''
	return ''.join(str(child) for child in body.contents).strip()


def build_panel_html(title: str, body_html: str) -> str:
	return (
		'<blockquote>'
		f'<p><strong>{escape_html(title)}</strong></p>'
		f'{body_html}'
		'</blockquote>'
	)


def build_expand_html(title: str, body_html: str) -> str:
	return (
		'<details>'
		f'<summary>{escape_html(title)}</summary>'
		f'{body_html}'
		'</details>'
	)


def build_message_html(label: str, body_html: str) -> str:
	return (
		'<blockquote>'
		f'<p><strong>{escape_html(label)}:</strong></p>'
		f'{body_html}'
		'</blockquote>'
	)


def table_to_gfm(table: Tag) -> str:
	rows = [row for row in table.find_all('tr') if row.find_all(['th', 'td'])]
	if not rows:
		return ''

	header_cells = rows[0].find_all(['th', 'td'])
	headers = [normalize_table_cell(cell) for cell in header_cells]
	data_rows = [
		[normalize_table_cell(cell) for cell in row.find_all(['th', 'td'])]
		for row in rows[1:]
	]

	column_count = max([len(headers), *(len(row) for row in data_rows)], default=len(headers))
	headers.extend([''] * (column_count - len(headers)))
	for row in data_rows:
		row.extend([''] * (column_count - len(row)))

	separator = ['---'] * column_count
	lines = [
		'| ' + ' | '.join(headers) + ' |',
		'| ' + ' | '.join(separator) + ' |',
	]
	for row in data_rows:
		lines.append('| ' + ' | '.join(row) + ' |')
	return '\n'.join(lines)


def normalize_table_cell(cell: Tag) -> str:
	cell_html = ''.join(str(child) for child in cell.contents)
	markdown = to_markdown(cell_html, heading_style='ATX', bullets='-')
	markdown = re.sub(r'\s+', ' ', markdown).strip()
	markdown = markdown.replace('|', '\\|')
	return markdown


def replace_with_html(tag: Tag, html: str) -> None:
	fragment = BeautifulSoup(html, 'html.parser')
	wrapper = fragment if fragment.contents else BeautifulSoup('<span></span>', 'html.parser')
	new_nodes = list(wrapper.contents)
	if not new_nodes:
		tag.decompose()
		return
		
	first_node = new_nodes[0]
	tag.replace_with(first_node)
	for node in new_nodes[1:]:
		first_node.insert_after(node)
		first_node = node


def escape_html(value: str) -> str:
	return (
		value.replace('&', '&amp;')
		.replace('<', '&lt;')
		.replace('>', '&gt;')
		.replace('"', '&quot;')
	)


if __name__ == '__main__':
	raise SystemExit(main())
