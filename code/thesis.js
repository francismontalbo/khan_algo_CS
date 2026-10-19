/* Progressive enhancement; every research entry is rendered by the Python builder. */
(() => {
  'use strict';
  const source = document.getElementById('thesis-data');
  const form = document.getElementById('research-filters');
  if (!source || !form) return;
  let data;
  try { data = JSON.parse(source.textContent); } catch (_) { return; }
  const records = new Map(data.papers.map(paper => [paper.id, paper]));
  const papers = [...document.querySelectorAll('.paper')];
  const groups = [...document.querySelectorAll('.theme-section')];
  const query = document.getElementById('research-query');
  const theme = document.getElementById('research-theme');
  const period = document.getElementById('research-period');
  const status = document.getElementById('research-status');
  const count = document.getElementById('visible-count');
  const empty = document.getElementById('empty-state');
  const exportButton = document.getElementById('export-filtered');
  const normalize = text => String(text).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const haystacks = new Map(papers.map(article => {
    const paper = records.get(article.dataset.paperId);
    return [paper.id, normalize([paper.title, ...paper.authors, paper.venue, paper.year, paper.doi,
      paper.finding, paper.proposal_use, paper.limit, paper.relation].join(' '))];
  }));
  function applyFilters() {
    const terms = normalize(query.value).trim().split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const article of papers) {
      const paper = records.get(article.dataset.paperId);
      const periodMatch = period.value === 'all' || (period.value === 'recent' && paper.year >= 2023 && paper.year <= 2026)
        || (period.value === '2026' && paper.year === 2026);
      const show = terms.every(term => haystacks.get(paper.id).includes(term)) &&
        (theme.value === 'all' || theme.value === paper.theme) && periodMatch &&
        (status.value === 'all' || status.value === paper.status);
      article.hidden = !show;
      if (show) visible += 1;
    }
    groups.forEach(group => { group.hidden = ![...group.querySelectorAll('.paper')].some(paper => !paper.hidden); });
    count.textContent = `${visible} of ${papers.length} sources`;
    empty.hidden = visible !== 0;
    exportButton.disabled = visible === 0;
    exportButton.textContent = `Export ${visible} filtered ${visible === 1 ? 'reference' : 'references'}`;
  }
  function resetFilters() { form.reset(); applyFilters(); }
  form.addEventListener('submit', event => event.preventDefault());
  form.addEventListener('input', applyFilters);
  form.addEventListener('change', applyFilters);
  document.querySelectorAll('[data-reset-filters]').forEach(button => {
    button.addEventListener('click', () => { resetFilters(); query.focus(); });
  });
  function revealLinkedPaper() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    if (!id.startsWith('paper-') && !id.startsWith('theme-')) return;
    const article = document.getElementById(id);
    if (!article || !(article.classList.contains('paper') || article.classList.contains('theme-section'))) return;
    if (article.hidden || article.closest('.theme-section').hidden) resetFilters();
    requestAnimationFrame(() => article.scrollIntoView({block: 'start', behavior: 'instant'}));
  }
  window.addEventListener('hashchange', revealLinkedPaper);
  // A repeated link to the current fragment does not emit hashchange.
  document.querySelectorAll('a[href^="#paper-"],a[href^="#theme-"]').forEach(link => {
    link.addEventListener('click', () => {
      if (link.getAttribute('href') === location.hash) revealLinkedPaper();
    });
  });
  async function copyCitation(button) {
    const paper = records.get(button.dataset.copyCitation);
    const article = button.closest('.paper');
    const message = article.querySelector('.copy-status');
    let copied = false;
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(paper.citation);
        copied = true;
      }
    } catch (_) { /* Local files and denied clipboard permission use a selected text fallback. */ }
    const fallback = article.querySelector('.citation-fallback');
    const textarea = fallback.querySelector('textarea');
    if (!copied) {
      fallback.hidden = false;
      textarea.value = paper.citation;
      textarea.focus();
      textarea.select();
      try { copied = document.execCommand('copy'); } catch (_) { copied = false; }
    }
    if (copied) {
      fallback.hidden = true;
      button.focus();
      message.textContent = 'Citation copied.';
    } else {
      message.textContent = 'Citation selected below. Press Ctrl+C or Command+C to copy.';
    }
  }
  document.querySelectorAll('[data-copy-citation]').forEach(button => {
    button.addEventListener('click', () => copyCitation(button));
  });
  exportButton.addEventListener('click', () => {
    const selectedIds = new Set(papers.filter(article => !article.hidden).map(article => article.dataset.paperId));
    const selected = data.papers.filter(paper => selectedIds.has(paper.id));
    if (!selected.length) return;
    const blob = new Blob([selected.map(paper => paper.bibtex).join('\n')], {type: 'application/x-bibtex;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'Thesis_References_filtered.bib';
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  });
  // Print the complete bibliography, including an expanded search audit.
  const audit = document.getElementById('search-audit-details');
  let auditWasOpen = false;
  window.addEventListener('beforeprint', () => { auditWasOpen = audit.open; audit.open = true; });
  window.addEventListener('afterprint', () => { audit.open = auditWasOpen; });
  document.querySelectorAll('[data-enhance]').forEach(element => { element.hidden = false; });
  applyFilters();
  revealLinkedPaper();
})();
