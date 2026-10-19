"""Independent finite checks of the SAME JavaScript engine embedded in the page.
Python 3 + NetworkX; Node.js runs the engine. No measured speedup is inferred.
"""
from __future__ import annotations
import itertools, json, random, subprocess, hashlib, sys
from pathlib import Path
from datetime import datetime, timezone
import networkx as nx
ROOT=Path(__file__).resolve().parents[2]
rng=random.Random(20261015)
D=json.loads((ROOT/'simulations/data.json').read_text())
requests=[]; checks=[]
def queue(alg, inp, tag, expected=None, trace=False):
 requests.append({'id':alg,'input':inp,'trace':trace});checks.append((tag,expected,inp,alg))
def G(inp):
 g=nx.DiGraph();g.add_nodes_from(inp['nodes']);g.add_edges_from(inp['edges']);return g
def score_order(inp):
 g=G(inp);done=set();order=[];all_scores=[]
 cost={v:sum(f['bytes'] for f in inp['files'] if f['producer']==v) for v in g}
 while len(done)<len(g):
  ready=[v for v in g if v not in done and set(g.predecessors(v))<=done]
  score={v:-cost[v] for v in ready}
  for f in inp['files']:
   if f['producer'] is None or not f['consumers']:continue
   left=set(f['consumers'])-done
   if len(left)==1:
    v=next(iter(left))
    if v in score:score[v]+=f['bytes']
  v=min(ready,key=lambda v:(-score[v],v));all_scores.append(score);order.append(v);done.add(v)
 return order,all_scores
# Every authored sample is executed, not just the default example.
for e in D['engines']:
 for sid in e['examples']:queue(e['id'],D['scenarios'][sid]['input'],'sample',trace=True)
# Accepted task names may also be properties on JavaScript's Object.prototype.
# Check real graph results and optional defaults, not just input acceptance.
named={'nodes':['A','toString','valueOf','B'],
       'edges':[['A','toString'],['toString','valueOf'],['valueOf','B'],['A','B']]}
ng=G(named)
for alg in ('fifo','lifo','priority','lexical','dfs'):
 queue(alg,named,'topological',list(nx.lexicographical_topological_sort(ng)) if alg in ('priority','lexical') else None,trace=True)
queue('scc',named,'scc',{frozenset(x) for x in nx.strongly_connected_components(ng)},trace=True)
named_cycle={**named,'edges':named['edges']+[['valueOf','toString']]}
queue('scc',named_cycle,'scc',{frozenset(x) for x in nx.strongly_connected_components(G(named_cycle))})
queue('reduction',named,'reduction',set(nx.transitive_reduction(ng).edges),trace=True)
queue('critical',named,'critical',{'A':1,'toString':2,'valueOf':3,'B':4},trace=True)
queue('critical',{**named,'duration':{}},'critical',{'A':1,'toString':2,'valueOf':3,'B':4})
queue('bfs',{**named,'source':'A','target':'B'},'bfs',1,trace=True)
queue('priority',{'nodes':['toString','A'],'edges':[],'priority':{'A':-1}},'topological',['toString','A'])
for alg in ('insertion','pk'):
 queue(alg,{**named,'order':named['nodes'],'insert':['B','A']},'insertion',False)
named_files={**named,'files':[
 {'id':'f','producer':'A','consumers':['toString','valueOf'],'bytes':5},
 {'id':'g','producer':'toString','consumers':['valueOf','B'],'bytes':3}]}
named_order,_=score_order(named_files)
for alg in ('fullscore','counters','grouped','maximal'):
 queue(alg,named_files,'storage',named_order,trace=True)
queue('heap',{'nodes':['toString','valueOf'],'edges':[],'events':[
 {'op':'push','task':'toString','priority':1},
 {'op':'push','task':'valueOf','priority':2},
 {'op':'update','task':'toString','priority':3},
 {'op':'pop'},{'op':'pop'},{'op':'pop'}]},'heap',['toString','valueOf'],trace=True)
