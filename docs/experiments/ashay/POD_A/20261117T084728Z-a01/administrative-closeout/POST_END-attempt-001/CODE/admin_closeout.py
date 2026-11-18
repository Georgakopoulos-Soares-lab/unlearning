"""One finite administrative-only Pod A handoff correction. No science or service start."""
from pathlib import Path,PurePosixPath
import argparse,ast,csv,datetime,fcntl,hashlib,json,os,re,shutil,subprocess,sys,tarfile,time

C=Path('/workspace/agent-handoff/POD_A/20261117T084728Z-a01/administrative-closeout/POST_END-attempt-001')
cfg=json.loads((C/'RUN_CONFIG.json').read_text());W=Path(cfg['worktree']);B=Path(cfg['run_docs']);D=Path(cfg['docs']);A=Path(cfg['artifacts']);REC=Path(cfg['recovery']);R=C.parent.parent;C9=R/'attempts/A09-attempt-001';D9=B/'attempts/A09-attempt-001';REPO='ashay-sriv/undo-evo2-pilot-backup-20261020'
OLD=cfg['research_input_commit'];PIN=cfg['prompt_commit'];NAMES=cfg['owned_root_files'];DENY=re.compile(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----)')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def bh(b):return hashlib.sha256(b).hexdigest()
def atomic(p,b):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name('.'+p.name+'.tmp');t.write_bytes(b);os.replace(t,p)
def put(p,v):
 assert isinstance(v,(dict,list));atomic(p,(json.dumps(v,indent=2,allow_nan=False)+'\n').encode())
def md(p,v):assert isinstance(v,str) and v.startswith('# ') and '\n\n' in v;atomic(p,(v.rstrip()+'\n').encode())
def g(*args,cwd=W):return subprocess.check_output(['git','-C',str(cwd),*args])
def git(*args):return g(*args).decode().strip()
def owned(p):return p in [str((B/n).relative_to(W)) for n in NAMES] or p.startswith(str(D.relative_to(W))+'/')
def expected_head():return read(C/'GIT_DELIVERY.json')['commit'] if (C/'GIT_DELIVERY.json').exists() else OLD
def guard(dirty=True,head=None):
 assert W.resolve()==W and git('rev-parse','--show-toplevel')==str(W)
 assert git('branch','--show-current')=='POD_A' and str(Path(git('rev-parse','--git-common-dir')).resolve())==cfg['research_common_directory']
 for flag in [[],['--push']]:assert git('remote','get-url',*flag,'origin')=='https://github.com/Georgakopoulos-Soares-lab/unlearning.git'
 M=Path('/workspace/repos/unlearning-pod-a');assert g('ls-files','--stage','-z',cwd=M)==(C/'MAIN_INDEX_BEFORE.z').read_bytes();assert g('status','--porcelain=v1','-z',cwd=M)==(C/'MAIN_STATUS_BEFORE.z').read_bytes()
 before=dict(l.split() for l in (C/'REFS_BEFORE.txt').read_text().splitlines());after=dict(l.split() for l in git('for-each-ref','--format=%(refname) %(objectname)').splitlines());exclude={'refs/heads/POD_A','refs/remotes/origin/POD_A'};assert {k:v for k,v in before.items() if k not in exclude}=={k:v for k,v in after.items() if k not in exclude}
 actual=git('rev-parse','HEAD');assert actual==(head or expected_head()),'Unexpected research advance'
 baseline=read(C/'BASELINE.json');assert git('rev-parse',actual+':'+str((B/'attempts').relative_to(W)))==baseline['attempts_git_tree'],'Immutable attempts changed'
 status=g('status','--porcelain=v1','-z','--untracked-files=all');assert dirty or not status
 for entry in status.split(b'\0'):
  if entry:assert owned(entry[3:].decode()),'Unowned dirty path'
 return {'status':'PASS','head':actual,'branch':'POD_A','worktree':str(W),'common_directory':cfg['research_common_directory'],'main_index_status_and_other_refs_unchanged':True,'A01_A09_attempts_tree_unchanged':baseline['attempts_git_tree']}
def write(p,data):
 guard();assert owned(str(p.relative_to(W))) and p.resolve().is_relative_to(B.resolve()) and not p.is_symlink()
 if isinstance(data,(dict,list)):put(p,data)
 elif p.suffix=='.md':md(p,data.decode() if isinstance(data,bytes) else data)
 else:atomic(p,data.encode() if isinstance(data,str) else data)
def alive(pid,ticks):
 try:
  s=(Path('/proc')/str(pid)/'stat').read_text().split();return s[2]!='Z' and s[21]==str(ticks)
 except (FileNotFoundError,ProcessLookupError):return False
