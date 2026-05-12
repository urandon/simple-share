# AGENTS.md

## Repo

- Canonical repo path: `/Users/urandon/workspace/tools/simple-share`
- Upstream repo name: `simple-share`
- User-facing entrypoint: `bin/simple-share`
- Convenience installer: `./install.sh`

## Purpose

`simple-share` is a small utility for quickly sharing:

- plain text
- markdown
- screenshots/images
- a browsable directory tree

It can run either:

- locally on `localhost` with `--local-only`
- through `cloudflared` for external access

## Current behavior

### Ad-hoc share mode

Used when text, `-f/--file`, or stdin is provided.

- builds a temporary static page in a temp dir
- supports markdown rendering
- supports screenshot gallery rendering
- serves temp output locally, optionally tunnels with `cloudflared`

### Directory mode

Used when no text/files/stdin are provided.

- default shared root is `$PWD/.`
- `--content-dir PATH` overrides the root
- refresh is live: browser reload re-reads the source tree
- directories are listed and browsable
- symlinked directories are supported
- symlinked files are supported
- image files are served through `/raw/...`
- markdown/text files are rendered on demand

Important nuance:

- if the tool is started with `--content-dir content`, only changes inside that directory show up
- sibling paths outside that chosen root are not included by design

## Key commands

Run from repo:

```bash
./bin/simple-share --local-only
./bin/simple-share
./bin/simple-share -m -f ./report.md
PORT=8899 ./bin/simple-share --local-only
```

Install symlink:

```bash
./install.sh
```

Expected installed command:

```bash
simple-share --local-only
```

## Runtime / dependencies

- Python dependency file: `requirements.txt`
- Project-local virtualenv is expected at `.venv/`
- `bin/simple-share` prefers `repo/.venv/bin/python` automatically if present
- `cloudflared` is required only when not using `--local-only`

Typical setup:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Architecture

- `bin/simple-share`: symlink-friendly shell entrypoint
- `install.sh`: installs `~/.bin/simple-share -> $REPO_ROOT/bin/simple-share`
- `simple_share/main.py`: top-level mode selection and orchestration
- `simple_share/app.py`: in-process HTTP server + tunnel lifecycle
- `simple_share/content.py`: path resolution, content classification, directory scanning
- `simple_share/site.py`: dynamic directory-mode request handler
- `simple_share/page.py`: Jinja-based page rendering
- `simple_share/templates/`: HTML templates
- `simple_share/static/`: CSS + browser JS
- `simple_share/markdown.py`: lightweight markdown rendering

## Important implementation choices

- Directory mode is dynamic, not a startup snapshot.
- Directory mode now uses an in-process HTTP handler instead of spawning `python -m http.server` for generated snapshots.
- One-off text/image mode still uses temp output plus a simple static server.
- Default content root is `$PWD/.`, not the repo-local `content/` directory.
- The old package name `share_text` has been replaced by `simple_share`.

## Known gotchas

- Port `8787` is the default and may already be occupied; set `PORT=8899` or another free port if needed.
- In sandboxed environments, binding a local port may fail even if the code is correct.
- `README.md` may lag behind the newest behavior if a session changed code but did not update docs yet; trust the code first.

## Useful checks

```bash
./bin/simple-share --help
.venv/bin/python -m py_compile simple_share/*.py
```

## Git state expectations

If a new session starts and sees a large rename diff, that is likely from the historical migration:

- `share_text/` -> `simple_share/`
- `simple-share.sh`/`simple-share.py` -> `bin/simple-share`
- repo moved from `~/workspace/ai-processing/cloud-bz-gz` to `~/workspace/tools/simple-share`

That migration is intentional, not stray noise.
