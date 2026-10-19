"""Build the standalone research index and BibTeX from reviewed source data.

Run python3 tools/build_thesis.py; use --check to detect stale output without writing.
No third-party packages, network access, or browser runtime are required.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
from html import escape
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")


def h(value: object) -> str:
    return escape(str(value), quote=True)


def validate(data: dict) -> None:
    """Reject broken anchors, unsafe links, and incomplete core source records."""
    date.fromisoformat(data["reviewed_on"])
    for key in ("coverage_note", "themes", "papers", "directions", "search_audit"):
        if key not in data:
            raise ValueError(f"Missing field: {key}")
    ids: dict[str, set[str]] = {}
    for kind in ("themes", "papers", "directions"):
        seen: set[str] = set()
        for item in data[kind]:
            item_id = item["id"]
            if not ID_PATTERN.fullmatch(item_id) or item_id in seen:
                raise ValueError(f"Invalid or duplicate {kind} ID: {item_id}")
            seen.add(item_id)
        ids[kind] = seen
    if not data["papers"]:
        raise ValueError("The bibliography must contain at least one reviewed paper.")
    for paper in data["papers"]:
        for key in ("title", "authors", "year", "venue", "status", "url", "theme", "relation", "finding", "proposal_use", "limit"):
            if not paper.get(key):
                raise ValueError(f"Missing paper {paper['id']} field: {key}")
        if paper["theme"] not in ids["themes"]:
            raise ValueError(f"Unknown theme for {paper['id']}")
        if paper["status"] not in ("peer-reviewed", "preprint"):
            raise ValueError(f"Unknown publication status for {paper['id']}")
        if paper["relation"] not in ("direct", "adjacent", "foundation", "benchmark"):
            raise ValueError(f"Unknown relation for {paper['id']}")
        if not isinstance(paper["year"], int) or not 1900 <= paper["year"] <= date.fromisoformat(data["reviewed_on"]).year:
            raise ValueError(f"Invalid or future year for {paper['id']}")
        if not isinstance(paper["authors"], list) or not all(isinstance(author, str) and author.strip() for author in paper["authors"]):
            raise ValueError(f"Invalid authors for {paper['id']}")
        for field in ("url", "access_url"):
            if paper.get(field):
                parsed = urlsplit(paper[field])
                if parsed.scheme not in ("https", "http") or not parsed.netloc:
                    raise ValueError(f"Unsafe {field} for {paper['id']}")
        if paper.get("doi") and not re.fullmatch(r"10\.\d{4,9}/\S+", paper["doi"]):
            raise ValueError(f"Invalid DOI for {paper['id']}")
    for direction in data["directions"]:
        for source_id in direction["source_ids"]:
            if source_id not in ids["papers"]:
                raise ValueError(f"Unknown source {source_id} in direction {direction['id']}")


def citation(paper: dict) -> str:
    authors = "; ".join(paper["authors"])
    metadata = paper["venue"]
    if paper.get("series"):
        metadata += f", {paper['series']}"
    if paper.get("volume"):
        metadata += f", {paper['volume']}"
    if paper.get("number"):
        metadata += f"({paper['number']})"
    if paper.get("article_number"):
        metadata += f", Article {paper['article_number']}"
    if paper.get("pages"):
        metadata += f", pp. {paper['pages'].replace('--', '–')}"
    link = f"https://doi.org/{paper['doi']}" if paper.get("doi") else paper["url"]
    status = " [Preprint]" if paper["status"] == "preprint" else ""
    return f"{authors} ({paper.get('citation_year', paper['year'])}). {paper['title']}. {metadata}.{status} {link}"


def bib_escape(value: object) -> str:
    replacements = {"\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(char, char) for char in str(value)).replace("\n", " ")


def bibtex(paper: dict) -> str:
    # Without an explicitly verified entry type, @misc preserves the supplied venue
    # without guessing whether it is a journal, conference, or archival report.
    entry_type = paper.get("bibtex_type", "misc")
    if entry_type not in ("article", "inproceedings", "book", "incollection", "techreport", "misc"):
        raise ValueError(f"Unsupported BibTeX type: {entry_type}")
    venue_field = "journal" if entry_type == "article" else "booktitle" if entry_type in ("inproceedings", "incollection") else "howpublished"
    fields = [("author", " and ".join(paper["authors"])), ("title", "{" + bib_escape(paper["title"]) + "}"),
              ("year", str(paper.get("citation_year", paper["year"]))), (venue_field, paper["venue"])]
    for key in ("series", "volume", "number", "pages", "doi", "url"):
        if paper.get(key):
            fields.append((key, str(paper[key])))
    notes = ["Preprint; not peer reviewed" if paper["status"] == "preprint" else "Peer-reviewed publication"]
    if paper.get("article_number"):
        fields.append(("eid", paper["article_number"]))
        notes.append("Article " + paper["article_number"])
    if paper.get("version"):
        notes.append(str(paper["version"]))
    if paper.get("publication_date"):
        notes.append("Publication date: " + str(paper["publication_date"]))
    fields.append(("note", "; ".join(notes)))
    lines = []
    for key, value in fields:
        # URLs and DOI identifiers retain underscores and other literal URL characters.
        encoded = value if key in ("title", "doi", "url") else bib_escape(value)
        lines.append(f"  {key} = {{{encoded}}}")
    return "@" + entry_type + "{" + paper["id"] + ",\n" + ",\n".join(lines) + "\n}\n"


def items(values: list) -> str:
    return "<ul>" + "".join(f"<li>{h(value)}</li>" for value in values) + "</ul>"


def prose_or_list(value: object) -> str:
    return items(value) if isinstance(value, list) else f"<p>{h(value)}</p>"


def render_paper(paper: dict) -> str:
    pid = h(paper["id"])
    status = "Preprint" if paper["status"] == "preprint" else "Peer reviewed"
    relation = {"direct": "Direct study", "adjacent": "Adjacent", "foundation": "Foundation", "benchmark": "Benchmark"}[paper["relation"]]
    primary_link = f'<a href="https://doi.org/{h(paper["doi"])}">DOI: {h(paper["doi"])}</a>' if paper.get("doi") else f'<a href="{h(paper["url"])}">Primary source</a>'
    access_link = f'<a href="{h(paper["access_url"])}">Open-access text</a>' if paper.get("access_url") else ""
    source_link = f'<a href="{h(paper["url"])}">Source record</a>' if paper.get("doi") and paper["url"] != f'https://doi.org/{paper["doi"]}' else ""
    if paper.get("existing_source_id"):
        source_link += f'<a href="Workflow_Research_Guide.html#ref-{h(paper["existing_source_id"])}">Guide source {h(paper["existing_source_id"])}</a>'
    evidence = f'<dt>Evidence checked</dt><dd>{h(paper["evidence_scope"])}</dd>' if paper.get("evidence_scope") else ""
    version = f'<dt>Version &amp; dates</dt><dd>{h(paper["version"])}</dd>' if paper.get("version") else ""
    return f'''<article class="paper" id="paper-{pid}" data-paper-id="{pid}" aria-labelledby="title-{pid}">
<div class="paper-aside"><div class="paper-year">{paper["year"]}</div><div class="paper-relation">{relation}</div></div>
<div class="paper-body"><h4 class="paper-title" id="title-{pid}"><a href="{h(paper["url"])}">{h(paper["title"])}</a></h4>
<p class="citation">{h(citation(paper))}</p>
<div class="paper-links"><span class="status status-{h(paper["status"])}">{status}</span>{primary_link}{source_link}{access_link}</div>
<dl class="paper-notes"><dt>Finding</dt><dd>{h(paper["finding"])}</dd><dt>Thesis use</dt><dd>{h(paper["proposal_use"])}</dd><dt>Limits</dt><dd>{h(paper["limit"])}</dd>{version}{evidence}</dl>
<div class="paper-actions"><button type="button" class="plain-button" data-copy-citation="{pid}" data-enhance hidden aria-label="Copy citation for {h(paper["title"])}">Copy citation</button><a class="permalink" href="#paper-{pid}" aria-label="Permanent link to {h(paper["title"])}">#{pid}</a></div>
<p class="copy-status" role="status" aria-live="polite"></p><div class="citation-fallback" hidden><label for="citation-{pid}">Citation text</label><textarea id="citation-{pid}" readonly spellcheck="false"></textarea></div></div></article>'''


def render_direction(direction: dict, index: int, papers: dict) -> str:
    rows = [("Proposed change", h(direction["change"])), ("Proof obligation", h(direction["proof"])),
            ("Baselines", items(direction["baselines"])), ("Measurements", items(direction["metrics"])),
            ("Ablations", items(direction["ablations"])), ("BSCS feasibility", h(direction["feasibility"])),
            ("Novelty check", h(direction["novelty_check"]))]
    sources = " ".join(f'<a href="#paper-{h(source_id)}">{h(papers[source_id]["authors"][0].split(",")[0])} et al. ({papers[source_id]["year"]})</a>' if len(papers[source_id]["authors"]) > 1 else f'<a href="#paper-{h(source_id)}">{h(papers[source_id]["authors"][0].split(",")[0])} ({papers[source_id]["year"]})</a>' for source_id in direction["source_ids"])
    return f'''<article class="direction" id="direction-{h(direction["id"])}"><p class="direction-number">DIRECTION {index:02d}</p><h3>{h(direction["title"])}</h3><p class="research-question">{h(direction["question"])}</p><dl>{"".join(f"<dt>{label}</dt><dd>{content}</dd>" for label, content in rows)}</dl><p class="direction-sources">Read with: {sources}</p></article>'''


LINEAR_MATH = '<math xmlns="http://www.w3.org/1998/Math/MathML" aria-label="O of the number of vertices plus the number of edges"><mi>O</mi><mo>(</mo><mo>|</mo><mi>V</mi><mo>|</mo><mo>+</mo><mo>|</mo><mi>E</mi><mo>|</mo><mo>)</mo></math>'
LOWER_MATH = '<math xmlns="http://www.w3.org/1998/Math/MathML" aria-label="Omega of the number of vertices plus the number of edges"><mi>Ω</mi><mo>(</mo><mo>|</mo><mi>V</mi><mo>|</mo><mo>+</mo><mo>|</mo><mi>E</mi><mo>|</mo><mo>)</mo></math>'


def render(data: dict, css: str, js: str) -> str:
    counts = Counter(paper["theme"] for paper in data["papers"])
    paper_lookup = {paper["id"]: paper for paper in data["papers"]}
    nav = "".join(f'<li><a href="#theme-{h(theme["id"])}">{h(theme["title"])} <span class="visually-hidden">({counts[theme["id"]]} sources)</span></a></li>' for theme in data["themes"])
    theme_options = "".join(f'<option value="{h(theme["id"])}">{h(theme["title"])}</option>' for theme in data["themes"])
    groups = []
    for theme in data["themes"]:
        entries = "\n".join(render_paper(paper) for paper in data["papers"] if paper["theme"] == theme["id"])
        groups.append(f'<section class="theme-section" id="theme-{h(theme["id"])}" aria-labelledby="theme-heading-{h(theme["id"])}"><header class="theme-heading"><h3 id="theme-heading-{h(theme["id"])}">{h(theme["title"])}</h3><p>{h(theme["description"])}</p></header>{entries}</section>')
    directions = "\n".join(render_direction(direction, i, paper_lookup) for i, direction in enumerate(data["directions"], 1))
    audit = data["search_audit"]
    audit_sources = "".join(f'<li><a href="{h(source)}">{h(source)}</a></li>' if isinstance(source, str) and source.startswith("https://") else f'<li>{h(source)}</li>' for source in audit["sources"])
    audit_queries = "".join(f'<li>{h(query)}</li>' for query in audit["queries"])
    payload = dict(data)
    payload["papers"] = [dict(paper, citation=citation(paper), bibtex=bibtex(paper)) for paper in data["papers"]]
    inline_data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    reviewed = date.fromisoformat(data["reviewed_on"])
    review_label = f"{reviewed.day} {reviewed.strftime('%B')} {reviewed.year}"
    return f'''<!doctype html>
<!-- Generated by tools/build_thesis.py from data/Thesis_Research.json. Edit source files, then rebuild. -->
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Thesis Research · Kahn's Algorithm and DAG Scheduling</title><meta name="description" content="A source-backed reading index and BSCS thesis directions for Kahn's topological sorting, dynamic DAGs, memory-aware scheduling, and evaluation through 2026."><meta name="theme-color" content="#096c68"><link rel="icon" href="favicon.svg" type="image/svg+xml"><style>{css}</style></head>
<body><a class="skip-link" href="#main-content">Skip to research content</a><header class="site-header"><div class="wrap header-inner"><a class="brand" href="index.html"><span class="brand-symbol" aria-hidden="true"><svg width="23" height="23" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M6 6h10M6 6v12m0 0h10"/><path d="m12 3 4 3-4 3m0 6 4 3-4 3"/><circle cx="5" cy="6" r="2" fill="currentColor"/><circle cx="18" cy="6" r="2" fill="currentColor"/><circle cx="18" cy="18" r="2" fill="currentColor"/></svg></span><span><strong>Workflow Algorithm Research</strong><small>BSCS research &amp; learning guide</small></span></a><nav class="header-nav" aria-label="Site navigation"><a class="home-link" href="index.html">Home</a><a href="Workflow_Research_Guide.html">Main guide ↗</a></nav></div></header>
<main id="main-content" class="wrap"><div class="page-intro"><p class="eyebrow">Research library · Through 2026</p><h1>Kahn’s algorithm:<br>from foundations to thesis questions</h1><p class="intro-copy">An annotated reading path for deriving, testing, and defending a focused BSCS contribution to topological ordering and DAG scheduling.</p><div class="review-meta"><span>Reviewed <strong><time datetime="{h(data["reviewed_on"])}">{review_label}</time></strong></span><span><strong>{len(data["papers"])} sources</strong> · {len(data["themes"])} themes · {len(data["directions"])} candidate directions</span></div></div>
<div class="document-layout"><aside class="reading-rail"><nav class="rail-inner" aria-label="Reading order"><p class="rail-label">Reading order</p><ol>{nav}</ol><div class="rail-links"><a href="#directions">Thesis directions</a><a href="#proposal-plan">Proposal plan</a><a href="#search-audit">Search &amp; coverage</a><a href="data/Thesis_References.bib" download>Download full BibTeX ↓</a></div><p class="rail-note">Sources support a research question. They do not establish that a proposed modification is novel or faster.</p></nav></aside><div class="main-column">
<section class="orientation" aria-labelledby="orientation-title"><h2 id="orientation-title">Start with the right claim</h2><p><strong>Kahn’s algorithm is indegree-based source removal.</strong> A vertex becomes ready only after every incoming dependency has been removed. A FIFO queue is one ready-set policy; this is not ordinary breadth-first traversal, which discovers vertices by distance from a starting vertex.</p><p><strong>State the model before claiming a speedup.</strong> For an explicit adjacency-list graph, the standard sequential algorithm takes {LINEAR_MATH} time with constant-time queue operations. Worst-case processing of the explicit vertices and edges costs {LOWER_MATH}; a static exact sort cannot improve that worst-case input-reading bound in this model. Preprocessed inputs, incremental updates, restricted graph families, external memory, and parallel work or span require separate assumptions and accounting.</p><p><strong>Ordering cost and schedule quality are different outcomes.</strong> Lower peak live memory or a shorter execution makespan can justify an ordering policy even when sorting itself takes longer. Treat the directions below as hypotheses: prove validity, include preprocessing and policy overhead, compare fair baselines, and check the closest prior art before making a novelty claim.</p></section>
<section class="library" id="papers" aria-labelledby="library-title"><div class="library-heading"><h2 id="library-title">Annotated bibliography</h2><span class="source-count" id="visible-count" role="status" aria-live="polite" aria-atomic="true">{len(data["papers"])} sources</span></div><p class="section-intro">Follow the themes in order, or narrow the list. “Direct study” concerns topological ordering; adjacent work supplies scheduling ideas and evaluation methods.</p>
<form id="research-filters" class="filter-form" data-enhance hidden role="search" aria-label="Filter the research bibliography"><div class="filter-grid"><div class="field search-field"><label for="research-query">Search papers</label><input id="research-query" type="search" autocomplete="off" placeholder="Title, author, method, finding, or DOI" aria-describedby="filter-help"></div><div class="field theme-field"><label for="research-theme">Research theme</label><select id="research-theme"><option value="all">All themes</option>{theme_options}</select></div><div class="field"><label for="research-period">Publication period</label><select id="research-period"><option value="all">All years</option><option value="recent">2023–2026</option><option value="2026">2026 only</option></select></div><div class="field"><label for="research-status">Publication status</label><select id="research-status"><option value="all">All statuses</option><option value="peer-reviewed">Peer reviewed</option><option value="preprint">Preprint</option></select></div></div><div class="filter-actions"><p id="filter-help" class="filter-help">Filters affect the bibliography. Thesis directions stay visible.</p><button type="button" class="plain-button" data-reset-filters>Reset filters</button></div></form>
<noscript><p class="nojs-note">All sources are shown below. Enable JavaScript for filtering and citation copying. The complete BibTeX download remains available.</p></noscript><div class="empty-state" id="empty-state" hidden><p>No sources match these filters.</p><button type="button" class="plain-button" data-reset-filters>Reset filters and show all sources</button></div>
{"".join(groups)}<div class="export-row"><a href="data/Thesis_References.bib" download>Download full BibTeX</a><button id="export-filtered" class="plain-button" type="button" data-enhance hidden>Export filtered references</button></div></section>
<section class="directions" id="directions" aria-labelledby="directions-title"><h2 id="directions-title">Candidate thesis directions</h2><p class="section-intro">Each direction pairs an implementable change with a proof obligation and an experiment. Feasibility is a scoping judgment; novelty and performance remain to be established.</p>{directions}</section>
<section class="proposal-plan directions" id="proposal-plan" aria-labelledby="proposal-title"><h2 id="proposal-title">Build a defensible proposal</h2><p class="section-intro">Use one candidate direction to complete this plan before committing to an implementation.</p><ol class="proposal-steps"><li><strong>Define the problem and model.</strong> Specify the graph representation, permitted updates, output, workload, resource constraints, and the outcome you intend to improve.</li><li><strong>Compare the closest three papers.</strong> Record each paper’s method, assumptions, and overlap with your idea. Identify the precise operation or evidence that your study would add.</li><li><strong>State the changed operation.</strong> Write baseline and proposed pseudocode side by side. Name the ready-set rule or maintained data structure; account for preprocessing and additional storage.</li><li><strong>Set the proof obligation.</strong> Establish dependency safety, termination, cycle detection where required, and the claimed cost bound. Separate correctness from an empirical speed or memory claim.</li><li><strong>Predefine the paired experiment.</strong> Run the same graph instances, seeds, machine, and stopping rules for every method. Measure preprocessing, ordering, schedule quality, and memory separately; report variability and failed cases.</li><li><strong>Plan limits and delivery.</strong> Reserve the first two weeks for replication and novelty checks, the next four to six for implementation and ablations, and the final two to three for analysis and writing. Adjust to your school’s calendar and state what will remain untested.</li></ol><p class="section-intro">Before proposing score-maintenance work, inspect the existing guide’s <a href="Workflow_Research_Guide.html#ref-E20">XLA scheduler record</a>, <a href="Workflow_Research_Guide.html#ref-E21">Dask ordering record</a>, and <a href="Workflow_Research_Guide.html#ref-E29">2026 XLA indexing change</a>. These implementation sources can rule out novelty even when a paper search does not. A useful outcome may be a well-supported boundary on when a modification helps. Keep negative results and report costs even when the preferred hypothesis is not supported.</p></section>
<section class="audit" id="search-audit" aria-labelledby="audit-title"><h2 id="audit-title">Search &amp; coverage</h2><p class="section-intro">{h(data["coverage_note"])}</p><p class="section-intro">This is a curated, non-exhaustive search reviewed on {review_label}. Publication status reflects the checked source record; repeat the search before submitting a proposal.</p><details id="search-audit-details" open><summary>Review the search trail and inclusion limits</summary><div class="audit-body"><h3>Queries used</h3><ul class="query-list">{audit_queries}</ul><h3>Sources consulted</h3><ul>{audit_sources}</ul><h3>Included</h3>{prose_or_list(audit["included"])}<h3>Excluded</h3>{prose_or_list(audit["excluded"])}<h3>Limits of this review</h3>{prose_or_list(audit["limits"])}</div></details></section>
</div></div></main><footer class="site-footer"><div class="wrap footer-inner"><p>Research index · Reviewed {review_label} · Read sources before citing claims.</p><a href="index.html">Back to the learning guide</a></div></footer><script type="application/json" id="thesis-data">{inline_data}</script><script>{js}</script></body></html>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check output is current without changing files.")
    args = parser.parse_args()
    try:
        data = json.loads((ROOT / "data/Thesis_Research.json").read_text(encoding="utf-8"))
        validate(data)
        css = (ROOT / "code/thesis.css").read_text(encoding="utf-8")
        js = (ROOT / "code/thesis.js").read_text(encoding="utf-8")
        outputs = {ROOT / "Thesis_Research.html": render(data, css, js),
                   ROOT / "data/Thesis_References.bib": "\n".join(bibtex(paper) for paper in data["papers"])}
        stale = []
        for path, content in outputs.items():
            if args.check:
                if not path.exists() or path.read_text(encoding="utf-8") != content:
                    stale.append(str(path.relative_to(ROOT)))
            else:
                path.write_text(content, encoding="utf-8")
        if stale:
            print("Stale generated output: " + ", ".join(stale), file=sys.stderr)
            print("Run: python3 tools/build_thesis.py", file=sys.stderr)
            return 1
        verb = "Checked" if args.check else "Built"
        print(f"{verb} Thesis_Research.html and data/Thesis_References.bib ({len(data['papers'])} papers).")
        return 0
    except (OSError, KeyError, ValueError, TypeError) as error:
        print(f"Research build failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
