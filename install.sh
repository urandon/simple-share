#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${HOME}/.bin"
TARGET_PATH="${TARGET_DIR}/simple-share"
SOURCE_PATH="${REPO_ROOT}/bin/simple-share"

mkdir -p "$TARGET_DIR"
ln -sfn "$SOURCE_PATH" "$TARGET_PATH"

printf 'Installed %s -> %s\n' "$TARGET_PATH" "$SOURCE_PATH"
case ":${PATH}:" in
  *":${TARGET_DIR}:"*) ;;
  *)
    printf 'Note: %s is not on PATH yet.\n' "$TARGET_DIR"
    ;;
esac
