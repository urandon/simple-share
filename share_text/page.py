import html
import json
from pathlib import Path

from share_text.markdown import render_markdown
from share_text.models import ContentItem, ImageAsset


PAGE_STYLES = """
      :root {
        --text-color: #1f2937;
        --page-bg: #f5f7fb;
        --border: #d4dae4;
        --panel: #ffffff;
        --accent: #0f766e;
        --accent-contrast: #ffffff;
        --muted: #5b6473;
      }
      * { box-sizing: border-box; }
      body { font-family: Inter, system-ui, sans-serif; margin: 0; line-height: 1.5; background: linear-gradient(180deg, #eef4ff 0%, #f7f8fb 45%, #edf2f7 100%); color: var(--text-color); }
      main { max-width: 1080px; margin: 0 auto; padding: 2rem 1rem 3rem; }
      pre, code { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
      pre { white-space: pre-wrap; word-break: break-word; padding: 1rem; border: 1px solid var(--border); border-radius: 16px; overflow-x: auto; background: var(--panel); }
      .text-panel, .image-panel { background: rgba(255, 255, 255, 0.82); border: 1px solid var(--border); border-radius: 20px; padding: 1rem; box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08); backdrop-filter: blur(12px); }
      .image-panel { margin-top: 1rem; }
      .toolbar { display: flex; gap: 0.75rem; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; }
      button { border: 1px solid var(--accent); background: var(--accent); color: var(--accent-contrast); border-radius: 999px; padding: 0.6rem 0.95rem; cursor: pointer; font-weight: 600; }
      button:hover { filter: brightness(0.96); }
      .markdown h1, .markdown h2, .markdown h3 { line-height: 1.25; }
      .markdown p, .markdown ul { margin: 0 0 1rem; }
      .markdown li { margin: 0.25rem 0; }
      .markdown code { padding: 0.1rem 0.3rem; border: 1px solid var(--border); border-radius: 6px; background: rgba(15, 23, 42, 0.04); }
      .image-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }
      .image-card { margin: 0; background: var(--panel); border: 1px solid var(--border); border-radius: 16px; overflow: hidden; }
      .image-card a { display: block; background: linear-gradient(180deg, #f8fbff 0%, #edf3fb 100%); }
      .image-card img { display: block; width: 100%; height: auto; max-height: 80vh; object-fit: contain; }
      .image-card figcaption { padding: 0.75rem 0.9rem; color: var(--muted); font-size: 0.95rem; }
      .hint { margin: 0 0 1rem; color: var(--muted); }
      .page-header { display: flex; gap: 1rem; align-items: center; justify-content: space-between; margin-bottom: 1rem; flex-wrap: wrap; }
      .page-title { margin: 0; font-size: clamp(1.4rem, 3vw, 2.4rem); line-height: 1.1; }
      .back-link { color: var(--accent); text-decoration: none; font-weight: 700; }
      .back-link:hover { text-decoration: underline; }
      .index-panel { background: rgba(255, 255, 255, 0.82); border: 1px solid var(--border); border-radius: 20px; padding: 1rem; box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08); backdrop-filter: blur(12px); }
      .index-lead { margin: 0 0 1rem; color: var(--muted); }
      .index-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }
      .index-card { display: block; padding: 1rem; border-radius: 18px; border: 1px solid var(--border); background: var(--panel); color: inherit; text-decoration: none; box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04); }
      .index-card:hover { transform: translateY(-1px); box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08); }
      .index-name { margin: 0 0 0.35rem; font-weight: 700; word-break: break-word; }
      .index-meta { margin: 0; color: var(--muted); font-size: 0.95rem; }
      .empty-state { padding: 1.25rem; border: 1px dashed var(--border); border-radius: 16px; color: var(--muted); background: rgba(255, 255, 255, 0.45); }
      #status { color: var(--accent); font-size: 0.95rem; font-weight: 600; }
      details { margin-top: 1rem; }
      @media (prefers-color-scheme: dark) {
        :root {
          --text-color: #e5edf7;
          --page-bg: #0f172a;
          --border: #334155;
          --panel: #0f172a;
          --accent: #2dd4bf;
          --accent-contrast: #042f2e;
          --muted: #9fb0c7;
        }
        body { background: linear-gradient(180deg, #08111f 0%, #0f172a 55%, #162033 100%); }
        .text-panel, .image-panel { background: rgba(15, 23, 42, 0.92); box-shadow: 0 18px 42px rgba(2, 6, 23, 0.44); }
        .image-card a { background: linear-gradient(180deg, #111827 0%, #0f172a 100%); }
      }
"""

PAGE_SCRIPT = """
      const rawContent = __RAW_CONTENT_JSON__;
      const contentNode = document.getElementById('content');
      const copyRichButton = document.getElementById('copy-rich');
      const copyMarkdownButton = document.getElementById('copy-md');
      const statusNode = document.getElementById('status');

      function setStatus(message) {
        if (!statusNode) return;
        statusNode.textContent = message;
        setTimeout(() => {
          if (statusNode.textContent === message) statusNode.textContent = '';
        }, 2000);
      }

      async function copyRichText() {
        if (!contentNode || !navigator.clipboard || !window.ClipboardItem) return;
        const htmlBlob = new Blob([contentNode.innerHTML], { type: 'text/html' });
        const textBlob = new Blob([contentNode.innerText], { type: 'text/plain' });
        await navigator.clipboard.write([
          new ClipboardItem({ 'text/html': htmlBlob, 'text/plain': textBlob })
        ]);
        setStatus('Copied');
      }

      async function copyMarkdown() {
        if (!navigator.clipboard) return;
        await navigator.clipboard.writeText(rawContent);
        setStatus('Copied');
      }

      if (copyRichButton) copyRichButton.addEventListener('click', copyRichText);
      if (copyMarkdownButton) copyMarkdownButton.addEventListener('click', copyMarkdown);
"""


def build_text_block(content: str, markdown: bool) -> str:
    if not content:
        return ""

    if not markdown:
        return f'<pre id="content">{html.escape(content)}</pre>'

    rendered = render_markdown(content)
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
          {''.join(gallery_items)}
        </div>
      </section>
    """


def build_body(content: str, markdown: bool, images: list[ImageAsset]) -> str:
    sections = [build_text_block(content, markdown), build_image_block(images)]
    return "\n".join(section for section in sections if section)


def build_page_shell(title: str, body: str, raw_content: str = "") -> str:
    raw_content_json = json.dumps(raw_content)
    escaped_title = html.escape(title)
    script = PAGE_SCRIPT.replace("__RAW_CONTENT_JSON__", raw_content_json)
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{escaped_title}</title>
    <style>
{PAGE_STYLES}
    </style>
  </head>
  <body>
    <main>
{body}
    </main>
    <script>
{script}
    </script>
  </body>
</html>
"""


def build_page(title: str, content: str, markdown: bool, images: list[ImageAsset], back_href: str | None = None) -> str:
    body = build_body(content, markdown, images)
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
    return build_page_shell(title, f"{header}\n{body}", raw_content=content)


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
    return build_page_shell(title, body)
