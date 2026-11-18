"""Exhaustive public key/type/provenance/link validation; no fitting or model access."""
from common import *
from research_guard import guard
import argparse,ast,collections,itertools,math,re
TASKS=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];REPS=['decoder.layers.'+str(i) for i in range(25)]+['decoder.final_norm'];SEEDS=[42,17,1234];POL=['independent_refit','fixed_original_base'];METRICS=['auroc','average_precision','accuracy','balanced_accuracy','classification_cross_entropy']
def rows(p):return list(csv.DictReader(Path(p).open()))
def primary(r,paired=False):return tuple(r[k] for k in (['original_endpoint_id','reference_endpoint_id','task','split','representation','CV_seed','policy','reference_policy','metric','protocol_sha256'] if paired else ['original_endpoint_id','task','split','representation','CV_seed','policy','metric','protocol_sha256']))
def axes():
 for task in TASKS:
  for split in ['dev','test_exploratory'] if task=='emp_H3' else ['dev']:
   for rep,seed,policy,metric in itertools.product(REPS,SEEDS,POL,METRICS):yield task,split,rep,str(seed),policy,metric
def validate():
 guard(allow_dirty=True);schema=read(D/'RESULT_SCHEMAS.json');part=read(D/'TABLE_PARTITIONS.json');points=rows(D/'VERIFIED_METRICS.csv');pairs=[]
 for p in part['logical_PAIRED_CONTRASTS']['partitions']:
  rr=rows(D/p['file']);assert len(rr)==p['rows'] and sha(D/p['file'])==p['sha256'];pairs+=rr
 lm=rows(D/'LM_METRICS_VERIFIED.csv');lp=rows(D/'LM_CONTRASTS_VERIFIED.csv');controls=rows(D/'CONTROL_METRICS_REUSED.csv');assert [len(v) for v in [points,pairs,lm,lp,controls]]==[27300,45360,70,112,210]
 filechecks=[]
 for name,rr,paired in [('VERIFIED_METRICS.csv',points,False),('logical_PAIRED_CONTRASTS',pairs,True),('LM_METRICS_VERIFIED.csv',lm,False),('LM_CONTRASTS_VERIFIED.csv',lp,True),('CONTROL_METRICS_REUSED.csv',controls,False)]:
  keys=[primary(r,paired) for r in rr];assert len(keys)==len(set(keys)),name
  for r in rr:
   assert r['status'] in ['VERIFIED','REUSED_VALIDATED'] and r['task'] in TASKS and r['split'] in ['dev','test_exploratory'];assert r['protocol_sha256']==cfg['protocol_sha256'] and r['coverage_plan_sha256']==cfg['coverage_plan_sha256']
   assert r['original_endpoint_id'] and r['producer_receipt_sha256'] and r['audit_receipt_sha256'];assert r['measurement_attempt'] and r['ingestion_status'] and r['verification_scope']
   if not name.startswith('CONTROL'):assert r['prediction_sha256'] and r['draw_sha256'] and r['prediction_hash_kind']
   for k in schema['numeric_fields']:
    if r[k]:assert math.isfinite(float(r[k]))
   assert r['estimate']
   for k in schema['integer_or_null']:
    if r[k]:assert str(int(r[k]))==r[k] and int(r[k])>=0
   assert int(r['sample_count'])==(1497 if r['task']=='emp_H3' else 512);assert int(r['group_count'])==(1497 if r['task']=='emp_H3' else 511 if r['task']=='gue_splice_reconstructed' else 512)
   if r['bootstrap_attempted']:assert int(r['bootstrap_valid'])+int(r['bootstrap_invalid'])==int(r['bootstrap_attempted'])==2000
   if r['ci_low'] or r['ci_high']:assert r['ci_low'] and r['ci_high'] and float(r['ci_low'])<=float(r['ci_high'])
   else:assert r['ci_missing_reason']
   if r['policy']=='actual_causal_head':assert not r['representation'] and not r['CV_seed'] and int(r['target_count'])>0
   elif r['policy']=='control':assert not r['representation'] and int(r['CV_seed']) in SEEDS
   else:assert r['policy'] in POL and r['representation'] in REPS and int(r['CV_seed']) in SEEDS
   if paired:assert r['direction']=='target-reference' and r['reference_endpoint_id'] and r['reference_policy'] and r['reference_prediction_sha256']
   else:assert r['direction']=='metric_value' and not r['reference']
  filechecks.append({'table':name,'rows':len(rr),'unique_keys':len(set(keys)),'types_provenance_status_counts':'PASS'})
 expected={(alias,*ax) for alias in ['base','R1','R3','R4','R6'] for ax in axes()};actual={(r['checkpoint_alias'],r['task'],r['split'],r['representation'],r['CV_seed'],r['policy'],r['metric']) for r in points};assert expected==actual
 new=[r for r in pairs if r['checkpoint_alias']=='R6' and r['reference']=='R4'];assert len(new)==5460;assert {tuple(r[k] for k in ['task','split','representation','CV_seed','policy','metric']) for r in new}==set(axes());assert sum(r['split']=='dev' for r in new)==4680;assert all(r['adjacent']=='False' for r in new)
 pcounter=collections.Counter((r['checkpoint_alias'],r['reference']) for r in pairs)
 for a,b in [('R1','base'),('R3','base'),('R3','R1'),('R4','base'),('R4','R1'),('R6','base'),('R6','R1'),('R6','R4')]:assert pcounter[a,b]==5460
 for a,b in itertools.product(['R4','R6'],['control_composition','control_kmer4']):assert pcounter[a,b]==420
 assert set(pcounter)=={('R1','base'),('R3','base'),('R3','R1'),('R4','base'),('R4','R1'),('R6','base'),('R6','R1'),('R6','R4')}|set(itertools.product(['R4','R6'],['control_composition','control_kmer4']))
 pointmap={(r['checkpoint_alias'],r['task'],r['split'],r['representation'],r['CV_seed'],r['policy'],r['metric']):r for r in points};cmap={(r['checkpoint_alias'],r['task'],r['split'],r['CV_seed'],r['metric']):r for r in controls};maxdelta=0.
 for r in pairs:
  target=pointmap[r['checkpoint_alias'],r['task'],r['split'],r['representation'],r['CV_seed'],r['policy'],r['metric']]
  reference=cmap[r['reference'],r['task'],r['split'],r['CV_seed'],r['metric']] if r['reference'].startswith('control_') else pointmap[r['reference'],r['task'],r['split'],r['representation'],r['CV_seed'],r['reference_policy'],r['metric']]
  err=abs(float(r['estimate'])-(float(target['estimate'])-float(reference['estimate'])));maxdelta=max(maxdelta,err);assert err<=1e-12
 lmmap={(r['checkpoint_alias'],r['task'],r['split'],r['metric']):r for r in lm};maxlm=0.
 for r in lp:
  err=abs(float(r['estimate'])-(float(lmmap[r['checkpoint_alias'],r['task'],r['split'],r['metric']]['estimate'])-float(lmmap[r['reference'],r['task'],r['split'],r['metric']]['estimate'])));maxlm=max(maxlm,err);assert err<=1e-12
  assert int(r['target_count'])==int(lmmap[r['checkpoint_alias'],r['task'],r['split'],r['metric']]['target_count'])==int(lmmap[r['reference'],r['task'],r['split'],r['metric']]['target_count'])
 # Explicit manual linear-quantile check on the seven saved new LM distributions.
 import numpy as np
 lmci=0.
 for p in (A/'analysis/LM_R6_minus_R4').rglob('ANALYSIS.json'):
  with np.load(p.parent/'paired_draws.npz',allow_pickle=False) as z:
   valid=z['valid'];assert valid.dtype==np.bool_ and valid.shape==(2000,) and valid.all()
   for r in read(p)['rows']:
    v=np.sort(z[r['metric']][valid]);ci=[]
    for q in [.025,.975]:
     rank=(len(v)-1)*q;lo=math.floor(rank);hi=math.ceil(rank);ci.append(float(v[lo]+(rank-lo)*(v[hi]-v[lo])))
    err=max(abs(ci[0]-r['ci_low']),abs(ci[1]-r['ci_high']));lmci=max(lmci,err);assert err<=1e-12
 pending=rows(D/'PENDING_ADJACENT_CONTRASTS.csv');plm=rows(D/'PENDING_ADJACENT_LM.csv');edges={('R2','R1'),('R3','R2'),('R4','R3'),('R5','R4'),('R6','R5')};assert len(pending)==27300 and len(plm)==70;assert {(r['target'],r['reference']) for r in pending}==edges
 for rr,fields in [(pending,['family','task','split','representation','CV_seed','policy','metric']),(plm,['family','task','split','metric'])]:
  assert len(rr)==len({tuple(r[k] for k in fields) for r in rr})
  for r in rr:assert not r['estimate'] and not r['ci_low'] and not r['ci_high'] and r['reason'] and r['status'] in ['BLOCKED','PENDING']
 pd=rows(D/'POLICY_POINT_DIFFERENCES.csv');assert len(pd)==5460
 for r in pd:
  p=pointmap[r['candidate'],r['task'],r['split'],r['representation'],r['CV_seed'],'independent_refit',r['metric']];f=pointmap[r['candidate'],r['task'],r['split'],r['representation'],r['CV_seed'],'fixed_original_base',r['metric']];assert float(r['refit_minus_fixed_point'])==float(p['estimate'])-float(f['estimate']);assert not r['ci_low'] and not r['ci_high'] and r['reason']
 claims=rows(D/'CLAIMS_TO_EVIDENCE.csv');assert len(claims)==6
 allkeys={primary(r):r for r in points+lm};pairkeys={primary(r,True):r for r in pairs+lp}
 for r in claims:
  for k in json.loads(r['row_keys']):
   fields=schema['paired_primary_key'] if k.get('reference_endpoint_id') else schema['metric_primary_key'];key=tuple(k.get(f,'') for f in fields);assert key in (pairkeys if k.get('reference_endpoint_id') else allkeys)
 # Every recorded plot value is an exact released row; no pending cell can enter.
 plot=rows(D/'PLOT_DATA/plotted_values.csv');assert len(plot)==30886
 for r in plot:
  r['protocol_sha256']=cfg['protocol_sha256']
  rr=pairkeys.get(primary(r,True)) if r['reference'] else allkeys.get(primary(r))
  if rr is None and r['checkpoint_alias'].startswith('control_'):rr=cmap[r['checkpoint_alias'],r['task'],r['split'],r['CV_seed'],r['metric']]
  assert rr is not None and r['status']==rr['status']
  for k in ['estimate','ci_low','ci_high']:assert r[k]==rr[k]
 figures=read(D/'FIGURE_VALIDATION.json');assert figures['status']=='PASS' and figures['figure_count']==31 and figures['plotted_values_csv_sha256']==sha(D/'PLOT_DATA/plotted_values.csv')
 for n,h in figures['data_sources'].items():assert sha(D/n)==h
 for r in figures['figures']:
  for f in r['files']:p=D/f['path'];assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256']
 # Generic parsability/privacy/safe-path/link sweep. Local absolute private provenance
 # locators in JSON/CSVs are metadata, never public downloadable payloads.
 jsons=csvs=jsonls=sources=links=0
 for p in sorted(D.rglob('*')):
  if not p.is_file():continue
  assert not p.is_symlink() and p.resolve().is_relative_to(D.resolve());data=p.read_bytes();assert p.suffix not in ['.npy','.npz','.joblib','.pt','.bin','.distcp'];assert len(data)<(50 if p.suffix=='.csv' else 20)*1024**2
  assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----)',data)
  assert not re.search(rb'"sequence"\s*:\s*"[ACGTN]{30,}"',data)
  if p.suffix=='.json':json.loads(data,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)));jsons+=1
  elif p.suffix=='.jsonl':
   for line in data.splitlines():json.loads(line,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
   jsonls+=1
  elif p.suffix=='.csv':
   reader=csv.reader(data.decode().splitlines());header=next(reader);assert len(header)==len(set(header));assert all(len(r)==len(header) for r in reader);csvs+=1
  elif p.suffix=='.py':ast.parse(data);sources+=1
  elif p.suffix=='.md':
   # Ignore code fences when checking actual Markdown hyperlinks.
   prose=re.sub(r'```.*?```','',data.decode(),flags=re.S)
   for target in re.findall(r'\]\(([^)]+)\)',prose):
    if target.startswith(('https:','http:','#','mailto:')):continue
    dest=target.split('#',1)[0];assert (p.parent/dest).exists(),(str(p),target);links+=1
 for e in read(D/'SOURCE_SUPPLEMENT.json')['report_plot_recovery_source']:assert sha(D/e['path'])==e['sha256']
 assert read(D/'JOB_DISPOSITION.json')['scientific_jobs']=='QUIESCENT';assert not read(D/'INVALIDATED_OUTPUTS.json').get('invalidated_units',[])
 result={'status':'PASS','scope':'A08 qualified complete released report; full project remains partial','tables':filechecks,'complete_classifier_keyspace':27300,'complete_new_contrast_keys':5460,'pending_adjacent_classifier_keys':27300,'pending_adjacent_LM_keys':70,'paired_point_join_max_abs':maxdelta,'LM_point_join_max_abs':maxlm,'new_LM_manual_interval_max_abs':lmci,'figure_count':31,'plotted_released_records':len(plot),'JSON_files_parsed':jsons,'JSONL_files_parsed':jsonls,'CSV_files_parsed':csvs,'Python_sources_parsed':sources,'relative_Markdown_links_checked':links,'public_payload_extensions_and_secret_scan':'PASS','duplicate_keys_or_dropped_keys':0,'scientific_jobs':'QUIESCENT','guard':guard(allow_dirty=True),'validated_utc':now()};put(C/'RELEASE_VALIDATION.json',result);publish('RELEASE_VALIDATION.json',result);print(json.dumps(result))
def seal():
 guard(allow_dirty=True);assert read(D/'RELEASE_VALIDATION.json')['status']=='PASS';files=[{'path':str(p.relative_to(D)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(D.rglob('*')) if p.is_file() and p.name!='OUTPUT_SHA256SUMS'];manifest=''.join(e['sha256']+'  '+e['path']+'\n' for e in files);publish('OUTPUT_SHA256SUMS',manifest);proof={'schema':'pod-a-a08-publication-seal-v1','status':'PASS','files':files,'output_manifest_sha256':sha(D/'OUTPUT_SHA256SUMS'),'sealed_utc':now(),'research_parent':git('rev-parse','HEAD'),'exact_commit_bound_separately':True};put(C/'PUBLICATION_SEAL.json',proof);print(json.dumps({'status':'SEALED','files':len(files),'bytes':sum(e['bytes'] for e in files),'manifest_sha256':proof['output_manifest_sha256']}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--seal',action='store_true');args=p.parse_args();seal() if args.seal else validate()
