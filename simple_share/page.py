import html
import json
from pathlib import Path, PurePosixPath
from urllib.parse import SplitResult, urlsplit, urlunsplit

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup

from simple_share.content import (
    build_browse_href,
    build_raw_href,
    build_view_href,
    is_image_file,
    normalize_relative_path,
    resolve_content_path,
)
from simple_share.markdown import render_markdown
from simple_share.models import ContentItem, ImageAsset

PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = PACKAGE_DIR / "templates"
TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(enabled_extensions=("html",), default_for_string=True),
)
DOCUMENT_TEMPLATE = TEMPLATE_ENV.get_template("document.html")
INDEX_TEMPLATE = TEMPLATE_ENV.get_template("index.html")


def resolve_markdown_url(content_dir: Path | None, base_dir: PurePosixPath | None, url: str) -> str:
    if not content_dir or not base_dir or not url:
        return url

    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or url.startswith(("/", "#", "mailto:", "tel:")):
        return url

    relative_path = normalize_relative_path((base_dir / parsed.path).as_posix())
    resolved_path = resolve_content_path(content_dir, relative_path)

    if resolved_path.is_dir():
        resolved_url = build_browse_href(relative_path)
    elif is_image_file(resolved_path):
        resolved_url = build_raw_href(relative_path)
    else:
        resolved_url = build_view_href(relative_path)

    rebuilt = SplitResult(
        scheme="",
        netloc="",
        path=resolved_url,
        query=parsed.query,
        fragment=parsed.fragment,
    )
    return urlunsplit(rebuilt)


def build_text_block(
    content: str,
    markdown: bool,
    markdown_base_dir: PurePosixPath | None = None,
    markdown_content_dir: Path | None = None,
) -> str:
    if not content:
        return ""

    if not markdown:
        return f'<pre id="content">{html.escape(content)}</pre>'

    rendered = render_markdown(
        content,
        url_resolver=lambda url: resolve_markdown_url(markdown_content_dir, markdown_base_dir, url),
    )
    escaped_source = html.escape(content)
    return f"""
      <section class="text-panel">
        <div class="toolbar">
          <button id="copy-rich" type="button">Copy rich text</button>
          <button id="copy-md" type="button">Copy markdown</button>
          <span id="status"></span>
        </div>
        <article id="content" class="markdown">{rendered}</article>
        <details>
          <summary>Source markdown</summary>
          <pre>{escaped_source}</pre>
        </details>
      </section>
    """


def build_image_block(images: list[ImageAsset]) -> str:
    if not images:
        return ""

    gallery_items = []
    for image in images:
        src = html.escape(image.published_href)
        caption = html.escape(image.original_name)
        gallery_items.append(
            f"""
            <figure class="image-card">
              <a href="{src}" target="_blank" rel="noreferrer">
                <img src="{src}" alt="{caption}" />
              </a>
              <figcaption>{caption}</figcaption>
            </figure>
            """
        )

    return f"""
      <section class="image-panel">
        <p class="hint">Click the image to open it full size.</p>
        <div class="image-grid">
          {"".join(gallery_items)}
        </div>
      </section>
    """


def build_body(
    content: str,
    markdown: bool,
    images: list[ImageAsset],
    markdown_base_dir: PurePosixPath | None = None,
    markdown_content_dir: Path | None = None,
) -> str:
    sections = [
        build_text_block(content, markdown, markdown_base_dir, markdown_content_dir),
        build_image_block(images),
    ]
    return "\n".join(section for section in sections if section)


def script_safe_json(value: str) -> str:
    return json.dumps(value).replace("</", "<\\/")


def render_document_template(title: str, header: str, body: str, raw_content: str) -> str:
    return DOCUMENT_TEMPLATE.render(
        title=title,
        header=Markup(header),
        body=Markup(body),
        raw_content_json=script_safe_json(raw_content),
    )


def build_page(
    title: str,
    content: str,
    markdown: bool,
    images: list[ImageAsset],
    back_href: str | None = None,
    markdown_base_dir: PurePosixPath | None = None,
    markdown_content_dir: Path | None = None,
) -> str:
    body = build_body(content, markdown, images, markdown_base_dir, markdown_content_dir)
    header = ""
    if back_href:
        escaped_back_href = html.escape(back_href)
        escaped_title = html.escape(title)
        header = f"""
      <header class="page-header">
        <a class="back-link" href="{escaped_back_href}">Back to index</a>
        <h1 class="page-title">{escaped_title}</h1>
      </header>
        """
    return render_document_template(title, header, body, raw_content=content)


def build_index_page(title: str, content_dir: Path, items: list[ContentItem]) -> str:
    escaped_title = html.escape(title)
    escaped_dir = html.escape(str(content_dir))
    if items:
        cards = []
        for item in items:
            cards.append(
                f"""
          <a class="index-card" href="{html.escape(item.page_href)}">
            <p class="index-name">{html.escape(item.relative_path.as_posix())}</p>
            <p class="index-meta">{html.escape(item.kind)}</p>
          </a>
                """
            )
        listing = f'<div class="index-list">{"".join(cards)}</div>'
    else:
        listing = """
        <div class="empty-state">
          Drop `.md`, screenshots, or text files into this directory and refresh the shared page.
        </div>
        """

    body = f"""
      <section class="index-panel">
        <header class="page-header">
          <h1 class="page-title">{escaped_title}</h1>
        </header>
        <p class="index-lead">Content directory: <code>{escaped_dir}</code></p>
        {listing}
      </section>
    """
    return INDEX_TEMPLATE.render(title=title, body=Markup(body))
