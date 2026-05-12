import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

from simple_share.content import (
    build_browse_href,
    build_raw_href,
    describe_path_kind,
    is_markdown_file,
    iter_directory_items,
    normalize_relative_path,
    resolve_content_path,
)
from simple_share.models import ImageAsset
from simple_share.page import build_index_page, build_page


def build_content_handler(
    content_dir: Path,
    title: str,
    static_dir: Path,
) -> type[BaseHTTPRequestHandler]:
    class ContentHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            route = unquote(urlsplit(self.path).path)
            try:
                if route in {"", "/"}:
                    self.respond_html(self.build_directory_page(PurePosixPath()))
                    return

                if route == "/index.html":
                    self.redirect("/")
                    return

                if route.startswith("/static/"):
                    self.respond_file(static_dir / route.removeprefix("/static/"))
                    return

                if route.startswith("/raw/"):
                    relative_path = normalize_relative_path(route.removeprefix("/raw/"))
                    self.respond_file(resolve_content_path(content_dir, relative_path))
                    return

                if route == "/browse":
                    self.redirect("/")
                    return

                if route.startswith("/browse/"):
                    browse_path = route.removeprefix("/browse/").rstrip("/")
                    relative_path = normalize_relative_path(browse_path)
                    self.respond_html(self.build_directory_page(relative_path))
                    return

                if route.startswith("/view/"):
                    relative_path = normalize_relative_path(route.removeprefix("/view/"))
                    self.respond_html(self.build_file_page(relative_path))
                    return

                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            except NotADirectoryError:
                self.send_error(HTTPStatus.NOT_FOUND, "Not a directory")
            except IsADirectoryError:
                self.send_error(
                    HTTPStatus.NOT_FOUND,
                    "Use the directory route for folders",
                )
            except ValueError:
                self.send_error(HTTPStatus.BAD_REQUEST, "Unsupported path")

        def build_directory_page(self, relative_dir: PurePosixPath) -> str:
            directory_path = resolve_content_path(content_dir, relative_dir)
            items = iter_directory_items(content_dir, relative_dir)
            page_title = title if not relative_dir.parts else f"{title} / {relative_dir.as_posix()}"
            return build_index_page(page_title, directory_path, items)

        def build_file_page(self, relative_path: PurePosixPath) -> str:
            source_path = resolve_content_path(content_dir, relative_path)
            if source_path.is_dir():
                raise IsADirectoryError(source_path)

            directory_relative = PurePosixPath(*relative_path.parts[:-1])
            back_href = build_browse_href(directory_relative)
            page_title = relative_path.as_posix()
            kind = describe_path_kind(source_path)

            if "image" in kind:
                return build_page(
                    title=page_title,
                    content="",
                    markdown=False,
                    images=[
                        ImageAsset(
                            source_path=source_path,
                            original_name=source_path.name,
                            mime_type=mimetypes.guess_type(source_path.name)[0] or "image/*",
                            published_href=build_raw_href(relative_path),
                        )
                    ],
                    back_href=back_href,
                )

            content = source_path.read_text(encoding="utf-8", errors="replace")
            return build_page(
                title=page_title,
                content=content,
                markdown=is_markdown_file(source_path),
                images=[],
                back_href=back_href,
                markdown_base_dir=directory_relative,
                markdown_content_dir=content_dir,
            )

        def respond_html(self, body: str) -> None:
            payload = body.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def respond_file(self, file_path: Path) -> None:
            if not file_path.exists() or file_path.is_dir():
                raise FileNotFoundError(file_path)
            payload = file_path.read_bytes()
            mime_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def redirect(self, location: str) -> None:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", location)
            self.end_headers()

        def log_message(self, format: str, *args: object) -> None:
            return

    return ContentHandler
