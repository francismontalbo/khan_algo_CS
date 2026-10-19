"""Browser checks of bundled, accessible equations and their offline exports.

Run with the project's Python environment. This harness does not change source
data or saved notes. Screenshots and a focused report go to output/playwright.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import threading
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
GUIDE = "Workflow_Research_Guide.html"
EMBEDDED_IDS = ["math-vendor-style", "math-vendor", "math-style", "math-catalog", "math-reference", "math-app"]

# Verify the result, rather than forcing a render from the harness. A broken
# mutation observer must fail when a lesson or simulation changes its contents.
HARNESS = r"""() => {
  window.__mathSettle = () => new Promise(resolve =>
    requestAnimationFrame(() => requestAnimationFrame(() => setTimeout(resolve, 0))));
  window.__mathNode = (node, expectedSource) => {
    if (!node) return {ok:false, reason:'missing equation host'};
    const marked = node.matches('[data-math-rendered]') || !!node.querySelector('[data-math-rendered]');
    const styled = node.matches('.wf-math') || !!node.querySelector('.wf-math');
    const math = node.querySelector('math');
    const annotation = node.querySelector('annotation[encoding="application/x-tex"]');
    const visual = node.querySelector('.katex-html,[class*="katex-html"]');
    const error = node.querySelector('.katex-error,[class*="katex-error"],[data-math-error]');
    let expected = null, parseError = null;
    try {
      if (expectedSource !== undefined) expected = workflowMath.texFor(expectedSource);
      if (expected) katex.renderToString(expected, {throwOnError:true, output:'htmlAndMathml', strict:'error'});
      if (annotation) katex.renderToString(annotation.textContent, {throwOnError:true, output:'htmlAndMathml', strict:'error'});
    } catch (e) { parseError = e.message; }
    const sameTex = !expected || !!annotation && annotation.textContent === expected;
    const ok = marked && styled && !!math && !!annotation && !!visual &&
      visual.getAttribute('aria-hidden') === 'true' && !error && !parseError && sameTex;
    return {ok, marked, styled, mathml:!!math, annotation:!!annotation,
      hiddenVisual:!!visual && visual.getAttribute('aria-hidden') === 'true',
      texMatches: sameTex, parseError,
      source: expectedSource === undefined ? undefined : String(expectedSource).slice(0,150)};
  };
  window.__mathViewport = () => {
    const width = innerWidth;
    const visible = el => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && !el.closest('[hidden]') &&
        (!el.closest('dialog') || el.closest('dialog').open);
    };
    const clipped = [];
    for (const el of document.querySelectorAll('.wf-math')) {
      if (!visible(el)) continue;
      const r = el.getBoundingClientRect();
      if (r.left < -1 || r.right > width + 1) {
        let scroller = el.parentElement;
        while (scroller && scroller !== document.body &&
          !['auto','scroll'].includes(getComputedStyle(scroller).overflowX)) scroller = scroller.parentElement;
        if (!scroller || scroller === document.body) clipped.push({left:Math.round(r.left),right:Math.round(r.right),text:el.textContent.slice(0,70)});
      }
    }
    const dialogs = [...document.querySelectorAll('dialog[open]')].map(el => {
      const r = el.getBoundingClientRect();
      return {id:el.id,left:Math.round(r.left),right:Math.round(r.right),width:Math.round(r.width)};
    });
    return {ok:document.documentElement.scrollWidth <= width + 1 &&
      dialogs.every(d => d.left >= -1 && d.right <= width+1) && clipped.length === 0,
      viewport:width, documentWidth:document.documentElement.scrollWidth, dialogs, clipped:clipped.slice(0,5)};
  };
}"""


def main() -> int:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "output/playwright/math-checks.json")
    ap.add_argument("--screenshots", type=Path, default=ROOT / "output/playwright")
    ap.add_argument("--chrome", default=os.environ.get("CHROMIUM_PATH"))
    args = ap.parse_args()
    checks: list[dict] = []
    errors: list[str] = []
    console_errors: list[str] = []
    resource_errors: list[str] = []
    unexpected_requests: list[str] = []
    counts = {"lessons":0, "engines":0, "simulation_frames":0, "symbols":0, "parsed_tex":0}

    def check(name: str, passed: bool, detail=None) -> None:
        item = {"check":name, "passed":bool(passed)}
        if detail is not None:
            item["detail"] = detail
        checks.append(item)
        if not passed:
            print("FAIL:", name, json.dumps(detail, ensure_ascii=False)[:1200], flush=True)

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *_args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1",0), functools.partial(QuietHandler,directory=str(ROOT.parent)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base = f"http://127.0.0.1:{server.server_port}/{quote(ROOT.name)}/"
    executable = args.chrome or shutil.which("chromium") or shutil.which("chromium-browser")
    mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if not executable and mac_chrome.is_file():
        executable = str(mac_chrome)
    launch = {"headless":True}
    if executable:
        launch["executable_path"] = executable
    if hasattr(os,"geteuid") and os.geteuid() == 0:
        launch["args"] = ["--no-sandbox"]

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(**launch)
            context = browser.new_context(viewport={"width":1440,"height":1080},accept_downloads=True)

            def guard(route):
                url = route.request.url
                if url.startswith(("data:","blob:","file:",base)):
                    route.continue_()
                else:
                    unexpected_requests.append(url[:200])
                    route.abort()

            context.route("**/*",guard)

            def page_for(label: str, url: str | None = None, html: str | None = None, offline=False):
                ctx = browser.new_context(viewport={"width":1440,"height":1080},accept_downloads=True,offline=True) if offline else context
                p = ctx.new_page()
                p.set_default_timeout(10000)
                p.on("pageerror",lambda err:errors.append(label+": "+str(err)))
                p.on("console",lambda msg:console_errors.append(label+": "+msg.text) if msg.type=="error" or (msg.type=="warning" and any(s in msg.text.lower() for s in ["katex","math","latex","parse"])) else None)
                p.on("response",lambda r:resource_errors.append(f"{label}: {r.status} {r.url[:150]}") if r.status>=400 and r.url.startswith(base) else None)
                if html is not None:
                    p.set_content(html,wait_until="load")
                else:
                    p.goto(url or base+GUIDE,wait_until="load")
                p.wait_for_function("!!window.workflowMath && !!window.katex")
                p.evaluate(HARNESS)
                p.evaluate("__mathSettle()")
                p.evaluate("document.fonts.ready")
                return p

            def node_check(p, selector: str, source=None):
                return p.evaluate("([selector,source]) => __mathNode(document.querySelector(selector),source === null ? undefined : source)",[selector,source])

            def screenshot(p, name):
                args.screenshots.mkdir(parents=True,exist_ok=True)
                p.screenshot(path=str(args.screenshots / ("math-"+name+".png")))

            p = page_for("http")
            assets = p.evaluate("ids => ids.map(id=>({id,count:document.querySelectorAll('#'+id).length}))",EMBEDDED_IDS)
            check("All six math assets are embedded once",all(a["count"]==1 for a in assets),assets)
            font_info = p.evaluate(r"""() => {
              const css = document.getElementById('math-vendor-style').textContent;
              const urls = [...css.matchAll(/url\(([^)]+)\)/g)].map(m=>m[1].replace(/^[\s'"]+|[\s'"]+$/g,''));
              const loaded = [...document.fonts].filter(f=>/KaTeX/i.test(f.family)&&f.status==='loaded').map(f=>f.family);
              return {count:urls.length,embedded:urls.every(u=>u.startsWith('data:font/woff2;base64,')),loaded:[...new Set(loaded)]};
            }""")
            check("KaTeX fonts are embedded WOFF2 and used",font_info["count"]>0 and font_info["embedded"] and bool(font_info["loaded"]),font_info)
            compiled = p.evaluate("""() => {
              const catalog = JSON.parse(document.getElementById('math-catalog').textContent);
              const ref = JSON.parse(document.getElementById('math-reference').textContent);
              const tex = [...new Set([...Object.values(catalog),...Object.values(ref.expressions||{}),...Object.values(ref.symbols||{})])];
              const errors=[];
              for (const t of tex) try { katex.renderToString(t,{throwOnError:true,strict:'error',output:'htmlAndMathml'}); }
              catch(e) { errors.push({tex:t.slice(0,150),error:e.message.slice(0,200)}); }
              return {count:tex.length,errors};
            }""")
            counts["parsed_tex"] = compiled["count"]
            check("Every curated TeX expression parses strictly",not compiled["errors"],compiled)

            static = p.evaluate("""() => {
              const nodes=[...document.querySelectorAll('main .wf-math')].filter(n=>!n.closest('dialog'));
              const failures=nodes.map(n=>__mathNode(n)).filter(r=>!r.ok);
              return {count:nodes.length,failures:failures.slice(0,8)};
            }""")
            check("Main guide mathematical statements use accessible math",static["count"]>0 and not static["failures"],static)
            check("Main preparation-time equation renders",node_check(p,"main .formula")["ok"],node_check(p,"main .formula"))
            p.locator("main .formula").first.scroll_into_view_if_needed()
            screenshot(p,"proof")

            p.evaluate("workflowExplorer.setView('all')")
            for method_id in ['S1','P1','P2','P3','P4','P5','D1','D4','D5','D8','E08']:
                source = p.evaluate("id => JSON.parse(document.getElementById('explorer-data').textContent).methods.find(m=>m.id===id).guarantee",method_id)
                p.evaluate("id => workflowExplorer.chooseMethod(0,id)",method_id)
                p.evaluate("__mathSettle()")
                result = p.evaluate("source => __mathNode([...document.querySelectorAll('.formula-cell')].find(n=>n.dataset.mathSource===source),source)",source)
                check("Comparison guarantee: "+method_id,result["ok"],result if not result["ok"] else None)

            lessons = p.evaluate("JSON.parse(document.getElementById('learning-data').textContent).algorithm_lessons.map(l=>({id:l.id,formula:l.formula}))")
            check("Exactly ten lesson equations are covered",len(lessons)==10,{"lessons":len(lessons)})
            for lesson in lessons:
                p.evaluate("id=>workflowLearning.showLesson(id)",lesson["id"])
                p.evaluate("__mathSettle()")
                result = node_check(p,".algorithm-formula",lesson["formula"])
                check("Lesson equation: "+lesson["id"],result["ok"],result if not result["ok"] else None)
                counts["lessons"] += 1
            p.evaluate("workflowLearning.showLesson('counting')")
            p.evaluate("__mathSettle()")
            screenshot(p,"lesson")
            p.evaluate("workflowLearning.close()")

            engines = p.evaluate("JSON.parse(document.getElementById('simulation-data').textContent).engines.map(e=>({id:e.id,equation:e.equation}))")
            check("Exactly 23 simulator equations are covered",len(engines)==23,{"engines":len(engines)})
            for engine in engines:
                result = p.evaluate("""async engine => {
                  workflowSimulation.open(engine.id);
                  await __mathSettle();
                  const general=__mathNode(document.querySelector('.sim-details-grid .wide > p'),engine.equation);
                  const count=workflowSimulation.getState().frames[0];
                  const input=JSON.parse(document.getElementById('sim-input-json').value);
                  const frames=workflowSimulation.run(engine.id,input).frames;
                  const failures=[];
                  for(let i=0;i<count;i++) {
                    const progress=document.getElementById('sim-progress');
                    progress.value=String(i);
                    progress.dispatchEvent(new Event('input',{bubbles:true}));
                    await __mathSettle();
                    const r=__mathNode(document.getElementById('sim-equation-0'),frames[i].equation||engine.equation);
                    if(!r.ok && failures.length<8)failures.push({frame:i,...r});
                  }
                  return {general,frames:count,failures,error:document.getElementById('sim-error').hidden?'':document.getElementById('sim-error').textContent};
                }""",engine)
                counts["engines"] += 1
                counts["simulation_frames"] += result["frames"]
                check("Simulator equations and every default trace frame: "+engine["id"],result["general"]["ok"] and not result["failures"] and not result["error"],result if not result["general"]["ok"] or result["failures"] or result["error"] else {"frames":result["frames"]})
            p.evaluate("workflowSimulation.open('counters');workflowSimulation.step(2)")
            p.evaluate("__mathSettle()")
            screenshot(p,"sim")
            p.evaluate("workflowSimulation.close()")

            symbols = p.evaluate("JSON.parse(document.getElementById('reference-data').textContent).entries.filter(e=>e.category==='Symbols').map(e=>({id:e.id,term:e.term}))")
            p.evaluate("workflowReference.open(null,'Symbols')")
            p.evaluate("__mathSettle()")
            table = p.evaluate("""symbols => symbols.map(s=>{
              const node=document.querySelector('[data-ref-entry="'+CSS.escape(s.id)+'"]');
              return {id:s.id,...__mathNode(node,s.term)};
            })""",symbols)
            check("All 35 glossary symbol rows render",len(symbols)==35 and all(r["ok"] for r in table),{"symbols":len(symbols),"failures":[r for r in table if not r["ok"]][:8]})
            details=[]
            for symbol in symbols:
                p.evaluate("id=>workflowReference.openTerm(id)",symbol["id"])
                p.evaluate("__mathSettle()")
                result=node_check(p,"#term-heading",symbol["term"])
                if not result["ok"]:
                    details.append({"id":symbol["id"],**result})
                counts["symbols"] += 1
            check("Every glossary symbol detail heading renders",not details,details[:8])
            p.evaluate("workflowReference.close()")

            # Formula containers may scroll; the page and open dialog must fit.
            for width in [320,390]:
                p.set_viewport_size({"width":width,"height":844})
                p.evaluate("window.scrollTo(0,0)")
                p.evaluate("__mathSettle()")
                result=p.evaluate("__mathViewport()")
                check(f"Main guide fits {width}px",result["ok"],result)
                for lesson in lessons:
                    p.evaluate("id=>workflowLearning.showLesson(id)",lesson["id"])
                    p.evaluate("__mathSettle()")
                    result=p.evaluate("__mathViewport()")
                    check(f"Lesson {lesson['id']} fits {width}px",result["ok"],result if not result["ok"] else None)
                p.evaluate("workflowLearning.close()")
                for engine in engines:
                    p.evaluate("id=>workflowSimulation.open(id)",engine["id"])
                    p.locator(".sim-run > details").first.evaluate("el=>el.open=true")
                    p.evaluate("__mathSettle()")
                    result=p.evaluate("__mathViewport()")
                    check(f"Simulator {engine['id']} fits {width}px",result["ok"],result if not result["ok"] else None)
                if width==390:
                    p.evaluate("workflowSimulation.open('counters');workflowSimulation.step(2)")
                    p.evaluate("__mathSettle()")
                    p.locator("#sim-equation-0").scroll_into_view_if_needed()
                    screenshot(p,"mobile")
                p.evaluate("workflowSimulation.close()")
                p.evaluate("workflowReference.open(null,'Symbols')")
                p.evaluate("__mathSettle()")
                result=p.evaluate("__mathViewport()")
                check(f"Glossary symbol table fits {width}px",result["ok"],result)
                p.evaluate("workflowReference.close()")

            p.set_viewport_size({"width":1440,"height":1080})
            # This preset includes mathematical guarantees in the exported
            # table; version-history guarantees are deliberately prose.
            p.locator("#comparison-preset").select_option("counters")
            p.evaluate("workflowExplorer.setView('all')")
            p.evaluate("__mathSettle()")
            with p.expect_download() as dl:
                p.locator("#export-comparison").click()
            # Read the existing Playwright artifact; do not duplicate the export.
            exported = Path(dl.value.path()).read_text(encoding="utf-8")
            check("Downloaded comparison embeds all math assets",all(('id="'+asset+'"') in exported for asset in EMBEDDED_IDS))
            ep = page_for("offline-export",html=exported,offline=True)
            export_math = ep.evaluate("""() => {
              const nodes=[...document.querySelectorAll('main .wf-math')];
              return {count:nodes.length,failures:nodes.map(n=>__mathNode(n)).filter(r=>!r.ok).slice(0,5),
                remoteAssets:document.querySelectorAll('script[src],link[rel="stylesheet"]').length};
            }""")
            check("Downloaded comparison retains accessible math while offline",export_math["count"]>0 and not export_math["failures"] and export_math["remoteAssets"]==0,export_math)
            ep.evaluate("id=>workflowLearning.showLesson(id)",lessons[0]["id"])
            ep.evaluate("__mathSettle()")
            result=node_check(ep,".algorithm-formula",lessons[0]["formula"])
            check("Downloaded comparison lesson renders while offline",result["ok"],result if not result["ok"] else None)
            ep.evaluate("workflowLearning.close();workflowSimulation.open('counters');workflowSimulation.step(2)")
            ep.evaluate("__mathSettle()")
            result=node_check(ep,"#sim-equation-0")
            check("Downloaded comparison dynamic equations render while offline",result["ok"],result if not result["ok"] else None)
            check("Downloaded comparison loads embedded fonts offline",ep.evaluate("[...document.fonts].some(f=>/KaTeX/i.test(f.family)&&f.status==='loaded')"))
            export_errors=ep.evaluate("workflowMath.errors")
            check("Offline export records no rejected TeX",not export_errors,export_errors[:8])
            ep.context.close()

            # Exercise the public download controls as well as the comparison
            # export. Their packaging paths are different from page generation.
            p.evaluate("workflowLearning.open()")
            with p.expect_download() as dl:
                p.locator("#learning-save").click()
            lesson_html=Path(dl.value.path()).read_text(encoding="utf-8")
            p.evaluate("workflowLearning.close()")
            check("Downloaded learning guide embeds all math assets",all(('id="'+asset+'"') in lesson_html for asset in EMBEDDED_IDS))
            lp=page_for("offline-learning-download",html=lesson_html,offline=True)
            lesson_failures=[]
            for lesson in lessons:
                lp.evaluate("id=>workflowLearning.showLesson(id)",lesson["id"])
                lp.evaluate("__mathSettle()")
                result=node_check(lp,".algorithm-formula",lesson["formula"])
                if not result["ok"]:
                    lesson_failures.append({"id":lesson["id"],**result})
            check("All ten lessons in actual learning download render offline",not lesson_failures,lesson_failures[:8])
            lp.evaluate("document.fonts.ready")
            check("Downloaded learning guide uses embedded fonts offline",lp.evaluate("[...document.fonts].some(f=>/KaTeX/i.test(f.family)&&f.status==='loaded')"))
            lesson_errors=lp.evaluate("workflowMath.errors")
            check("Downloaded learning guide records no rejected TeX",not lesson_errors,lesson_errors[:8])
            lp.context.close()

            p.evaluate("workflowReference.open(null,'Symbols')")
            with p.expect_download() as dl:
                p.locator("#reference-save").click()
            glossary_html=Path(dl.value.path()).read_text(encoding="utf-8")
            p.evaluate("workflowReference.close()")
            check("Downloaded glossary embeds all math assets",all(('id="'+asset+'"') in glossary_html for asset in EMBEDDED_IDS))
            gp=page_for("offline-glossary-download",html=glossary_html,offline=True)
            static_symbols=gp.evaluate("""symbols => symbols.map(s=>({id:s.id,...__mathNode(document.querySelector('body > section a[data-term-id="'+CSS.escape(s.id)+'"]'),s.term)}))""",symbols)
            static_failures=[r for r in static_symbols if not r["ok"]]
            check("Downloaded glossary initial symbol table renders offline",len(static_symbols)==35 and not static_failures,static_failures[:8])
            gp.evaluate("workflowReference.open(null,'Symbols')")
            gp.evaluate("__mathSettle()")
            glossary_results=gp.evaluate("""symbols => symbols.map(s=>({id:s.id,...__mathNode(document.querySelector('[data-ref-entry="'+CSS.escape(s.id)+'"]'),s.term)}))""",symbols)
            glossary_failures=[r for r in glossary_results if not r["ok"]]
            check("All 35 symbols in actual glossary download render offline",len(glossary_results)==35 and not glossary_failures,glossary_failures[:8])
            gp.evaluate("document.fonts.ready")
            check("Downloaded glossary uses embedded fonts offline",gp.evaluate("[...document.fonts].some(f=>/KaTeX/i.test(f.family)&&f.status==='loaded')"))
            glossary_errors=gp.evaluate("workflowMath.errors")
            check("Downloaded glossary records no rejected TeX",not glossary_errors,glossary_errors[:8])
            gp.context.close()

            fp = page_for("offline-file",url=(ROOT/GUIDE).as_uri(),offline=True)
            result=node_check(fp,"main .formula")
            check("Guide file renders equations without network access",result["ok"],result if not result["ok"] else None)
            fp.evaluate("id=>workflowLearning.showLesson(id)",lessons[0]["id"])
            fp.evaluate("__mathSettle()")
            result=node_check(fp,".algorithm-formula",lessons[0]["formula"])
            check("Guide file lesson renders without network access",result["ok"],result if not result["ok"] else None)
            file_errors=fp.evaluate("workflowMath.errors")
            check("Offline file records no rejected TeX",not file_errors,file_errors[:8])
            fp.context.close()
            render_errors=p.evaluate("workflowMath.errors")
            check("Renderer records no rejected TeX",not render_errors,render_errors[:8])
            p.close()
            context.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    check("No JavaScript page errors",not errors,errors[:12])
    check("No math or console errors",not console_errors,console_errors[:12])
    check("No failed local resources",not resource_errors,resource_errors[:12])
    check("Rendering requests no external resources",not unexpected_requests,list(dict.fromkeys(unexpected_requests))[:12])
    report={"executed_at":datetime.now(timezone.utc).isoformat(),"passed":sum(c["passed"] for c in checks),"checks":len(checks),"counts":counts,
      "scope":"Chromium: strict curated TeX, all lesson formulas, all simulator general equations and default trace frames, glossary symbols, 320/390px layout, actual comparison/learning/glossary downloads with network disabled, and file:// offline rendering.",
      "errors":errors,"console_errors":console_errors,"resource_errors":resource_errors,"external_requests":unexpected_requests,"details":checks}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"passed":report["passed"],"checks":report["checks"],"counts":counts,"report":str(args.out)},ensure_ascii=False),flush=True)
    return int(report["passed"]!=report["checks"])


if __name__=="__main__":
    raise SystemExit(main())
