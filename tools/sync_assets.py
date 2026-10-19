"""Synchronize existing embedded assets without rebuilding the research narrative.

Run from any directory. Uses Python's standard library. --check does not write.
"""
from __future__ import annotations
import argparse
import base64
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_ASSETS = {
    'explorer-style': 'code/explorer.css', 'visual-style': 'code/visual.css',
    'explorer-app': 'code/explorer.js', 'learning-style': 'code/learning.css',
    'learning-app': 'code/learning.js', 'reference-style': 'code/reference.css',
    'reference-app': 'code/reference.js', 'ui-polish-style': 'code/ui-polish.css',
    'ui-polish-app': 'code/ui-polish.js', 'final-edition-style': 'release/final.css',
    'final-edition-app': 'release/final.js', 'simulation-style': 'simulations/simulator.css',
    'simulation-engine': 'simulations/engine.js', 'simulation-ui': 'simulations/ui.js',
    'applications-style': 'applications/applications.css',
    'applications-ui': 'applications/applications.js', 'home-entry-routes': 'release/home_routes.js',
    'math-vendor': 'vendor/katex/katex.min.js', 'math-style': 'code/math.css',
    'math-app': 'code/math.js',
}
JSON_ASSETS = {
    'explorer-data': 'data/Explorer_Data.json', 'visual-data': 'data/Visual_Summaries.json',
    'learning-data': 'data/Learning_Resources.json', 'reference-data': 'data/Terminology.json',
    'simulation-data': 'simulations/data.json', 'applications-data': 'applications/data.json',
    'math-catalog': 'code/math-catalog.json', 'math-reference': 'code/math-reference.json',
}

MATH_PAGES = {'index.html', 'Workflow_Research_Guide.html', 'Workflow_Visual_Comparison.html',
              'Algorithm_Lessons.html', 'Algorithm_Simulations.html', 'Algorithm_Applications.html',
              'Workflow_Learning_Resources.html', 'Workflow_Terms_and_Nomenclature.html'}

def math_styles() -> str:
    """Embed the required WOFF2 fonts so file:// and saved exports stay portable."""
    folder = ROOT / 'vendor/katex'
    css = (folder / 'katex.min.css').read_text(encoding='utf-8')
    def font(match):
        encoded = base64.b64encode((folder / match[1]).read_bytes()).decode('ascii')
        return f'src:url(data:font/woff2;base64,{encoded}) format("woff2")'
    css = re.sub(r'src:url\((fonts/[^)]+\.woff2)\)[^;}]+', font, css)
    return '/* KaTeX 0.19.0; MIT License\n' + (folder / 'LICENSE').read_text() + '\n*/\n' + css

class EmbeddedBlocks(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=False)
        self.starts = [0]
        for line in text.splitlines(keepends=True):
            self.starts.append(self.starts[-1] + len(line))
        self.active = None
        self.blocks: dict[str, tuple[int, int]] = {}
        self.feed(text)
    def position(self) -> int:
        row, col = self.getpos()
        return self.starts[row - 1] + col
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style') and attrs.get('id'):
            self.active = (tag, attrs['id'], self.position() + len(self.get_starttag_text()))
    def handle_endtag(self, tag):
        if self.active is not None and tag == self.active[0]:
            _, ident, start = self.active
            if ident in self.blocks:
                raise ValueError(f'Duplicate embedded asset: {ident}')
            self.blocks[ident] = (start, self.position())
            self.active = None

def main() -> int:
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument('--check', action='store_true', help='Report drift without changing files.')
    opts = args.parse_args()
    sources = json.loads((ROOT / 'data/Reviewed_Sources.json').read_text(encoding='utf-8'))
    explorer = json.loads((ROOT / 'data/Explorer_Data.json').read_text(encoding='utf-8'))
    if explorer['sources'] != sources:
        raise SystemExit('Source records differ. Update both Reviewed_Sources.json and Explorer_Data.json before syncing.')
    raw = {k: (ROOT / v).read_text(encoding='utf-8') for k, v in TEXT_ASSETS.items()}
    raw['math-vendor-style'] = math_styles()
    # The minified runtime retains its license in each self-contained export.
    raw['math-vendor'] = '/* KaTeX 0.19.0; MIT License\n' + (ROOT/'vendor/katex/LICENSE').read_text() + '\n*/\n' + raw['math-vendor']
    structured = {k: json.loads((ROOT / v).read_text(encoding='utf-8')) for k, v in JSON_ASSETS.items()}
    changed = []
    for page in sorted(ROOT.glob('*.html')):
        original = page.read_text(encoding='utf-8')
        if page.name in MATH_PAGES and 'id="math-app"' not in original:
            changed.append(f'{page.name}: offline math support')
            original = original.replace('</head>', '<style id="math-vendor-style"></style>\n<style id="math-style"></style>\n</head>', 1)
            support = '<script id="math-vendor"></script>\n<script id="math-catalog" type="application/json">{}</script>\n<script id="math-reference" type="application/json">{}</script>\n<script id="math-app"></script>\n'
            before, after = original.rsplit('</body>', 1)
            original = before + support + '</body>' + after
        blocks = EmbeddedBlocks(original).blocks
        edits = []
        for ident, (start, end) in blocks.items():
            current = original[start:end]
            replacement = None
            if ident in raw and current.strip() != raw[ident].strip():
                replacement = '\n' + raw[ident].strip() + '\n'
            elif ident in structured and json.loads(current) != structured[ident]:
                replacement = json.dumps(structured[ident], ensure_ascii=False).replace('<', '\\u003c')
            elif ident == 'download-data':
                payload = json.loads(current)
                if payload.get('sources') != sources:
                    payload['sources'] = sources
                    replacement = json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')
            if replacement is not None:
                edits.append((start, end, replacement))
                changed.append(f'{page.name}: {ident}')
        if edits and not opts.check:
            text = original
            for start, end, replacement in sorted(edits, reverse=True):
                text = text[:start] + replacement + text[end:]
            page.write_text(text, encoding='utf-8')
    main_page = ROOT / 'Workflow_Research_Guide.html'
    alias = ROOT / 'Workflow_Visual_Comparison.html'
    if main_page.read_bytes() != alias.read_bytes():
        changed.append('Main and compatibility pages differ.')
        if not opts.check:
            alias.write_bytes(main_page.read_bytes())
    if changed:
        print(('OUT OF SYNC' if opts.check else 'SYNCHRONIZED') + '\n' + '\n'.join(changed))
    else:
        print('PASS: embedded assets agree with their editable source files.')
    return 1 if opts.check and changed else 0

if __name__ == '__main__':
    raise SystemExit(main())
