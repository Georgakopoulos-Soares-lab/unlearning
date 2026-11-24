"""Complete deterministic plot-source mappings; no additional inferential families."""
from s09_common import *
import sys,collections
COLORS=['#246b9e','#db7840','#6a4c93'];POLICY_LABEL={'independent_refit':'Refitted','fixed_original_base':'Original readout'}
def make_specs(root):
 prof=rows(root/'LAYER_PROFILES.jsonl');ref=rows(root/'REFERENCE_MARGINALS.jsonl');lm=rows(root/'LM_MARGINALS_REUSED.jsonl');cases=read(root/'CANDIDATES.json');contr=[]
 for c in cases:
  for t in TASKS:contr.extend(rows(root/'contrasts'/c/t/'CONTRASTS.jsonl'))
 pi={(r['candidate'],r['task'],r['representation'],r['seed'],r['policy'],r['metric']):r for r in prof};ci={(r['c'],r['t'],r['r'],r['s'],r['p'],r['m'],r['f'],r['reference_label']):r for r in contr}
 source={r['endpoint_id']:r for r in prof+ref};source.update({r['id']:r for r in contr});source.update({r['planned_spec_id']:r for r in lm})
 captions={
 'profiles':'All 26 representations and all three CV seeds; seed42 has 95% pointwise exploratory conditional marginal intervals. Colors distinguish CV partitions, not intervention replicates. Block16 is the seventeenth decoder block; FN is final normalization. Ranking accessibility and original-readout compatibility differ across supplied endpoints; no layer is selected for inference.',
 'forests':'Target minus exact qualified reference at frozen block16 and final normalization anchors. All three seeds, both policies and original-base/composition/4mer references are shown. Bars are paired 95% pointwise exploratory conditional intervals; crossing zero does not establish equivalence. Negative classifier CE differences favor the candidate; other metric differences favor positive values.',
 'heatmaps':'Complete candidate-by-representation signed candidate-minus-original-base differences for every CV seed and policy. A common zero-centered scale is used across panels within this metric/task. Values are descriptive; cell color does not imply familywise significance. Readout compatibility need not follow refitted accessibility.',
 'gaps':'All admitted anchor AUROC(refitted)-AUROC(original readout) gaps, three seeds and nine checkpoints. Bars are paired 95% pointwise exploratory conditional intervals. Positive means greater refitted AUROC, with no universal higher-is-better ordering or causal mechanism claim.',
 'sweep':'Each supplied checkpoint is a separate labeled endpoint with observed intervention label and checkpoint step. LM NLL and perplexity are distinct from classifier CE. DEV is primary; TRAIN is diagnostic in its separate figure. No verified common lineage, matched exposure, seed/layer replication or checkpoint-pair inference is implied.',
 'metrics':'All five classifier metrics at the two frozen anchors for all checkpoints, both policies and three seeds. CE is in nats; all other values are unitless. Ranking, thresholded decisions and probability loss need not agree. LM remains separately displayed in the supplied-endpoint figures; no synthetic capability score is used.',
 'seeds':'Descriptive maximum-minus-minimum point estimate across all three frozen CV partitions, for every checkpoint/representation/policy/metric. These ranges are not confidence intervals or independent intervention replication. Zero ranges can reflect identical all-TRAIN models and predictions; S08 diagnostics document those coincidences.',
 'coverage':'Frozen intended comparison universe with admitted and deferred categories explicitly separated. Deferred cells are unknown, not measured zero. Whole-delivery inventory remains PARTIAL despite complete admitted nine-checkpoint benign scope.'}
 def label(c):
  r=cases[c];return c.replace('candidate_','C')+' '+r['label'].replace('saliency_maxent_ht_emp_h3_','')+' / step'+str(r['step'])
 def point_id(r):return r.get('endpoint_id',r.get('id',r.get('planned_spec_id')))
 def line(rr,x=None,color='#246b9e',name='',interval=False,horizontal=False,marker='o',linestyle='-'):
  return {'row_ids':[point_id(r) for r in rr],'x':list(range(len(rr))) if x is None else x,'y':[r['canonical_metric']['estimate'] if 'planned_spec_id' in r and r.get('policy')=='LM' else r['estimate'] for r in rr],'low':[(r['canonical_metric'] if r.get('policy')=='LM' else r).get('ci_low') for r in rr] if interval else None,'high':[(r['canonical_metric'] if r.get('policy')=='LM' else r).get('ci_high') for r in rr] if interval else None,'color':color,'label':name,'horizontal':horizontal,'marker':marker,'linestyle':linestyle}
 specs=[]
 def add(fid,family,title,panels,nrows,ncols,size):
  specs.append({'id':fid,'family':family,'title':title,'caption':captions[family],'panels':panels,'nrows':nrows,'ncols':ncols,'size_inches':size,'split':'dev' if not fid.endswith('train') else 'train','uncertainty':'95% pointwise exploratory conditional where intervals shown; seed ranges are descriptive','dpi':130,'seed_convention':'All42/17/1234; seed42onlycompact marginalCI convention','representation_convention':'Layer16 iszero-based17thdecoderblock; FN=finalnormalization','candidate_labels':{c:label(c) for c in cases}})
 for t in TASKS:
  for metric in METRICS:
   panels=[];allvals=[]
   for c in cases:
    for policy in POLICIES:
     lines=[]
     for j,seed in enumerate(SEEDS):
      rr=[pi[c,t,r,seed,policy,metric] for r in REPS];lines.append(line(rr,color=COLORS[j],name='CV seed '+str(seed),interval=seed==42,marker='.',linestyle='-'));allvals.extend(v for r in rr for v in [r['estimate'],r['ci_low'],r['ci_high']] if v is not None)
     panels.append({'title':label(c)+' | '+POLICY_LABEL[policy],'kind':'lines','lines':lines,'xlabel':'Representation: zero-based blocks, FN','ylabel':metric+(' (nats/example)' if metric=='cross_entropy' else ''),'representation_axis':True})
   lo=min(allvals);hi=max(allvals);pad=max(.01,(hi-lo)*.06)
   for panel in panels:panel['ylim']=[max(0,lo-pad) if metric=='cross_entropy' else 0,hi+pad if metric=='cross_entropy' else 1.02]
   add('profiles-'+t+'-'+metric,'profiles',t+' · '+metric+' · all checkpoints / policies / CV seeds',panels,9,2,[18,24])
   panels=[]
   for c in cases:
    for representation in ['decoder.layers.16','decoder.final_norm']:
     lines=[]
     for sj,seed in enumerate(SEEDS):
      for pj,policy in enumerate(POLICIES):
       for rj,reference in enumerate(['original_base','composition','4mer']):
        family='base_reference' if reference=='original_base' else 'DNA_control';row=ci[c,t,representation,seed,policy,metric,family,reference];lines.append(line([row],x=[sj*6+pj*3+rj],color=COLORS[rj],name=reference+' / '+POLICY_LABEL[policy]+' / seed'+str(seed),interval=True,horizontal=True,marker='o' if pj==0 else 's',linestyle='none'))
     panels.append({'title':label(c)+' | '+('block16 (17th)' if representation==REPS[16] else 'final normalization'),'kind':'lines','lines':lines,'xlabel':'Signed '+metric+' difference (candidate − reference)','ylabel':'CV seed (6 readout/reference combinations)','zero':True,'yticks':[2.5,8.5,14.5],'yticklabels':['42','17','1234']})
   add('forests-'+t+'-'+metric,'forests',t+' · '+metric+' · paired anchor comparisons',panels,9,2,[18,25])
   panels=[];mx=max(abs(r['estimate']) for r in contr if r['t']==t and r['m']==metric and r['f']=='base_reference') or 1
   for seed in SEEDS:
    for policy in POLICIES:
     rr=[[ci[c,t,r,seed,policy,metric,'base_reference','original_base'] for r in REPS] for c in cases];panels.append({'title':'CV seed '+str(seed)+' | '+POLICY_LABEL[policy],'kind':'matrix','values':[[r['estimate'] for r in row] for row in rr],'row_ids':[[r['id'] for r in row] for row in rr],'vmin':-mx,'vmax':mx,'cmap':'RdBu_r','ylabel':'Supplied checkpoint','xlabel':'Representation: zero-based blocks, FN','representation_axis':True,'yticklabels':[label(c) for c in cases],'colorbar_label':'Signed '+metric+' difference'})
   add('heatmaps-'+t+'-'+metric,'heatmaps',t+' · '+metric+' · differences from original base',panels,3,2,[21,15])
  panels=[]
  for representation in [REPS[16],REPS[-1]]:
   lines=[]
   for sj,seed in enumerate(SEEDS):
    rr=[ci[c,t,representation,seed,'independent_refit','AUROC','anchor_policy_gap','fixed_original_base'] for c in cases];lines.append(line(rr,x=[i+sj*.2-.2 for i in range(9)],color=COLORS[sj],name='CV seed '+str(seed),interval=True,horizontal=True,linestyle='none'))
   panels.append({'title':'block16 (17th block)' if representation==REPS[16] else 'final normalization','kind':'lines','lines':lines,'xlabel':'AUROC refitted − original readout','ylabel':'Supplied checkpoint','zero':True,'yticks':list(range(9)),'yticklabels':[label(c) for c in cases]})
  add('gaps-'+t,'gaps',t+' · all 54 admitted anchor policy gaps',panels,1,2,[20,7])
  panels=[]
  for metric in METRICS:
   for representation in [REPS[16],REPS[-1]]:
    lines=[]
    for sj,seed in enumerate(SEEDS):
     for pj,policy in enumerate(POLICIES):
      rr=[pi[c,t,representation,seed,policy,metric] for c in cases];lines.append(line(rr,x=[i+(sj-1)*.10+pj*.04 for i in range(9)],color=COLORS[sj],name='seed'+str(seed)+' / '+POLICY_LABEL[policy],marker='o' if pj==0 else 's',linestyle='none'))
    panels.append({'title':metric+' | '+('block16 (17th)' if representation==REPS[16] else 'final norm'),'kind':'lines','lines':lines,'xlabel':'Checkpoint endpoint (labels/steps below)','ylabel':metric+(' (nats/example)' if metric=='cross_entropy' else ''),'xticks':list(range(9)),'xticklabels':[c.replace('candidate_','C') for c in cases]})
  add('metrics-'+t,'metrics',t+' · ranking, decisions and classifier probability loss',panels,5,2,[17,18])
  panels=[]
  for metric in METRICS:
   for policy in POLICIES:
    matrix=[];ids=[]
    for c in cases:
     rr=[[pi[c,t,r,s,policy,metric] for s in SEEDS] for r in REPS];matrix.append([max(q['estimate'] for q in item)-min(q['estimate'] for q in item) for item in rr]);ids.append([[q['endpoint_id'] for q in item] for item in rr])
    panels.append({'title':metric+' | '+POLICY_LABEL[policy],'kind':'range_matrix','values':matrix,'row_ids':ids,'vmin':0,'vmax':max(max(v) for v in matrix) or 1e-15,'cmap':'viridis','ylabel':'Checkpoint','xlabel':'Representation: zero-based blocks, FN','representation_axis':True,'yticklabels':[c.replace('candidate_','C') for c in cases],'colorbar_label':metric+' seed range (not CI)'})
  add('seeds-'+t,'seeds',t+' · descriptive sensitivity to frozen CV partitions',panels,5,2,[18,22])
 for split in ['dev','train']:
  panels=[]
  for t in TASKS:
   for metric in ['LM_NLL','LM_PPL']:
    rr=[next(r for r in lm if r['candidate_alias']==c and r['task']==t and r['split']==split and r['canonical_metric']['metric']==metric) for c in cases];panels.append({'title':t+' | '+metric,'kind':'lines','lines':[line(rr,interval=split=='dev',linestyle='none')],'xlabel':'Supplied endpoint: nominal label / observed step','ylabel':metric+(' (nats/target)' if metric=='LM_NLL' else ' (exp NLL)'),'xticks':list(range(9)),'xticklabels':[label(c) for c in cases],'rotate_labels':True})
  add('supplied-LM-'+split,'sweep','Supplied endpoints · '+('DEV primary LM measurements' if split=='dev' else 'TRAIN LM diagnostics only'),panels,6,2,[22,30])
 disp=read(root/'COMPARISON_DISPOSITION.json');panels=[{'kind':'coverage','title':'Exact frozen specification counts','labels':['base reference','DNA controls','anchor policy gap','immediate parent (deferred)','LM base (deferred)'],'values':[42120,6480,324,42120,108],'colors':['#246b9e']*3+['#999999']*2,'source_disposition_sha256':sha(root/'COMPARISON_DISPOSITION.json')}];add('coverage','coverage','Frozen scientific scope · nine checkpoints / six benign tasks',panels,1,1,[12,6])
 # Apply outcome-independent comparable-axis rules to the entire displayed scope.
 for spec in specs:
  if spec['family'] in ['forests','gaps']:
   vals=[v for p in spec['panels'] for line in p['lines'] for field in ['y','low','high'] for v in (line[field] or []) if v is not None];low=min(0,min(vals));high=max(0,max(vals));pad=max(.005,(high-low)*.04)
   for p in spec['panels']:p['xlim']=[low-pad,high+pad]
  elif spec['family']=='metrics':
   for j in range(0,10,2):
    pair=spec['panels'][j:j+2];values=[v for p in pair for line in p['lines'] for v in line['y']];low=min(values);high=max(values);pad=max(.005,(high-low)*.05)
    for p in pair:p['ylim']=[max(0,low-pad),high+pad]
  elif spec['family']=='seeds':
   for j in range(0,10,2):
    pair=spec['panels'][j:j+2];maximum=max(v for p in pair for row in p['values'] for v in row)
    for p in pair:p['vmax']=maximum if maximum else 1;p['all_exact_zero']=maximum==0
 # Validate every mapping before any rendering, including nested three-seed range dependencies.
 for spec in specs:
  identifiers=[]
  for panel in spec['panels']:
   if panel['kind']=='coverage':continue
   if panel['kind']=='lines':
    for item in panel['lines']:
     for i,rid in enumerate(item['row_ids']):
      row=source[rid];val=row['canonical_metric'] if row.get('policy')=='LM' else row;assert item['y'][i]==val['estimate'];identifiers.append(rid)
      if item['low'] is not None:assert item['low'][i]==val['ci_low'] and item['high'][i]==val['ci_high']
   else:
    for i,row in enumerate(panel['row_ids']):
     for j,rid in enumerate(row):
      if panel['kind']=='range_matrix':vv=[source[x]['estimate'] for x in rid];assert panel['values'][i][j]==max(vv)-min(vv);identifiers.extend(rid)
      else:assert panel['values'][i][j]==source[rid]['estimate'];identifiers.append(rid)
  spec['source_row_ids']=sorted(set(identifiers));spec['source_rows_sha256']=digest([source[rid] for rid in spec['source_row_ids']]);spec['spec_sha256']=digest(spec)
 return specs,source

if __name__=='__main__':
 root=Path(sys.argv[1]) if len(sys.argv)>1 else P;out=Path(sys.argv[2]) if len(sys.argv)>2 else P
 specs,source=make_specs(root);sd=out/'figure-specs';sd.mkdir(parents=True,exist_ok=True)
 for s in specs:save(sd/(s['id']+'.json'),s)
 save(out/'PLOT_SOURCE_INDEX.json',{'status':'PASS_ALL_VALUES_AND_BOUNDS_JOINED','figure_count':len(specs),'unique_profile_rows_in_profiles':len({rid for s in specs if s['family']=='profiles' for rid in s['source_row_ids']}),'unique_contrasts_in_figures':len({rid for s in specs for rid in s['source_row_ids'] if rid in source and 'f' in source[rid]}),'figures':[{'id':s['id'],'family':s['family'],'source_row_ids':s['source_row_ids'],'source_rows_sha256':s['source_rows_sha256'],'spec_sha256':s['spec_sha256'],'spec_file_sha256':sha(sd/(s['id']+'.json'))} for s in specs]});print('FIGURE_SOURCE_SPECIFICATIONS_VERIFIED',len(specs),flush=True)
