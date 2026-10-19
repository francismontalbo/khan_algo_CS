"""Verify content preservation, exports and local assets of the final reader."""
from pathlib import Path
import json, hashlib, re
from html.parser import HTMLParser
from datetime import datetime,timezone
from zipfile import ZipFile
ROOT=Path(__file__).resolve().parents[2]
class Document(HTMLParser):
 def __init__(self,t):
  super().__init__(convert_charrefs=True);self.ids=[];self.links=[];self.media=[];self.scripts={};self.current=None;self.template_depth=0;self.feed(t)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if tag=='template':self.template_depth+=1;return
  if self.template_depth:return
  if a.get('id'):self.ids.append(a['id'])
  if tag=='a' and a.get('href'):self.links.append(a['href'])
  if tag in ['img','script','link'] and (a.get('src') or a.get('href')):self.media.append(a.get('src') or a.get('href'))
  if tag=='script':self.current=a.get('id');self.scripts[self.current]=''
 def handle_data(self,data):
  if self.current is not None:self.scripts[self.current]+=data
 def handle_endtag(self,tag):
  if tag=='template':self.template_depth=max(0,self.template_depth-1);return
  if self.template_depth:return
  if tag=='script':self.current=None
results=[]
def ck(name,test):
 results.append({'check':name,'passed':bool(test)});assert test,name
p=Document((ROOT/'Workflow_Research_Guide.html').read_text())
d=json.loads(p.scripts['explorer-data']);sources=json.loads((ROOT/'data/Reviewed_Sources.json').read_text())
ck('58 selectable records preserved',len([m for m in d['methods'] if not m.get('branch')])==58)
ck('36 evidence records including local record',len(sources)==36 and sum(x['id']=='E25' for x in sources)==1)
ck('35 external records preserved',sum(x['id']!='E25' for x in sources)==35)
ck('Original source identifiers preserved',{s['id'] for s in sources}=={s['id'] for s in json.loads((ROOT/'archive/Before_Final_Edition/data/Reviewed_Sources.json').read_text())})
ck('Displayed and exported records agree',json.loads(p.scripts['download-data'])['sources']==sources and d['sources']==sources)
for id,path in [('explorer-data','data/Explorer_Data.json'),('learning-data','data/Learning_Resources.json'),('reference-data','data/Terminology.json'),('simulation-data','simulations/data.json'),('applications-data','applications/data.json')]:
 ck('Embedded data matches '+path,json.loads(p.scripts[id])==json.loads((ROOT/path).read_text()))
old=json.loads((ROOT/'release/Original_Algorithm_Hashes.json').read_text())
with ZipFile(ROOT/'reference/Original_Research_Package.zip') as original:
 for fn,sha in old.items():
  ck('Original algorithm retained in reference ZIP '+fn,hashlib.sha256(original.read('Workflow_Research_Guide/'+fn)).hexdigest()==sha)
  if fn!='simulations/engine.js':ck('Unchanged working algorithm preserved '+fn,hashlib.sha256((ROOT/fn).read_bytes()).hexdigest()==sha)
ck('Browser executes the tested simulator',p.scripts['simulation-engine'].strip()==(ROOT/'simulations/engine.js').read_text().strip())
t=json.loads((ROOT/'data/Terminology.json').read_text());ids={e['id'] for e in t['entries']}
ck('249 distinct definitions',len(t['entries'])==len(ids)==249)
ck('Related terminology resolves',all(x in ids for e in t['entries'] for x in e.get('related',[])))
l=json.loads((ROOT/'data/Learning_Resources.json').read_text());ck('Every term has a learning route',ids<=set(l['term_routes']))
ck('63 learning resources',len(l['resources'])==63)
ck('Learning counts agree',sum(r['kind']=='Video' for r in l['resources'])==27 and sum(r['kind']!='Video' for r in l['resources'])==36)
sim=json.loads((ROOT/'simulations/data.json').read_text());ck('23 simulators and 33 scenarios',len(sim['engines'])==23 and len(sim['scenarios'])==33)
ck('Every selectable method has a qualified simulation route',set(sim['methods'])=={m['id'] for m in d['methods'] if not m.get('branch')})
app=json.loads((ROOT/'applications/data.json').read_text());ck('Application catalog preserved',len(app['profiles'])==23 and len(app['sources'])==31 and len(app['scenarios'])==16)
ck('All examples resolve',all(a['scenario'] in sim['scenarios'] for a in app['profiles']))
for fn in ['Workflow_Research_Guide.html','Workflow_Visual_Comparison.html','Algorithm_Applications.html','Algorithm_Simulations.html','Algorithm_Lessons.html','Workflow_Learning_Resources.html','Workflow_Terms_and_Nomenclature.html']:
 doc=Document((ROOT/fn).read_text());ck('Unique element IDs '+fn,len(doc.ids)==len(set(doc.ids)))
 ck('No remote script required '+fn,all(not x.startswith(('http:','https:')) for x in doc.media))
 ck('No unsafe hyperlink schemes '+fn,all(not x.lower().startswith(('javascript:','vbscript:','data:')) for x in doc.links))
ck('Compatible entry names are identical',(ROOT/'Workflow_Research_Guide.html').read_bytes()==(ROOT/'Workflow_Visual_Comparison.html').read_bytes())
report={'executed_at':datetime.now(timezone.utc).isoformat(),'checks':len(results),'passed':sum(x['passed'] for x in results),'details':results,'working_simulator_sha256':hashlib.sha256((ROOT/'simulations/engine.js').read_bytes()).hexdigest(),'original_simulator_sha256':old['simulations/engine.js'],'scope':'Internal artifact consistency and original algorithm retention in the reference ZIP. The working simulator includes maintenance fixes and is checked against the embedded browser engine; not independent validation of all scientific claims.'}
(ROOT/'tests/final/Integrity_Results.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(results),'artifact integrity checks')
