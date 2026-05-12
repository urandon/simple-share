import subprocess
import time
from pathlib import Path


class App:
    def __init__(self, html_file: Path, port: str) -> None:
        self.html_file = html_file
        self.port = port
        self.server: subprocess.Popen[str] | None = None
        self.tunnel: subprocess.Popen[str] | None = None

    def cleanup(self, *_args: object) -> None:
        for process in (self.tunnel, self.server):
            if process and process.poll() is None:
                process.terminate()
        raise SystemExit(0)

    def start_server(self) -> None:
        self.server = subprocess.Popen(
            ["python3", "-m", "http.server", self.port, "--directory", str(self.html_file.parent)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        time.sleep(1)

    def start_tunnel(self) -> int:
        print(f"Serving on http://127.0.0.1:{self.port}")
        print("Press Ctrl+C to stop.\n")
        self.tunnel = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://127.0.0.1:{self.port}"],
            text=True,
        )
        return self.tunnel.wait()
