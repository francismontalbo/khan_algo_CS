/* Interface helpers only. Research state and algorithm behavior are untouched. */
(() => {
 'use strict';
 const header=document.getElementById('ui-header');
 const menu=document.getElementById('ui-more');
 const links=[...document.querySelectorAll('[data-ui-nav]')];
 const back=document.getElementById('ui-back-top');
 const reduced=()=>window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 const destinations=['compare','lineage-tree','questions','test','idea','review-audit','references'].map(id=>document.getElementById(id)).filter(Boolean);
 function updateHeight(){if(header)document.documentElement.style.setProperty('--header-height',header.getBoundingClientRect().height+'px');}
 function currentSection(){let id='compare';const edge=(header?.getBoundingClientRect().height||0)+100;for(const el of destinations){if(el.getBoundingClientRect().top<=edge)id=el.id;}return id;}
 function paintNav(){const lessonOpen=document.getElementById('learning-dialog')?.open;const id=lessonOpen?'algorithms':currentSection();for(const a of links){if(a.dataset.uiNav===id)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');}if(back)back.hidden=window.scrollY<650;}
 let raf=false;
 window.addEventListener('scroll',()=>{if(!raf){raf=true;requestAnimationFrame(()=>{raf=false;paintNav();});}},{passive:true});
 window.addEventListener('resize',updateHeight);
 if(window.ResizeObserver&&header)new ResizeObserver(updateHeight).observe(header);
 const summary=menu?.querySelector('summary');
 if(menu){menu.addEventListener('toggle',()=>summary?.setAttribute('aria-expanded',String(menu.open)));document.addEventListener('click',e=>{if(menu.open&&!menu.contains(e.target))menu.open=false;});document.addEventListener('keydown',e=>{if(e.key==='Escape'&&menu.open&&!document.querySelector('dialog[open]')){menu.open=false;summary?.focus();}});}
 function jump(id){const target=document.getElementById(id);if(!target)return;for(let parent=target;parent;parent=parent.parentElement)if(parent.tagName==='DETAILS')parent.open=true;if(id==='top')window.scrollTo({top:0,behavior:'instant'});else target.scrollIntoView({behavior:'instant',block:'start'});try{history.replaceState(null,'','#'+id);}catch(_){}const heading=target.querySelector('h1,h2')||target;heading.setAttribute('tabindex','-1');heading.focus({preventScroll:true});paintNav();}
 document.addEventListener('click',e=>{const a=e.target.closest('[data-ui-jump]');if(a){e.preventDefault();if(menu)menu.open=false;jump(a.dataset.uiJump);return;}const trigger=e.target.closest('[data-ui-forward]');if(trigger){e.preventDefault();if(menu)menu.open=false;document.getElementById(trigger.dataset.uiForward)?.click();return;}if(menu?.open&&e.target.closest('.ux-menu-panel button'))menu.open=false;});
 if(back)back.onclick=()=>jump('top');
 for(const d of document.querySelectorAll('dialog')){new MutationObserver(paintNav).observe(d,{attributes:true,attributeFilter:['open']});d.addEventListener('close',()=>{paintNav();requestAnimationFrame(()=>{if(document.activeElement===document.body||!document.activeElement?.getClientRects().length){(links.find(x=>x.dataset.uiNav==='algorithms')||summary)?.focus({preventScroll:true});}});});}
 updateHeight();paintNav();
})();
