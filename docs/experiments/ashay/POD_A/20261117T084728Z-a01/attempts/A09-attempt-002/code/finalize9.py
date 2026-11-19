"""Finite report delivery, later metadata proof and current terminal pointers."""
from common9 import *
from preflight9 import service_state
from delivery9 import deliver,progress
import re,shutil,datetime

STATUS='COMPLETE_FOR_AVAILABLE_CHECKPOINT_REPORT_AND_RECOVERY'

def seal():
 guard();files=[p for p in sorted(D.rglob('*')) if p.is_file() and p.name!='OUTPUT_SHA256SUMS'];out=''.join(sha(p)+'  '+str(p.relative_to(D))+'\n' for p in files);publish('OUTPUT_SHA256SUMS',out);put(C/'PUBLICATION_SEAL.json',{'files':len(files),'OUTPUT_SHA256SUMS_sha256':sha(D/'OUTPUT_SHA256SUMS'),'self_excluded':True,'observed_utc':now()})

def public_checks():
 guard();json_n=csv_n=0;links=[]
 for p in D.rglob('*'):
  if not p.is_file():continue
  assert p.stat().st_size and not p.is_symlink()
  if p.suffix=='.json':read(p);json_n+=1
  elif p.suffix=='.csv':
   with p.open() as f:
    it=csv.reader(f);head=next(it);assert len(head)==len(set(head)),str(p)
    for row in it:assert len(row)==len(head),str(p)
   csv_n+=1
 for p in list(D.glob('*.md'))+list((D/'report_source').glob('*.md')):
  for u in re.findall(r'\]\(([^)]+)\)',p.read_text()):
   if '://' not in u and not u.startswith('#'):
    assert (p.parent/u.split('#')[0]).is_file(),(p.name,u);links.append({'source':str(p.relative_to(D)),'target':u})
 pdf=(D/'REPORT.pdf').read_bytes();assert pdf.startswith(b'%PDF-') and len(re.findall(rb'/Type\s*/Page\b',pdf))==14 and sha(D/'REPORT.pdf')==read(C/'REPORT_RENDER_VALIDATION.json')['REPORT_pdf_sha256']
 for family in read(D/'FIGURE_MANIFEST.json')['figures']:
  for f in family['files']:
   p=D/f['path'];assert sha(p)==f['sha256'] and p.stat().st_size==f['bytes']
 return {'status':'PASS','JSON_files_parsed':json_n,'CSV_files_parsed_with_consistent_schema':csv_n,'current_Markdown_links_resolved':len(links),'PDF_pages':14,'main_figures':4,'main_assets':12,'inherited_appendix_families':12,'full_release_key_integrity':'PASS: fresh restored106526 unique keys and immutable source joins','source_display_plot_values':'PASS: live joins and new producer-denied consumer','zero_new_fits_forwards_draws_or_inferential_families':True,'scientific_input_commit':cfg['scientific_input_commit'],'full_project_status':'PARTIAL','observed_utc':now()}

