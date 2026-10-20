"""Validate fixed core artifacts read-only, independently refitting saved probes."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import sys
import subprocess
import uuid
from threadpoolctl import threadpool_limits

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from benign_pilot.validation import validate_saved
from benign_pilot.identity import file_sha256


def validate(run, output_dir, archive='/workspace/data/gue/GUE.zip', source_root=None, expected_source_commit=None):
    run,output_dir=Path(run).resolve(),Path(output_dir).resolve()
    if output_dir==run or run in output_dir.parents:
        raise ValueError('Validation output must be outside the input run directory')
    output_dir.mkdir(parents=True,exist_ok=True)
    destination=output_dir/'artifact_validation.json'
    if destination.exists():
        raise FileExistsError('Use a new audit output directory; preserve earlier validation results')
    try:
        with threadpool_limits(limits=4):
            result=validate_saved(run,archive,source_root,expected_source_commit)
    except Exception as exc:
        record=dict(all_passed=False,error=f'{type(exc).__name__}: {exc}',utc=datetime.now(timezone.utc).isoformat(),input_run=str(run))
        (output_dir/('validation_failure-'+uuid.uuid4().hex+'.json')).write_text(json.dumps(record,indent=2))
        raise
    repository=Path(__file__).resolve().parents[1]
    paths=['benign_pilot/identity.py','benign_pilot/validation.py','benign_pilot/validation_data.py',
           'scripts/validate_benign_pilot_results.py','configs/evo2_backend_identity.json']
    revision=subprocess.run(['git','-C',str(repository),'rev-parse','HEAD'],text=True,capture_output=True)
    dirty=subprocess.run(['git','-C',str(repository),'status','--porcelain'],text=True,capture_output=True)
    result['verification_source']=dict(commit=revision.stdout.strip() if revision.returncode==0 else None,
        dirty=bool(dirty.stdout.strip()) if dirty.returncode==0 else None,
        file_hashes={name:file_sha256(repository/name) for name in paths},utc=datetime.now(timezone.utc).isoformat())
    destination.write_text(json.dumps(result,indent=2,allow_nan=False))
    print(json.dumps(dict(all_passed=result['all_passed'],samples_verified=result['samples_verified'],probes_verified=len(result['checks']),candidates_verified=len(result['candidate_checks']),output=str(destination)),indent=2))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--archive',type=Path,default='/workspace/data/gue/GUE.zip')
    parser.add_argument('--source-root',type=Path)
    parser.add_argument('--expected-source-commit')
    args=parser.parse_args()
    result=validate(args.run_dir,args.output_dir,args.archive,args.source_root,args.expected_source_commit)
    sys.exit(0 if result['all_passed'] else 1)
