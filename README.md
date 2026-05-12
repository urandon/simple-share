# simple-share

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
chmod +x ./bin/simple-share ./install.sh
```

`bin/simple-share` is the user-facing entrypoint.
If a repo-local `.venv` exists, it is picked automatically.

Install a convenient symlink into `~/.bin`:

```bash
./install.sh
```

Start directory mode:

```bash
./bin/simple-share
```

By default this serves `$PWD/.` as an index page.

Start local-only mode for faster layout work:

```bash
./bin/simple-share --local-only
```

This keeps the site on `http://127.0.0.1:$PORT` and does not start `cloudflared`.

Pass plain text directly:

```bash
./bin/simple-share "hello from special network"
```

Pass Markdown directly:

```bash
./bin/simple-share -m "# Weekly Report"
```

Pass a file:

```bash
./bin/simple-share -f ./notes.txt
```

Pass a Markdown file:

```bash
./bin/simple-share -m -f ./report.md
```

Pass a screenshot:

```bash
./bin/simple-share -f ~/Desktop/screenshot.png
```

Pass multiple screenshots:

```bash
./bin/simple-share -f ~/Desktop/step-1.png -f ~/Desktop/step-2.png
```

Pass stdin:

```bash
pbpaste | ./bin/simple-share
```

Pass Markdown via stdin:

```bash
cat ./report.md | ./bin/simple-share -m
```

Custom port:

```bash
PORT=8899 ./bin/simple-share "temporary text"
```

Custom page title:

```bash
TITLE="one-time share" ./bin/simple-share "temporary text"
```

Custom content directory:

```bash
./bin/simple-share --content-dir ~/shared-drop
```

Installed usage from any directory:

```bash
simple-share --local-only
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

If you run `./bin/simple-share` with no arguments, the tool serves an index page from `$PWD/.`.

- run it inside the folder you want to share
- or point it elsewhere with `--content-dir`
- open the shared root URL to see the index
- click any entry to open its own page
- nested folders are supported and browsable
- symlinked directories and files are supported
- browser refresh re-reads the source tree, so new entries show up without restart
- `content/` is ignored by git by default except for `.gitkeep`

## Local-only mode

If you add `--local-only`, the tool serves the same content on localhost without starting a tunnel.

- useful for faster HTML/CSS iteration
- works with plain text, markdown, screenshots, and directory mode
- `cloudflared` is not required in this mode

## Notes

- the script keeps running while the page is available
- stop it with `Ctrl+C`
- ad-hoc text/image mode is served from a temporary directory and removed on exit
- directory mode is rendered live from the chosen source tree on each request
- Markdown rendering is intentionally lightweight, not a full Markdown engine

## Layout

- `bin/simple-share`: shell entrypoint
- `install.sh`: symlink installer for `~/.bin/simple-share`
- `simple_share/cli.py`: argument parsing
- `simple_share/content.py`: input loading and image staging
- `simple_share/site.py`: content-directory site generation
- `simple_share/markdown.py`: lightweight Markdown rendering
- `simple_share/page.py`: template rendering and page composition
- `simple_share/templates/`: HTML templates
- `simple_share/static/`: CSS and browser-side JS
- `requirements.txt`: Python template dependency
- `simple_share/app.py`: local server and `cloudflared` lifecycle
- `simple_share/main.py`: orchestration