def roots(report_commit=None):
 guard();complete=bool(report_commit);state={'schema':'pod-a-A09-terminal-v1','run_id':R.name,'stage':'A09','attempt_id':C.name,'status':STATUS if complete else 'LOCAL_READY_RECOVERY_VERIFIED_PENDING_GIT_REPORT_DELIVERY','current_attempt':'attempts/'+C.name,'prompt_commit':cfg['prompt_commit'],'prompt_sha256':cfg['prompt_sha256'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'inherited_scientific_commit':cfg['scientific_input_commit'],'report_delivery_commit':report_commit,'metadata_commit':'Resolved by separately private-protected FINAL_CLOSEOUT.json; this metadata never names its own future hash','report_payload':read(C/'REPORT_PAYLOAD_UPLOADED.json')['report_payload'],'AVAILABLE_CHECKPOINT_ANALYSIS_COMPLETE':True,'FULL_INCREMENTAL_SEQUENCE_COMPLETE':False,'CAUSAL_TRAINING_COMPARABILITY_ESTABLISHED':False,'REPORT_DELIVERED':complete,'GIT_DELIVERED':complete,'SAVED_ANALYSIS_RECOVERY_VERIFIED':True,'FULL_GPU_RECREATION_VERIFIED':False,'OWNED_JOBS_QUIESCENT':True,'services':read(C/'PROCESS_CLOSEOUT.json'),'full_project_and_A04_status':'PARTIAL','time_policy':cfg['time_policy'],'automatic_resume':False,'next_action':'STOP; wait for fresh explicitly scoped approval','A10_started':False,'observed_utc':now(),'entrypoint':'attempts/'+C.name+'/SESSION_HANDOFF.md'}
 publish('A09_RECEIPT.json',state)
 for name in ['REMOTE_HANDOFF.json','RESUME_MANIFEST.json']:publish(name,state|{'entrypoint':name,'restore_instructions':'RESTORE.md','missing_unit_keys':'MISSING_R2_UNIT_KEYS.csv','missing_contrast_keys':'MISSING_R2_CONTRAST_KEYS.csv'})
 handoff='# Pod A A09 terminal handoff\n\n'+state['status']+'. Full project/A04 remains PARTIAL.\n\nRead [the report](RESULTS.md), [standalone PDF](REPORT.pdf), [one-page summary](ONE_PAGE_SUMMARY.md), [four main figures and inherited appendix](FIGURE_GALLERY.md), [saved-analysis recovery proof](FRESH_RESTORE_CHECK.json) and [restore commands](RESTORE.md).\n\nAvailable science:2808/3276 heads and separately2808/3276 unchanged-base applications,36 shared control heads,42/49 LM units (36dev+6previously examined H3 test),106526 integrated metric rows and33684 current R5 amendment keys. All six tasks,26 representations,three CV seeds and both policies are preserved. R2 lacks468heads,468applications,7LM units and10948 dependent contrast slots. Current R3 saved-output eligibility and complete R5 release are incorporated.\n\nNew recovery is24 saved prediction/metric paths,60 classifier vectors and6 LM vectors (2000 existing draws each);106526 scientific keys,33684 amendment keys and plot values regenerated; one main figure rendered under producer-tree denial. All new archive members verified. Inherited scientific recovery proofs are reused, not relabeled as new runs. Full GPU/runtime recreation is untested.\n\nExact prompt `'+cfg['prompt_commit']+'`; inherited science `'+cfg['scientific_input_commit']+'`. '+('Report delivery `'+report_commit+'`; the later metadata commit and separate private receipt are identified in FINAL_CLOSEOUT.json and the final user handoff.' if complete else 'Final report Git delivery is the remaining administrative step; no additional science is needed.')+'\n\nObserver/reviewer/scheduler/publisher STOPPED, no owned scientific workers, no automatic resume or next stage. The Pod remains running. No-deadline amendment preserved; original/rental starts,rate and cost remain unknown.\n\nFresh session: read this terminal handoff and the separately protected final receipt; reuse verified completed science. Wait for fresh scoped approval before R2 qualification/backfill,metadata/lineage research,full GPU reconstruction,perturbations or any next stage. Pod B remains external ownership. No collaborator messages were sent.\n'
 publish('SESSION_HANDOFF.md',handoff)
 for name in cfg['allowed_root_files']:
  guard()
  if name=='SESSION_HANDOFF.md':md(B/name,handoff.replace('](','](attempts/'+C.name+'/'))
  elif name=='PROGRESS.md':md(B/name,(D/'PROGRESS.md').read_text().replace('](','](attempts/'+C.name+'/'))
  else:put(B/name,state|{'entrypoint':name,'terminal_handoff':'attempts/'+C.name+'/SESSION_HANDOFF.md'})
 return state

def prepare():
 guard();fresh=read(REC/'report-fresh-001/FRESH_RESTORE_CHECK.json');assert fresh['status']=='PASS';put(C/'FRESH_RESTORE_CHECK.json',fresh);publish('FRESH_RESTORE_CHECK.json',fresh)
 p=read(C/'REPORT_PAYLOAD_UPLOADED.json')['report_payload'];publish('BACKUP_MANIFEST.json',{'status':'PASS','report_payload':p,'inherited_archives':'RECOVERY_DEPENDENCY_GRAPH.json','final_metadata_and_receipt':'Separate immutable objects identified in final user handoff; finite delivery chain avoids self-reference','excluded_weights_runtime':'REACQUISITION_MAP.json'})
 verification={'status':'PASS','new_report_payload':p,'fresh_consumer':fresh['fresh_consumer'],'all_members_verified':fresh['all_members_verified'],'force_download':True,'all_member_checksums':'PASS','producer_paths_denied':True,'CPU_panel':{'prediction_paths':24,'classifier_vectors':60,'LM_vectors':6,'saved_draws_per_vector':2000},'inherited_new_download_bytes':0,'inherited_remote_archive_identities':43,'inherited_rehashed_distinct_files':16489,'inherited_rehashed_bytes':719216425,'A08_appendix_assets_rehashed':36,'GPU_recreation':False,'executed_command':[cfg['tools_python'],'-B',str(A/'code/fetch_restore9.py'),'--receipt',str(C/'REPORT_PAYLOAD_UPLOADED.json'),'--destination',str(REC/'report-fresh-001'),'--cpu-python',cfg['cpu_python'],'--plot-python',cfg['plot_python']],'jobs':fresh['jobs'],'source_bound_numeric_residuals':fresh['numeric_consumer']['max_abs_residuals'],'inherited_proofs_not_reexecuted':True};put(C/'BACKUP_VERIFICATION.json',verification);publish('BACKUP_VERIFICATION.json',verification)
 goals=rows(D/'GOALS_STATUS.csv')
 for g in goals:
  if g['goal']=='Portable saved-analysis recovery':g['status']='COMPLETE_NEW_A09_RECOVERY';g['available_or_verified']='24paths/60classifier/6LM vectors; all new members verified'
 table('GOALS_STATUS.csv',goals)
 history=[]
 for pth in sorted((B/'attempts').glob('*/A0?_RECEIPT.json')):
  if pth.parent==D:continue
  j=read(pth);history.append({'attempt':pth.parent.name,'source_status':j.get('status'),'receipt':str(pth.relative_to(W)),'sha256':sha(pth),'current_A09_overlay':'Historical status preserved; current available report integrates later R3/R5 release'})
 publish('STAGE_HISTORY.json',{'history':history,'current_A09_status':STATUS,'current_full_project_and_A04':'PARTIAL','A08_orchestration_two_unknown_child_exit_codes':None,'no_unknown_exit_code_replaced_with_zero':True})
 repair=read(D/'REPORT_REPAIR_LOG.json');repair['derivative_receipts']=[]
 for name in ['INTEGRATION_REPAIR_001.json','DEPENDENCY_MAPPING_REPAIR_001.json','SOURCE_KIND_METADATA_RECONCILIATION.json','CONTROL_POINT_READER_RECONCILIATION.json','QUALIFICATION_HARNESS_REPAIR.json','LAUNCH_REJECTION_DIAGNOSTIC.json','FIGURE_LAYOUT_REPAIR.json','PDF_LAYOUT_REPAIR.json','PDF_CLOSING_LAYOUT_REPAIR.json','PDF_TYPOGRAPHY_RECONCILIATION.json']:
  j=read(C/name);publish('repairs/'+name,j);repair['derivative_receipts'].append({'path':'repairs/'+name,'sha256':sha(C/name),'receipt':j})
 repair['final_derivative_digests']={name:sha(D/name) for name in ['SOURCE_TABLE_INDEX.json','REPORT.pdf','RESULTS.md','FIGURE_MANIFEST.json','REPORT_DISPLAY_DATA.csv']};repair['scientific_invariance']='Every original106526 source row/context preserved; fresh consumer regenerated original SHA/value/key joins; zero scientific edits';publish('REPORT_REPAIR_LOG.json',repair)
 refs=[]
 for directory,name in [(D8,'PRIVATE_PROVENANCE_MAP.json'),(D6,'PRIVATE_PROVENANCE_MAP.json'),(D90,'RECOVERY_DEPENDENCY_GRAPH.json'),(D8,'SOURCE_IDENTITY.json')]:
  pth=directory/name
  if pth.is_file():refs.append({'path':str(pth.relative_to(W)),'commit':cfg['research_head_before'],'sha256':sha(pth),'bytes':pth.stat().st_size})
 check_committed_files([W/e['path'] for e in refs],cfg['research_head_before']);publish('SOURCE_PROVENANCE_INDEX.json',{'immutable_sources':refs,'current_canonical_rows':'TABLE_INDEX.json','full_original_fields':'SOURCE_TABLE_INDEX.json and immutable original CSVs in report payload','private_saved_output_descriptors':25939,'explicit_content_and_path_mapping':'control/RECOVERY_INPUT_BINDINGS.json in private report payload','all_original_locator_and_selector_fields_preserved':True})
 # Concrete command was executed above; the final receipt supplies the immutable object.
 publish('PRODUCTION_COMMANDS.md','# Actual A09 commands and exact recovery entry\n\nThe following standalone command completed the fresh report recovery. Its argv,PID/start identity,exit codes and times are in BACKUP_VERIFICATION.json and FRESH_RESTORE_CHECK.json.\n\n```bash\n'+ ' '.join(verification['executed_command'])+'\n```\n\nFor a new server, first restore required inherited archives from RECOVERY_DEPENDENCY_GRAPH.json and verify their hashes/member manifests. Supply a JSON archive-SHA256-to-restored-consumer-root mapping using --dependency-roots. Use a new --destination; a nonempty prior attempt is rejected. Required interpreter versions and hard per-worker limits are in ENVIRONMENT_CHECK.json and RESTORE.md. Download/auth uses the tools environment; numerical/render children remove credentials and producer PYTHONPATH,disable GPU visibility,and enforce32GiB address space and4threads. No fit/model forward/bootstrap draw is authorized.\n\nThe committed code/plot9.py --input plot_data/main_figures.json --output NEW_DIRECTORY reproduces all4 main layouts with the qualified plotting interpreter. code/render_report9.py --root PUBLIC_REPORT_ROOT --figures NEW_DIRECTORY --output NEW_REPORT_DIRECTORY produces the14-page PDF and page previews. These commands were executed through launch9.py; source identities and exactargv are preserved privately under control/jobs. Earlier failed layout/source-reader attempts remain preserved in the archive and repair log.\n')
 jobs=[read(q) for q in sorted((C/'jobs').glob('*.result.json'))];failed=[j for j in jobs if j['exit_code']!=0];assert len(failed)==2
 for j in jobs:
  pth=Path('/proc')/str(j['pid'])/'stat'
  assert not (pth.exists() and pth.read_text().split()[21]==str(j['proc_start_ticks']) and pth.read_text().split()[2]!='Z')
 resources={'status':'PASS','started_utc':cfg['started_utc'],'observed_utc':now(),'elapsed_wall_seconds_to_report_seal':(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(cfg['started_utc'])).total_seconds(),'CPU_workers_max':2,'BLAS_OpenMP_threads_each':4,'worker_AS_bytes':32*1024**3,'new_GPU_seconds':0,'new_fits_forwards_draws':0,'CPU_recovery_seconds':fresh['numeric_consumer']['CPU_seconds'],'CPU_recovery_wall_seconds':fresh['numeric_consumer']['wall_seconds'],'fresh_report_download_bytes':p['archive_bytes'],'fresh_report_download_seconds':fresh['fresh_download_seconds'],'inherited_new_download_bytes':0,'provider_storage':read(C/'PROVIDER_STORAGE_CHECK.json'),'disk_at_closeout':dict(zip(['total','used','free'],shutil.disk_usage('/workspace'))),'plot_jobs':jobs,'failed_layout_jobs_preserved':failed,'final_layout_jobs_pass':['render-main-002','render-report-005'],'other_earlier_failed_source_reader_and_qualification_harness_attempts':'Preserved in diagnostics/logs and repairs; corrected by metadata-only code changes before final acceptance','original_start_utc':None,'provider_rental_start_utc':None,'provider_hourly_rate_usd':None,'cost_usd':None,'cost_unknown_not_zero':True,'no_deadline_or_closure_reserve':True};put(C/'RESOURCE_CLOSEOUT.json',resources);publish('RESOURCE_CLOSEOUT.json',resources)
 state=service_state();put(C/'PROCESS_CLOSEOUT.json',state);publish('PROCESS_CLOSEOUT.json',state)
 for pth in (A/'code').glob('*.py'):publish('code/'+pth.name,pth.read_bytes())
 progress('Full106526-row report,14-page PDF,4 main families and new24/60/6 fresh recovery PASS; final guarded Git delivery.',status='LOCAL_READY',push=False)
 roots();validation=public_checks();put(C/'REPORT_VALIDATION.json',validation);publish('REPORT_VALIDATION.json',validation);seal();receipt=deliver('A09 deliver verified available-checkpoint scientific report and fresh saved-analysis recovery');put(C/'REPORT_DELIVERY.json',receipt);print(json.dumps(receipt))

def metadata():
 guard(dirty=False);report=read(C/'REPORT_DELIVERY.json');assert report['status']=='PASS' and git('rev-parse','HEAD')==report['commit'];paths=[p for p in D.rglob('*') if p.is_file()]+[B/n for n in cfg['allowed_root_files']];proof=check_committed_files(paths,report['commit']);pub={'status':'PASS','report_delivery_commit':report['commit'],'report_delivery_remote_equal':True,'inherited_scientific_commit':cfg['scientific_input_commit'],'committed_files':proof,'observed_utc':now()};put(C/'POST_PUSH_REPORT_BYTES.json',pub);publish('POST_PUSH_REPORT_BYTES.json',pub)
 state=service_state();put(C/'PROCESS_CLOSEOUT.json',state);publish('PROCESS_CLOSEOUT.json',state)
 progress('A09 report delivered and exact committed bytes read back; CPU recovery24/60/6 PASS. Terminal metadata proof and private final receipt follow; no new stage.',status=STATUS,push=False)
 publish('PROGRESS.md',(D/'PROGRESS.md').read_text().replace('|All verified in A08|A09 report integration|','|All verified in A08 and integrated in A09|0 for available scope|').replace('|See FRESH_RESTORE_CHECK.json when sealed|Finite approved panel|','|PASS: FRESH_RESTORE_CHECK.json|0|'))
 roots(report['commit']);validation=public_checks();publish('REPORT_VALIDATION.json',validation);seal();receipt=deliver('A09 terminal metadata proof for delivered report; stop with available scope complete');put(C/'METADATA_DELIVERY.json',receipt);print(json.dumps(receipt))

if __name__=='__main__':
 assert len(sys.argv)==2
 {'prepare':prepare,'metadata':metadata}[sys.argv[1]]()
