"""Independent finite checks for new teaching code; no performance claims."""
from pathlib import Path
from datetime import datetime,timezone
from itertools import permutations
from graphlib import TopologicalSorter,CycleError
import json,random,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'code'))
from algorithm_foundations import *

def valid(g,o):
    return len(o)==len(g) and sorted(o)==list(range(len(g))) and all(o.index(u)<o.index(v) for u,row in enumerate(g) for v in row)
def closure(g):
    n=len(g);a=[[i==j or j in g[i] for j in range(n)] for i in range(n)]
    for k in range(n):
        for i in range(n):
            for j in range(n):a[i][j]=a[i][j] or (a[i][k] and a[k][j])
    return a
def oracle_cyclic(g):
    pred={v:[u for u,row in enumerate(g) if v in row] for v in range(len(g))}
    try:list(TopologicalSorter(pred).static_order());return False
    except CycleError:return True
checks=0
for bits in range(64):
    possible=[(i,j) for i in range(4) for j in range(i+1,4)]
    g=make_graph(4,[e for k,e in enumerate(possible) if bits>>k&1])
    orders=[p for p in permutations(range(4)) if valid(g,list(p))]
    assert tuple(kahn(g)) in orders and tuple(dfs_order(g)) in orders
    assert is_topological(g,kahn(g))
    tr=transitive_reduction(g);assert closure(g)==closure(tr)
    for u,row in enumerate(tr):
        for v in row:assert not reachable(tr,u,v,skip=(u,v))
    for u in range(4):
        for v in range(4):
            gg=[list(r) for r in g]
            if v not in gg[u]:gg[u].append(v)
            try:
                result,o=insert_edge_reference(g,kahn(g),u,v)
                assert not oracle_cyclic(gg) and valid(result,o)
            except ValueError:assert oracle_cyclic(gg)
            checks+=1
rng=random.Random(841901)
for _ in range(400):
    n=rng.randrange(0,19);per=list(range(n));rng.shuffle(per)
    g=make_graph(n,[(per[i],per[j]) for i in range(n) for j in range(i+1,n) if rng.random()<0.2])
    assert valid(g,kahn(g)) and valid(g,dfs_order(g))
    score=[rng.randrange(-4,7) for _ in range(n)]
    out=priority_kahn(g,score);completed=set()
    for u in out:
        ready=[v for v in range(n) if v not in completed and all(p in completed for p,row in enumerate(g) if v in row)]
        assert u==min(ready,key=lambda v:(-score[v],v));completed.add(u)
    c=closure(g);tr=transitive_reduction(g);assert c==closure(tr)
    for u in range(n):
        for v in range(n):assert reachable(g,u,v)==c[u][v]
    duration=[rng.randrange(0,8) for _ in range(n)];ef=earliest_finish(g,duration)
    # Independent path accumulation from each vertex rather than topological DP.
    costs=[0]*n
    def walk(u,total):
        total+=duration[u];costs[u]=max(costs[u],total)
        for v in g[u]:walk(v,total)
    for u in range(n):walk(u,0)
    assert ef==costs
for n in range(1,10):
    order=list(range(n));rng.shuffle(order);rows=consumer_events(range(n),order,8)
    credits=[r for r in rows if r['credit']]
    assert len(credits)==1 and credits[0]['credit_to']==order[-1]
    assert len(rows[-1]['remaining'])==0
negative=0
for fn in (kahn,dfs_order,transitive_reduction):
    try:fn(make_graph(2,[(0,1),(1,0)]));raise AssertionError('cycle accepted')
    except ValueError:negative+=1
assert not is_topological(make_graph(2,[(0,1)]),[1,0]);negative+=1
try:make_graph(2,[(0,1),(0,1)]);raise AssertionError('duplicate accepted')
except ValueError:negative+=1
report={'executed_at':datetime.now(timezone.utc).isoformat(),'random_seed':841901,'exhaustive_forward_four_vertex_graphs':64,'edge_insertion_cases':checks,'random_dags':400,'negative_checks':negative,'same_policy_agreement':True,'reachability_and_reduction_verified':True,'critical_path_checked_independently':True,'examples':traces(),'scope':'Finite checks of independently written teaching code only. No video-content audit, novelty certification, or Montage performance benchmark.'}
(R/'tests/algorithm_lessons/Code_Checks.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k!='examples'},indent=2))
