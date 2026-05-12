import html
import re


def format_inline(text: str) -> str:
    text = html.escape(text)
    replacements = [
        (r"`([^`]+)`", r"<code>\1</code>"),
        (r"\*\*([^*]+)\*\*", r"<strong>\1</strong>"),
        (r"__([^_]+)__", r"<strong>\1</strong>"),
        (r"\*([^*]+)\*", r"<em>\1</em>"),
        (r"_([^_]+)_", r"<em>\1</em>"),
        (r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>'),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)
    return text


def render_markdown(text: str) -> str:
    lines = text.splitlines()
    parts: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_tag: str | None = None
    code_lines: list[str] = []
    in_code_block = False

    def flush_paragraph() -> None:
        if paragraph:
            parts.append(f"<p>{format_inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_tag
        if list_items and list_tag:
            items = "".join(f"<li>{format_inline(item)}</li>" for item in list_items)
            parts.append(f"<{list_tag}>{items}</{list_tag}>")
            list_items.clear()
            list_tag = None

    def append_list_item(tag: str, item: str) -> None:
        nonlocal list_tag
        if list_tag and list_tag != tag:
            flush_list()
        list_tag = tag
        list_items.append(item)

    def flush_code_block() -> None:
        nonlocal in_code_block
        if in_code_block:
            code = html.escape("\n".join(code_lines))
            parts.append(f"<pre><code>{code}</code></pre>")
            code_lines.clear()
            in_code_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            if in_code_block:
                flush_code_block()
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            continue

        heading_level = 0
        for prefix, level in (("### ", 3), ("## ", 2), ("# ", 1)):
            if stripped.startswith(prefix):
                heading_level = level
                heading_text = stripped[len(prefix):]
                break

        if heading_level:
            flush_paragraph()
            flush_list()
            parts.append(f"<h{heading_level}>{format_inline(heading_text)}</h{heading_level}>")
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            flush_paragraph()
            append_list_item("ul", stripped[2:])
            continue

        ordered_match = re.match(r"\d+\.\s+(.*)", stripped)
        if ordered_match:
            flush_paragraph()
            append_list_item("ol", ordered_match.group(1))
            continue

        paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    if in_code_block:
        flush_code_block()

    return "\n".join(parts)
