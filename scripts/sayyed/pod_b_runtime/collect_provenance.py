"""Explicit-path, read-only producer observations. Standard library only.

This never imports Torch/CUDA/model code, deserializes weights, sends a message,
or treats observations of today's files as evidence of a historical load.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import urlsplit,urlunsplit


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def no_secrets(value):
    if isinstance(value,dict):
        for key,item in value.items():
            if re.search(r'(?:^|_)(?:password|secret|access_token|auth_token|api_key|credential)(?:$|_)',key.lower()) and item not in (None,''):
                raise ValueError('Credential field detected; provide sanitized metadata (values omitted)')
            no_secrets(item)
    elif isinstance(value,list):
        for item in value:no_secrets(item)
    body=json.dumps(value)
    if re.search(r'github_pat_[A-Za-z0-9_]{20,}|hf_[A-Za-z0-9]{25,}|X-Amz-Signature=|Authorization:\s*Bearer|--(?:password|api-key|access-token)\s+\S+|https?://[^/\s"@]+:[^/\s"@]+@',body):
        raise ValueError('Secret/private access material detected; provide a sanitized request (values omitted)')


def safe_origin(value):
    parsed=urlsplit(value)
    if parsed.scheme in ('http','https','ssh'):
        host=parsed.hostname or ''
        if parsed.port:host+=':'+str(parsed.port)
        return urlunsplit((parsed.scheme,host,parsed.path,'',''))
    return value.split('?',1)[0]


def collect(request,output):
    no_secrets(request);output=Path(output)
    if not output.is_absolute() or output.exists():raise ValueError('Select a new absolute output directory')
    entries=request.get('files',[]);sources=request.get('sources',[])
    inputs=[Path(x['path']).resolve()for x in entries+sources]+[Path(x).resolve()for x in request.get('package_roots',[])]
    for source in inputs:
        # No output inside an observed file's directory or source/environment tree.
        protected=source if source.is_dir() else source.parent
        if output.resolve().is_relative_to(protected):raise ValueError('Output overlaps an observed input tree')
    observations=[]
    for record in entries:
        p=Path(record['path'])
        if not p.is_absolute() or p.is_symlink() or not p.is_file():raise ValueError('Explicit regular input files required')
        limit=request.get('maximum_file_bytes',64*1024*1024)
        if p.stat().st_size>limit:raise ValueError('Selected file exceeds explicit hashing limit')
        observations.append(dict(label=record['label'],path=str(p),bytes=p.stat().st_size,sha256=sha(p),
                                 modified_ns=p.stat().st_mtime_ns,scope='OBSERVED_CURRENT_BYTES_NOT_HISTORICAL_LOAD'))
    source_results=[]
    for record in sources:
        p=Path(record['path'])
        if not p.is_absolute() or p.is_symlink() or not p.is_dir():raise ValueError('Explicit source directories required')
        def git(*args):return subprocess.check_output(['git','--no-optional-locks','-C',str(p),*args],stderr=subprocess.DEVNULL)
        head=git('rev-parse','HEAD').decode().strip();status=git('status','--porcelain','--untracked-files=no')
        diff=git('diff','HEAD','--binary')
        try:origin=safe_origin(git('remote','get-url','origin').decode().strip())
        except subprocess.CalledProcessError:origin=None
        source_results.append(dict(label=record['label'],path=str(p),commit=head,origin=origin,
            tracked_dirty=bool(status),tracked_diff_sha256=hashlib.sha256(diff).hexdigest(),
            dirty_diff_contents_included=False,scope='OBSERVED_CURRENT_SOURCE_NOT_EXECUTED_JOB_PROOF'))
    packages={}
    for dist in importlib.metadata.distributions(path=request.get('package_roots',[])):
        name=dist.metadata.get('Name')
        if name and name.lower() in {n.lower()for n in request.get('package_names',[])}:packages[name]=dist.version
    result=dict(schema='POD_B.producer_observations.v1',observed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        job_metadata=request.get('job_metadata',{}),observed_current_files=observations,observed_current_sources=source_results,
        observed_distribution_metadata=packages,producer_attestations=request.get('producer_attestations',[]),
        attestation_policy='Producer-supplied statements are separate unreviewed assertions; collector cannot authenticate historical loading',
        CUDA_or_native_imports=False,checkpoint_deserialization=False,source_environment_or_branch_mutations=False)
    no_secrets(result);output.mkdir(parents=True,exist_ok=False)
    (output/'OBSERVATIONS.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(argv);result=collect(json.loads(args.request.read_text()),args.output)
    print(json.dumps(dict(status='CURRENT_OBSERVATIONS_ONLY',files=len(result['observed_current_files']),sources=len(result['observed_current_sources']),historical_identity_authenticated=False)))
if __name__=='__main__':main()
