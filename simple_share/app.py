import subprocess
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import Any


class App:
    def __init__(
        self,
        port: str,
        serve_dir: Path | None = None,
        request_handler_class: type[Any] | None = None,
    ) -> None:
        self.port = port
        self.serve_dir = serve_dir
        self.request_handler_class = request_handler_class
        self.httpd: ThreadingHTTPServer | None = None
        self.server_thread: Thread | None = None
        self.tunnel: subprocess.Popen[str] | None = None

    def cleanup(self, *_args: object) -> None:
        if self.tunnel and self.tunnel.poll() is None:
            self.tunnel.terminate()
        if self.httpd is not None:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self.server_thread is not None and self.server_thread.is_alive():
            self.server_thread.join(timeout=1)
        raise SystemExit(0)

    def start_server(self) -> None:
        try:
            handler: Any
            if self.request_handler_class is not None:
                handler = self.request_handler_class
            elif self.serve_dir is not None:
                handler = partial(SimpleHTTPRequestHandler, directory=str(self.serve_dir))
            else:
                raise RuntimeError("No content source configured for server")
            self.httpd = ThreadingHTTPServer(("127.0.0.1", int(self.port)), handler)
        except OSError:
            raise SystemExit(
                f"Failed to start local server on port {self.port}. "
                "Set PORT to a free port and try again."
            )
        self.server_thread = Thread(target=self.httpd.serve_forever, daemon=True)
        self.server_thread.start()
        time.sleep(0.1)

    def start_tunnel(self) -> int:
        print(f"Serving on http://127.0.0.1:{self.port}")
        print("Press Ctrl+C to stop.\n")
        self.tunnel = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{self.port}"],
            text=True,
        )
        return self.tunnel.wait()

    def serve_local(self) -> int:
        print(f"Serving locally on http://127.0.0.1:{self.port}")
        print("Local-only mode; cloudflared is disabled.")
        print("Press Ctrl+C to stop.\n")
        if self.server_thread is None:
            raise RuntimeError("Server was not started")
        self.server_thread.join()
        return 0
