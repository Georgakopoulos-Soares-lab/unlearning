"""Finite fresh saved-analysis/report reconstruction from the declared restored capsule."""
from pathlib import Path
import sys,os,json,hashlib,subprocess,time,shutil
root=Path(sys.argv[1]).resolve();work=root/'regenerated';work.mkdir(exist_ok=True);public=work/'public';public.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):tmp=p.with_name(p.name+'.partial');tmp.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');tmp.replace(p)
envlock=read(root/'public/ENVIRONMENT_LOCK.json');cpu=envlock['CPU_runtime_python'];plot=envlock['plot_runtime_python'];pdf=envlock['report_python'];software=[str(Path(x).parent.parent) for x in [cpu,plot,pdf]];env={**os.environ,'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','CUDA_VISIBLE_DEVICES':'','PYTHONNOUSERSITE':'1','HF_HUB_OFFLINE':'1','S11_REUSED_SOFTWARE_ROOTS':os.pathsep.join(software),'MPLCONFIGDIR':str(work/'matplotlib-config'),'XDG_CACHE_HOME':str(work/'tex-cache'),'SOURCE_DATE_EPOCH':'1795470000'};env.pop('S11_FIGURE_ONLY',None)
stages=[];logs=work/'logs';logs.mkdir(exist_ok=True)
def run(label,args):
 out=logs/(label+'.stdout');err=logs/(label+'.stderr');assert not out.exists() and not err.exists(),'Preserve failed job logs and reconcile continuation before retry';start=time.monotonic()
 with out.open('xb') as o,err.open('xb') as e:
  p=subprocess.Popen(args,env=env,stdout=o,stderr=e,start_new_session=True);row={'label':label,'pid':p.pid,'start_ticks':Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(')',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'status':'RUNNING','argv':args};save(work/'RECOVERY_STATE.json',{'completed_stages':stages,'active':row});print('RESTORED_CHILD_START',label,p.pid,flush=True)
  while p.poll() is None:
   try:p.wait(timeout=20)
   except subprocess.TimeoutExpired:row['elapsed_seconds']=time.monotonic()-start;save(work/'RECOVERY_STATE.json',{'completed_stages':stages,'active':row});print('RESTORED_CHILD_PROGRESS',label,round(row['elapsed_seconds'],1),flush=True)
  row.update(status='PASS' if p.returncode==0 else 'FAILED',exit_status=p.returncode,elapsed_seconds=time.monotonic()-start);stages.append(row);save(work/'RECOVERY_STATE.json',{'completed_stages':stages,'active':None});assert p.returncode==0,(label,p.returncode);print('RESTORED_CHILD_END',label,p.returncode,flush=True)
def py(label,python,script,*args):run(label,[python,str(root/'code/guarded_entry.py'),str(root),str(root/'code'/script),*map(str,args)])
py('numerical-panel',cpu,'reconstruct_panel_v2.py',root,work/'numerical','fresh');numeric=read(work/'numerical/NUMERICAL_PANEL_RESULT.json');assert numeric['saved_prediction_paths_reconstructed']==252 and numeric['existing_paired_contrasts_reconstructed']==108
py('report-tables','/usr/local/bin/python3','report_data_v2.py',root,public)
for directory in ['source-evidence','source-index']:(public/directory).mkdir(exist_ok=True)
for ext in ['png','pdf','svg']:shutil.copy2(root/'inputs/s10/figures'/('SOURCE_LOG_TRACES.'+ext),public/'source-evidence'/('SOURCE_LOG_TRACES.'+ext))
shutil.copy2(root/'inputs/s09/FIGURE_MANIFEST.json',public/'source-index/S09_FIGURE_MANIFEST.json')
py('report-main-figures',plot,'render_report_figures_v5.py',public,public/'figures');py('source-appendix',plot,'render_source_appendix.py',root,public);py('report-prose-LaTeX','/usr/local/bin/python3','write_reports_v6.py',public)
# Exact deterministic reporting output set was frozen before private upload.
expected=read(root/'inputs/REPORT_REGENERATION_MANIFEST.json');actual={str(p.relative_to(public)):sha(p) for p in public.rglob('*') if p.is_file()};assert set(actual)==set(expected['deterministic_files'])
for n,h in expected['deterministic_files'].items():assert actual[n]==h,(n,'REPORT_REGENERATION_BYTES_CHANGED')
py('independent-publication-check','/usr/local/bin/python3','publication_check.py',root,public,work)
cache=work/'tex-cache';shutil.copytree(root/'software/latex-cache',cache,dirs_exist_ok=True);engine=root/'software/tectonic';engine.chmod(0o700);dependencies=[]
for name in ['REVIEWER_SUMMARY','RESULTS']:
 dep=work/(name+'.d');run('compile-'+name,[str(engine),'--only-cached','--untrusted','--keep-logs','--makefile-rules',str(dep),'--outdir',str(public),str(public/(name+'.tex'))]);text=dep.read_text();assert '/workspace/pod-a-saliency/research' not in text and '/workspace/pod-a-saliency/control' not in text
 for line in text.splitlines():
  if '/workspace/pod-a-saliency/' in line:
   tokens=[s for s in line.split() if s.startswith('/workspace/pod-a-saliency/')]
   for token in tokens:assert token.rstrip(':').startswith(str(root)),('Compiler producer fallback',token)
 dependencies.append({'document':name,'dependency_rules_sha256':sha(dep)})
code=root/'code/compare_pdfs.py';py('PDF-content-and-render-check',pdf,'compare_pdfs.py',root/'public',public,work/'PDF_RECONSTRUCTION.json');pdfproof=read(work/'PDF_RECONSTRUCTION.json');assert pdfproof['status']=='PASS';result={'status':'PASS','numerical':numeric,'all_deterministic_report_files_exact_bytes':len(actual),'deterministic_file_SHA256':actual,'independent_publication_validation':read(work/'PUBLICATION_VALIDATION.json'),'rendered_figure_exports_regenerated_exactly':sum(p.suffix in ['.png','.pdf','.svg'] for p in(public/'figures').iterdir()),'PDF_reconstruction':pdfproof,'TeX_dependencies':dependencies,'producer_tree_and_unrecorded_cache_fallback':False,'GPU_replay':False,'clean_scientific_runtime_recreation':False,'runtime_environment_reused':True,'source_identity_sha256':sha(root/'public/SOURCE_IDENTITY.json'),'stages':stages};save(work/'RECOVERY_RESULT.json',result);print('S11_FRESH_SAVED_ANALYSIS_AND_REPORT_REGENERATION_PASS',len(actual),flush=True)
