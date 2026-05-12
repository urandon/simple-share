from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImageAsset:
    source_path: Path
    original_name: str
    mime_type: str
    published_href: str


@dataclass
class SharePayload:
    content: str
    image_paths: list[Path]


@dataclass
class ContentItem:
    source_path: Path
    relative_path: Path
    kind: str
    page_href: str
