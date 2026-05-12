import argparse


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="share-text")
    parser.add_argument("text", nargs="*", help="Text to publish")
    parser.add_argument("-m", "--markdown", action="store_true", help="Render markdown")
    parser.add_argument("-f", "--file", action="append", help="Read content from file; repeat for multiple files")
    parser.add_argument("--content-dir", help="Serve index from content directory; defaults to ./content in directory mode")
    return parser.parse_args()
