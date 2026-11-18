#!/usr/bin/env python3
"""Estate portal generator: registry + crates.io -> markdown for docs-compiler.

Reads the estate manifest (estate.yml from engineering-standards) and the
crates.io API, then emits one markdown page per published crate plus a
homepage and the site config that docs-compiler's `build` subcommand
consumes. Deterministic: same registry + same crates.io state -> same
bytes, so nightly runs diff cleanly.
"""

import json
import sys
import time
import urllib.request
from pathlib import Path

import yaml

UA = "estate-portal/0.1 (wyatt_au@protonmail.com)"
CRATES_API = "https://crates.io/api/v1/crates"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content"
ESTATE_YML = "https://raw.githubusercontent.com/WyattAu/engineering-standards/main/estate.yml"

SITE = {
    "base_url": "https://wyattau.github.io/estate-portal",
    "base_path": "/estate-portal",
    "site_title": "WyattAu Estate",
    "author": "Wyatt",
    "ai_crawlers": "allow",
    "og_image": "https://wyattau.github.io/estate-portal/og.png",
}


def fetch(url: str, ok404: bool = False) -> bytes | None:
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as err:
        if ok404 and err.code == 404:
            return None
        raise
    except urllib.error.URLError as err:
        raise SystemExit(f"network error fetching {url}: {err.reason}") from err


def load_manifest() -> dict:
    raw = fetch(ESTATE_YML)
    return yaml.safe_load(raw.decode())


def collect_crates(manifest: dict) -> list[dict]:
    """Walk repos -> crates, carrying area + status from the repo entry."""
    crates: list[dict] = []
    for name, repo in sorted((manifest.get("repos") or {}).items()):
        if not isinstance(repo, dict):
            continue
        area = repo.get("area", "")
        status = repo.get("status", "")
        for crate in repo.get("crates") or []:
            if isinstance(crate, str) and crate.strip():
                crates.append(
                    {"name": crate.strip(), "repo": name, "area": area, "status": status}
                )
    return crates


def crate_meta(name: str) -> dict | None:
    raw = fetch(f"{CRATES_API}/{name}", ok404=True)
    if raw is None:
        return None
    payload = json.loads(raw)
    return payload.get("crate")


def main() -> None:
    manifest = load_manifest()
    crates = collect_crates(manifest)
    print(f"registry: {len(crates)} crate names")

    OUT.mkdir(parents=True, exist_ok=True)
    published: list[dict] = []
    skipped: list[str] = []

    for crate in crates:
        name = crate["name"]
        meta = crate_meta(name)
        if meta is None:
            skipped.append(name)  # registered but not yet published
            continue
        entry = {
            "name": name,
            "version": meta.get("max_version", ""),
            "description": (meta.get("description") or "").strip(),
            "repository": meta.get("repository") or "",
            "documentation": meta.get("documentation") or "",
            "updated_at": (meta.get("updated_at") or "")[:10],
            "area": crate["area"],
            "status": crate["status"],
        }
        page = render_crate_page(entry)
        (OUT / f"{name}.md").write_text(page, encoding="utf-8")
        published.append(entry)
        time.sleep(1.1)  # crates.io fair-use

    # index.md: the portal homepage, grouped by area.
    by_area: dict[str, list[dict]] = {}
    for entry in published:
        by_area.setdefault(entry["area"] or "misc", []).append(entry)
    lines = [
        "---",
        "title: WyattAu Estate",
        f"description: {len(published)} published crates across the WyattAu estate.",
        "slug: index",
        "---",
        "",
        "# WyattAu Estate",
        "",
        f"{len(published)} published crates in {len(by_area)} areas, "
        "indexed nightly from the estate registry.",
        "",
    ]
    for area in sorted(by_area):
        lines.append(f"## {area}")
        lines.append("")
        for entry in sorted(by_area[area], key=lambda e: e["name"]):
            lines.append(f"- [{entry['name']}](/{entry['name']}.html) — {entry['description'][:100]}")
        lines.append("")
    (OUT / "index.md").write_text("\n".join(lines), encoding="utf-8")

    # site config for docs-compiler (base_path = project Pages subpath).
    config_lines = [f"{k} = {json.dumps(v)}" for k, v in SITE.items()]
    config_lines.append(f"base_path = {json.dumps('/estate-portal')}")
    (OUT / "site.toml").write_text("\n".join(config_lines) + "\n", encoding="utf-8")

    print(f"published pages: {len(published)}, skipped (unpublished): {len(skipped)}")
    if skipped:
        print("skipped crates:", ", ".join(sorted(skipped)[:20]))


def render_crate_page(entry: dict) -> str:
    links = f"- crates.io: https://crates.io/crates/{entry['name']}\n"
    if entry["documentation"]:
        links += f"- docs.rs: {entry['documentation']}\n"
    if entry["repository"]:
        links += f"- repository: {entry['repository']}\n"
    return (
        "---\n"
        f"title: {entry['name']}\n"
        f"description: {entry['description'][:155]}\n"
        f"date: {entry['updated_at']}\n"
        "---\n\n"
        f"# {entry['name']}\n\n"
        f"{entry['description']}\n\n"
        f"- version: {entry['version']}\n"
        f"- area: {entry['area']}\n"
        f"- estate status: {entry['status']}\n\n"
        "## Links\n\n"
        f"{links}\n"
        "Part of the [WyattAu estate](/index.html).\n"
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