# All four-node DAGs in one canonical forward orientation; all edge insertions.
ns=list('ABCD');possible=list(itertools.combinations(ns,2));exhaustive_graphs=0
for mask in range(1<<len(possible)):
 edges=[list(e) for j,e in enumerate(possible) if mask>>j&1];inp={'nodes':ns,'edges':edges};g=G(inp);exhaustive_graphs+=1
 queue('enumeration',inp,'enumeration',{tuple(x) for x in nx.all_topological_sorts(g)})
 for u,v in itertools.product(ns,repeat=2):
  gi=g.copy();gi.add_edge(u,v)
  queue('pk',{**inp,'order':ns,'insert':[u,v]},'insertion',nx.is_directed_acyclic_graph(gi))
# Random DAGs: independent topological, reachability, reduction and timing checks.
for case in range(300):
 n=rng.randint(2,7);nodes=list('ABCDEFG'[:n]);perm=rng.sample(nodes,n)
 edges=[[u,v] for i,u in enumerate(perm) for v in perm[i+1:] if rng.random()<.28]
 inp={'nodes':nodes,'edges':edges,'priority':{v:rng.randint(-3,5) for v in nodes},'duration':{v:rng.randint(0,6) for v in nodes},'source':rng.choice(nodes),'target':rng.choice(nodes),'budget':rng.randint(0,8)};g=G(inp)
 for alg in ['fifo','lifo','priority','lexical','dfs']:
  exp=list(nx.lexicographical_topological_sort(g,key=(lambda v:-inp['priority'][v]) if alg=='priority' else None)) if alg in ('priority','lexical') else None
  queue(alg,inp,'topological',exp)
 queue('generations',inp,'generations',[set(x) for x in nx.topological_generations(g)])
 length=nx.shortest_path_length(g,inp['source'],inp['target']) if nx.has_path(g,inp['source'],inp['target']) else None
 queue('bfs',inp,'bfs',length);queue('bounded',inp,'bounded',length)
 queue('reduction',inp,'reduction',set(nx.transitive_reduction(g).edges))
 ef={}
 for v in nx.topological_sort(g):ef[v]=inp['duration'][v]+max([ef[u] for u in g.predecessors(v)]+[0])
 queue('critical',inp,'critical',ef)
 order=list(nx.topological_sort(g));new=rng.sample(nodes,2);gg=g.copy();gg.add_edge(*new)
 for alg in ('pk','insertion'):queue(alg,{**inp,'order':order,'insert':new},'insertion',nx.is_directed_acyclic_graph(gg))
# General directed graphs: cycles and SCCs, not only canonical DAGs.
for case in range(180):
 n=rng.randint(1,7);nodes=list('ABCDEFG'[:n]);edges=[[u,v] for u in nodes for v in nodes if rng.random()<.15]
 inp={'nodes':nodes,'edges':edges,'source':rng.choice(nodes),'target':rng.choice(nodes),'budget':rng.randint(0,7)};g=G(inp)
 queue('scc',inp,'scc',{frozenset(x) for x in nx.strongly_connected_components(g)})
 for alg in ('fifo','lifo','dfs','generations'):queue(alg,inp,'cyclic',not nx.is_directed_acyclic_graph(g))
# Fixed workflow model: Python recomputation independently checks every selection.
for case in range(500):
 n=rng.randint(2,7);nodes=list('ABCDEFG'[:n]);perm=rng.sample(nodes,n)
 edges=[[u,v] for i,u in enumerate(perm) for v in perm[i+1:] if rng.random()<.32]
 inp={'nodes':nodes,'edges':edges};g=G(inp);files=[]
 for k in range(rng.randint(1,16)):
  producer=rng.choice(nodes+[None]);available=nodes if producer is None else sorted(nx.descendants(g,producer))
  consumers=rng.sample(available,rng.randint(0,len(available)))
  files.append({'id':f'f{k}','producer':producer,'consumers':consumers,'bytes':rng.randint(0,40)})
 inp['files']=files;expected,scores=score_order(inp)
 for alg in ('fullscore','counters','grouped','maximal'):queue(alg,inp,'storage',expected,trace=case<15)
 # Independent lifetime calculation, under the declared allocate-before-release model.
 live=set();done=set();peak=0
 for u in expected:
  live.update(i for i,f in enumerate(files) if f['producer']==u)
  peak=max(peak,sum(files[i]['bytes'] for i in live));done.add(u)
  live={i for i in live if not files[i]['consumers'] or not set(files[i]['consumers'])<=done}
 queue('lifetime',{**inp,'order':expected},'lifetime',{'peak':peak,'retained':sum(files[i]['bytes'] for i in live)})
