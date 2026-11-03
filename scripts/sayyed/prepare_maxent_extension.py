"""Prepare pinned qualified benign official train/dev subsets; never reads test members."""
import argparse,json,hashlib
from pathlib import Path
from benign_pilot.data import prepare,eligibility_for_run

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',required=True);ap.add_argument('--archive',required=True);ap.add_argument('--output',required=True);ap.add_argument('--tasks',nargs='+',required=True);a=ap.parse_args()
    cfg=json.loads(Path(a.config).read_text());allowed={'gue_prom_300_all','gue_splice_reconstructed','gue_prom_core_all','gue_tf_0','gue_mouse_0'}
    if not set(a.tasks)<=allowed:raise ValueError('Task not in benign extension allowlist')
    actual=hashlib.file_digest(Path(a.archive).open('rb'),'sha256').hexdigest()
    if actual!=cfg['data_archive_sha256']:raise ValueError('Archive changed')
    cfg['tasks']={k:v for k,v in cfg['tasks'].items() if k in a.tasks};out=Path(a.output);out.mkdir(parents=True,exist_ok=True)
    (out/'config.json').write_text(json.dumps(cfg,indent=2));info=prepare(cfg,a.archive,out);rows=list(map(json.loads,(out/'subset_manifest.jsonl').read_text().splitlines()));eligibility=eligibility_for_run(cfg,out,rows)
    if any(not v['eligible'] for v in eligibility.values()):raise ValueError('Ineligible exact/RC overlap')
    for row in rows:
        row['source_split']=row['split'];row['split']='dev' if row['split']=='validation' else row['split'];row['exact_rc_group']=row['full_sequence_rc_sha256']
    target=out/'evaluation_manifest.jsonl';target.write_text(''.join(json.dumps(r,sort_keys=True)+'\n' for r in rows));info.update(eligibility=eligibility,evaluation_manifest_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),split_alias='validation means official dev; original source_split preserved',archive_sha256=actual)
    (out/'preparation.json').write_text(json.dumps(info,indent=2));print('Prepared',len(rows),'benign train/dev rows',flush=True)
if __name__=='__main__':main()
