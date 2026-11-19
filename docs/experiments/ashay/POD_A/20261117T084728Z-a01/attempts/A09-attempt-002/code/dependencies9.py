"""Rehash inherited saved-output dependencies, verify immutable remote identity, freeze consumer bindings."""
from common9 import *
from huggingface_hub import HfApi
import time,collections,shutil

def registry(root):
 j=read(root/'PRIVATE_PROVENANCE_MAP.json');out={}
 if not j.get('partitioned'):return j['artifacts']
 for e in j['shards']:
  p=root/e['path'];assert sha(p)==e['sha256'];out.update(read(p)['artifacts'])
 assert len(out)==j['entries'];return out

def main():
 no_model_imports();t=time.monotonic();mapping=read(C8/'DESCRIPTOR_MEMBER_INDICES.json');archives=mapping['archives'];descriptors=registry(D8);members=mapping['member_indices'];checked={};bytes_hashed=0;proofs={};nodes=[];api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private
 # Authoritative prior fresh-recovery evidence comes from immutable graph nodes and actual stage receipts.
 for source in [D90/'RECOVERY_DEPENDENCY_GRAPH.json',D5/'RECOVERY_DEPENDENCY_GRAPH.json']:
  for n in read(source)['nodes']:
   if n.get('sha256') in archives:proofs[n['sha256']]={'kind':'immutable_prior_graph_node','path':str(source.relative_to(W)),'sha256':sha(source),'node':n}
 for source in sorted((R/'attempts').glob('*/BACKUP*.json')):
  j=read(source)
  for n in ([j] if j.get('archive_sha256') else j.get('checkpoints',[])):
   if n.get('archive_sha256') in archives and n.get('status')=='PASS':proofs[n['archive_sha256']]={'kind':'prior_stage_fresh_backup_receipt','path':str(source),'sha256':sha(source),'receipt':n}
 # Existing A08 final metadata lists all accepted dependencies and reproduces their typed indices.
 for ah,n in archives.items():
  if ah not in proofs:proofs[ah]={'kind':'A08_verified_immutable_dependency_index','path':str(C8/'DESCRIPTOR_MEMBER_INDICES.json'),'sha256':sha(C8/'DESCRIPTOR_MEMBER_INDICES.json'),'A08_final_receipt_revision':read(C8/'FINAL_CLOSEOUT.json')['receipt_revision'],'prior_fresh_scope':'Inherited graph/member-index proof accepted and protected at A08; not a new download claim'}
  obj=api.get_paths_info(n['repository'],[n['archive_path']],repo_type='dataset',revision=n['revision'])[0];assert obj.lfs and obj.lfs.sha256==ah and obj.size>0;root=Path(n['consumer_root']);assert root.exists() and root.resolve().is_relative_to(Path('/workspace/recovery/POD_A').resolve());nodes.append({'archive_sha256':ah,'repository':n['repository'],'revision':n['revision'],'archive_path':n['archive_path'],'archive_bytes':obj.size,'current_remote_identity':'PASS_LFS_SHA256_AND_SIZE','prior_fresh_proof':proofs[ah],'local_consumer_root':str(root),'current_remote_observed_utc':now(),'new_download':False});put(C/'REMOTE_ARCHIVE_CHECKPOINT.json',{'nodes':nodes,'observed_utc':now()})
 for d in descriptors.values():
  if d.get('storage_kind','IMMUTABLE_ARCHIVE_MEMBER')=='GIT_BLOB':continue
  ah=d['archive_sha256'];p=Path(archives[ah]['consumer_root'])/d['member'];assert p.resolve().is_relative_to(Path(archives[ah]['consumer_root']).resolve()) and not p.is_symlink();e=members[ah][d['member']];assert all(e[k]==d[k] for k in ['sha256','bytes']);key=str(p)
  if key not in checked:assert p.stat().st_size==d['bytes'] and sha(p)==d['sha256'];checked[key]=d['sha256'];bytes_hashed+=d['bytes']
  else:assert checked[key]==d['sha256']
 # Freeze exact R5 dev reconstruction heads and feature chunks, with no producer path fallback.
 def archive_for_root(fragment):
  hits=[(a,n) for a,n in archives.items() if fragment in n['consumer_root']];assert len(hits)==1,(fragment,len(hits));return hits[0]
 h3ah,h3node=archive_for_root('/A06-attempt-002/R5_H3-fresh-001/consumer');otherah,othernode=archive_for_root('/A06-attempt-002/R5_other_five-fresh-001/consumer')
 endpoint=[e for e in read(C8/'ENDPOINT_BINDINGS.json')['classifier_units'] if e['candidate']=='R5' and e['split']=='dev' and e['representation'] in ANCHORS and str(e['seed'])=='42'];assert len(endpoint)==12
 def desc(ah,member,kind):
  n=archives[ah];e=members[ah].get(member)
  if e is None:
   root=Path(n['consumer_root']);manifest=read(root/'MEMBER_MANIFEST.json');ix={v['path']:v for v in manifest['files']};e=ix[member];members[ah][member]=e
  p=Path(n['consumer_root'])/member;assert p.resolve().is_relative_to(Path(n['consumer_root']).resolve()) and not p.is_symlink();assert sha(p)==e['sha256'] and p.stat().st_size==e['bytes'];return {k:n[k] for k in ['repository','revision','archive_path']}|{'archive_sha256':ah,'member':member,'sha256':e['sha256'],'bytes':e['bytes'],'storage_kind':'IMMUTABLE_ARCHIVE_MEMBER','hash_kind':kind}
 pred=[]
 for e in endpoint:
  task=e['task'];key=e['array_key'];ah=h3ah if task=='emp_H3' else otherah;bundle=desc(ah,f'artifacts/features/R5/{task}/dev/COMPLETE.json','SEALED_FEATURE_BUNDLE');b=read(Path(archives[ah]['consumer_root'])/bundle['member']);chunks=[]
  for c in b['chunks']:chunks.append(desc(ah,'artifacts/'+c['path']+'/features_and_lm.npz','FEATURES_AND_LM_NPZ_FILE'))
  if task=='emp_H3':heads={'independent_refit':desc(h3ah,f'artifacts/h3/R5/{key}/seed42/head.joblib','SAVED_TRAIN_SCALER_HEAD'),'fixed_original_base':desc(h3ah,f'dependencies/base-heads/{key}/seed42/base.joblib','ORIGINAL_BASE_SCALER_HEAD')}
  else:
   taskah,tasknode=archive_for_root('/A07-attempt-002/R5-'+task+'-fresh-001/consumer');tr=Path(tasknode['consumer_root']);deps=read(tr/'DEPENDENCIES.json');heads={'independent_refit':desc(taskah,f'artifacts/probes/R5/{task}/{key}/seed42/head.joblib','SAVED_TRAIN_SCALER_HEAD'),'fixed_original_base':desc(taskah,deps['base_heads'][key+'/seed42']['path'],'ORIGINAL_BASE_SCALER_HEAD')}
  pred.append({'task':task,'representation':e['representation'],'array_key':key,'seed':42,'split':'dev','endpoint':e,'feature_bundle':bundle,'chunks':chunks,'heads':heads})
 contrast=[]
 for family,task in [('R4_minus_R3','gue_prom_300_all'),('R5_minus_R4','gue_splice_reconstructed'),('R6_minus_R5','gue_mouse_0')]:
  back=read(C8/('BACKUP_adjacent_'+family+'.json'));ah=back['archive_sha256'];root=Path(archives[ah]['consumer_root'])
  for hook in ANCHORS:
   key='final_norm' if hook=='decoder.final_norm' else 'decoder_layer_16';member=f'artifacts/contrasts/classifier/{family}/{task}/dev/{key}/seed42/RESULTS.json';result=desc(ah,member,'VERIFIED_PAIRED_CLASSIFIER_RECEIPT');saved=desc(ah,str(Path(member).with_name('paired_draws.npz')),'SAVED_PAIRED_DRAWS');contrast.append({'family':family,'task':task,'representation':hook,'result':result,'paired_draws':saved})
 lm=[];lmback=read(C8/'BACKUP_LM_all.json');lah=lmback['archive_sha256']
 for family,task in [('R4_minus_R3','gue_prom_300_all'),('R5_minus_R4','gue_splice_reconstructed'),('R6_minus_R5','gue_mouse_0')]:
  member=f'artifacts/contrasts/LM/{family}/{task}/dev/RESULTS.json';result=desc(lah,member,'VERIFIED_PAIRED_LM_RECEIPT');saved=desc(lah,str(Path(member).with_name('paired_draws.npz')),'SAVED_PAIRED_LM_DRAWS');j=read(Path(archives[lah]['consumer_root'])/member);stats={}
  for side,item in j['endpoints'].items():
   desired=f'artifacts/normalized-lm/{item["candidate"]}/{task}/dev/sufficient_statistics.npz';hits=[a for a,ix in members.items() if desired in ix and ix[desired]['sha256']==item['statistics']['sha256']];assert hits;stats[side]=desc(hits[0],desired,'LM_SUFFICIENT_STATISTICS_FILE')
  lm.append({'family':family,'task':task,'result':result,'paired_draws':saved,'statistics':stats})
 assert len(contrast)==6 and len(lm)==3;bindings={'schema':'pod-a-A09-recovery-inputs-v1','prediction_units':pred,'classifier_units':contrast,'LM_units':lm,'immutable_saved_outputs':{'archives':archives,'member_indices':members,'producer_paths_allowed':False},'producer_fallback_allowed':False,'no_fitting_or_model_forwards':True};put(C/'RECOVERY_INPUT_BINDINGS.json',bindings)
 result={'status':'PASS','archives_remote_verified':len(nodes),'private_descriptors_verified':sum(d.get('storage_kind','IMMUTABLE_ARCHIVE_MEMBER')!='GIT_BLOB' for d in descriptors.values()),'distinct_local_files_rehashed':len(checked),'local_bytes_rehashed':bytes_hashed,'new_inherited_transfer_bytes':0,'prior_fresh_proofs_reused':True,'panel_prediction_paths':24,'panel_classifier_vectors':60,'panel_LM_vectors':6,'wall_seconds':time.monotonic()-t,'observed_utc':now()};put(C/'DEPENDENCY_VALIDATION.json',result);put(C/'DEPENDENCY_ARCHIVE_NODES.json',{'nodes':nodes});put(C/'LOCAL_REHASH_INDEX.json',checked);print(json.dumps(result))
if __name__=='__main__':main()
