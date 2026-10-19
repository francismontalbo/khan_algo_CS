# Maintainer checks

Students need only a browser. These checks help maintainers verify the checked-in website and its teaching implementations.

## Set up the test environment

Use Python 3.11 or newer and Node.js 22. CI uses Python 3.12 and Node.js 22 on Ubuntu. The pinned NetworkX version requires Python 3.11 or newer; Python's package installer applies its remaining version constraints.

```bash
python3 -m venv .venv
# macOS or Linux
source .venv/bin/activate
# Windows PowerShell alternative
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

The website has no npm packages to install. Node.js executes the same JavaScript simulation engine that the pages embed.

## Check the packaged site

Run these from the repository root before generating new test reports.

```bash
python tools/check_manifest.py
python tools/check_site.py
python tools/sync_assets.py --check
```

The checks cover the recorded file hashes, local page destinations, portable relative paths, required source/license files, and agreement between editable assets and their embedded HTML copies. They do not validate external links or every literature claim.

After intentionally changing the shipped files, synchronize the editable assets, review the resulting HTML changes, and refresh the checksum manifest.

```bash
python tools/sync_assets.py
python tools/check_manifest.py --write
python tools/check_manifest.py
```

Commit the manifest together with changed source files and synchronized HTML. Keep historical packages and original media intact. Do not replay the old generators from the reference ZIP.

## Verify the algorithms

```bash
python verify.py
```

The entry point checks the browser's JavaScript engine against independent Python/NetworkX oracles. It also runs foundational algorithm checks and workflow equivalence tests, then validates the application examples and artifact integrity. Generated reports go into the corresponding `tests/` subdirectories. The console identifies each suite and returns a failing exit status if a suite fails.

To run only the workflow equivalence suite with Python's standard library, use a separate output path so the shipped historical result stays intact.

```bash
python code/run_checks.py --cases 5000 --out output/ci/proof_checks.json
```

The suites use finite synthetic inputs, including small application-shaped teaching examples. Passing them supports the declared models and tested cases; research novelty and production benefits need separate evidence. The tests cannot establish correctness outside their declared assumptions.

## Exercise the browser interface

Install the separate browser test dependency and Chromium.

```bash
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
python tools/check_browser.py --require-http --out output/ci/browser-checks.json
```

On a Linux CI runner, install Chromium's system dependencies with `python -m playwright install --with-deps chromium`. An existing Chromium executable can be selected through `CHROMIUM_PATH`.

The script starts a temporary local HTTP server and exercises the main application routes and comparison views. It checks responsive layouts and note import/export while stepping through simulations. It records JavaScript errors and reports its coverage limits. The `--require-http` flag makes an unavailable local HTTP route fail the run. Without that flag, the script may test local HTML contents and disclose that fallback in its report.

For screenshots during visual review, add `--screenshots output/ci/screenshots`. The smoke tests use Chromium and leave external video playback and a live GitHub Pages deployment unverified. Other browser engines and physical devices need separate checks.

HTTP success does not verify a browser's handling of local `file:` URLs. Also open the downloaded `index.html` manually and exercise the primary routes when reviewing offline distribution.

## Continuous integration

[The Checks workflow](.github/workflows/checks.yml) runs the static and algorithm suites alongside a Chromium smoke job on every push and pull request. It also supports manual dispatch. It checks the manifest before tests write fresh results, requires a working local HTTP route in browser tests, and uploads available JSON reports as workflow artifacts. The workflow has read-only repository permissions and no deployment step.

The pins in [requirements-dev.txt](requirements-dev.txt) and [requirements-browser.txt](requirements-browser.txt) record the maintainer test dependencies. Update them deliberately and rerun the full checks when changing versions.

## Research freshness

The retained literature snapshot and its coverage limits are dated 15 October 2026. Packaging and interface checks do not refresh that research. Recheck the closest papers and implementation versions before a student makes a novelty claim.
