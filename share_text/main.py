import os
import signal
import tempfile
from pathlib import Path

from share_text.app import App
from share_text.cli import parse_args
from share_text.content import (
    build_payload,
    default_title,
    ensure_content_dir,
    require_command,
    resolve_content_dir,
    should_use_content_dir_mode,
    stage_images,
)
from share_text.page import build_page
from share_text.site import build_content_site


def main() -> int:
    args = parse_args()
    require_command("cloudflared")
    require_command("python3")
    port = os.environ.get("PORT", "8787")

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir)
        if should_use_content_dir_mode(args.file, args.text):
            content_dir = resolve_content_dir(args.content_dir)
            ensure_content_dir(content_dir)
            title = os.environ.get("TITLE", "shared content")
            html_file = build_content_site(content_dir, output_dir, title)
        else:
            payload = build_payload(args.file, args.text)
            title = os.environ.get("TITLE", default_title(payload))
            images = stage_images(payload.image_paths, output_dir)
            html_file = output_dir / "index.html"
            html_file.write_text(build_page(title, payload.content, args.markdown, images), encoding="utf-8")

        app = App(html_file, port)
        signal.signal(signal.SIGINT, app.cleanup)
        signal.signal(signal.SIGTERM, app.cleanup)
        app.start_server()
        return app.start_tunnel()
