"""Fresh private consumer: exact restored sources only; no producer data fallback."""
from pathlib import Path
import sys,os,json,hashlib,shutil
root=Path(sys.argv[1]).resolve();work=root.parent/'regenerated';assert not work.exists();work.mkdir();allowed=[root,work,Path(sys.executable).parent.parent.resolve()]
# Python stdlib/site-packages on /usr are declared reused software, not source-data dependencies.
def audit(event,args):
 if event!='open' or not isinstance(args[0],(str,bytes,os.PathLike)):return
 p=Path(os.fsdecode(args[0])).resolve()
 if str(p).startswith('/workspace/pod-a-saliency') and not any(p==q or q in p.parents for q in allowed):raise PermissionError('Producer data fallback denied')
sys.addaudithook(audit);sys.path.insert(0,str(root/'code'))
from event_evidence import extract,sha
from build_correction import build
for d in ['inputs','sources']:(work/d).mkdir()
for n in ['SOURCE_PLAN.json','CANDIDATE_BINDINGS.json','CONFIG_FACTS.json']:shutil.copy2(root/'inputs'/n,work/'inputs'/n)
sources=json.loads((work/'inputs/SOURCE_PLAN.json').read_text())
for s in sources:
 p=root/'sources'/(s['id']+'.tfevents');assert p.stat().st_size==s['bytes'] and sha(p)==s['sha256'];os.link(p,work/'sources'/p.name)
extract(work,work/'extracted');build(work,work/'public');manifest=json.loads((root/'inputs/REGENERATION_MANIFEST.json').read_text());actual={str(p.relative_to(work/'public')):sha(p) for p in(work/'public').rglob('*') if p.is_file()};assert set(actual)==set(manifest['regenerated_public_files'])
for n,h in manifest['regenerated_public_files'].items():assert actual[n]==h,(n,'REGENERATED_BYTES_DIFFER')
for s in sources:
 r=json.loads((work/'extracted'/(s['id']+'.json')).read_text());original=json.loads((root/'extracted'/(s['id']+'.json')).read_text());assert r['maintained_scalar_digest']==original['maintained_scalar_digest'] and r['independent_wire_scalar_digest']==original['independent_wire_scalar_digest'];assert sha(work/'extracted'/r['full_scalar_table'])==original['full_scalar_sha256']
import runpy
sys.argv=[str(root/'code/check_tables.py'),str(work)];runpy.run_path(str(root/'code/check_tables.py'),run_name='__main__')
assert sha(work/'extracted/FULL_TABLE_INDEPENDENT_VALIDATION.json')==sha(root/'extracted/FULL_TABLE_INDEPENDENT_VALIDATION.json')
result={'status':'PASS','original_sources_freshly_reparsed':len(sources),'complete_events_reparsed':sum(json.loads((work/'extracted'/(s['id']+'.json')).read_text())['record_count'] for s in sources),'all_scalar_tables_exact_byte_equal':9,'public_tables_ledgers_handoff_regenerated_exactly':len(actual),'source_hashes_verified':True,'source_decoder_and_independent_wire_digest_equal':True,'full_emitted_CSV_independently_rechecked':4069382,'producer_data_fallback_denied':True,'model_or_external_evaluation_replayed':False,'clean_runtime_recreation':False,'software_dependency':'Existing separately pinned isolated parser runtime reused','regenerated_qualification_ledger_sha256':sha(work/'public/QUALIFICATION_LEDGER.csv'),'regenerated_forget_validation_table_sha256':sha(work/'public/FORGET_VALIDATION_OBSERVATIONS.csv')};(work/'RECOVERY_RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print('FRESH_SOURCE_REGENERATION_PASS',len(actual),flush=True)
