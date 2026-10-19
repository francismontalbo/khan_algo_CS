"""Test Download ZIP → extract once → open index.html from committed HEAD.

Optional maintainer check: Python, Playwright and Chrome are test tools only.
The extracted student guide runs offline without installation or a server.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "index.html", "Workflow_Research_Guide.html", "Workflow_Visual_Comparison.html",
    "Algorithm_Lessons.html", "Algorithm_Simulations.html", "Algorithm_Applications.html",
    "Workflow_Learning_Resources.html", "Workflow_Terms_and_Nomenclature.html",
    "Verification.html", "Audit_Report.html", "favicon.svg", ".nojekyll",
    "README.md", "START_HERE.txt", "DEPLOY.md", "TESTING.md", "NOTICE.md",
    "tools/check_setup.py", "Thesis_Research.html", "data/Thesis_References.bib",
)
LOCAL_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "output",
              ".playwright-cli", "private-notes", "local-exports"}
LOCAL_FILES = re.compile(r"^(?:\.env(?:\..*)?|\.DS_Store|Thumbs\.db|"
                         r"Workflow_(?:Comparison_Notes|Research_Notes).*\.json|"
                         r"Algorithm_Simulation_Run.*\.json|"
                         r"Workflow_Visual_Comparison_Saved.*\.html|Thesis_References_filtered.*\.bib)$")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "output/ci/setup-checks.json")
    args = ap.parse_args()
    checks, errors, resource_errors = [], [], []
    revision = None

    def check(name, passed, detail=""):
        checks.append({"check": name, "passed": bool(passed), "detail": detail})

    try:
        from playwright.sync_api import sync_playwright

        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        archive = subprocess.check_output(
            ["git", "archive", "--format=zip", "--prefix=khan_algo_CS/", revision], cwd=ROOT)
        with tempfile.TemporaryDirectory(prefix="guide setup with spaces ") as temporary:
            target = Path(temporary).resolve()
            with ZipFile(BytesIO(archive)) as bundle:
                names = [PurePosixPath(item.filename) for item in bundle.infolist()]
                safe = all(not p.is_absolute() and ".." not in p.parts
                           and p.parts[0] == "khan_algo_CS" for p in names)
                check("Archive paths stay inside the extracted folder", safe)
                if not safe:
                    raise ValueError("Unsafe ZIP member path; extraction cancelled.")
                local = [str(p) for p in names if LOCAL_DIRS.intersection(p.parts)
                         or LOCAL_FILES.fullmatch(p.name)]
                check("Download omits local environments, private notes and generated outputs", not local, local)
                bundle.extractall(target)
            site = target / "khan_algo_CS"
            missing = [name for name in REQUIRED if not (site / name).is_file()]
            check("Extracted download contains entry pages, companions and setup documents", not missing, missing)
            hardcoded = [p.name for p in site.glob("*.html") if re.search(
                r'''(?:href|src)\s*=\s*["'](?:file:|/Users/|/home/|/mnt/)''',
                p.read_text(encoding="utf-8"), re.I)]
            check("Published pages have no developer-machine asset paths", not hardcoded, hardcoded)
            launch = {"headless": True}
            chrome = os.environ.get("CHROMIUM_PATH") or shutil.which("chromium") or shutil.which("chromium-browser")
            mac_chrome = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
            if not chrome and mac_chrome.is_file():
                chrome = str(mac_chrome)
            if chrome:
                launch["executable_path"] = chrome
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                launch["args"] = ["--no-sandbox"]
            with sync_playwright() as pw:
                browser = pw.chromium.launch(**launch)
                context = browser.new_context(offline=True, viewport={"width": 1440, "height": 960})
                page = context.new_page()
                page.set_default_timeout(10000)
                page.on("pageerror", lambda err: errors.append(str(err)[:300]))
                page.on("console", lambda msg: errors.append(msg.text[:300]) if msg.type == "error" else None)
                page.on("requestfailed", lambda req: resource_errors.append(
                    f"{req.failure}: {req.url.replace(target.as_uri(), '<extracted>')}"[:300])
                    if req.url.startswith("file:") else None)
                home = (site / "index.html").as_uri()
                page.goto(home, wait_until="load")
                check("Offline file entry opens from a path containing spaces", " " in str(site) and "Home" in page.title())
                page.get_by_role("link", name="Start with Kahn", exact=False).click()
                page.wait_for_selector("#learning-dialog[open] #algorithm-lesson-heading")
                page.wait_for_selector("#learning-dialog .algorithm-formula math", state="attached")
                check("Start with Kahn navigates to the extracted guide and opens its lesson",
                      page.url.startswith((site / "Workflow_Research_Guide.html").as_uri())
                      and "Kahn" in page.locator("#algorithm-lesson-heading").inner_text())
                check("Lesson equation renders accessible MathML offline",
                      page.locator("#learning-dialog .algorithm-formula math").count() > 0)
                page.locator("#learning-close").click()
                page.locator('button[data-sim-open="fifo"]:visible').first.click()
                page.wait_for_selector("#sim-dialog[open]")
                before = page.locator("#sim-step-0").inner_text()
                page.locator("#sim-next").click()
                page.wait_for_selector("#sim-equation-0 math", state="attached")
                check("FIFO simulation advances through the visible step control",
                      page.evaluate("workflowSimulation.getState().id === 'fifo' && workflowSimulation.getState().index === 1")
                      and page.locator("#sim-step-0").inner_text() != before
                      and not page.locator("#sim-error").is_visible())
                check("Simulation equation renders MathML after stepping",
                      page.locator("#sim-equation-0 math").count() > 0)
                page.goto(home, wait_until="load")
                page.get_by_role("link", name="Open the thesis research library", exact=True).click()
                check("Thesis library opens from the extracted homepage offline",
                      page.url.startswith((site / "Thesis_Research.html").as_uri())
                      and page.locator(".paper:visible").count() > 0)
                page.locator("#research-period").select_option("2026")
                check("Current-year paper filter works in the download",
                      page.locator(".paper:visible").count() > 0
                      and all(year == "2026" for year in page.locator(".paper:visible .paper-year").all_text_contents()))
                context.close()
                browser.close()
    except Exception as exc:
        check("Download-and-open check completes", False, str(exc).splitlines()[0][:400])
    check("No JavaScript or console errors", not errors, errors)
    check("No missing local browser resources", not resource_errors, resource_errors)
    report = {"executed_at": datetime.now(timezone.utc).isoformat(), "commit": revision,
              "passed": sum(c["passed"] for c in checks), "checks": len(checks),
              "scope": "Committed Git ZIP extracted once; actual offline file navigation in Chromium. No server or student installation. Not a live GitHub download or cross-browser test.",
              "details": checks}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("commit", "passed", "checks")} | {"report": str(args.out)}))
    return int(report["passed"] != report["checks"])


if __name__ == "__main__":
    raise SystemExit(main())
