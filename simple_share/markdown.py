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
    table_headers: list[str] = []
    table_rows: list[list[str]] = []
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

    def flush_table() -> None:
        if table_headers:
            header_html = "".join(f"<th>{format_inline(cell)}</th>" for cell in table_headers)
            body_html = "".join(
                f"<tr>{''.join(f'<td>{format_inline(cell)}</td>' for cell in row)}</tr>"
                for row in table_rows
            )
            parts.append(
                f"<div class=\"table-wrap\"><table><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table></div>"
            )
            table_headers.clear()
            table_rows.clear()

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

    def parse_table_cells(line: str) -> list[str]:
        raw_cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        return [cell for cell in raw_cells]

    def is_table_divider(line: str) -> bool:
        cells = parse_table_cells(line)
        return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)

    line_index = 0
    while line_index < len(lines):
        line = lines[line_index]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            flush_list()
            flush_table()
            if in_code_block:
                flush_code_block()
            else:
                in_code_block = True
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
            line_index += 1
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
            flush_table()
            parts.append(f"<h{heading_level}>{format_inline(heading_text)}</h{heading_level}>")
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
    if in_code_block:
        flush_code_block()

    return "\n".join(parts)
