import html
import re
from collections.abc import Callable

ESCAPE_SENTINEL = "\u0000"


def apply_escapes(text: str) -> str:
    return re.sub(r"\\(.)", lambda match: f"{ESCAPE_SENTINEL}{ord(match.group(1)):04x}", text)


def restore_escapes(text: str) -> str:
    return re.sub(
        rf"{ESCAPE_SENTINEL}([0-9a-f]{{4}})",
        lambda match: chr(int(match.group(1), 16)),
        text,
    )


def slugify_heading(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def restore_inline_html_tags(text: str) -> str:
    return re.sub(
        r"&lt;(/?[A-Za-z][^<>]*?)&gt;",
        lambda match: html.unescape(match.group(0)),
        text,
    )


def format_inline(
    text: str,
    footnote_numbers: dict[str, int] | None = None,
    reference_links: dict[str, tuple[str, str | None]] | None = None,
    url_resolver: Callable[[str], str] | None = None,
) -> str:
    text = apply_escapes(text)
    text = html.escape(text)

    if reference_links is not None:
        text = re.sub(
            r"!\[([^\]]*)\]\[([^\]]+)\]",
            lambda match: render_reference_image(
                match.group(1),
                match.group(2),
                reference_links,
                url_resolver,
            ),
            text,
        )
        text = re.sub(
            r"!\[([^\]]*)\]\[\]",
            lambda match: render_reference_image(
                match.group(1),
                match.group(1),
                reference_links,
                url_resolver,
                collapsed=True,
            ),
            text,
        )
        text = re.sub(
            r"!\[([^\]]*)\](?![\[(])",
            lambda match: render_reference_image(
                match.group(1),
                match.group(1),
                reference_links,
                url_resolver,
                shortcut=True,
            ),
            text,
        )
        text = re.sub(
            r"\[([^\]]+)\]\[([^\]]+)\]",
            lambda match: render_reference_link(
                match.group(1),
                match.group(2),
                reference_links,
                url_resolver,
            ),
            text,
        )
        text = re.sub(
            r"\[([^\]]+)\]\[\]",
            lambda match: render_reference_link(
                match.group(1),
                match.group(1),
                reference_links,
                url_resolver,
                collapsed=True,
            ),
            text,
        )
        text = re.sub(
            r"\[([^\]]+)\](?![\[(^])",
            lambda match: render_reference_link(
                match.group(1),
                match.group(1),
                reference_links,
                url_resolver,
                shortcut=True,
            ),
            text,
        )

    replacements = [
        (r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+&quot;([^"]*)&quot;)?\)', render_image),
        (r'\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;([^"]*)&quot;)?\)', render_link),
        (r"&lt;(https?://[^\s<>]+)&gt;", r'<a href="\1">\1</a>'),
        (r"`([^`]+)`", r"<code>\1</code>"),
        (r"~~([^~]+)~~", r"<del>\1</del>"),
        (r"\*\*([^*]+)\*\*", r"<strong>\1</strong>"),
        (r"__([^_]+)__", r"<strong>\1</strong>"),
        (r"\*([^*]+)\*", r"<em>\1</em>"),
        (r"_([^_]+)_", r"<em>\1</em>"),
        (r"~([^~]+)~", r"<sub>\1</sub>"),
        (r"\^([^\^\s][^\^]*?)\^", r"<sup>\1</sup>"),
    ]
    for pattern, replacement in replacements:
        if callable(replacement):
            text = re.sub(pattern, lambda match: replacement(match, url_resolver), text)
            continue
        text = re.sub(pattern, replacement, text)
    if footnote_numbers is not None:
        text = re.sub(
            r"\[\^([^\]]+)\]",
            lambda match: render_footnote_ref(match.group(1), footnote_numbers),
            text,
        )
    text = restore_inline_html_tags(text)
    return restore_escapes(text)


def resolve_url(url: str, url_resolver: Callable[[str], str] | None) -> str:
    if url_resolver is None:
        return url
    return url_resolver(url)


def render_link(match: re.Match[str], url_resolver: Callable[[str], str] | None = None) -> str:
    label, href, title = match.group(1), resolve_url(match.group(2), url_resolver), match.group(3)
    title_attr = f' title="{title}"' if title else ""
    return f'<a href="{href}"{title_attr}>{label}</a>'


def render_image(match: re.Match[str], url_resolver: Callable[[str], str] | None = None) -> str:
    alt, src, title = match.group(1), resolve_url(match.group(2), url_resolver), match.group(3)
    title_attr = f' title="{title}"' if title else ""
    return f'<img src="{src}" alt="{alt}"{title_attr} />'


def render_reference_link(
    label: str,
    key: str,
    reference_links: dict[str, tuple[str, str | None]],
    url_resolver: Callable[[str], str] | None = None,
    collapsed: bool = False,
    shortcut: bool = False,
) -> str:
    href, title = reference_links.get(key.lower(), ("", None))
    if not href:
        if shortcut:
            return f"[{label}]"
        if collapsed:
            return f"[{label}][]"
        return f"[{label}][{key}]"
    href = resolve_url(href, url_resolver)
    title_attr = f' title="{title}"' if title else ""
    return f'<a href="{href}"{title_attr}>{label}</a>'


def render_reference_image(
    alt: str,
    key: str,
    reference_links: dict[str, tuple[str, str | None]],
    url_resolver: Callable[[str], str] | None = None,
    collapsed: bool = False,
    shortcut: bool = False,
) -> str:
    src, title = reference_links.get(key.lower(), ("", None))
    if not src:
        if shortcut:
            return f"![{alt}]"
        if collapsed:
            return f"![{alt}][]"
        return f"![{alt}][{key}]"
    src = resolve_url(src, url_resolver)
    title_attr = f' title="{title}"' if title else ""
    return f'<img src="{src}" alt="{alt}"{title_attr} />'


def render_footnote_ref(name: str, footnote_numbers: dict[str, int]) -> str:
    number = footnote_numbers.setdefault(name, len(footnote_numbers) + 1)
    escaped_name = html.escape(name)
    return (
        f'<sup class="footnote-ref" id="fnref-{escaped_name}">'
        f'<a href="#fn-{escaped_name}">[{number}]</a></sup>'
    )


def is_table_divider(line: str) -> bool:
    cells = parse_table_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def parse_table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_horizontal_rule(line: str) -> bool:
    compact = line.replace(" ", "")
    return compact in {"---", "***", "___"}


def parse_task_item(text: str) -> tuple[bool, str] | None:
    match = re.fullmatch(r"\[( |x|X)\]\s+(.*)", text)
    if not match:
        return None
    return (match.group(1).lower() == "x", match.group(2))


def is_html_block_start(line: str) -> bool:
    return bool(re.match(r"<([A-Za-z][\w-]*)(\s|>|/>)", line))


def render_markdown(text: str, url_resolver: Callable[[str], str] | None = None) -> str:
    lines = text.splitlines()
    parts: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    list_tag: str | None = None
    table_headers: list[str] = []
    table_rows: list[list[str]] = []
    blockquote_lines: list[str] = []
    code_lines: list[str] = []
    footnotes: dict[str, str] = {}
    footnote_order: dict[str, int] = {}
    reference_links: dict[str, tuple[str, str | None]] = {}
    heading_ids: dict[str, int] = {}
    in_code_block = False
    code_language = ""
    footnote_pattern = re.compile(r"\[\^([^\]]+)\]:\s*(.*)")
    reference_pattern = re.compile(r'\[([^\]]+)\]:\s*(\S+)(?:\s+"([^"]*)")?')

    for raw_line in lines:
        stripped_line = raw_line.strip()
        footnote_match = footnote_pattern.fullmatch(stripped_line)
        if footnote_match:
            footnotes[footnote_match.group(1)] = footnote_match.group(2)
            continue
        reference_match = reference_pattern.fullmatch(stripped_line)
        if reference_match:
            reference_links[reference_match.group(1).lower()] = (
                reference_match.group(2),
                reference_match.group(3),
            )

    def flush_paragraph() -> None:
        if paragraph:
            rendered = format_inline(
                " ".join(paragraph),
                footnote_order,
                reference_links,
                url_resolver,
            )
            parts.append(f"<p>{rendered}</p>")
            paragraph.clear()

    def flush_list() -> None:
        nonlocal list_tag
        if list_items and list_tag:
            items = "".join(list_items)
            parts.append(f"<{list_tag}>{items}</{list_tag}>")
            list_items.clear()
            list_tag = None

    def flush_table() -> None:
        if table_headers:
            header_html = "".join(
                f"<th>{format_inline(cell, footnote_order, reference_links, url_resolver)}</th>"
                for cell in table_headers
            )
            body_html = "".join(
                "<tr>"
                + "".join(
                    f"<td>{format_inline(cell, footnote_order, reference_links, url_resolver)}</td>"
                    for cell in row
                )
                + "</tr>"
                for row in table_rows
            )
            parts.append(
                '<div class="table-wrap"><table><thead><tr>'
                f"{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>"
            )
            table_headers.clear()
            table_rows.clear()

    def flush_blockquote() -> None:
        if blockquote_lines:
            rendered = render_markdown("\n".join(blockquote_lines), url_resolver=url_resolver)
            parts.append(f"<blockquote>{rendered}</blockquote>")
            blockquote_lines.clear()

    def append_list_item(tag: str, item: str) -> None:
        nonlocal list_tag
        if list_tag and list_tag != tag:
            flush_list()
        list_tag = tag
        task = parse_task_item(item)
        if task:
            checked, label = task
            checkbox = " checked" if checked else ""
            rendered = format_inline(label, footnote_order, reference_links, url_resolver)
            list_items.append(
                '<li class="task-item">'
                f'<input type="checkbox" disabled{checkbox} /> '
                f"<span>{rendered}</span></li>"
            )
            return
        rendered = format_inline(item, footnote_order, reference_links, url_resolver)
        list_items.append(f"<li>{rendered}</li>")

    def flush_code_block() -> None:
        nonlocal in_code_block, code_language
        if in_code_block:
            code = html.escape("\n".join(code_lines))
            language_attr = ""
            if code_language:
                language_attr = f' class="language-{code_language}" data-language="{code_language}"'
            parts.append(f"<pre><code{language_attr}>{code}</code></pre>")
            code_lines.clear()
            code_language = ""
            in_code_block = False

    line_index = 0
    while line_index < len(lines):
        line = lines[line_index]
        stripped = line.strip()

        footnote_match = footnote_pattern.fullmatch(stripped)
        if footnote_match and not in_code_block:
            line_index += 1
            continue

        reference_match = reference_pattern.fullmatch(stripped)
        if reference_match and not in_code_block:
            line_index += 1
            continue

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_table()
            flush_blockquote()
            if in_code_block:
                flush_code_block()
            else:
                in_code_block = True
                code_language = stripped.removeprefix("```").strip().lower()
            line_index += 1
            continue

        if in_code_block:
            code_lines.append(line)
            line_index += 1
            continue

        if not stripped:
            flush_paragraph()
            flush_list()
            flush_table()
            flush_blockquote()
            line_index += 1
            continue

        if stripped.startswith(">"):
            flush_paragraph()
            flush_list()
            flush_table()
            content = stripped[1:]
            if content.startswith(" "):
                content = content[1:]
            blockquote_lines.append(content)
            line_index += 1
            continue
        flush_blockquote()

        if is_html_block_start(stripped):
            flush_paragraph()
            flush_list()
            flush_table()
            html_lines = [line]
            line_index += 1
            while line_index < len(lines) and lines[line_index].strip():
                html_lines.append(lines[line_index])
                line_index += 1
            parts.append("\n".join(html_lines))
            continue

        if is_horizontal_rule(stripped):
            flush_paragraph()
            flush_list()
            flush_table()
            parts.append("<hr />")
            line_index += 1
            continue

        heading_level = 0
        heading_text = ""
        for level in range(6, 0, -1):
            prefix = "#" * level + " "
            if stripped.startswith(prefix):
                heading_level = level
                heading_text = stripped[len(prefix) :]
                break

        if heading_level:
            flush_paragraph()
            flush_list()
            flush_table()
            slug = slugify_heading(heading_text)
            count = heading_ids.get(slug, 0)
            heading_ids[slug] = count + 1
            heading_id = slug if count == 0 else f"{slug}-{count + 1}"
            rendered_heading = format_inline(
                heading_text,
                footnote_order,
                reference_links,
                url_resolver,
            )
            parts.append(
                f'<h{heading_level} id="{heading_id}">{rendered_heading}</h{heading_level}>'
            )
            line_index += 1
            continue

        next_line = lines[line_index + 1].strip() if line_index + 1 < len(lines) else ""
        if "|" in stripped and "|" in next_line and is_table_divider(next_line):
            flush_paragraph()
            flush_list()
            flush_table()
            table_headers.extend(parse_table_cells(stripped))
            line_index += 2
            while line_index < len(lines):
                row_line = lines[line_index].strip()
                if not row_line or "|" not in row_line:
                    break
                table_rows.append(parse_table_cells(row_line))
                line_index += 1
            flush_table()
            continue

        if stripped.startswith("- ") or stripped.startswith("* "):
            flush_paragraph()
            flush_table()
            append_list_item("ul", stripped[2:])
            line_index += 1
            continue

        task_item = parse_task_item(stripped)
        if task_item:
            flush_paragraph()
            flush_table()
            append_list_item("ul", stripped)
            line_index += 1
            continue

        ordered_match = re.match(r"\d+\.\s+(.*)", stripped)
        if ordered_match:
            flush_paragraph()
            flush_table()
            append_list_item("ol", ordered_match.group(1))
            line_index += 1
            continue

        paragraph.append(stripped)
        line_index += 1

    flush_paragraph()
    flush_list()
    flush_table()
    flush_blockquote()
    if in_code_block:
        flush_code_block()

    if footnote_order:
        note_items = []
        for name, number in sorted(footnote_order.items(), key=lambda item: item[1]):
            content = format_inline(
                footnotes.get(name, ""),
                footnote_order,
                reference_links,
                url_resolver,
            )
            escaped_name = html.escape(name)
            note_items.append(
                f'<li id="fn-{escaped_name}">{content} <a href="#fnref-{escaped_name}">↩</a></li>'
            )
        parts.append(f'<section class="footnotes"><hr /><ol>{"".join(note_items)}</ol></section>')

    return "\n".join(parts)
