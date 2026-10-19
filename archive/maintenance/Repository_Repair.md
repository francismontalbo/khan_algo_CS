# Repository repair — 19 October 2026

The repository contained a homepage, deployment instructions and an uploaded ZIP,
but the homepage's destination pages were still inside that ZIP. GitHub Pages
cannot serve files within an archive. The complete application, editable modules,
data, attribution and maintainer tools are now checked in at the repository root.
The uploaded ZIP remains byte-for-byte unchanged.

## Maintenance corrections

- Added `.nojekyll` for branch-based static hosting and a local favicon.
- Replaced the deployment-only README with project documentation; retained and
  updated the hosting instructions in `DEPLOY.md`.
- Corrected simulator dictionaries so valid task names such as `toString`,
  `valueOf` and `hasOwnProperty` work in graph traversal, dependency checks,
  reductions and the displayed intermediate state.
- Normalized imported and stored comparison state before rendering. Invalid
  layout and method identifiers recover safely while valid draft fields survive.
- Fixed ignore rules so the integrity test is included in a fresh checkout.
- Added checksum verification and CI for packaging, embedded assets, algorithms
  and actual HTTP browser navigation. Local dependencies and private exports are
  excluded from distribution checks.

The original hash records remain unchanged. Integrity checks verify the retained
original source inside `reference/Original_Research_Package.zip`, distinguish the
maintained simulator from that baseline, and verify that the Python algorithms
still match their originals. The current repository manifest is `SHA256SUMS.json`.

## Verification

The maintenance checks passed locally: 8,518 JavaScript/oracle cases, the
5,000-workflow Python suite with its exhaustive and negative controls, foundational
Python checks, 35 application checks and 47 artifact-integrity checks. All 204
browser checks passed over HTTP, covering comparison views, lessons, all
simulations, saved exports, malformed notes recovery, local resources and
320–1440 px layouts. See `TESTING.md` to reproduce
the checks and the pull request's CI artifacts for subsequent runs.

Desktop and mobile Chromium screenshots were visually inspected. These checks
do not establish runtime speedups, new research findings, complete external-link
availability, or compatibility with every browser. The literature snapshot remains
15 October 2026. Earlier reports and release notes retain their original scope;
this document records the subsequent repository repair.
