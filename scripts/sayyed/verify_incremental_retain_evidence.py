"""Independent table/alias/missingness checks; no new scientific measurements."""
from pathlib import Path
import csv,json,hashlib,subprocess,time,math,shutil
r=Path('/workspace/meeting-artifacts/incremental-retain-eval-v1');w=Path('/workspace/wt-incremental-retain-eval');d=w/'docs/experiments/ashay/incremental-retain-eval-v1';n=Path('/workspace/meeting-artifacts/multiretain-comparison-v1');start=time.monotonic();cpu=time.process_time()
def read(p):return list(csv.DictReader(p.open()))
def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
expected=['emp_H3','gue_tf_0','gue_prom_core_all','gue_prom_300_all','gue_splice_reconstructed','gue_mouse_0'];declared={'R1':{'emp_H3'},'R3':set(expected[:3])};mapping={'base_refit':('base','refit'),'h3_only_refit':('R1','refit'),'h3_only_fixed_base':('R1','fixed_base'),'new_refit':('R3','refit'),'new_fixed_base':('R3','fixed_base')}
protocol=load(r/'COMPARISON_PROTOCOL.json');assert protocol['authoritative_sequence']=={f'R{i}':expected[:i] for i in range(1,7)};assert load(r/'PROTOCOL_FROZEN.json')['protocol_sha256']==sha(r/'COMPARISON_PROTOCOL.json')
original=read(n/'reports/native_metrics.csv');annotated=read(r/'tables/REUSED_METRICS.csv');assert len(original)==len(annotated)==13650
for a,b in zip(original,annotated):
 assert all(a[k]==b[k] for k in a);assert (b['stage_alias'],b['readout'])==mapping[a['policy']];assert math.isfinite(float(b['value']));assert b['origin']=='REUSED_COMPLETED'
lookup={(x['stage_alias'],x['task'],x['split'],x['layer'],x['cv_seed'],x['readout'],x['metric']):x for x in annotated};assert len(lookup)==len(annotated)
anchors=read(r/'tables/STAGE_ANCHORS.csv');assert len(anchors)==2520;missing=0
for x in anchors:
 stage=x['stage'];task=x['task'];assert x['split']==('test' if task=='emp_H3' else 'dev')
 if stage not in ['base','R1','R3']:
  assert x['value']=='' and x['source_row']=='' and x['status']=='AWAITING_DELIVERY';assert x['checkpoint_declaration']=='unresolved-no-checkpoint';missing+=1
 else:
  q=lookup[(stage,task,x['split'],x['layer'],x['cv_seed'],'refit' if stage=='base' else x['policy'],x['metric'])];assert x['value']==q['value'];assert x['source_row']==q['source_row']
  if stage!='base':assert x['checkpoint_declaration']==('included-in-config' if task in declared[stage] else 'not-in-config')
 assert x['exposure']=='unknown'
 if stage=='base':expected_role='separate-pretrained-reference'
 else:
  index=int(stage[1:]);ti=expected.index(task);expected_role='newly-included-in-plan' if ti==index-1 else 'already-included-in-plan' if ti<index-1 else 'not-yet-included-in-plan'
 assert x['meeting_role']==expected_role
assert missing==1440
# Index source tables once; never recompute or average saved confidence intervals.
sources={name:read(n/'reports'/name) for name in ['native_contrasts.csv','h3_only_minus_base_reference.csv']};contrasts=read(r/'tables/REUSED_CONTRASTS.csv');assert len(contrasts)==16380
for x in contrasts:
 y=sources[Path(x['source_file']).name][int(x['source_row'])-2];assert all(x[k]==v for k,v in y.items());assert x['contrast_relation']==('nonadjacent' if x['stage']=='R3' and x['reference_stage']=='R1' else 'base-reference')
adj=read(r/'tables/ADJACENT_STAGE_STATUS.csv');assert len(adj)==5
for i,x in enumerate(adj,2):assert x['previous']==f'R{i-1}' and x['current']==f'R{i}' and x['status']=='awaiting-delivery' and x['difference']==x['ci_low']==x['ci_high']==''
# All three Markdown tables bind unique source points and original conditional CIs.
text=(d/'RESULTS.md').read_text();policy='new_refit';layer='decoder_layer_16';mdrows=0
for line in text.splitlines():
 if line.startswith('A fixed-base probe'):policy='new_fixed_base'
 if line.startswith('The new/refitted'):policy='new_refit';layer='final_norm'
 if not line.startswith('| ') or not any(line.startswith('| '+t+'/') for t in expected):continue
 cells=[v.strip() for v in line.strip('|').split('|')];task,split=cells[0].split('/')
 for stage,cell in zip(['base','R1','R3'],cells[1:4]):
  key=(stage,task,split,layer,'42','fixed_base' if policy=='new_fixed_base' and stage!='base' else 'refit','auroc');assert cell==f"{float(lookup[key]['value']):.6f}"
 for ref,cell in zip(['R1','base'],cells[4:6]):
  x=next(x for x in contrasts if all(x[k]==v for k,v in dict(stage='R3',reference_stage=ref,task=task,split=split,layer=layer,cv_seed='42',policy=policy,metric='auroc').items()));assert cell==f"{float(x['difference']):+.6f} [{float(x['ci_low']):+.6f}, {float(x['ci_high']):+.6f}]"
 mdrows+=1
assert mdrows==18
fig=load(r/'FIGURE_INPUTS.json');assert fig['stage_coverage_source_sha256']==sha(r/'tables/STAGE_ANCHORS_AUROC.csv')
for x in fig['figures']:assert sha(Path(x['path']))==x['sha256']
for path in (d/'figures').glob('*.png'):
 if path.name=='stage_coverage.png':continue
 b=subprocess.check_output(['git','show','c79ab07e763a9754c68fdaf7d0730d8458f508dc:docs/experiments/ashay/multiretain-comparison-v1/figures/'+path.name],cwd=w);assert hashlib.sha256(b).hexdigest()==sha(path)
for p in (r/'tables').glob('*.csv'):assert sha(p)==sha(d/'tables'/p.name)
result=dict(status='PASS',reused_scalar_rows=13650,annotated_anchor_rows=2520,missing_anchor_rows=1440,reused_contrast_rows=16380,markdown_anchor_rows=18,adjacent_stage_rows=5,all_adjacent_pending=True,stage_coverage_visually_reviewed=True,figure_scope='New coverage PNG visually inspected; old four PNGs verified byte-identical to previously reviewed c79ab07 figures. No GPU extraction or numerical model metric recalculation.',new_model_measurements=0,tests='2 focused stage/adjacency tests PASS; synthetic planning logic, not scientific measurements',wall_seconds=time.monotonic()-start,cpu_process_seconds=time.process_time()-cpu,source_sha256=sha(Path(__file__)),files=[dict(path=str(p.relative_to(r)),sha256=sha(p)) for p in [r/'CHECKPOINT_REGISTRY.json',r/'COMPARISON_PROTOCOL.json',r/'LIVE_INVENTORY.json',*sorted((r/'tables').glob('*.csv'))]],reuse_check={k:v for k,v in load(r/'REUSE_VERIFICATION.json').items() if k!='sources'})
for p in [r/'VERIFY.json',d/'VERIFY.json']:p.write_text(json.dumps(result,indent=2)+'\n')
print({k:v for k,v in result.items() if k not in ['files','reuse_check']},flush=True)