# HEFT: independent interval-insertion implementation, plus legality checks.
def heft_reference(inp):
 g=G(inp);rank={};cost=inp['costs'];comm=inp['communication']
 for v in reversed(list(nx.topological_sort(g))):rank[v]=sum(cost[v])/2+max([comm+rank[u] for u in g.successors(v)]+[0])
 intervals=[[],[]];assigned={};finish={};result=[]
 for v in sorted(g,key=lambda v:(-rank[v],v)):
  candidates=[]
  for p in range(2):
   earliest=max([finish[u]+(0 if assigned[u]==p else comm) for u in g.predecessors(v)]+[0])
   for start,end,_ in sorted(intervals[p]):
    if earliest+cost[v][p]<=start:break
    earliest=max(earliest,end)
   candidates.append((earliest+cost[v][p],p,earliest))
  end,p,start=min(candidates);intervals[p].append((start,end,v));assigned[v]=p;finish[v]=end;result.append({'task':v,'p':p,'start':start,'end':end})
 return result
for case in range(150):
 nodes=list('ABCDEFG'[:rng.randint(2,7)]);perm=rng.sample(nodes,len(nodes));inp={'nodes':nodes,'edges':[[u,v] for i,u in enumerate(perm) for v in perm[i+1:] if rng.random()<.3],'costs':{v:[rng.randint(1,10),rng.randint(1,10)] for v in nodes},'communication':rng.randint(0,5)}
 queue('heft',inp,'heft',heft_reference(inp))
named_heft={**named,'costs':{v:[2,3] for v in named['nodes']},'communication':1}
queue('heft',named_heft,'heft',heft_reference(named_heft),trace=True)
# Versioned heaps: compare with a simple current-priority dictionary.
for case in range(150):
 nodes=list('ABCDE');events=[];current={};out=[]
 for i in range(25):
  if rng.random()<.65:
   v=rng.choice(nodes);pr=rng.randint(-5,8);events.append({'op':'update' if v in current else 'push','task':v,'priority':pr});current[v]=pr
  else:
   events.append({'op':'pop'})
   if current:v=min(current,key=lambda v:(-current[v],v));out.append(v);del current[v]
 queue('heap',{'nodes':nodes,'edges':[],'events':events},'heap',out)
# Negative inputs must be refused; early stopping is checked separately as UNKNOWN.
for alg,inp in [
 ('fifo',{'nodes':['A','A'],'edges':[]}),('fifo',{'nodes':['A'],'edges':[['A','B']]}),('fifo',{'nodes':['A','B'],'edges':[['A','B'],['A','B']]}),
 ('fifo',{'nodes':['constructor'],'edges':[]}),('reduction',{'nodes':['A'],'edges':[['A','A']]}),
 ('counters',{'nodes':['A','B'],'edges':[],'files':[{'id':'f','producer':'A','consumers':['B'],'bytes':1}]}),
 ('heft',{'nodes':['A'],'edges':[],'costs':{'A':[0,1]}}),('pk',{'nodes':['A','B'],'edges':[['A','B']],'order':['B','A'],'insert':['B','A']}),
 ('bounded',{'nodes':['A'],'edges':[],'budget':-1}),('enumeration',{'nodes':list('ABCDEFG'),'edges':[]})]:queue(alg,inp,'reject')
for alg in ('toString','valueOf','constructor','__proto__'):
 queue(alg,{'nodes':['A'],'edges':[]},'reject')
