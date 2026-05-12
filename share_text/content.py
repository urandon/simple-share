import mimetypes
import os
import shutil
import sys
from pathlib import Path

from share_text.models import ContentItem, ImageAsset, SharePayload

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONTENT_DIR = REPO_ROOT / "content"
MARKDOWN_SUFFIXES = {".md", ".markdown"}


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"Missing required command: {name}")


def is_image_file(path: Path) -> bool:
    mime_type, _ = mimetypes.guess_type(path.name)
    return bool(mime_type and mime_type.startswith("image/"))


def is_markdown_file(path: Path) -> bool:
    return path.suffix.lower() in MARKDOWN_SUFFIXES


def should_use_content_dir_mode(file_paths: list[str] | None, text_args: list[str]) -> bool:
    return not file_paths and not text_args and sys.stdin.isatty()


def build_payload(file_paths: list[str] | None, text_args: list[str]) -> SharePayload:
    text_parts: list[str] = []
    image_paths: list[Path] = []

    for raw_path in file_paths or []:
        path = Path(raw_path)
        if is_image_file(path):
            image_paths.append(path)
        else:
            text_parts.append(path.read_text(encoding="utf-8"))

    if text_args:
        text_parts.append(" ".join(text_args))
    elif not text_parts and not image_paths and not sys.stdin.isatty():
        text_parts.append(sys.stdin.read())

    if not text_parts and not image_paths:
        raise SystemExit("No input provided")

    content = "\n\n".join(part.rstrip("\n") for part in text_parts if part)
    return SharePayload(content=content, image_paths=image_paths)


def stage_images(image_paths: list[Path], output_dir: Path) -> list[ImageAsset]:
    staged_images: list[ImageAsset] = []

    for index, image_path in enumerate(image_paths, start=1):
        mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        suffix = image_path.suffix.lower() or mimetypes.guess_extension(mime_type) or ".bin"
        published_name = f"image-{index}{suffix}"
        shutil.copy2(image_path, output_dir / published_name)
        staged_images.append(
            ImageAsset(
                source_path=image_path,
                original_name=image_path.name,
                mime_type=mime_type,
                published_href=published_name,
            )
        )

    return staged_images


def default_title(payload: SharePayload) -> str:
    if payload.image_paths and not payload.content:
        return "shared screenshots"
    return "shared text"


def resolve_content_dir(raw_path: str | None) -> Path:
    if not raw_path:
        return DEFAULT_CONTENT_DIR
    return Path(raw_path).expanduser().resolve()


def ensure_content_dir(content_dir: Path) -> None:
    content_dir.mkdir(parents=True, exist_ok=True)


def list_content_files(content_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(content_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.relative_to(content_dir).parts):
            continue
        files.append(path)
    return files


def build_content_items(content_dir: Path) -> list[ContentItem]:
    items: list[ContentItem] = []
    for source_path in list_content_files(content_dir):
        relative_path = source_path.relative_to(content_dir)
        page_href = f"pages/{relative_path.as_posix()}.html"
        kind = "image" if is_image_file(source_path) else "markdown" if is_markdown_file(source_path) else "text"
        items.append(
            ContentItem(
                source_path=source_path,
                relative_path=relative_path,
                kind=kind,
                page_href=page_href,
            )
        )
    return items


def copy_content_file(source_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, output_path)


def make_relative_href(from_file: Path, to_file: Path) -> str:
    relative = os.path.relpath(to_file, start=from_file.parent)
    return relative.replace(os.sep, "/")
