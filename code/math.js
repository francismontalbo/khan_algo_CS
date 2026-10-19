/* Presentation only: preserve the original evidence, inputs and algorithm traces. */
(() => {
  'use strict';
  if (window.workflowMath || !window.katex) return;
  const read = id => JSON.parse(document.getElementById(id)?.textContent || '{}');
  const reference = read('math-reference');
  const normalize = value => String(value ?? '').replace(/\s+/g, ' ').trim();
  const expressions = new Map(Object.entries({...read('math-catalog'), ...reference.expressions})
    .map(([source, tex]) => [normalize(source), tex]));
  const symbols = new Map(Object.entries(reference.symbols || {}).map(([source, tex]) => [normalize(source), tex]));
  const errors = [];
  const options = {throwOnError:true, strict:'error', trust:false, output:'htmlAndMathml', maxExpand:1000, maxSize:10};
  const escapeText = value => String(value).replace(/[\\{}%$&#_^~]/g, c => ({
    '\\':'\\textbackslash{}','{':'\\{','}':'\\}','%':'\\%','$':'\\$','&':'\\&',
    '#':'\\#','_':'\\_','^':'\\textasciicircum{}','~':'\\textasciitilde{}'
  })[c]);
  const operator = {'⇒':'\\Longrightarrow','⇔':'\\Longleftrightarrow','≤':'\\le','≥':'\\ge','≠':'\\ne',
    '∈':'\\in','∉':'\\notin','∪':'\\cup','∩':'\\cap','⊆':'\\subseteq','⊂':'\\subset',
    '→':'\\to','⇝':'\\rightsquigarrow','←':'\\leftarrow','−':'-','·':'\\cdot','×':'\\times',
    'Σ':'\\sum','∀':'\\forall','∅':'\\varnothing','∖':'\\setminus','∞':'\\infty',
    '₀':'_{0}','ᵥ':'_{v}','ₜ':'_{t}','²':'^{2}','³':'^{3}'};
  // Trace labels are generated from user-supplied task names. Tokenize them as
  // text/notation, never treat arbitrary task names as executable TeX commands.
  function traceTex(source) {
    const tokens = source.match(/[A-Za-z][A-Za-z0-9_]*|\d+(?:\.\d+)?|\s+|[^\s]/gu) || [];
    return tokens.map((token, i) => {
      if (/^\s+$/.test(token)) return '\\, ';
      if (Object.hasOwn(operator, token)) return operator[token] + ' ';
      if (/^\d/.test(token)) return token;
      if (/^[A-Za-z]/.test(token)) {
        const next = tokens.slice(i + 1).find(t => !/^\s+$/.test(t));
        if (next === '(' && token.length > 1) return '\\operatorname{' + escapeText(token) + '}';
        if (token.includes('_')) {
          const [base, ...sub] = token.split('_');
          return (base.length === 1 ? base : '\\operatorname{' + escapeText(base) + '}') + '_{\\mathrm{' + escapeText(sub.join('_')) + '}}';
        }
        return token.length === 1 || token === 'EF' || token === 'EFT' ? token : '\\text{' + escapeText(token) + '}';
      }
      if (token === '{' || token === '}') return '\\' + token;
      if ('=+-(),:;[]|<>.!'.includes(token)) return token;
      return '\\text{' + escapeText(token) + '}';
    }).join('');
  }
  function texFor(source) {
    const text = normalize(source);
    return expressions.get(text) || symbols.get(text) || traceTex(text);
  }
  function typeset(element, source, tex, display = false) {
    if (element.dataset.mathRendered === 'true' && element.querySelector('.katex')) return;
    element.dataset.mathSource = source;
    element.dataset.mathTex = tex;
    element.setAttribute('data-no-glossary', '');
    element.classList.add('wf-math', display ? 'wf-math-display' : 'wf-math-inline');
    try {
      katex.render(tex, element, {...options, displayMode:display});
      element.dataset.mathRendered = 'true';
    } catch (error) {
      element.textContent = source;
      element.dataset.mathRendered = 'false';
      const detail = {source, tex, message:error.message};
      if (!errors.some(e => e.source === source)) errors.push(detail);
    }
  }
  const blockSelector = '.algorithm-formula,.math-statement,.formula,.equation,.formula-cell,.sim-equation .math,.sim-details-grid .wide>p:first-of-type';
  const symbolSelector = '.term-select,#term-heading,.term-related button,#term-tooltip h3,.reference-table a,.term-link[data-term-id]';
  const excluded = 'script,style,pre,code,svg,math,textarea,input,select,option,button,.katex,.wf-math,[contenteditable="true"]';
  const inlineExpressions = new Map([
    ...[...expressions].filter(([text]) => text.length >= 4 && /[=<>≤≥∈Σ⇒∖→⇝]|^[OΘΩ]\(/.test(text)),
    ...[...symbols].filter(([text]) => text.length > 1 && /[_^()₀-₉]/u.test(text))
  ]);
  const inlineSources = [...inlineExpressions.keys()].sort((a,b) => b.length-a.length);
  function elements(root, selector) {
    return [...(root.matches?.(selector) ? [root] : []), ...root.querySelectorAll(selector)];
  }
  function render(root = document.body) {
    if (!root || root.nodeType !== 1 || root.closest?.('script,style,svg,math,.katex')) return;
    for (const element of elements(root, blockSelector)) {
      if (element.dataset.mathRendered === 'true' && element.querySelector('.katex')) continue;
      const source = normalize(element.textContent), known = expressions.get(source);
      if (known || element.matches('.sim-equation .math,.equation')) typeset(element, source, known || texFor(source), true);
    }
    for (const element of elements(root, symbolSelector)) {
      const source = normalize(element.textContent), tex = symbols.get(source);
      if (tex) typeset(element, source, tex, false);
    }
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: node => node.parentElement?.closest(excluded) || !node.nodeValue.trim()
        ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      if (!node.isConnected) continue;
      const text = node.nodeValue;
      let start = 0, fragment = null;
      while (start < text.length) {
        let match = null;
        for (const source of inlineSources) {
          let at = text.indexOf(source, start);
          while (at >= 0 && ((at && /[\p{L}\p{N}_]/u.test(text[at-1])) || /[\p{L}\p{N}_]/u.test(text[at+source.length] || ''))) at = text.indexOf(source, at+1);
          if (at >= 0 && (!match || at < match.at)) match = {source,at};
        }
        if (!match) break;
        fragment ||= document.createDocumentFragment();
        fragment.append(document.createTextNode(text.slice(start, match.at)));
        const span = document.createElement('span');
        typeset(span, match.source, inlineExpressions.get(match.source), false);
        fragment.append(span);
        start = match.at + match.source.length;
      }
      if (fragment) { fragment.append(document.createTextNode(text.slice(start))); node.replaceWith(fragment); }
    }
  }
  function addToExport(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    if (doc.getElementById('math-app')) return html;
    const ids = ['math-vendor-style','math-style','math-vendor','math-catalog','math-reference','math-app'];
    for (const id of ids) {
      const original = document.getElementById(id);
      if (original) (original.tagName === 'STYLE' ? doc.head : doc.body).append(original.cloneNode(true));
    }
    return '<!doctype html>\n' + doc.documentElement.outerHTML;
  }
  window.workflowMath = {render,texFor,addToExport,errors};
  let scheduled = false;
  const pending = new Set();
  const observer = new MutationObserver(changes => {
    for (const change of changes) {
      const target = change.target.nodeType === 1 ? change.target : change.target.parentElement;
      if (!target || target.closest('script,style,svg,math,.katex')) continue;
      if (target.closest('.wf-math')?.querySelector('.katex') && !target.matches('.sim-equation .math')) continue;
      pending.add(target);
    }
    if (!pending.size || scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      const work = [...pending]; pending.clear();
      observer.disconnect();
      for (const node of work) if (node.isConnected && !work.some(other => other !== node && other.contains(node))) render(node);
      observer.observe(document.body, {childList:true,subtree:true,characterData:true});
    });
  });
  render();
  observer.observe(document.body, {childList:true,subtree:true,characterData:true});
})();
