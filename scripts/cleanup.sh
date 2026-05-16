#!/usr/bin/env sh
set -eu

APPLY=0
if [ "${1:-}" = "--apply" ]; then
  APPLY=1
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)

TARGETS="
backend.log
.ruff_cache
htmlcov
node_modules
frontend/node_modules
frontend/.next
frontend/.swc
frontend/tsconfig.tsbuildinfo
shared/dist
"

PY_CACHE_TARGETS=$(find "$REPO_ROOT" -type d -name "__pycache__" -prune 2>/dev/null || true)

FOUND=0
printf '%s\n' "Cleanup targets:"

for target in $TARGETS; do
  path="$REPO_ROOT/$target"
  if [ -e "$path" ]; then
    FOUND=1
    printf ' - %s\n' "$path"
  fi
done

for path in $PY_CACHE_TARGETS; do
  case "$path" in
    "$REPO_ROOT"/*)
      FOUND=1
      printf ' - %s\n' "$path"
      ;;
    *)
      printf '%s\n' "Refusing path outside repo: $path" >&2
      exit 1
      ;;
  esac
done

if [ "$FOUND" -eq 0 ]; then
  printf '%s\n' "No cleanup targets found."
  exit 0
fi

if [ "$APPLY" -eq 0 ]; then
  printf '\n%s\n' "Dry run only. Re-run with --apply to delete these generated local artifacts."
  exit 0
fi

for target in $TARGETS; do
  path="$REPO_ROOT/$target"
  if [ -e "$path" ]; then
    case "$path" in
      "$REPO_ROOT"/*) rm -rf -- "$path" ;;
      *)
        printf '%s\n' "Refusing path outside repo: $path" >&2
        exit 1
        ;;
    esac
  fi
done

for path in $PY_CACHE_TARGETS; do
  if [ -e "$path" ]; then
    case "$path" in
      "$REPO_ROOT"/*) rm -rf -- "$path" ;;
      *)
        printf '%s\n' "Refusing path outside repo: $path" >&2
        exit 1
        ;;
    esac
  fi
done

printf '%s\n' "Cleanup complete."
