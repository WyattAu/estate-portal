# AGENTS.md — operating contract for estate-portal

The WyattAu estate docs portal: every published crate, rendered nightly
by docs-compiler (the estate's own static-site generator) and deployed
to GitHub Pages.

## The loop

`scripts/gen_pages.py` reads the estate manifest
(`engineering-standards/estate.yml`, fetched from `main`) and the
crates.io API, emits `content/` (markdown + site config), then
`docs-compiler build content --out _site --base-path /estate-portal`
renders and wraps every page in the estate chrome with the full
SEO/GEO floor. `deploy-docs.yml` runs the loop nightly and on push;
GitHub Pages serves `_site`.

## Rules

1. The generator is stdlib + PyYAML only — no third-party Python deps.
   The site build tooling is the published `docs-compiler` crate;
   never vendor it.
2. crates.io fair-use: ≥ 1.1 s between API calls; a 404 for a
   registered name means "not yet published" — skip with a warning,
   never fail the run.
3. The portal reads `estate.yml` as the registry of record and never
   mutates it. Corrections land in
   `engineering-standards` (or the owning repo), then flow here
   naturally on the next nightly.
4. Determinism: same registry + same crates.io state → same bytes.
   Don't add timestamps or random ordering to emitted pages.
5. Unpublished or renamed crates: skipped pages are listed in the run
   summary. The estate-audit gate (in engineering-standards) is the
   authority on registry accuracy, not this portal.
