"""Exercise the thesis library offline, including references, filters and exports.

Uses the optional browser test environment; students need no installation.
This validates the website, not the novelty or empirical results of cited papers.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=ROOT / 'output/ci/thesis-checks.json')
    ap.add_argument('--screenshots', type=Path)
    args = ap.parse_args()
    checks, errors, failures = [], [], []

    def check(name, passed, detail=''):
        checks.append({'check': name, 'passed': bool(passed), 'detail': detail})
        if not passed:
            print('FAIL:', name, detail)

    data = json.loads((ROOT / 'data/Thesis_Research.json').read_text())
    papers = data['papers']
    expected_ids = {p['id'] for p in papers}
    url = (ROOT / 'Thesis_Research.html').as_uri()
    chrome = os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or shutil.which('chromium-browser')
    mac = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    if not chrome and mac.is_file():
        chrome = str(mac)
    launch = {'headless': True}
    if chrome:
        launch['executable_path'] = chrome
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        launch['args'] = ['--no-sandbox']
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**launch)
            context = browser.new_context(offline=True, viewport={'width': 1440, 'height': 1000})
            # Clipboard tests stay inside this browser context, without changing the user's clipboard.
            context.add_init_script("""Object.defineProperty(navigator, 'clipboard', {
              value: {writeText: async text => {window.copiedCitation = text;}}});""")
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
            page.on('requestfailed', lambda request: failures.append(request.url))
            page.goto(url)
            page.locator('#research-filters').wait_for(state='visible')
            embedded = json.loads(page.locator('#thesis-data').text_content())
            check('All source records are embedded offline', {p['id'] for p in embedded['papers']} == expected_ids)
            check('All papers and proposal directions are present', page.locator('.paper').count() == len(papers)
                  and page.locator('.direction').count() == len(data['directions']))
            anchors = page.evaluate("""() => ({
              ids: [...document.querySelectorAll('[id]')].map(node => node.id),
              broken: [...document.querySelectorAll('a[href^="#"]')].map(a => a.hash.slice(1))
                .filter(id => id && !document.getElementById(decodeURIComponent(id)))
            })""")
            check('Stable paper and navigation links resolve without duplicate IDs',
                  len(anchors['ids']) == len(set(anchors['ids'])) and not anchors['broken'], anchors['broken'])

            def visible_ids():
                return set(page.locator('.paper:visible').evaluate_all('(nodes) => nodes.map(n => n.dataset.paperId)'))

            def reset():
                page.locator('#research-filters [data-reset-filters]').click()

            for theme in data['themes']:
                page.locator('#research-theme').select_option(theme['id'])
                check('Theme filter: ' + theme['title'], visible_ids() == {p['id'] for p in papers if p['theme'] == theme['id']})
            reset()
            for period in ['recent', '2026']:
                page.locator('#research-period').select_option(period)
                expected = {p['id'] for p in papers if 2023 <= p['year'] <= 2026} if period == 'recent' else {p['id'] for p in papers if p['year'] == 2026}
                check('Publication-period filter: ' + period, visible_ids() == expected)
            reset()
            for status in ['peer-reviewed', 'preprint']:
                page.locator('#research-status').select_option(status)
                check('Publication-status filter: ' + status, visible_ids() == {p['id'] for p in papers if p['status'] == status})
            page.locator('#research-period').select_option('2026')
            selected = {p['id'] for p in papers if p['status'] == 'preprint' and p['year'] == 2026}
            check('Year and status combine correctly', visible_ids() == selected)
            with page.expect_download() as event:
                page.locator('#export-filtered').click()
            download = event.value
            exported = Path(download.path()).read_text()
            check('Filtered BibTeX contains exactly the displayed references',
                  exported == '\n'.join(p['bibtex'] for p in embedded['papers'] if p['id'] in selected), download.suggested_filename)
            page.locator('#research-query').fill('zz-no-paper-<script>')
            check('Empty search is clear and cannot export stale results', not visible_ids()
                  and page.locator('#empty-state').is_visible() and page.locator('#export-filtered').is_disabled())
            page.locator('#empty-state [data-reset-filters]').click()
            check('Empty-state reset restores all records', visible_ids() == expected_ids)
            first = papers[0]
            page.locator('#research-query').fill(first['title'])
            check('Title search finds the intended paper', first['id'] in visible_ids())
            page.locator('#research-query').fill('zz-no-paper')
            page.evaluate('(id) => {location.hash = "paper-" + id;}', first['id'])
            page.wait_for_function('(id) => !document.getElementById("paper-" + id).hidden', arg=first['id'])
            check('A citation deep link reveals a filtered-out paper', visible_ids() == expected_ids)
            button = page.locator(f'[data-copy-citation="{first["id"]}"]')
            button.click()
            page.wait_for_function('window.copiedCitation !== undefined')
            check('Copy citation uses the complete reference', page.evaluate('window.copiedCitation') == embedded['papers'][0]['citation'])
            page.evaluate("""() => { navigator.clipboard.writeText = async () => {throw Error('denied');};
                document.execCommand = () => false; }""")
            button.click()
            fallback = page.locator(f'#paper-{first["id"]} .citation-fallback')
            fallback.wait_for(state='visible')
            check('Denied clipboard offers selected reference text', fallback.locator('textarea').input_value() == embedded['papers'][0]['citation'])
            reset()
            for width in [320, 390, 1440]:
                page.set_viewport_size({'width': width, 'height': 1000})
                check(f'No horizontal page overflow at {width}px', page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
                if args.screenshots and width in [390, 1440]:
                    args.screenshots.mkdir(parents=True, exist_ok=True)
                    page.evaluate('scrollTo(0, 0)')
                    page.screenshot(path=str(args.screenshots / f'thesis-{width}.png'))
            page.locator('#research-period').select_option('2026')
            page.emulate_media(media='print')
            check('Print includes references hidden by filters', visible_ids() == expected_ids)
            context.close()
            nojs = browser.new_context(offline=True, java_script_enabled=False)
            page = nojs.new_page()
            page.goto(url)
            check('Reading and citation links work without JavaScript', page.locator('.paper:visible').count() == len(papers)
                  and page.locator('#directions').is_visible() and not page.locator('#research-filters').is_visible())
            nojs.close()
            browser.close()
    except Exception as error:
        check('Thesis browser suite completes', False, str(error).splitlines()[0][:500])
    check('No browser script errors', not errors, errors)
    check('No failed offline resources', not failures, failures)
    report = {'executed_at': datetime.now(timezone.utc).isoformat(), 'checks': len(checks),
              'passed': sum(c['passed'] for c in checks), 'details': checks,
              'scope': 'Offline Chromium behavior, filtering, links, citation export, clipboard fallback, print, responsive layout and no-JavaScript reading. Does not certify research novelty or reproduce papers.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(f"{report['passed']}/{report['checks']} thesis library checks passed; {args.out}")
    return int(report['passed'] != report['checks'])


if __name__ == '__main__':
    raise SystemExit(main())
