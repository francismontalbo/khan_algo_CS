"""Chromium smoke checks. A blocked local server is disclosed, not treated as a deployment pass."""
from __future__ import annotations
import argparse
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import threading
from datetime import datetime, timezone
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]

def main() -> int:
    from playwright.sync_api import sync_playwright
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path, default=ROOT/'tests/deployment/Browser_Checks.json')
    ap.add_argument('--screenshots', type=Path, help='Optional screenshot output directory.')
    ap.add_argument('--require-http', action='store_true', help='Fail unless actual local HTTP navigation succeeds; intended for CI.')
    args = ap.parse_args()
    checks, errors, limits, resource_errors = [], [], [], []
    def check(name, ok, detail=''):
        checks.append({'check': name, 'passed': bool(ok), 'detail': detail})
        if not ok:
            print('FAIL:', name, detail, flush=True)
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    server = None
    base = None
    try:
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT.parent)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        base = f'http://127.0.0.1:{server.server_port}/{quote(ROOT.name)}/'
    except OSError as exc:
        limits.append('Local HTTP server unavailable: '+str(exc).splitlines()[0])
    executable = os.getenv('CHROMIUM_PATH') or shutil.which('chromium') or shutil.which('chromium-browser')
    launch_options = {'headless': True}
    if executable:
        launch_options['executable_path'] = executable
    # Needed only when the test is run as root in a disposable build environment.
    if hasattr(os, 'geteuid') and os.geteuid() == 0:
        launch_options['args'] = ['--no-sandbox']
    live_http = False
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**launch_options)
        first = browser.new_page()
        try:
            if base:
                first.goto(base+'index.html', wait_until='domcontentloaded', timeout=8000)
                live_http = 'Workflow' in first.title()
        except Exception as exc:
            limits.append('Local HTTP navigation unavailable: '+str(exc).splitlines()[0])
        first.close()
        if args.require_http:
            check('Actual local HTTP navigation required', live_http, '; '.join(limits))
        if not live_http:
            limits.append('Interaction tests used local HTML contents. Query parameters and a repository-style base URL were supplied in the test harness. They are not end-to-end HTTP checks.')
        def load(relative='Workflow_Research_Guide.html', width=1440, height=960, saved_state=None):
            p = browser.new_page(viewport={'width':width, 'height':height}, accept_downloads=True)
            p.set_default_timeout(6000)
            p.on('pageerror', lambda exc: errors.append(str(exc)))
            p.on('response', lambda response: resource_errors.append(f'{response.status} {response.url}') if base and response.url.startswith(base) and response.status>=400 else None)
            p.on('requestfailed', lambda request: resource_errors.append(f'{request.failure} {request.url}') if base and request.url.startswith(base) else None)
            if saved_state is not None:
                p.add_init_script("localStorage.setItem('workflow-comparison-v1', "+json.dumps(json.dumps(saved_state))+");localStorage.setItem('unrelated-notes','Keep these notes.');")
            if live_http:
                p.goto(base+relative, wait_until='domcontentloaded')
            else:
                u=urlsplit(relative)
                text=(ROOT/(u.path or 'index.html')).read_text(encoding='utf-8')
                if u.query:
                    text=text.replace('new URLSearchParams(window.location.search)', 'new URLSearchParams('+json.dumps('?'+u.query)+')')
                text=text.replace('<head>', '<head><base href="https://example.invalid/student-research/">', 1)
                p.set_content(text, wait_until='domcontentloaded')
            p.wait_for_timeout(220)
            return p
        p=load('index.html')
        check('Home renders', 'Home' in p.title())
        check('Start action exists', p.get_by_role('link',name='Start with Kahn',exact=False).count()==1)
        check('One home heading', p.locator('h1').count()==1)
        check('Homepage has no remote scripts or players', p.locator('script[src],iframe,video').count()==0)
        local_urls=p.locator('a[href]').evaluate_all('(xs)=>xs.filter(a=>!a.getAttribute("href").startsWith("#")).map(a=>a.href)')
        expected=base if live_http else 'https://example.invalid/student-research/'
        check('Home links preserve repository prefix', all(h.startswith(expected) for h in local_urls))
        p.close()
        p=load()
        check('All five modules present',p.evaluate('[workflowExplorer,workflowLearning,workflowReference,workflowSimulation,workflowApplications].every(Boolean)'))
        check('Initial comparison retains Kahn',p.evaluate('workflowExplorer.getState().selected.slice(0,2).join(",")==="S1,S3"'))
        for preset in ['static','versions','closest','counters','reductions','dynamic','memory','audit']:
            p.locator('#comparison-preset').select_option(preset)
            for view in ['summary','code','all']:
                p.evaluate('(v)=>workflowExplorer.setView(v)',view)
                check(f'Compare {preset} in {view}', bool(p.locator('#compare-table').inner_text().strip()))
        methods=p.evaluate('JSON.parse(document.getElementById("explorer-data").textContent).methods.filter(m=>!m.branch).map(m=>m.id)')
        for mid in methods:
            p.evaluate('(id)=>workflowExplorer.showSource(id)',mid)
            check('Source dialog '+mid,p.locator('dialog[open]').count()>0)
            p.evaluate("document.querySelectorAll('dialog[open]').forEach(d=>d.close())")
        for view in p.evaluate('workflowExplorer.views'):
            p.locator('#tree-view').select_option(view)
            check('Research tree '+view,p.locator('[data-tree-node]').count()>0)
        simids=p.evaluate('JSON.parse(document.getElementById("simulation-data").textContent).engines.map(e=>e.id)')
        for sid in simids:
            p.evaluate('(id)=>workflowSimulation.open(id)',sid)
            p.locator('#sim-next').click()
            p.locator('#sim-last').click()
            check('Simulation '+sid,p.evaluate('workflowSimulation.getState().id')==sid and not p.locator('#sim-error').is_visible())
            p.locator('#sim-close').click()
        for term in ['xla','dag','lattice']:
            p.evaluate('(id)=>workflowReference.openTerm(id)',term)
            check('Term '+term,p.locator('#reference-dialog').is_visible())
            p.evaluate('workflowReference.close()')
        for lesson in p.evaluate('workflowLearning.lessonIds'):
            p.evaluate('(id)=>workflowLearning.showLesson(id)',lesson)
            check('Lesson '+lesson,p.locator('#learning-dialog').is_visible())
            p.evaluate('workflowLearning.close()')
        for profile in p.evaluate('workflowApplications.data.profiles.map(p=>p.id)'):
            p.evaluate('(id)=>workflowApplications.open(id)',profile)
            check('Application '+profile,p.locator('#app-dialog').is_visible())
            p.evaluate('workflowApplications.close()')
        # Saved comparisons must keep glossary and executable simulations.
        p.locator('#comparison-preset').select_option('versions')
        with p.expect_download() as download:
            p.locator('#export-comparison').click()
        exported=Path(download.value.path()).read_text(encoding='utf-8')
        ep=browser.new_page()
        ep.on('pageerror',lambda exc:errors.append('export: '+str(exc)))
        ep.set_content(exported,wait_until='domcontentloaded');ep.wait_for_timeout(200)
        check('Comparison export retains teaching modules',ep.evaluate('!!workflowReference && !!workflowLearning && !!workflowSimulation && !!workflowApplications'))
        ep.evaluate("workflowSimulation.open('fifo')");ep.locator('#sim-last').click()
        check('Exported simulator completes',not ep.locator('#sim-error').is_visible())
        ep.close()
        # Export and import notes without adding student data to the repository.
        p.locator('#comparison-preset').select_option('versions')
        with p.expect_download() as download:
            p.locator('#export-workspace').click()
        note_path=Path(download.value.path())
        original=p.evaluate('workflowExplorer.getState()')
        p.locator('#comparison-preset').select_option('static')
        p.locator('#workspace-file').set_input_files(note_path)
        p.wait_for_timeout(100)
        check('Notes round trip restores complete comparison state',p.evaluate('workflowExplorer.getState()')==original)
        def import_notes(payload):
            p.locator('#workspace-file').set_input_files({'name':'test-notes.json','mimeType':'application/json','buffer':json.dumps(payload).encode()})
            p.wait_for_timeout(100)
        draft={'name':'Retained student draft','mechanism':'Keep this explanation.','code':'A < B','older_field':'Keep older saved text.'}
        import_notes({'format':'workflow-comparison','version':1,'state':{'selected':['S1','toString','OWN'],'view':'toString','active':'valueOf','own':draft,'display':'code','diff':True}})
        restored=p.evaluate('workflowExplorer.getState()')
        check('Notes import normalizes inherited method and layout names',restored['selected']==['S1',None,'OWN'] and restored['view']=='focus' and restored['active']=='E29')
        check('Notes import preserves legitimate draft text and preferences',restored['own']==draft and restored['display']=='code' and restored['diff'])
        for malformed in [None,{'format':'workflow-comparison','version':1,'state':None}]:
            import_notes(malformed)
            check('Invalid notes envelope preserves the current draft '+str(malformed is None),p.evaluate('workflowExplorer.getState()')==restored)
        import_notes({'format':'workflow-comparison','version':1,'state':{'selected':['OWN','S3',None],'own':None}})
        check('Null draft body remains editable',p.evaluate('workflowExplorer.getState().selected')==['OWN','S3',None])
        p.locator('[data-edit-own]').click()
        check('Recovered draft editor opens',p.locator('#own-dialog').is_visible())
        p.locator('#own-dialog [data-close-dialog]').first.click()
        p.close()
        if live_http:
            for own in [draft,None]:
                p=load(saved_state={'selected':['OWN','S3','toString'],'view':'toString','active':'valueOf','display':'all','own':own})
                restored=p.evaluate('workflowExplorer.getState()')
                check('Saved notes recover invalid fields with '+('retained' if own else 'null')+' draft',restored['selected']==['OWN','S3',None] and restored['view']=='focus' and restored['active']=='E29' and restored['own']==(own or {}))
                check('Recovery preserves unrelated browser notes '+str(own is None),p.evaluate("localStorage.getItem('unrelated-notes')")=='Keep these notes.')
                p.close()
        else:
            limits.append('Saved localStorage recovery checks require an HTTP origin and were not executed.')
        routes=[('lesson','kahn','#algorithm-lesson-heading'),('algorithms',None,'#algorithm-index-heading'),
                ('simulation','dfs','#sim-dialog'),('applications','pk','#app-dialog'),('terms','xla','#reference-dialog'),
                ('videos',None,'#learning-dialog'),('simulation','not-a-method','#sim-dialog')]
        for view, ident, selector in routes:
            q='?open='+view+('&id='+ident if ident else '')
            p=load('Workflow_Research_Guide.html'+q)
            check('Direct route '+view+' '+str(ident),p.locator(selector).is_visible())
            if view=='simulation':
                check('Simulation route chooses the requested method '+str(ident),p.evaluate('workflowSimulation.getState().id')==('fifo' if ident=='not-a-method' else ident))
            if view=='applications':
                check('Application route chooses requested profile',p.evaluate('workflowApplications.getState().engine')==ident)
            p.close()
        companions=['Algorithm_Lessons.html','Algorithm_Simulations.html','Algorithm_Applications.html',
                    'Workflow_Learning_Resources.html','Workflow_Terms_and_Nomenclature.html','Verification.html','Audit_Report.html']
        for name in companions:
            p=load(name)
            check('Standalone '+name,p.locator('h1').count()>0 and p.locator('a[href="index.html"]').count()>0)
            p.close()
        for width in [320,390,768,1440]:
            for name in ['index.html','Workflow_Research_Guide.html']:
                p=load(name,width,844 if width<768 else 960)
                check(f'No page overflow {name} {width}',p.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                if name=='Workflow_Research_Guide.html':
                    p.evaluate("workflowSimulation.open('fifo')");p.locator('#sim-next').click()
                    check('Simulator controls at '+str(width),p.locator('#sim-next').is_visible() and p.locator('#sim-close').is_visible())
                    p.locator('#sim-close').click()
                if args.screenshots and width in [390,1440]:
                    args.screenshots.mkdir(parents=True,exist_ok=True)
                    p.screenshot(path=str(args.screenshots/f'{name.removesuffix(".html")}_{width}.png'))
                p.close()
        check('No JavaScript page errors',not errors,str(errors))
        check('No failed local resource requests',not resource_errors,str(resource_errors))
        browser.close()
    if server:
        server.shutdown();server.server_close()
    report={'executed_at':datetime.now(timezone.utc).isoformat(), 'passed':sum(x['passed'] for x in checks),
            'checks':len(checks),'live_local_http_test':live_http,'errors':errors,'limitations':limits,
            'scope':'Browser smoke checks of shipped pages, shared record views and representative controls. No live GitHub deployment, external playback, Safari or Firefox test.', 'details':checks}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='details'},indent=2))
    return int(report['passed']!=report['checks'])
if __name__=='__main__':
    raise SystemExit(main())
