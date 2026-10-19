# Workflow Algorithm Research Guide

A browser-based teaching and research guide for graph algorithms and workflow scheduling, starting with Kahn's topological sort. Compare methods and step through executable examples with the assumptions and sources behind each record.

The repository name retains its original spelling, `khan_algo_CS`. The algorithm is named after Arthur B. Kahn.

## Open the guide

Clone or download this repository, then open [index.html](index.html) in a modern browser. The checked-in files are ready to use; there is no build step or archive to extract after cloning. External papers and recordings require internet access.

For a local HTTP preview, run this command from the repository root and open the [local preview](http://localhost:8000/).

```bash
python3 -m http.server 8000
```

To publish the guide for a class, follow [DEPLOY.md](DEPLOY.md). GitHub's repository file viewer displays source files; GitHub Pages serves the interactive website.

## Explore

| Page | What you can do |
| --- | --- |
| [Research guide](Workflow_Research_Guide.html) | Compare method records, inspect code and evidence, and save a comparison or notes. |
| [Algorithm lessons](Algorithm_Lessons.html) | Study explanations and invariants with worked examples and source links. |
| [Simulations](Algorithm_Simulations.html) | Step through 23 teaching implementations of graph algorithms and scheduling mechanisms. |
| [Applications](Algorithm_Applications.html) | Connect the algorithms to application profiles with stated assumptions. |
| [Learning resources](Workflow_Learning_Resources.html) | Find linked lectures and written tutorials. |
| [Terms and nomenclature](Workflow_Terms_and_Nomenclature.html) | Look up definitions and related concepts. |
| [Verification](Verification.html) and [source audit](Audit_Report.html) | Review the recorded checks and evidence limits. |

`Workflow_Visual_Comparison.html` remains an identical compatibility entry for the main research guide.

## Save your work

Notes and selections use the current browser's storage where available. Export notes before changing devices or clearing browser data, and keep a copy before moving the project. Import the saved file to restore them. The guide has no accounts or shared notes service, and a GitHub upload does not synchronize browser storage. See [NOTICE.md](NOTICE.md) for privacy and attribution details.

## Maintain the project

The site runs JavaScript in static HTML pages with CSS. Python and Node.js support maintainer checks; students do not need them to open the downloaded guide.

| Location | Purpose |
| --- | --- |
| `index.html` and root `*.html` pages | Ready-to-open application and companion pages. |
| `code/`, `simulations/`, `applications/`, `release/` | Editable application assets and release records. |
| `data/` | Structured method and learning records with evidence metadata. |
| `tools/` | Asset synchronization and site/browser checks. |
| `tests/` | Algorithm tests and verification reports. |
| `archive/` and `reference/` | Preserved source snapshots and the original research package. |

The HTML pages embed their modules and data so the teaching material can work offline. After editing the corresponding source modules or JSON data, synchronize the embedded copies and review the changes.

```bash
python3 tools/sync_assets.py
python3 tools/sync_assets.py --check
python3 tools/check_site.py
python3 tools/check_manifest.py --write
python3 tools/check_manifest.py
```

[TESTING.md](TESTING.md) explains the full algorithm suite and Chromium checks. The [Checks workflow](.github/workflows/checks.yml) runs them on pushes and pull requests and uploads their reports. It does not publish the site.

Keep original packages and historical reports intact. The root `Workflow_Research_Guide_Local_Use.zip` and `reference/Original_Research_Package.zip` preserve earlier deliveries; use the checked-in working files for current changes. Historical setup notes may describe earlier packaging decisions. [DEPLOY.md](DEPLOY.md) and [TESTING.md](TESTING.md) contain the current operating instructions.

## Evidence and reuse

The retained literature snapshot is dated 15 October 2026. The automated suites check finite synthetic cases and internal consistency under the models declared in the guide. Research novelty and production speedups need separate evidence, and the examples do not establish scheduling optimality. Recheck the original papers and implementation versions before making a novelty claim.

See [source attribution](code/SOURCE_ATTRIBUTION.md) for the third-party code excerpts and their [Apache 2.0 license](code/APACHE-2.0.txt). The repository does not assign a blanket license to the owner's original material or to linked publications.
