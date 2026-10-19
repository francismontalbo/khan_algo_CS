"""Check named application fixtures independently of the browser rendering."""
from pathlib import Path
import json,subprocess,hashlib,zipfile
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[2]
d=json.loads((ROOT/'applications/data.json').read_text());s=json.loads((ROOT/'simulations/data.json').read_text())
req=[{'id':p['engine'],'input':s['scenarios'][p['scenario']]['input']} for p in d['profiles']]
runner="const E=require(process.argv[1]);let s='';process.stdin.on('data',x=>s+=x);process.stdin.on('end',()=>console.log(JSON.stringify(JSON.parse(s).map(x=>E.run(x.id,x.input,false).result))));"
r=json.loads(subprocess.check_output(['node','-e',runner,str(ROOT/'simulations/engine.js')],input=json.dumps(req).encode()))
res=dict(zip([p['id'] for p in d['profiles']],r));checks=[]
def ck(name,ok):
 checks.append({'name':name,'passed':bool(ok)})
 assert ok,name
ck('Every profile has a source and a named example',all(p['refs'] and p['scenario'] in s['scenarios'] for p in d['profiles']))
ck('All source IDs resolve',all(i in d['sources'] for p in d['profiles'] for i in p['refs']))
ck('All method routes resolve',all(x['engine'] in res for x in d['routes'].values()))
for p in d['profiles']:
 x=res[p['id']];inp=s['scenarios'][p['scenario']]['input']
 if 'order' in x and p['id'] not in ['insertion','pk','heap']:
  order=x['order'];pos={v:i for i,v in enumerate(order)}
  ck('Dependencies respected: '+p['id'],len(order)==len(inp['nodes']) and len(pos)==len(inp['nodes']) and all(pos[a]<pos[b] for a,b in inp['edges']))
ck('Django-shaped script order',res['fifo']['order']==['jQuery','calendar','time','noConflict'])
ck('Cycle-free lock repair',res['pk']['order']==res['insertion']['order']==['ConfigLock','CacheLock','UserLock','LogLock'])
ck('BFS shortest lock path',res['bfs']['path']==['CacheLock','UserLock','LogLock'])
ck('Unfinished search is unknown',res['bounded']['status']=='unknown')
ck('Only necessary CI edges retained',res['reduction']['edges']==[['Compile','UnitTests'],['UnitTests','Package'],['Package','Deploy']])
ck('Two exact tiny plans',len(res['enumeration']['orders'])==2)
ck('Critical path arithmetic',res['critical']['makespan']==2+5+2+1)
ck('Recursive functions grouped',set(map(frozenset,res['scc']['components']))=={frozenset(['ParseCfg','ExpandVar']),frozenset(['ReadCfg']),frozenset(['StartApp'])})
ck('Stale Email entry not executed',res['heap']['order']==['Email','Backup','Index'])
ck('Equivalent byte priorities',res['fullscore']['order']==res['counters']['order']==res['grouped']['order'])
ck('Counter counts on named fixture',res['counters']['decrements']==2 and res['grouped']['decrements']==1 and res['maximal']['decrements']==0)
# Independent file-lifetime replay, output allocation precedes input release.
inp=s['scenarios']['app-photo-files']['input'];live=set();done=set();peak=0
for v in res['lifetime']['order']:
 for f in inp['files']:
  if f['producer']==v:live.add(f['id'])
 peak=max(peak,sum(f['bytes'] for f in inp['files'] if f['id'] in live))
 done.add(v)
 for f in inp['files']:
  if f['consumers'] and set(f['consumers'])<=done:live.discard(f['id'])
ck('Independent file lifetime accounting',peak==1240000==res['lifetime']['peak'] and res['lifetime']['retained']==100000)
ck('HEFT modeled schedule contract',len(res['heft']['schedule'])==5 and res['heft']['makespan']==12)
ck('Low remaining-use cache choice',res['lrc']['victim']=='Temp')
ck('Equivalent positional recovery',res['sortscan']['sorted']==res['sortscan']['scanned']==['BuildB','BuildE','BuildG'])
# Preserve original implementations in the reference ZIP while testing the maintained engine above.
original=json.loads((ROOT/'release/Original_Algorithm_Hashes.json').read_text())
with zipfile.ZipFile(ROOT/'reference/Original_Research_Package.zip') as archive:
 for rel, expected in original.items():
  ck('Original algorithm retained in reference ZIP: '+rel,hashlib.sha256(archive.read('Workflow_Research_Guide/'+rel)).hexdigest()==expected)
  if rel!='simulations/engine.js':ck('Unchanged working algorithm: '+rel,hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected)
ck('Current preprint version retained',next(x for x in json.loads((ROOT/'data/Reviewed_Sources.json').read_text()) if x['id']=='E34')['url'].endswith('v3'))
report={'checked':datetime.now(timezone.utc).isoformat(),'checks':len(checks),'passed':sum(c['passed'] for c in checks),'details':checks,'application_results':res,'scope':'Synthetic application-shaped fixtures. Correctness and preservation checks, not production benchmarks or novelty evidence.'}
(ROOT/'tests/applications/Example_Results.json').write_text(json.dumps(report,indent=2))
print('PASS',len(checks),'application-specific checks')