def observe():
 root=Path('/workspace/agent-handoff/POD_A/review-loop');h=read(root/'heartbeat.json');observer=[];workers=[]
 for p in Path('/proc').glob('[0-9]*'):
  try:
   args=[os.fsdecode(a) for a in (p/'cmdline').read_bytes().split(b'\0') if a];s=(p/'stat').read_text().split()
   if not args or s[2]=='Z' or int(p.name)==os.getpid():continue
   # Inspect executable/script tokens, not embedded shell command text or stale receipts.
   if not re.search(r'(?:python[0-9.]*|bash|sh|torchrun|accelerate)$',Path(args[0]).name):continue
   scripts=[a for a in args[1:] if a.startswith('/workspace/') and '\n' not in a and ' ' not in a]
   row={'pid':int(p.name),'proc_start_ticks':s[21],'executable':Path(args[0]).name,'script_paths':scripts}
   if any(str(root) in a and ('review_loop' in a or 'publisher' in a or 'reviewer' in a) for a in scripts):observer.append(row)
   elif any(cfg['run_id'] in a for a in scripts):workers.append(row)
  except (FileNotFoundError,ProcessLookupError):pass
 assert not observer and not workers,{'unexpected_observer_processes':observer,'unexpected_run_workers':workers}
 prior_alive=alive(h['pid'],h['proc_start_ticks']);assert not prior_alive and (root/'STOP').exists()
 locks=[]
 for p in [root/'service.lock',root/'observer.lock',C9/'report.lock',C9/'final-delivery.lock',R/'GPU_EXECUTION.lock']:
  if not p.exists():locks.append({'path':str(p),'state':'ABSENT_NOT_CREATED'});continue
  with p.open('r') as f:fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(f,fcntl.LOCK_UN)
  locks.append({'path':str(p),'state':'EXCLUSIVE_LOCK_AVAILABLE'})
 tmux=subprocess.run(['tmux','has-session','-t','pod-a-prompt-observer'],capture_output=True);assert tmux.returncode!=0
 return {'schema':'pod-a-fresh-terminal-state-v1','status':'PASS','observed_utc':now(),'observer_status':'STOPPED','prior_observer_pid':h['pid'],'prior_observer_proc_start_ticks':h['proc_start_ticks'],'prior_observer_identity_alive':prior_alive,'fresh_proc_scan_owned_observers':observer,'fresh_proc_scan_owned_workers':workers,'scientific_jobs':'QUIESCENT','reviewer_status':'DRAFT_ONLY_NOT_RUNNING','publisher_status':'BLOCKED_NOT_RUNNING','locks':locks,'observer_tmux_session_exists':False,'STOP_flag_exists':True,'historical_heartbeat_utc':h['observed_utc'],'heartbeat_is_historical_not_current_liveness':True,'observer_restarted':False,'pod_left_running':True,'current_administrative_process':{'pid':os.getpid(),'proc_start_ticks':Path('/proc/self/stat').read_text().split()[21],'scope':'This finite metadata closeout only'}}
def a9ref(name):
 p=D9/name;data=p.read_bytes();assert data==g('show',OLD+':'+str(p.relative_to(W)))
 return {'path':str(p.relative_to(B)),'url':'https://github.com/Georgakopoulos-Soares-lab/unlearning/blob/'+OLD+'/'+str(p.relative_to(W)),'bytes':len(data),'sha256':bh(data),'commit':OLD}
def private_a09_readback():
 from huggingface_hub import HfApi,hf_hub_download
 api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private;final=read(R/'FINAL_CLOSEOUT.json');dest=REC/'a09-receipt-fresh-cache';assert not dest.exists()
 path=Path(hf_hub_download(REPO,final['receipt_path'],repo_type='dataset',revision=final['receipt_revision'],force_download=True,cache_dir=str(dest)));assert sha(path)==final['receipt_sha256'] and path.read_bytes()==(C9/'DELIVERY_RECEIPT.json').read_bytes()
 proof={'status':'PASS','scope':'Fresh exact A09 final metadata receipt object only; no scientific payload transferred or consumer rerun','revision':final['receipt_revision'],'path':final['receipt_path'],'sha256':sha(path),'private':api.repo_info(REPO,repo_type='dataset').private,'force_download':True,'observed_utc':now()};put(C/'A09_RECEIPT_READBACK.json',proof);return read(path)
