#!/usr/bin/env python3
"""Ensure tokens.json logoURI entries resolve to files under the repo root."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Local assets are published at this GitHub Pages prefix; paths after it mirror the repo root.
LOGO_URI_PREFIX = "https://ovafi.github.io/public-assets/"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def relative_asset_path(logo_uri: str) -> str | None:
    if not logo_uri.startswith(LOGO_URI_PREFIX):
        return None
    rest = logo_uri[len(LOGO_URI_PREFIX) :].split("?")[0].split("#")[0]
    if not rest or rest.startswith("/"):
        return None
    # Normalize away accidental duplicate slashes in JSON
    return str(Path(rest))


def collect_logo_uris(data: object) -> list[tuple[str, str]]:
    """Return list of (json_pointer_context, logo_uri)."""
    found: list[tuple[str, str]] = []
    if not isinstance(data, dict):
        return found
    root_logo = data.get("logoURI")
    if isinstance(root_logo, str):
        found.append(("logoURI", root_logo))
    tokens = data.get("tokens")
    if isinstance(tokens, list):
        for i, tok in enumerate(tokens):
            if isinstance(tok, dict):
                u = tok.get("logoURI")
                if isinstance(u, str):
                    found.append((f"tokens[{i}].logoURI", u))
    return found


def main() -> int:
    root = repo_root()
    path = root / "tokens.json"
    if not path.is_file():
        print(f"verify-token-assets: missing {path}", file=sys.stderr)
        return 1
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"verify-token-assets: invalid JSON in tokens.json: {e}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for ctx, uri in collect_logo_uris(data):
        rel = relative_asset_path(uri)
        if rel is None:
            continue
        target = (root / rel).resolve()
        try:
            target.relative_to(root.resolve())
        except ValueError:
            errors.append(f"{ctx}: path escapes repo root ({uri})")
            continue
        if not target.is_file():
            errors.append(f"{ctx}: missing file {rel} (from {uri})")

    if errors:
        print("verify-token-assets: token asset check failed:", file=sys.stderr)
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
