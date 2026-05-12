import mimetypes
import os
import shutil
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import quote

from simple_share.models import ContentItem, ImageAsset, SharePayload

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
        return Path(".").resolve()
    return Path(raw_path).expanduser().resolve()


def ensure_content_dir(content_dir: Path) -> None:
    content_dir.mkdir(parents=True, exist_ok=True)


def is_hidden_relative_path(relative_path: PurePosixPath) -> bool:
    return any(part.startswith(".") for part in relative_path.parts)


def normalize_relative_path(raw_path: str = "") -> PurePosixPath:
    normalized = PurePosixPath(raw_path.strip("/"))
    if normalized.is_absolute() or ".." in normalized.parts:
        raise ValueError(f"Unsupported relative path: {raw_path}")
    if normalized == PurePosixPath("."):
        return PurePosixPath()
    return normalized


def resolve_content_path(content_dir: Path, relative_path: PurePosixPath) -> Path:
    if not relative_path.parts:
        return content_dir
    return content_dir.joinpath(*relative_path.parts)


def build_browse_href(relative_path: PurePosixPath) -> str:
    if not relative_path.parts:
        return "/"
    return f"/browse/{quote(relative_path.as_posix(), safe='/')}/"


def build_view_href(relative_path: PurePosixPath) -> str:
    return f"/view/{quote(relative_path.as_posix(), safe='/')}"


def build_raw_href(relative_path: PurePosixPath) -> str:
    return f"/raw/{quote(relative_path.as_posix(), safe='/')}"


def describe_path_kind(path: Path) -> str:
    prefix = "symlink " if path.is_symlink() else ""
    if path.is_dir():
        return f"{prefix}directory"
    if is_image_file(path):
        return f"{prefix}image"
    if is_markdown_file(path):
        return f"{prefix}markdown"
    return f"{prefix}text"


def iter_directory_items(content_dir: Path, relative_dir: PurePosixPath = PurePosixPath()) -> list[ContentItem]:
    directory_path = resolve_content_path(content_dir, relative_dir)
    if not directory_path.is_dir():
        raise NotADirectoryError(directory_path)

    items: list[ContentItem] = []
    if relative_dir.parts:
        parent_relative = PurePosixPath(*relative_dir.parts[:-1])
        items.append(
            ContentItem(
                source_path=directory_path.parent,
                relative_path=Path(".."),
                kind="parent directory",
                page_href=build_browse_href(parent_relative),
            )
        )

    children = []
    for child in directory_path.iterdir():
        child_relative = relative_dir / child.name
        if is_hidden_relative_path(child_relative):
            continue
        children.append(child)

    for child in sorted(children, key=lambda path: (0 if path.is_dir() else 1, path.name.lower(), path.name)):
        child_relative = relative_dir / child.name
        href = build_browse_href(child_relative) if child.is_dir() else build_view_href(child_relative)
        items.append(
            ContentItem(
                source_path=child,
                relative_path=Path(child.name),
                kind=describe_path_kind(child),
                page_href=href,
            )
        )

    return items


def build_content_items(content_dir: Path) -> list[ContentItem]:
    return iter_directory_items(content_dir)


def copy_content_file(source_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, output_path)


def make_relative_href(from_file: Path, to_file: Path) -> str:
    relative = os.path.relpath(to_file, start=from_file.parent)
    return relative.replace(os.sep, "/")