def prepare():
 guard(dirty=False);assert not D.exists();obs=observe();put(C/'TERMINAL_OBSERVATION.before.json',obs);receipt=private_a09_readback();final=read(R/'FINAL_CLOSEOUT.json');backup=read(D9/'BACKUP_MANIFEST.json');old=read(C/'BASELINE.json')
 # Preserve original bytes, including the historical checksum authority.
 for e in old['historical_root_files']:
  p=C/'historical-root-before'/e['path'];assert sha(p)==e['sha256'];write(D/'historical-A01-run-root-before-correction'/e['path'],p.read_bytes())
 write(D/'historical-A01-run-root-before-correction/README.md','# Historical A01 run-root entrypoints\n\nThese files preserve the exact bytes present before this administrative correction at research commit `'+OLD+'`. They describe historical A01 state and confer no current authority. Their old budget blocker, zero accepted coverage and pending-stage language are superseded by completed A09 and its explicit no-deadline amendment.\n\nThe copied OUTPUT_SHA256SUMS is the original A01 seal. Its three handoff paths resolve to the byte-identical files here; its other paths resolve to unchanged files at the run root. The original run-root manifest stays unchanged as historical evidence. The new administrative OUTPUT_SHA256SUMS seals the corrected current entrypoints.\n')
 write(D/'HISTORICAL_PRESERVATION.json',{'status':'PASS','source_commit':OLD,'files':old['historical_root_files'],'all_previous_bytes_preserved':True,'original_A01_manifest_matched_all_16_files_before_correction':all(e['matches_historical_A01_manifest'] for e in old['A01_root_checksum_current_match']),'original_root_manifest_retained_as_historical':True})
 refs={n:a9ref(n) for n in ['RESULTS.md','ONE_PAGE_SUMMARY.md','FIGURE_GALLERY.md','RESTORE.md','BACKUP_MANIFEST.json','BACKUP_VERIFICATION.json','FRESH_RESTORE_CHECK.json','RECOVERY_DEPENDENCY_GRAPH.json','REACQUISITION_MAP.json','RESUME_MANIFEST.json','MISSING_INPUTS_DRAFT.md','MISSING_UNIT_KEYS.csv','TABLE_INDEX.json','GOALS_STATUS.csv','A09_RECEIPT.json','OUTPUT_SHA256SUMS']}
 src=read(C9/'A09_RECEIPT.json');resume=read(C9/'RESUME_MANIFEST.json');fresh=read(D9/'FRESH_RESTORE_CHECK.json');graph=read(D9/'RECOVERY_DEPENDENCY_GRAPH.json')
 private=[{'kind':'A09_saved_analysis_payload','repository':REPO,'revision':backup['revision'],'path':backup['archive_path'],'bytes':backup['archive_bytes'],'sha256':backup['archive_sha256'],'member_manifest_sha256':backup['member_manifest_sha256']},{'kind':'A09_final_metadata','repository':REPO,'revision':final['final_metadata_revision'],'path':final['final_metadata_path'],'bytes':receipt['final_metadata_bytes'],'sha256':final['final_metadata_sha256'],'member_manifest_sha256':receipt['final_metadata_member_manifest_sha256']},{'kind':'A09_final_delivery_receipt','repository':REPO,'revision':final['receipt_revision'],'path':final['receipt_path'],'bytes':(C9/'DELIVERY_RECEIPT.json').stat().st_size,'sha256':final['receipt_sha256']}]
 core={'owner':'POD_A','run_id':cfg['run_id'],'current_stage':'A09','stopped_stage':'A09','attempt_id':'A09-attempt-001','status':'COMPLETE_QUALIFIED_REPORT_AND_SAVED_ANALYSIS_HANDOFF','full_project_status':'PARTIAL','A04_status':'PARTIAL','terminal_status':'STOPPED: POD_A HANDOFF DELIVERED','administrative_closeout_attempt':cfg['attempt_id'],'administrative_prompt_commit':PIN,'administrative_prompt_sha256':cfg['prompt_sha256'],'A09_prompt_commit':'ff579ad98b7970213c97cf0bb86fa2017cfa126e','scientific_commit':final['scientific_commit'],'report_delivery_commit':final['report_delivery_commit'],'metadata_commit':final['metadata_commit'],'administrative_delivery_commit':None,'administrative_commit_null_reason':'The containing commit is identified by separate post-push/private delivery proof; no self-hash cycle','scope_booleans':final['scope_booleans'],'protocol_sha256':src['protocol_sha256'],'coverage_plan_sha256':src['coverage_plan_sha256'],'coverage':src['coverage'],'authoritative_A09_outputs':refs,'immutable_private_backups':private,'private_receipt_fresh_readback':read(C/'A09_RECEIPT_READBACK.json'),'recovery_scope':{'A09_payload_files_hashed':fresh['all_payload_files_verified'],'A09_final_metadata_files_hashed':receipt['final_metadata_files_verified'],'saved_prediction_metric_paths':8,'saved_audit_refit_artifacts':2,'classifier_saved_draw_delta_values':20000,'LM_saved_draw_delta_values':4000,'prediction_metric_draw_and_interval_residuals':0.0,'dependency_nodes':len(graph['nodes']),'proof_reused_from_A09':True,'new_scientific_recovery_or_audit_executed':False,'model_weights_and_installed_runtime_excluded':True,'full_GPU_recreation_verified':False},'current_terminal_observation':obs,'historical_service_snapshots':'ACTIVE service values inside immutable A05-A09 receipts describe their observation times. The current state is the fresh /proc, PID/start and lock check above.','budget':src['budget'],'automatic_resume':False,'new_fits_or_forwards_authorized':False,'requires_new_direct_approval_for_additional_science':True,'required_approval':'Only if more work is requested: fresh explicit identity/qualification/bridge/backfill scope for each needed stage, or a revised scoped controller. No A10 exists.','blockers':resume['blockers'],'exact_missing_unit_count':1886,'exact_missing_unit_index':refs['MISSING_UNIT_KEYS.csv'],'remaining_science':'R2 and R5 each 468 heads plus separate corresponding fixed applications; 14 primary LM units; all five adjacent comparisons; R3 live bridge for affected new contrasts; ancestry/objective/exposure/source-label gaps.','restore_entry':refs['RESTORE.md'],'further_work_running':False,'peer_filesystem_assumed_shared':False,'new_admin_private_proof':'A separate immutable POST_END delivery archive/receipt is produced after this Git commit, without mutating A01-A09.','observed_utc':now()}
 write(B/'REMOTE_HANDOFF.json',{'schema':'pod-a-current-remote-handoff-v2',**core})
 write(B/'RESUME_MANIFEST.json',{'schema':'pod-a-current-resume-manifest-v2',**core,'completed_work_excluded':resume['excluded_completed_units'],'missing_unit_ids_in_priority_order':'See immutable exact MISSING_UNIT_KEYS.csv and A09 RESUME_MANIFEST.json; no completed units are rescheduled.','future_recovery_command_documented_not_executed':resume['recovery_command_after_archive_is_available'],'fresh_server_setup':refs['RESTORE.md'],'no_current_A01_budget_blocker':True,'no_clock_reset':True})
 write(B/'TERMINAL_STATE_RECEIPT.json',{'schema':'pod-a-current-terminal-state-receipt-v1',**core,'status':'VERIFIED_TERMINAL_STATE_AND_CORRECTED_CURRENT_ENTRYPOINTS','sanitized':True,'historical_preservation_manifest':str((D/'HISTORICAL_PRESERVATION.json').relative_to(B)),'new_scientific_measurements':0,'new_fits':0,'new_forwards':0,'new_analyses':0,'new_bootstrap_draws':0,'new_model_weight_downloads':0,'observer_restarts':0,'pod_shutdown':False})
 def link(n,label):return '['+label+']('+refs[n]['url']+')'
 text='# Pod A current handoff — A09 delivered\n\n**A09 qualified reporting and saved-analysis recovery are COMPLETE. The full incremental experiment and A04 remain PARTIAL.** This is the current run-root entrypoint for `'+cfg['run_id']+'`; the previous A01 handoffs are preserved byte-for-byte in [historical administrative evidence](administrative-closeout/'+cfg['attempt_id']+'/historical-A01-run-root-before-correction/README.md).\n\n## Read first\n\n'+link('ONE_PAGE_SUMMARY.md','One-page summary')+' · '+link('RESULTS.md','Full results')+' · '+link('FIGURE_GALLERY.md','31-figure gallery')+' · '+link('RESTORE.md','Exact recovery instructions')+' · '+link('MISSING_INPUTS_DRAFT.md','Remaining inputs and gaps')+'\n\n[Current machine handoff](REMOTE_HANDOFF.json), [future resume requirements](RESUME_MANIFEST.json) and [fresh terminal-state receipt](TERMINAL_STATE_RECEIPT.json) bind the same completed A09 and immutable evidence. No science is launched by these files.\n\n## Scientific delivery and remaining coverage\n\nScientific publication `'+final['scientific_commit']+'`; report delivery `'+final['report_delivery_commit']+'`; final A09 metadata `'+final['metadata_commit']+'`. A09 prompt `ff579ad98b7970213c97cf0bb86fa2017cfa126e`. This administrative correction uses post-end prompt `'+PIN+'`, SHA256 `'+cfg['prompt_sha256']+'`. The later administrative Git commit and private backup are bound by separate post-push proof to avoid self-reference.\n\nAvailable coverage remains 2,340/3,276 production heads and a separate 2,340/3,276 unchanged-base applications, 35/49 primary LM units and 36 controls. All six tasks, 26 representations, three CV seeds and both policies remain represented in the released evidence. The 27,300 marginal classifier rows, all 45,360 paired rows, 31 figure pairs and 30,886 plotted records are unchanged. This administrative attempt adds zero inference, fits, scientific analyses, draws or weight downloads.\n\nR2 and R5 each still need 468 heads and the corresponding separate applications. There are 1,886 exact pending ledger units and 14 missing primary LM units. All five adjacent comparisons remain pending; R6−R4 is nonadjacent. R3 historical evidence remains valid within its accepted domain; affected new contrasts need a qualified live bridge. Parent/objective/exposure/source-label metadata gaps constrain interpretation. H3 exploratory test remains separate. '+link('MISSING_UNIT_KEYS.csv','Exact missing keys')+' and '+link('GOALS_STATUS.csv','goal status')+' retain the full gaps.\n\n## Recovery proof and exclusions\n\nThe private dataset is `'+REPO+'`. A09 freshly checked 254 payload files, eight prediction/metric paths, two saved audit-refit artifacts, 20,000 classifier and 4,000 LM saved-draw deltas with zero residuals; final metadata checked 317 files. These are reused A09 results, with no repeated consumer or audit during this administrative attempt. The 42-node inherited dependency graph remains linked in '+link('RECOVERY_DEPENDENCY_GRAPH.json','recovery dependencies')+'. Weights and installed runtime binaries are excluded; '+link('REACQUISITION_MAP.json','reacquisition recipes')+' records exact IDs and access limitations. Full GPU recreation is unverified.\n\n| A09 object | Immutable revision | SHA256 |\n|---|---|---|\n'
 for obj in private:text+='| '+obj['kind']+' | `'+obj['revision']+'` | `'+obj['sha256']+'` |\n'
 text+='\nExact object paths/sizes and receipt bindings are in REMOTE_HANDOFF.json. The A09 final receipt object was freshly downloaded and compared during this correction; completed scientific payloads were reused. New administrative metadata gets its own unique private archive and all-member readback after Git delivery.\n\n## Actual current service state\n\nFresh inspection at `'+obs['observed_utc']+'` found the observer STOPPED, prior PID `'+str(obs['prior_observer_pid'])+'`/start ticks `'+str(obs['prior_observer_proc_start_ticks'])+'` absent as an identity, no owned scientific workers or observer replacement, and available owned locks. The observer tmux session is absent and its STOP flag remains. Historical ACTIVE service snapshots inside immutable stage receipts remain historical. Reviewer is DRAFT_ONLY/not running; publisher is BLOCKED/not running. The current administrative executor only publishes these corrections and terminates. The Pod remains running.\n\n## Policy and fresh-session entry\n\nPreserve the explicit no-deadline supersession. Original/rental start, rate and cost remain unknown. The historical A01 budget blocker and three-hour reserve are inactive; no original start is invented and no clock is reset. Other original A01 root receipts and OUTPUT_SHA256SUMS are historical. Their original three handoff bytes and checksum authority remain archived; the new administrative checksum manifest seals the current entrypoints.\n\nIn a fresh session, read this handoff and the current JSON entrypoints, then '+link('RESTORE.md','the pinned restore instructions')+'. No automatic resume, A10, observer/scheduler restart, missing-checkpoint backfill or perturbation work is authorized. Additional work requires a new direct, explicitly scoped approval only if requested.\n\nSTOPPED: POD_A HANDOFF DELIVERED\n'
 write(B/'SESSION_HANDOFF.md',text)
 write(D/'README.md','# Administrative closeout '+cfg['attempt_id']+'\n\nThis is one finite post-A09 metadata correction under the user-requested post-end prompt. A01–A09 attempt outputs, original science and the stopped observer are preserved. Current entrypoints are [handoff](../../SESSION_HANDOFF.md), [resume](../../RESUME_MANIFEST.json), [remote handoff](../../REMOTE_HANDOFF.json) and [terminal observation](../../TERMINAL_STATE_RECEIPT.json).\n\n[Historical A01 entrypoints](historical-A01-run-root-before-correction/README.md) retain original bytes and checksum authority. The original root OUTPUT_SHA256SUMS remains historical and the new OUTPUT_SHA256SUMS in this directory seals only the correction. The containing commit and later immutable private protection proof are reported separately without recursive self-hashing.\n')
 for name in ['APPROVAL_RECORD.json','PACKAGE_VERIFICATION.json','RUN_CONFIG.json','BASELINE.json','A09_RECEIPT_READBACK.json']:write(D/name,(C/name).read_bytes())
 write(D/'post-end.prompt.txt',(C/'post-end.md').read_bytes())
 for p in (A/'code').glob('*.py'):write(D/'CODE'/p.name,p.read_bytes())
 put(C/'PREPARED.json',{'status':'PASS','prepared_utc':now(),'terminal_observation':obs,'new_scientific_work':0});print(json.dumps({'status':'CURRENT_HANDOFF_CORRECTED_LOCALLY','stage':'A09','science_repeated':False,'observer':'STOPPED'}))

