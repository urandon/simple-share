import mimetypes
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote, urlsplit

from simple_share.assets import STATIC_DIR
from simple_share.content import build_payload, default_title
from simple_share.models import ImageAsset
from simple_share.page import build_page


@dataclass
class AdHocConfig:
    file_paths: list[str] | None
    text_args: list[str]
    markdown: bool
    title: str | None


def build_adhoc_handler(config: AdHocConfig) -> type[BaseHTTPRequestHandler]:
    class AdHocHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            route = unquote(urlsplit(self.path).path)
            try:
                if route in {"", "/", "/index.html"}:
                    self.respond_html(self.build_page())
                    return

                if route.startswith("/static/"):
                    self.respond_file(STATIC_DIR / route.removeprefix("/static/"), cache_static=True)
                    return

                if route.startswith("/image-"):
                    self.respond_image(route.removeprefix("/"))
                    return

                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            except ValueError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Unsupported path")

        def current_images(self) -> list[ImageAsset]:
            payload = build_payload(config.file_paths, config.text_args)
            images: list[ImageAsset] = []
            for index, image_path in enumerate(payload.image_paths, start=1):
                mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
                suffix = image_path.suffix.lower() or mimetypes.guess_extension(mime_type) or ".bin"
                images.append(
                    ImageAsset(
                        source_path=image_path,
                        original_name=image_path.name,
                        mime_type=mime_type,
                        published_href=f"image-{index}{suffix}",
                    )
                )
            return images

        def build_page(self) -> str:
            payload = build_payload(config.file_paths, config.text_args)
            title = config.title or default_title(payload)
            return build_page(title, payload.content, config.markdown, self.current_images())

        def respond_image(self, name: str) -> None:
            for image in self.current_images():
                if image.published_href == name:
                    self.respond_file(image.source_path)
                    return
            raise FileNotFoundError(name)

        def respond_html(self, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def respond_file(self, file_path: Path, cache_static: bool = False) -> None:
            if not file_path.exists() or file_path.is_dir():
                raise FileNotFoundError(file_path)
            payload = file_path.read_bytes()
            mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(payload)))
            if cache_static:
                self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            return

    return AdHocHandler
