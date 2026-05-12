from pathlib import Path

from share_text.content import (
    build_content_items,
    copy_content_file,
    is_markdown_file,
    make_relative_href,
)
from share_text.models import ContentItem, ImageAsset
from share_text.page import build_index_page, build_page


def build_content_site(content_dir: Path, output_dir: Path, title: str) -> Path:
    items = build_content_items(content_dir)
    pages_dir = output_dir / "pages"
    files_dir = output_dir / "files"
    pages_dir.mkdir(parents=True, exist_ok=True)
    files_dir.mkdir(parents=True, exist_ok=True)

    for item in items:
        build_content_page(item, pages_dir, files_dir)

    index_file = output_dir / "index.html"
    index_file.write_text(build_index_page(title, content_dir, items), encoding="utf-8")
    return index_file


def build_content_page(item: ContentItem, pages_dir: Path, files_dir: Path) -> None:
    page_file = pages_dir / f"{item.relative_path.as_posix()}.html"
    page_file.parent.mkdir(parents=True, exist_ok=True)
    back_href = make_relative_href(page_file, pages_dir.parent / "index.html")

    if item.kind == "image":
        asset_file = files_dir / item.relative_path
        copy_content_file(item.source_path, asset_file)
        image_href = make_relative_href(page_file, asset_file)
        html = build_page(
            title=item.relative_path.as_posix(),
            content="",
            markdown=False,
            images=[
                ImageAsset(
                    source_path=item.source_path,
                    original_name=item.relative_path.name,
                    mime_type="image/*",
                    published_href=image_href,
                )
            ],
            back_href=back_href,
        )
    else:
        content = item.source_path.read_text(encoding="utf-8", errors="replace")
        html = build_page(
            title=item.relative_path.as_posix(),
            content=content,
            markdown=is_markdown_file(item.source_path),
            images=[],
            back_href=back_href,
        )

    page_file.write_text(html, encoding="utf-8")
