#!/usr/bin/env bash
set -euo pipefail

# Dev-only counterpart to link-skills.sh. Remove links created for this
# checkout, including broken links left by renamed or deleted skills.
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DESTS=("$HOME/.claude/skills" "$HOME/.agents/skills")

for DEST in "${DESTS[@]}"; do
  # Do not traverse a symlinked destination and risk changing source files.
  if [ -L "$DEST" ]; then
    echo "skipped symlinked skill directory: $DEST" >&2
    continue
  fi
  [ -d "$DEST" ] || continue

  for target in "$DEST"/* "$DEST"/.[!.]* "$DEST"/..?*; do
    [ -L "$target" ] || continue
    src="$(readlink "$target")"

    # Match the absolute targets written by link-skills.sh. Reading the link
    # itself also works when the source skill no longer exists.
    case "$src" in
      "$REPO/skills/"*)
        # A hand-written path containing '..' could point outside the repo.
        case "/$src/" in
          */../*) continue ;;
        esac
        unlink "$target"
        echo "unlinked $target -> $src"
        ;;
    esac
  done
done