js="""const fs=require('fs'),S=require(process.argv[1]);const q=JSON.parse(fs.readFileSync(0,'utf8'));const out=q.map(x=>{try{const r=S.run(x.id,x.input,!!x.trace);return {result:r.result,frames:x.trace?r.frames:undefined};}catch(e){return {error:e.message};}});process.stdout.write(JSON.stringify(out));"""
proc=subprocess.run(['node','-e',js,str(ROOT/'simulations/engine.js')],input=json.dumps(requests),text=True,capture_output=True,check=True,timeout=40)
results=json.loads(proc.stdout);failures=[];counts={};trace_count=0;winners=0
for k,((tag,exp,inp,alg),got) in enumerate(zip(checks,results)):
 counts[tag]=counts.get(tag,0)+1
 try:
  if tag=='reject':assert got.get('error');continue
  assert not got.get('error'),got.get('error');r=got['result'];g=G(inp)
  if tag=='sample':assert got['frames'];continue
  if tag=='topological':
   assert set(r['order'])==set(g) and len(r['order'])==len(g)
   pos={v:i for i,v in enumerate(r['order'])};assert all(pos[u]<pos[v] for u,v in g.edges)
   if exp is not None:assert r['order']==exp,(r['order'],exp)
  elif tag=='generations':assert [set(x) for x in r['layers']]==exp
  elif tag in ('bfs','bounded'):
   if tag=='bounded':assert r['inspected']<=inp['budget']
   if r['status']=='found':assert exp is not None and len(r['path'])-1==exp and r['path'][0]==inp['source'] and r['path'][-1]==inp['target'] and all(g.has_edge(a,b) for a,b in zip(r['path'],r['path'][1:]))
   if r['status']=='unreachable':assert exp is None
   if tag=='bfs':assert r['status']!='unknown'
  elif tag=='reduction':assert {tuple(e) for e in r['edges']}==exp
  elif tag=='critical':assert r['finish']==exp
  elif tag=='insertion':
   assert r['cycle']==(not exp)
   if exp:
    g.add_edge(*inp['insert']);pos={v:i for i,v in enumerate(r['order'])};assert set(pos)==set(g);assert all(pos[u]<pos[v] for u,v in g.edges)
   else:assert r['order']==inp['order']
  elif tag=='scc':assert {frozenset(c) for c in r['components']}==exp
  elif tag=='cyclic':assert r['cycle']==exp
  elif tag=='enumeration':assert {tuple(x) for x in r['orders']}==exp and len(r['orders'])==len(exp)
  elif tag=='storage':
   assert r['order']==exp,(r['order'],exp)
   if got.get('frames'):
    selected=[f['current'] for f in got['frames'] if f['key']=='choose'];assert selected==exp;winners+=len(selected)
   if alg!='fullscore':assert r['decrements']==sum(max(0,len(q['consumers'])-1) for q in r['groups'])
  elif tag=='lifetime':assert r['peak']==exp['peak'] and r['retained']==exp['retained']
  elif tag=='heft':assert r['schedule']==exp
  elif tag=='heap':assert r['order']==exp
  if got.get('frames'):
   for f in got['frames']:
    assert isinstance(f['message'],str) and f['message'];assert all(x in inp['nodes'] for x in f.get('ready',[]));trace_count+=1
    if alg=='heap':assert all(isinstance(row[2],int) and row[2]>=1 for row in f.get('table',{}).get('rows',[]))
    if alg in ('bfs','heft') and f.get('table'):
     assert all(cell is not None for row in f['table']['rows'] for cell in row), 'Uninitialized task metadata must display a placeholder, not a serialized inherited function.'
 except Exception as e:failures.append({'index':k,'algorithm':alg,'test':tag,'error':str(e),'input':inp,'actual':got.get('result')})
report={'executed_utc':datetime.now(timezone.utc).isoformat(),'seed':20261015,'engine_sha256':hashlib.sha256((ROOT/'simulations/engine.js').read_bytes()).hexdigest(),'oracle':'Independent Python + NetworkX; same JS engine used by browser','cases':len(checks),'counts':counts,'canonical_four_node_DAGs':exhaustive_graphs,'inspected_selection_events':winners,'checked_frames':trace_count,'failures':failures,'scope':'Finite checks of independent teaching implementations on synthetic inputs. No benchmark, novelty, full specialist reproduction or formal verification claim.'}
(ROOT/'tests/simulations/Algorithm_Validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ('failures',)},indent=2));print('FAILURES',len(failures));print(json.dumps(failures[:3],indent=2))
if failures:sys.exit(1)