def finish_preparation():
 # Continue only the failed verbatim-source export, preserving completed work.
 guard();assert D.exists() and not (C/'PREPARED.json').exists();assert read(C/'A09_RECEIPT_READBACK.json')['status']=='PASS'
 for n in NAMES[1:]:assert read(B/n)['current_stage']=='A09'
 for e in read(C/'BASELINE.json')['historical_root_files']:assert sha(D/'historical-A01-run-root-before-correction'/e['path'])==e['sha256']
 write(D/'post-end.prompt.txt',(C/'post-end.md').read_bytes())
 for p in (A/'code').glob('*.py'):write(D/'CODE'/p.name,p.read_bytes())
 diagnostic={'status':'RESOLVED','reason':'Typed Markdown writer rejected the exact upstream prompt because it begins with an approval line instead of a Markdown heading. Preserve the original bytes in post-end.prompt.txt; do not alter the prompt or relax report writer validation.','original_diagnostic_log':'prepare.001.stderr.log','earlier_entrypoint_and_archive_work_preserved':True,'private_receipt_transfer_not_repeated':True,'resolved_utc':now()};put(C/'SOURCE_EXPORT_DIAGNOSTIC.json',diagnostic);write(D/'SOURCE_EXPORT_DIAGNOSTIC.json',diagnostic)
 put(C/'PREPARED.json',{'status':'PASS','prepared_utc':now(),'terminal_observation':observe(),'new_scientific_work':0,'continued_after_source_export_correction':True});print(json.dumps({'status':'CURRENT_HANDOFF_CORRECTED_LOCALLY','stage':'A09','science_repeated':False,'observer':'STOPPED'}))

