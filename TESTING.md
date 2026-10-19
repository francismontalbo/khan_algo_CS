# Testing

Students can open `index.html` in a browser; no installation is needed. The commands below are optional maintainer checks for the website and its teaching implementations.

## Set up the test environment

Maintainer checks use a Git checkout with Python 3.11 or newer and Node.js 22. CI uses Python 3.12 and Node.js 22 on Ubuntu. Reuse an existing test environment, or create one from the repository root:

```bash
python3 -m venv .venv
# macOS or Linux
source .venv/bin/activate
# Windows PowerShell alternative
# .venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
```

The website has no npm packages to install. The pinned dependency in `requirements-dev.txt` is only for testing; Node.js runs the JavaScript engine embedded in the pages.

## Check the packaged site

Run these from the repository root before generating new test reports.

```bash
python tools/check_manifest.py
python tools/check_site.py --out output/ci/static-checks.json
python tools/sync_assets.py --check
python tools/build_thesis.py --check
python verify.py
```

Check the recorded hashes first, before producing new reports. The other checks cover local page destinations, portable paths, required source/license files, embedded assets, and the algorithm suites described below. They do not validate external links or every literature claim.

After intentionally changing the shipped files, synchronize the editable assets, review the resulting HTML changes, and refresh the checksum manifest.

```bash
python tools/sync_assets.py
python tools/check_manifest.py --write
python tools/check_manifest.py
```

Commit the manifest together with changed source files and synchronized HTML. Keep historical packages and original media intact. Do not replay the old generators from the reference ZIP.

## Verify the algorithms

The `python verify.py` command above checks the browser's JavaScript engine against independent Python/NetworkX oracles, foundational algorithms, workflow equivalence, application examples, and artifact integrity. It returns a failing exit status if a suite fails.

Fresh reports go into the ignored `output/ci/` directory as `simulations-checks.json`, `algorithm-lessons-checks.json`, `proof-checks.json`, `applications-checks.json`, and `integrity-checks.json`. Use `python verify.py --out-dir output/my-run` to choose another directory. Each individual report script also accepts `--out` and creates its parent directory. Historical reports remain under `archive/verification/`.

To run only the workflow equivalence suite with Python's standard library:

```bash
python code/run_checks.py --cases 5000
```

The suites use finite synthetic inputs, including small application-shaped teaching examples. Passing them supports the declared models and tested cases; research novelty and production benefits need separate evidence. The tests cannot establish correctness outside their declared assumptions.

## Exercise the browser interface

Install the separate browser test dependency and Chromium.

```bash
python -m pip install -r requirements-browser.txt
python -m playwright install chromium
python tools/check_browser.py --require-http
python tools/check_math.py --out output/ci/math-checks.json
python tools/check_setup.py
python tools/check_thesis.py
```

On a Linux CI runner, install Chromium's system dependencies with `python -m playwright install --with-deps chromium`. An existing Chromium executable can be selected through `CHROMIUM_PATH`.

The equation suite checks strict LaTeX parsing, lesson formulas, simulator steps,
glossary symbols, narrow layouts and offline HTML exports. KaTeX and its fonts are
bundled locally. Edit `code/math-catalog.json` or `code/math-reference.json` to
maintain notation, then run `tools/sync_assets.py` to update the HTML copies.

The script starts a temporary local HTTP server and exercises the main application routes and comparison views. It checks responsive layouts and note import/export while stepping through simulations. It records JavaScript errors and reports its coverage limits. The `--require-http` flag makes an unavailable local HTTP route fail the run. Without that flag, the script may test local HTML contents and disclose that fallback in its report.

The browser report defaults to `output/ci/browser-checks.json`. For screenshots during visual review, add `--screenshots output/ci/screenshots`. The smoke tests use Chromium and leave external video playback and a live GitHub Pages deployment unverified. Other browser engines and physical devices need separate checks.

HTTP success does not verify a browser's handling of local `file:` URLs. Also open the downloaded `index.html` manually and exercise the primary routes when reviewing offline distribution.

The setup check tests the committed `HEAD` as a ZIP download. It extracts that
archive into a path containing spaces, opens `index.html` offline and follows the
lesson and simulation controls. Commit changes before running this check so it
tests the files students will receive. Its report is `output/ci/setup-checks.json`.

## Continuous integration

[The Checks workflow](.github/workflows/checks.yml) runs the static and algorithm suites alongside a Chromium smoke job on every push and pull request. It also supports manual dispatch. It checks the manifest before generating algorithm reports, requires a working local HTTP route in browser tests, and uploads fresh reports from `output/ci/` as workflow artifacts. The workflow has read-only repository permissions and no deployment step.

The pins in [requirements-dev.txt](requirements-dev.txt) and [requirements-browser.txt](requirements-browser.txt) record the maintainer test dependencies. Update them deliberately and rerun the full checks when changing versions.

## Research freshness

The retained literature snapshot and its coverage limits are dated 15 October 2026. Packaging and interface checks do not refresh that research. Recheck the closest papers and implementation versions before a student makes a novelty claim.

## Maintain the thesis research library

The additive library is maintained in `data/Thesis_Research.json`, with presentation
sources in `code/thesis.css` and `code/thesis.js`. After verifying primary paper
records and updating the dated search audit, regenerate its offline page and
BibTeX references:

```bash
python tools/build_thesis.py
python tools/build_thesis.py --check
python tools/check_thesis.py
python tools/check_manifest.py --write
```

The builder validates source IDs, publication status, reference links and metadata.
The browser check covers filters, citation copying and its permission-denied
fallback, filtered BibTeX export, deep links, responsive layouts, print, and reading
without JavaScript. The setup test also opens this page from the committed ZIP.
These checks do not certify novelty or reproduce the papers' experiments. Existing
source records remain intact; the library links back to reused evidence IDs.
