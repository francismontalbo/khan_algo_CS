/* Final navigation and export integration; algorithms are untouched. */
(() => {
 'use strict';
 if(window.workflowFinalEdition)return;
 const info={edition:'Final edition',updated:'2026-10-15',scope:'Targeted final verification; not exhaustive novelty certification.'};
 const sim=document.querySelector('[data-ui-nav="simulations"]')||document.querySelector('#ui-header [data-sim-open]');
 if(sim)sim.dataset.uiNav='simulations';
 const nav=[...document.querySelectorAll('[data-ui-nav]')];
 let scheduled=false;
 const activeNav=()=>{scheduled=false;
  const top=[...document.querySelectorAll('dialog[open]')].find(d=>d.contains(document.activeElement));
  let key=top?.id==='sim-dialog'?'simulations':top?.id==='learning-dialog'?'algorithms':null;
  if(!key){key='compare';const edge=(document.getElementById('ui-header')?.getBoundingClientRect().height||0)+100;for(const id of ['compare','lineage-tree','questions','test','idea','review-audit','references']){const el=document.getElementById(id);if(el&&el.getBoundingClientRect().top<=edge)key=id;}}
  for(const item of nav){if(item.dataset.uiNav===key)item.setAttribute('aria-current','location');else item.removeAttribute('aria-current');}
 };
 const queue=()=>{if(!scheduled){scheduled=true;requestAnimationFrame(activeNav);}};
 for(const d of document.querySelectorAll('dialog'))new MutationObserver(queue).observe(d,{attributes:true,attributeFilter:['open']});
 document.addEventListener('focusin',queue);
 window.addEventListener('scroll',queue,{passive:true});
 const back=document.getElementById('ui-back-top');if(back)back.setAttribute('aria-label','Return to the top of the research guide');
 // Retain the final presentation when a comparison is saved and opened offline.
 function addToExport(html){
  if(html.includes('id="final-edition-style"'))return html;
  const style=document.getElementById('final-edition-style');
  const script=document.getElementById('final-edition-app');
  const module=(style?style.outerHTML:'')+(script?script.outerHTML:'');
  const i=html.toLowerCase().lastIndexOf('</body>');return i<0?html+module:html.slice(0,i)+module+html.slice(i);
 }
 if(window.workflowReference){const prior=workflowReference.addToExport;workflowReference.addToExport=html=>addToExport(prior(html));}
 // Method-reference links use published addresses. Never open an untrusted scheme.
 for(const a of document.querySelectorAll('a[target="_blank"]'))a.rel='noopener noreferrer';
 window.workflowFinalEdition={...info,addToExport};
})();
