# estate-portal

The WyattAu estate docs portal: **every published crate, rendered nightly
by docs-compiler with full-text search** — deployed to GitHub Pages.

## How it works

1. `scripts/gen_pages.py` fetches the estate manifest
   (`engineering-standards/estate.yml`) and the crates.io API, and emits
   one markdown page per published crate into `content/` plus the site
   config (`content/site.toml`) and a homepage (`content/index.md`).
2. `docs-compiler build content --out _site --base-path /estate-portal`
   renders every page through docs-core with the full chrome (sidebar,
   TOC, breadcrumbs, theme toggle), the SEO/GEO floor (canonical, OG,
   JSON-LD, llms.txt, sitemap, atom, robots), precompression
   (brotli/zstd/gzip sidecars), an RFC 9842 shared dictionary, and a
   client-search corpus (`search.json`) + FST binary index (`search.bin`).
3. GitHub Pages serves `_site` at
   `https://wyattau.github.io/estate-portal/`.

The workflow runs nightly (crates.io metadata refreshes) and on every
push that touches the generator or config.

## Layout

- `scripts/gen_pages.py` — the generator (stdlib only + PyYAML).
- `content/` — generated markdown + site config (gitignored; build output).
- `.github/workflows/deploy-docs.yml` — nightly + push deploy.

## Contract

- The generator is stdlib-plus-PyYAML only; crates.io fair-use rate
  limit honored (1.1 s between calls).
- crates.io API failures on individual crates skip that page with a
  warning; network failures fail the run.
- The portal never mutates the estate manifest — it reads
  `engineering-standards/estate.yml` as the registry of record and
  links back to each crate's repo and docs.rs.