def owned_files():return sorted([B/n for n in NAMES]+[p for p in D.rglob('*') if p.is_file()])
def validate():
 proof=guard();obs=observe();baseline=read(C/'BASELINE.json')
 for e in baseline['historical_root_files']:assert sha(D/'historical-A01-run-root-before-correction'/e['path'])==e['sha256']
 assert sha(B/'OUTPUT_SHA256SUMS')==next(e['sha256'] for e in baseline['historical_root_files'] if e['path']=='OUTPUT_SHA256SUMS')
 # The old checksum is now historical: resolve its moved handoffs to their exact archived bytes.
 for line in (B/'OUTPUT_SHA256SUMS').read_text().splitlines():
  digest,name=line.split('  ',1);p=D/'historical-A01-run-root-before-correction'/name if name in NAMES[:3] else B/name;assert sha(p)==digest
 links=0
 for p in owned_files():
  assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(B.resolve());data=p.read_bytes();assert len(data)<2*1024**2 and not DENY.search(data)
  assert p.suffix not in ['.npz','.npy','.joblib','.pt','.bin','.distcp'];assert not re.search(rb'"sequence"\s*:\s*"[ACGTN]{30,}"',data)
  if p.suffix=='.json':json.loads(data)
  if p.suffix=='.py':ast.parse(data)
  if p.suffix=='.md':
   text=data.decode();assert text.startswith('# ') and '\n\n' in text
   for target in re.findall(r'\]\(([^)]+)\)',text):
    if target.startswith(('https:','http:','#')):continue
    assert (p.parent/target).resolve().exists(),(p,target);links+=1
 for name in ['REMOTE_HANDOFF.json','RESUME_MANIFEST.json','TERMINAL_STATE_RECEIPT.json']:
  v=read(B/name);assert v['current_stage']==v['stopped_stage']=='A09' and v['automatic_resume'] is False and v['full_project_status']=='PARTIAL' and v['A04_status']=='PARTIAL';assert v['metadata_commit']==OLD and v['report_delivery_commit']=='409e860f03dc0b4a78fd47e6e83bd6ca8d0f34fd';assert v['current_terminal_observation']['observer_status']=='STOPPED' and not v['new_fits_or_forwards_authorized'];assert v['budget']['active_hard_deadline_utc'] is None and v['budget']['active_fixed_closure_reserve_hours'] is None
  for r in v['authoritative_A09_outputs'].values():assert sha(B/r['path'])==r['sha256'] and g('show',OLD+':'+str((B/r['path']).relative_to(W)))==(B/r['path']).read_bytes()
 changes=git('diff','--name-only',OLD).splitlines();assert all(owned(p) for p in changes)
 result={'schema':'pod-a-post-end-validation-v1','status':'PASS','guard':proof,'historical_A01_root_manifest_reconciled_all_16_entries':True,'archived_files_exact_bytes':len(baseline['historical_root_files']),'A01_A09_attempt_tree_unchanged':True,'all_current_entrypoints_identify_completed_A09':True,'exact_A09_report_restore_and_gap_links_checked':16,'local_Markdown_links_resolved':links,'privacy':'PASS','new_scientific_measurements':0,'scientific_audits_repeated':False,'fresh_terminal_state':obs,'checked_utc':now()};put(C/'VALIDATION.json',result);write(D/'VALIDATION.json',result)
 entries=[{'path':str(p.relative_to(B)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in owned_files() if p!=D/'OUTPUT_SHA256SUMS'];write(D/'OUTPUT_SHA256SUMS',''.join(e['sha256']+'  '+e['path']+'\n' for e in entries));put(C/'PUBLICATION_SEAL.json',{'files':entries,'manifest_path':str((D/'OUTPUT_SHA256SUMS').relative_to(B)),'manifest_sha256':sha(D/'OUTPUT_SHA256SUMS'),'self_excluded':True,'sealed_utc':now()});print(json.dumps({'status':'VALIDATED_AND_SEALED','files':len(entries),'current_observer':'STOPPED','no_science_repeated':True}))
def public_proof():
 check=guard(dirty=False);head=git('rev-parse','HEAD');assert git('ls-remote','--heads','origin','POD_A').split()[0]==head;seal=read(C/'PUBLICATION_SEAL.json');entries=seal['files']+[{'path':seal['manifest_path'],'sha256':seal['manifest_sha256']}]
 for e in entries:
  p=B/e['path'];assert sha(p)==e['sha256'];assert bh(g('show',head+':'+str(p.relative_to(W))))==e['sha256']
 changed=git('diff','--name-only',OLD,head).splitlines();assert all(owned(p) for p in changed)
 return {'status':'PASS','administrative_delivery_commit':head,'parent_A09_metadata_commit':OLD,'remote_equal':True,'all_committed_bytes_match':True,'files_including_manifest':len(entries),'manifest_sha256':seal['manifest_sha256'],'changed_paths':changed,'guard':check,'verified_utc':now()}
def publish():
 guard();seal=read(C/'PUBLICATION_SEAL.json');assert sha(D/'OUTPUT_SHA256SUMS')==seal['manifest_sha256'];remote=git('ls-remote','--heads','origin','POD_A').split()[0];assert remote==OLD
 paths=[str(p.relative_to(W)) for p in owned_files()]
 for e in seal['files']:assert sha(B/e['path'])==e['sha256']
 guard();subprocess.run(['git','-C',str(W),'add','--',*paths],check=True);staged=git('diff','--cached','--name-only').splitlines();assert staged and set(staged)<=set(paths);subprocess.run(['git','-C',str(W),'diff','--cached','--check'],check=True);guard();assert git('ls-remote','--heads','origin','POD_A').split()[0]==remote
 subprocess.run(['git','-C',str(W),'-c','user.name=AshaySrivastava','-c','user.email=149273902+ashay-sriv-06@users.noreply.github.com','commit','-m','POD_A: reconcile current run-root handoff with completed A09 and stopped services'],check=True,stdout=subprocess.PIPE);head=git('rev-parse','HEAD');guard(head=head);subprocess.run(['git','-C',str(W),'push','origin','HEAD:refs/heads/POD_A'],check=True);assert git('ls-remote','--heads','origin','POD_A').split()[0]==head;guard(dirty=False,head=head);put(C/'GIT_DELIVERY.json',{'status':'PASS','commit':head,'parent':OLD,'remote_equal':True,'delivered_utc':now()});proof=public_proof();put(C/'POST_PUSH_PROOF.json',proof);print(json.dumps(proof))

def verify_archive(path,expected_root,expected):
 with tarfile.open(path) as tf:
  members=tf.getmembers();seen=set();actual=set()
  for m in members:
   p=PurePosixPath(m.name);assert m.name and not p.is_absolute() and '..' not in p.parts and '\\' not in m.name and str(p)==m.name and p.parts[0]==expected_root;assert m.name not in seen and not m.issym() and not m.islnk() and (m.isdir() or m.isfile());seen.add(m.name)
   if m.isfile():
    rel=str(p.relative_to(expected_root));assert rel in expected and rel not in actual;actual.add(rel);e=expected[rel];data=tf.extractfile(m).read();assert len(data)==e['bytes'] and bh(data)==e['sha256']
  assert actual==set(expected)
 return len(actual)
def protect():
 from huggingface_hub import HfApi,hf_hub_download
 proof=public_proof();obs=observe();api=HfApi();assert api.repo_info(REPO,repo_type='dataset').private
 root=A/'payload-build-001/POST_END-administrative-metadata-001';assert not root.exists();root.mkdir(parents=True);(root/'public-owned').mkdir()
 for p in owned_files():
  dest=root/'public-owned'/p.relative_to(B);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 shutil.copytree(C/'prompt-package',root/'prompt-package');shutil.copytree(A/'code',root/'code',ignore=shutil.ignore_patterns('__pycache__'));shutil.copytree(A/'logs',root/'logs',ignore=shutil.ignore_patterns('protect*'))
 (root/'control').mkdir()
 for p in C.iterdir():
  if p.is_file() and p.suffix in ['.json','.md','.txt','.z']:shutil.copyfile(p,root/'control'/p.name)
 put(root/'POST_PUSH_PROOF.json',proof);put(root/'FRESH_TERMINAL_STATE.json',obs);files=[]
 for p in sorted(root.rglob('*')):
  assert not p.is_symlink()
  if p.is_file():assert not DENY.search(p.read_bytes());files.append({'path':str(p.relative_to(root)),'bytes':p.stat().st_size,'sha256':sha(p)})
 put(root/'MEMBER_MANIFEST.json',{'schema':'pod-a-exact-members-v1','files':files,'self_excluded':True});archive=A/'post-end-administrative-metadata-001.tar.gz';assert not archive.exists();t=time.monotonic()
 with tarfile.open(archive,'w:gz',compresslevel=6) as tf:tf.add(root,arcname=root.name)
 compress=time.monotonic()-t;ah=sha(archive);prefix='POD_A/'+cfg['run_id']+'/POST_END/'+cfg['attempt_id']+'/delivery-001';key=prefix+'/'+archive.name;assert not api.file_exists(REPO,key,repo_type='dataset');t=time.monotonic();up=api.upload_file(path_or_fileobj=str(archive),path_in_repo=key,repo_id=REPO,repo_type='dataset',commit_message='Protect administrative-only correction of completed A09 current handoff');upload=time.monotonic()-t
 dest=REC/'metadata-fresh-001';assert not dest.exists();dest.mkdir();t=time.monotonic();fresh=Path(hf_hub_download(REPO,key,repo_type='dataset',revision=up.oid,force_download=True,cache_dir=str(dest/'new-cache')));assert fresh.stat().st_size==archive.stat().st_size and sha(fresh)==ah
 expected={e['path']:e for e in files};expected['MEMBER_MANIFEST.json']={'bytes':(root/'MEMBER_MANIFEST.json').stat().st_size,'sha256':sha(root/'MEMBER_MANIFEST.json')};count=verify_archive(fresh,root.name,expected);verify=time.monotonic()-t;assert api.repo_info(REPO,repo_type='dataset').private;assert public_proof()['administrative_delivery_commit']==proof['administrative_delivery_commit'];finalobs=observe()
 receipt={'schema':'pod-a-post-end-delivery-receipt-v1','status':'PASS','scope':'One administrative-only closeout; original A01-A09 science and outputs preserved','run_id':cfg['run_id'],'attempt_id':cfg['attempt_id'],'prompt_commit':PIN,'prompt_sha256':cfg['prompt_sha256'],'scientific_commit':read(R/'FINAL_CLOSEOUT.json')['scientific_commit'],'report_delivery_commit':read(R/'FINAL_CLOSEOUT.json')['report_delivery_commit'],'metadata_commit':OLD,'administrative_delivery_commit':proof['administrative_delivery_commit'],'public_proof':proof,'current_terminal_state':finalobs,'A09_immutable_private_backups':read(B/'REMOTE_HANDOFF.json')['immutable_private_backups'],'administrative_backup':{'repository':REPO,'private':True,'revision':up.oid,'path':key,'bytes':archive.stat().st_size,'sha256':ah,'member_manifest_sha256':sha(root/'MEMBER_MANIFEST.json'),'all_member_files_verified':count,'force_fresh_download':True,'new_empty_cache':str(dest),'archive_safety_and_exact_member_set':'PASS','compression_seconds':compress,'upload_seconds':upload,'fresh_download_and_all_member_verification_seconds':verify},'receipt_revision':None,'receipt_revision_null_reason':'Returned immutable receipt revision is named in separate FINAL_CLOSEOUT.json; no self-hash cycle','new_scientific_measurements':0,'new_inference_or_fits':0,'new_scientific_analyses':0,'scientific_recovery_repeated':False,'new_weight_downloads':0,'observer_restarted':False,'automatic_resume':False,'pod_shutdown':False,'original_start_utc':None,'rental_start_utc':None,'hourly_rate_usd':None,'cost_usd':None,'completed_utc':now()};path=C/'DELIVERY_RECEIPT.json';put(path,receipt);put(C/'BACKUP_VERIFICATION.json',receipt['administrative_backup']);rk=prefix+'/POST_END_DELIVERY_RECEIPT.final.json';assert not api.file_exists(REPO,rk,repo_type='dataset');up2=api.upload_file(path_or_fileobj=str(path),path_in_repo=rk,repo_id=REPO,repo_type='dataset',commit_message='Bind corrected A09 root entrypoints to exact Git bytes and fresh private metadata proof');fr=Path(hf_hub_download(REPO,rk,repo_type='dataset',revision=up2.oid,force_download=True,cache_dir=str(REC/'receipt-fresh-cache-001')));assert fr.read_bytes()==path.read_bytes() and api.repo_info(REPO,repo_type='dataset').private
 final={'status':'PASS','terminal_status':'STOPPED: POD_A CURRENT HANDOFF CORRECTED','administrative_delivery_commit':proof['administrative_delivery_commit'],'A09_metadata_commit':OLD,'administrative_backup_revision':up.oid,'administrative_backup_path':key,'administrative_backup_sha256':ah,'administrative_backup_bytes':archive.stat().st_size,'all_member_files_verified':count,'receipt_revision':up2.oid,'receipt_path':rk,'receipt_sha256':sha(path),'receipt_fresh_readback':'PASS','final_current_terminal_state':observe(),'research_guard':guard(dirty=False),'scientific_work_repeated':False,'observer_restarted':False,'pod_left_running':True,'completed_utc':now()};put(C/'FINAL_CLOSEOUT.json',final);print(json.dumps(final))

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('operation',choices=['prepare','finish-prepare','validate','publish','protect','observe']);args=parser.parse_args()
 with (C/'administrative-writer.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  if args.operation=='prepare':prepare()
  elif args.operation=='finish-prepare':finish_preparation()
  elif args.operation=='validate':validate()
  elif args.operation=='publish':publish()
  elif args.operation=='protect':protect()
  else:print(json.dumps(observe()))
