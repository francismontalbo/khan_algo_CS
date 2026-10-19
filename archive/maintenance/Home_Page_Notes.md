# Home page revision

Added to the existing 15 October 2026 research edition. This is a navigation and presentation change, not a new literature audit.

## Start here

Open `index.html`. The page links into the existing guide through normal local links. Keep the extracted folder together. The home page is self-contained and uses no third-party scripts, analytics, accounts, or autoplay. Its illustration is a static screenshot of the existing Kahn simulation. Selecting it opens the live simulation.

## Changes

- Added the home page, a direct Kahn lesson entry, and direct links to the existing algorithms, simulation, applications, glossary, and learning views.
- Changed the guide's brand link to return to the home page and added Home to its More menu.
- Added a Home link to the seven direct-entry and review pages.
- Updated the README and added START_HERE.txt.
- Preserved the research records, computational code, glossary content, lessons, simulations, old verification logs, and all prior package files.

## Checks in this revision

386 of 386 recorded checks passed. These include static retention checks and UI checks; they are not 386 independent algorithm tests. No JavaScript page errors were observed during the tested entry routes. All previous named embedded modules, data files, code files, simulation files, and application files were unchanged by hash.

The home page was rendered and inspected at desktop and emulated tablet and phone widths, including 320 pixels. The primary controls, keyboard skip link, queried entry routes, simulation stepping, section targets, and home-return links were checked.

## Limits

Browser policy in this execution environment blocks direct local-file and network navigation. Tests selected actual links and loaded their local target HTML in memory, supplying the query to the entry adapter. This does not certify end-to-end navigation from `file://` on a physical device. External articles and video playback were not tested. Only Chromium was used. The previous research and algorithm verification results retain their original scope.

## Reproduce the local-content checks

Install Playwright and a Chromium browser, then run `python tests/home/check_home.py`. The script currently points to `/usr/bin/chromium`; adjust that executable path for another environment. Results are recorded in `tests/home/Home_Checks.json`. The actual local links can also be checked directly by opening `index.html` on your own computer.

The preceding edition's hash manifest is retained as `release/SHA256SUMS_before_home.json`. The root `SHA256SUMS.json` describes the updated package and excludes itself.
