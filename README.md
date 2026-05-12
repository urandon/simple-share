# cloud-bz-gz

Tiny reusable script to publish text, Markdown, screenshots, or a browsable content directory through either `localhost` or `cloudflared`.

## What it does

- takes text from an argument, stdin, or a file
- optionally renders Markdown to HTML in the browser
- can publish one or more local screenshots/images
- can serve a small index site from a local content directory
- can copy rendered rich text as `text/html` for pasting into Confluence
- serves the page locally with `python3`
- can expose it with a temporary `trycloudflare.com` URL

## Requirements

- `cloudflared` for external sharing
- `python3`
- `Jinja2` Python package: `python3 -m pip install -r requirements.txt`

## Usage

```bash
chmod +x ./share-text.sh
```

`share-text.sh` is a thin wrapper around `share-text.py`.
If a repo-local `.venv` exists, both entrypoints prefer it automatically.

Start directory mode:

```bash
./share-text.sh
```

By default this serves the repo-local `./content` directory as an index page.

Start local-only mode for faster layout work:

```bash
./share-text.sh --local-only
```

This keeps the site on `http://127.0.0.1:$PORT` and does not start `cloudflared`.

Pass plain text directly:

```bash
./share-text.sh "hello from special network"
```

Pass Markdown directly:

```bash
./share-text.sh -m "# Weekly Report"
```

Pass a file:

```bash
./share-text.sh -f ./notes.txt
```

Pass a Markdown file:

```bash
./share-text.sh -m -f ./report.md
```

Pass a screenshot:

```bash
./share-text.sh -f ~/Desktop/screenshot.png
```

Pass multiple screenshots:

```bash
./share-text.sh -f ~/Desktop/step-1.png -f ~/Desktop/step-2.png
```

Pass stdin:

```bash
pbpaste | ./share-text.sh
```

Pass Markdown via stdin:

```bash
cat ./report.md | ./share-text.sh -m
```

Custom port:

```bash
PORT=8899 ./share-text.sh "temporary text"
```

Custom page title:

```bash
TITLE="one-time share" ./share-text.sh "temporary text"
```

Custom content directory:

```bash
./share-text.sh --content-dir ~/shared-drop
```

## Markdown mode

In Markdown mode the page shows:

- rendered HTML preview
- `Copy rich text` button for `text/html` clipboard copy
- `Copy markdown` button for raw Markdown copy
- collapsible source view

This is intended for quick paste into tools like Confluence.

## Screenshot mode

If you pass image files (`png`, `jpg`, `jpeg`, `gif`, `webp`, etc.) with `-f`, the page shows them as a responsive gallery.

- click an image to open it full size
- you can mix text and screenshots in the same page
- if only screenshots are passed, the default page title becomes `shared screenshots`

## Directory mode

If you run `./share-text.sh` with no arguments, the tool serves an index page from `./content`.

- drop `.md`, screenshots, and text files into `./content`
- open the shared root URL to see the index
- click any entry to open its own page
- nested folders are supported and show up in the index
- `content/` is ignored by git by default except for `.gitkeep`

## Local-only mode

If you add `--local-only`, the tool serves the same content on localhost without starting a tunnel.

- useful for faster HTML/CSS iteration
- works with plain text, markdown, screenshots, and directory mode
- `cloudflared` is not required in this mode

## Notes

- the script keeps running while the page is available
- stop it with `Ctrl+C`
- data is served from a temporary directory and removed on exit
- Markdown rendering is intentionally lightweight, not a full Markdown engine

## Layout

- `share-text.sh`: shell wrapper
- `share-text.py`: Python entrypoint
- `share_text/cli.py`: argument parsing
- `share_text/content.py`: input loading and image staging
- `share_text/site.py`: content-directory site generation
- `share_text/markdown.py`: lightweight Markdown rendering
- `share_text/page.py`: template rendering and page composition
- `share_text/templates/`: HTML templates
- `share_text/static/`: CSS and browser-side JS
- `requirements.txt`: Python template dependency
- `share_text/app.py`: local server and `cloudflared` lifecycle
- `share_text/main.py`: orchestration
