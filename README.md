# cloud-bz-gz

Tiny reusable script to publish text as a temporary web page through `cloudflared`.

## What it does

- takes text from an argument, stdin, or a file
- creates a temporary HTML page
- serves it locally with `python3`
- exposes it with a temporary `trycloudflare.com` URL

## Requirements

- `cloudflared`
- `python3`

## Usage

```bash
chmod +x ./share-text.sh
```

Pass text directly:

```bash
./share-text.sh "hello from special network"
```

Pass a file:

```bash
./share-text.sh -f ./notes.txt
```

Pass stdin:

```bash
pbpaste | ./share-text.sh
```

Custom port:

```bash
PORT=8899 ./share-text.sh "temporary text"
```

Custom page title:

```bash
TITLE="one-time share" ./share-text.sh "temporary text"
```

## Notes

- the script keeps running while the page is available
- stop it with `Ctrl+C`
- data is served from a temporary directory and removed on exit
