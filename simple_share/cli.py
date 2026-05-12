import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="simple-share")
    parser.add_argument("text", nargs="*", help="Text to publish")
    parser.add_argument(
        "-m",
        "--markdown",
        action="store_true",
        help="Render markdown",
    )
    parser.add_argument(
        "-f",
        "--file",
        action="append",
        help="Read content from file; repeat for multiple files",
    )
    parser.add_argument(
        "--content-dir",
        help="Serve index from content directory; defaults to $PWD/. in directory mode",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Serve only on localhost without starting cloudflared",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Rebuild ad-hoc shares on refresh without restarting the tunnel",
    )
    return parser.parse_args()
