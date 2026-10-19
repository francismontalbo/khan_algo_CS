"""Check local app pages and portable relative links with no dependencies."""
from __future__ import annotations
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
import argparse
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.as_uri() + '/'
class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links, self.ids = [], set()
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        for key in ('href', 'src', 'poster', 'action'):
            if a.get(key):
                self.links.append((tag, key, a[key]))

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path)
    opts = ap.parse_args()
    checks = []
    def check(name, passed, detail=''):
        checks.append({'check': name, 'passed': bool(passed), 'detail': detail})
        if not passed:
            print('FAIL:', name, detail)
    needed = ['.nojekyll', 'favicon.svg', 'index.html', 'Workflow_Research_Guide.html',
              'Workflow_Visual_Comparison.html', 'README.md', 'DEPLOY.md', 'TESTING.md',
              'code/APACHE-2.0.txt', 'code/SOURCE_ATTRIBUTION.md',
              'reference/Original_Research_Package.zip', 'verify.py',
              'tests/final/check_integrity.py', 'tests/simulations/validate_algorithms.py',
              'tests/check_algorithm_foundations.py', 'tests/applications/verify_examples.py']
    for name in needed:
        check('Required file: ' + name, (ROOT / name).is_file())
    pages = sorted(ROOT.glob('*.html'))
    parsed = {p.name: Page(p.read_text(encoding='utf-8')) for p in pages}
    destinations = set()
    for p in pages:
        text = p.read_text(encoding='utf-8')
        check('No active sandbox or local-machine URL: ' + p.name,
              not re.search(r'(?:href|src)\s*=\s*[\"\'](?:sandbox:|file:|/mnt/|https?://(?:localhost|127\.0\.0\.1))', text, re.I))
        for tag, attribute, href in parsed[p.name].links:
            u = urlsplit(href)
            if u.scheme or u.netloc:
                check('Safe link scheme: ' + p.name + ' ' + href[:70],
                      u.scheme.lower() not in ('javascript', 'vbscript'))
                continue
            if href.startswith('#'):
                continue  # UI-managed dialogs and generated source anchors are checked in the browser.
            resolved = urlsplit(urljoin(BASE + p.name, href))
            check('App folder path preserved: ' + p.name + ' ' + href,
                  resolved.path.startswith(urlsplit(BASE).path))
            dest = (p.parent / unquote(u.path)).resolve()
            check('Local destination exists: ' + p.name + ' ' + href, dest.is_file(), str(dest.relative_to(ROOT)) if dest.is_relative_to(ROOT) else str(dest))
            destinations.add(str(dest))
            if u.fragment and dest.name in parsed:
                check('Cross-page section exists: ' + p.name + ' ' + href,
                      unquote(u.fragment) in parsed[dest.name].ids)
    # Local dependencies and browser diagnostics are not part of the distributed site.
    # Prune them before walking so a maintainer's environment cannot break the check.
    local_dirs = {'.git', '.venv', 'venv', 'node_modules', '__pycache__',
                  '.playwright-cli', 'output', 'private-notes', 'local-exports'}
    all_files = []
    for directory, dirs, files in os.walk(ROOT):
        dirs[:] = [name for name in dirs if name not in local_dirs]
        all_files.extend(Path(directory) / name for name in files)
    check('Each file is below the browser upload limit', all(p.stat().st_size < 25 * 1024 * 1024 for p in all_files))
    check('Main entry and compatibility entry are identical',
          (ROOT/'Workflow_Research_Guide.html').is_file()
          and (ROOT/'Workflow_Visual_Comparison.html').is_file()
          and (ROOT/'Workflow_Research_Guide.html').read_bytes() == (ROOT/'Workflow_Visual_Comparison.html').read_bytes())
    report = {'executed_at': datetime.now(timezone.utc).isoformat(), 'passed': sum(c['passed'] for c in checks),
              'checks': len(checks), 'pages': len(pages), 'local_destinations': len(destinations), 'details': checks,
              'scope': 'Local destination, scheme and portable-path checks. Not browser execution or external-link verification.'}
    if opts.out:
        opts.out.parent.mkdir(parents=True, exist_ok=True)
        opts.out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f"{report['passed']} of {report['checks']} static checks passed; {len(pages)} HTML pages.")
    return int(report['passed'] != report['checks'])
if __name__ == '__main__':
    raise SystemExit(main())
