"""Validate required deliverables and seal every owned public file before delivery."""
from common import *
from research_guard import guard
import ast,re
required=['A07_INPUTS.json','APPROVAL_RECORD.json','PACKAGE_VERIFICATION.json','A06_ACCEPTANCE_RECONCILIATION.md','A06_REPORT_SCHEMA_REPAIR.json','A06_PAIRED_CONTRASTS.normalized.v1.csv','A07_EXECUTION_MANIFEST.json','PRODUCTION_COMMANDS.md','PROBE_INDEX.json','CONVERGENCE_REPORT.json','SEED_DIAGNOSTICS.csv','FIXED_REFERENCE_MAP.json','CONTROL_REUSE_MAP.json','RESULTS_LONG.csv','PAIRED_CONTRASTS.csv','LM_RESULTS.reused_A06.csv','RESULT_SCHEMAS.json','COVERAGE.csv','COMPARABILITY_MATRIX.csv','GOALS_GAPS_LEDGER.json','PRODUCER_VALIDATION.json','A08_AUDIT_HANDOFF_PLAN.json','FIT_RESOURCE_REPORT.json','BACKUP_VERIFICATION.json','RESTORE.md','RESUME_MANIFEST.json','A07_RECEIPT.json','SESSION_HANDOFF.md','NEXT_PROMPT_RECOMMENDATIONS.md','OWNED_JOB_DISPOSITION.json','PROGRESS.md','PROGRESS_EVENTS.jsonl']
def seal():
 guard(allow_dirty=True)
 for n in required:assert (D/n).is_file(),n
 schemas=read(D/'RESULT_SCHEMAS.json')
 for name in ['RESULTS_LONG','PAIRED_CONTRASTS']:
  schema=schemas[name];rows=list(csv.DictReader((D/(name+'.csv')).open()));assert set(schema['required'])<=set(rows[0]);assert len({tuple(r[k] for k in schema['primary_key']) for r in rows})==len(rows);assert len(rows)==(7800 if name=='RESULTS_LONG' else 16800)
 assert read(D/'A07_RECEIPT.json')['new_output_status']=='COMPLETE_UNVERIFIED' and not read(D/'A07_RECEIPT.json')['A08_started']
 for p in (D/'CODE').rglob('*.py'):ast.parse(p.read_text())
 files=[]
 for p in sorted(D.rglob('*')):
  if not p.is_file() or p.name=='OUTPUT_SHA256SUMS':continue
  assert not p.is_symlink();data=p.read_bytes();assert not re.search(rb'(?:hf_[A-Za-z0-9]{25,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----)',data);assert not re.search(rb'"sequence"\s*:\s*"[ACGTN]{30,}"',data);assert p.suffix not in ['.npz','.npy','.joblib','.pt','.bin','.distcp'];files.append({'path':str(p.relative_to(D)),'bytes':len(data),'sha256':sha(p)})
 publish('OUTPUT_SHA256SUMS',''.join(e['sha256']+'  '+e['path']+'\n' for e in files));proof={'status':'PASS','files':files,'required_outputs':required,'output_manifest_sha256':sha(D/'OUTPUT_SHA256SUMS'),'sealed_utc':now(),'scientific_release_status':'NEW_A07_PRODUCER_COMPLETE_PENDING_A08','A06_original_bytes_preserved':True};put(C/'PUBLICATION_SEAL.json',proof);print(json.dumps({'status':'SEALED','files':len(files),'manifest_sha256':proof['output_manifest_sha256']}))
if __name__=='__main__':seal()
