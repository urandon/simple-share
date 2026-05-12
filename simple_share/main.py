import os
import signal
import tempfile
from pathlib import Path

from simple_share.adhoc import AdHocConfig, build_adhoc_handler
from simple_share.app import App
from simple_share.assets import publish_static_assets
from simple_share.cli import parse_args
from simple_share.content import (
    build_payload,
    default_title,
    ensure_content_dir,
    require_command,
    resolve_content_dir,
    should_use_content_dir_mode,
    stage_images,
)
from simple_share.page import build_page
from simple_share.site import build_content_handler

STATIC_DIR = Path(__file__).resolve().parent / "static"


def main() -> int:
    args = parse_args()
    require_command("python3")
    if not args.local_only:
        require_command("cloudflared")
    port = os.environ.get("PORT", "8787")

    if should_use_content_dir_mode(args.file, args.text):
        content_dir = resolve_content_dir(args.content_dir)
        ensure_content_dir(content_dir)
        title = os.environ.get("TITLE", "shared content")
        handler = build_content_handler(content_dir, title, STATIC_DIR)
        app = App(port=port, request_handler_class=handler)
        signal.signal(signal.SIGINT, app.cleanup)
        signal.signal(signal.SIGTERM, app.cleanup)
        app.start_server()
        if args.local_only:
            return app.serve_local()
        return app.start_tunnel()

    if args.reload:
        title = os.environ.get("TITLE")
        handler = build_adhoc_handler(
            AdHocConfig(
                file_paths=args.file,
                text_args=args.text,
                markdown=args.markdown,
                title=title,
            )
        )
        app = App(port=port, request_handler_class=handler)
        signal.signal(signal.SIGINT, app.cleanup)
        signal.signal(signal.SIGTERM, app.cleanup)
        app.start_server()
        if args.local_only:
            return app.serve_local()
        return app.start_tunnel()

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        publish_static_assets(output_dir)
        payload = build_payload(args.file, args.text)
        title = os.environ.get("TITLE", default_title(payload))
        images = stage_images(payload.image_paths, output_dir)
        html_file = output_dir / "index.html"
        html = build_page(title, payload.content, args.markdown, images)
        html_file.write_text(html, encoding="utf-8")

        app = App(port=port, serve_dir=output_dir)
        signal.signal(signal.SIGINT, app.cleanup)
        signal.signal(signal.SIGTERM, app.cleanup)
        app.start_server()
        if args.local_only:
            return app.serve_local()
        return app.start_tunnel()
