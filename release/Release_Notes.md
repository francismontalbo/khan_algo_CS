# Final edition — 15 October 2026

## Main file

Open `Workflow_Research_Guide.html`. `Workflow_Visual_Comparison.html` is an identical compatibility copy. Start with Algorithms or the initial two-column Kahn comparison. No account, server or software installation is required by the page itself. External source pages and recordings require internet.

## What changed

- Consolidated the latest applications, simulations, lessons, glossary, source audit and comparison tools without changing the computational algorithms.
- Made Kahn versus priority selection the fresh-start comparison. Existing saved selections still load.
- Refined desktop and narrow-screen navigation, button sizing, keyboard focus, active-section highlighting and nested-dialog dismissal.
- Corrected the simulation code highlight so the Kahn decrement step shows the changed indegree rather than the adjacent operation counter.
- Kept definitions, lessons, simulations and presentation styling in standalone comparison exports.
- Corrected current record E34 to LATTICE, arXiv:2607.17422v3, with the current author list and the previous DAN-Scheduler version explicitly preserved. Newer source access is abstract-level, not an implied full-method audit.
- Added a local reproduction entry point, preserved algorithm hashes, and a short verification summary. Historical source snapshots and audit notes remain under `archive`.

## Included collection

58 selectable records; 36 core evidence records (35 external and one local validation record); 249 definitions; 10 algorithm lessons; 63 learning resources (27 video and 36 written); 23 runnable simulations; 33 small scenarios; 23 real-application profiles with 31 application references. Counts describe different collections and must not be summed as independent studies.

## Verification performed in this edition

| Check | Recorded outcome | Boundary |
|---|---|---|
| JavaScript algorithm checks | 8,494 finite checks, no recorded failures | Same engine as the page; not runtime benchmarks. |
| Python proof suite | 5,000 randomized workflows and included exhaustive boundary tests passed | Restricted sequential workflow model; not a proof assistant certificate. |
| Foundational Python suite | 64 forward DAGs, 1,024 insertion cases, 400 randomized DAGs and negative controls passed | Synthetic teaching examples. |
| Application checks | 33 checks passed | Example output, attribution routing and unchanged engine checks. |
| Artifact integrity | 45 checks passed | Embedded records, exports, routes, hash preservation and active document identifiers. |
| Browser checks | 499 of 499 checks passed; no JavaScript errors | Chromium desktop and emulated 320, 390 and 768 px widths; shared paths, not every comparison permutation. |

Raw results are under `tests/final` and the corresponding test subfolders. Screenshots from the final build are in `assets/final`. The computational engine and original Python methods match their saved hashes; only display and review metadata were changed.

## Important remaining limits

This is a curated research and teaching tool. Its literature cutoff is 15 October 2026, not the remainder of 2026. This finishing pass refreshed selected consequential records; it did not repeat all literature searches or audit every paper in full. Abstract-only and version-family labels remain visible.

No real Montage speedup, new scheduling optimum, or cleared historical novelty is claimed. Examples are synthetic unless specifically identified otherwise. Each simulation states its assumptions and whether it represents the exact algorithm or only a limited mechanism. Students still need the complete benchmark inputs and a fair experiment for their own contribution.

External videos were not audited end to end or played back in this environment. Firefox, Safari and physical devices were not tested. Browser policy blocked file-origin navigation, so the HTML contents were loaded locally for interface tests. The page has no required remote scripts; offline content and downloaded-comparison behavior were tested in that mode.

## Reproduce

`python verify.py` runs the delivered algorithm and integrity suites. It needs Python 3.10 or newer, Node.js and NetworkX. Browser tests additionally need Playwright and Chromium. Consult `README.md` for details. Avoid replaying older patch scripts; `release/build_final.py` is the final presentation builder.

Keep a notes export before moving the guide. Browser storage is not a durable backup. The supplied hashes support later integrity checking; they do not establish scientific correctness.
