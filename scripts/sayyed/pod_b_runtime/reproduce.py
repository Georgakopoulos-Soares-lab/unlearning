"""Reproduce the observed candidate assembly from explicit trusted dependencies.

Requires the preserved pinned binary environment; this is not a wheel rebuild
or historical-runtime authentication. No model/native module is imported and no
GPU work is launched. Default --dry-run validates inputs without writing.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import io
import json
import shutil
import subprocess
import tarfile

PINS=dict(bionemo='7dd1659f2103982562d7a23896fb2091200a1f1d',bridge='18ef1b61309dd45bc0535fb7c60064b9d8829a35',core='92c8482e6dcd11c3666c61bb8d1f7e8d0730ed13')
LORA_SHA='9b481000249879695c266b2489ac40999732c3e8f81f024027f96b9d972a6af3'
PATCH_SHA='ba9225905a35669f30ec59f753ae7cb43c76c3e8e09c416105679badeb8db4ee'

def sha(p):
    with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()

def build(args):
    target=args.output
    if not target.is_absolute() or target.exists():raise ValueError('New absolute output root required')
    if sha(args.official_lora)!=LORA_SHA or sha(args.patch)!=PATCH_SHA:raise ValueError('Pinned official source/backport bytes differ')
    inputs=[args.binary_environment,args.bionemo_source,args.bridge_source,args.core_source,args.official_lora,args.patch,args.environment_lock,args.binary_manifest]
    for p in inputs:
        if not p.is_absolute() or p.is_symlink() or not p.exists():raise ValueError('Explicit existing nonsymlink input required')
        protected=p if p.is_dir()else p.parent
        if target.resolve().is_relative_to(protected.resolve()):raise ValueError('Output overlaps a preserved input')
    for label in PINS:
        p=getattr(args,label+'_source');head=subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip()
        if head!=PINS[label]:raise ValueError('Wrong source pin: '+label)
    cfg=args.binary_environment/'pyvenv.cfg'
    if not cfg.is_file():raise ValueError('A separately recovered trusted binary venv is required')
    site_input=args.binary_environment/'lib/python3.12/site-packages'
    expected=json.loads(args.environment_lock.read_text())['packages']
    installed={d.metadata['Name'].lower().replace('_','-'):d.version for d in importlib.metadata.distributions(path=[str(site_input)])}
    for name,version in expected.items():
        if installed.get(name.lower().replace('_','-'))!=version:raise ValueError('Pinned distribution differs: '+name)
    binary=json.loads(args.binary_manifest.read_text())
    if args.dry_run:return dict(status='VALIDATED_DRY_RUN',binary_rebuild=False,GPU_launched=False,source_pins=PINS)
    # Deep binary checks are required for an actual replacement assembly, once.
    # Dry-run checks metadata only and does not claim a restore roundtrip.
    for record in binary['files']:
        if '.so' in record['path'] and 'sha256' in record:
            p=args.binary_environment/record['path']
            if not p.is_file() or sha(p)!=record['sha256']:raise ValueError('Binary identity differs: '+record['path'])
    target.mkdir(parents=True,exist_ok=False);sources=target/'src';sources.mkdir()
    for label,pin in PINS.items():
        original=getattr(args,label+'_source');payload=subprocess.check_output(['git','-C',str(original),'archive',pin])
        (target/(label+'.tar')).write_bytes(payload);destination=sources/label;destination.mkdir()
        with tarfile.open(fileobj=io.BytesIO(payload))as archive:archive.extractall(destination,filter='data')
    providers=list((sources/'bionemo').rglob('evo2_provider.py'))
    if len(providers)!=1:raise ValueError('Ambiguous provider source')
    shutil.copyfile(args.official_lora,providers[0].with_name('evo2_lora.py'))
    peft=sources/'bridge/src/megatron/bridge/peft'
    subprocess.run(['git','-C',str(peft),'apply','--check','-p0',str(args.patch)],check=True)
    subprocess.run(['git','-C',str(peft),'apply','-p0',str(args.patch)],check=True)
    shutil.copyfile(args.patch,target/'NATIVE_BACKPORT.patch')
    subprocess.run(['cp','-a','--reflink=never',str(args.binary_environment),str(target/'venv')],check=True)
    site=target/'venv/lib/python3.12/site-packages'
    if not site.is_dir():raise ValueError('Observed candidate requires Python3.12 layout')
    for p in site.glob('__editable__*.pth'):p.unlink()  # new copy only
    (site/'pod_b_isolated_sources.pth').write_text('\n'.join(map(str,[providers[0].parents[3],sources/'bridge/src',sources/'core']))+'\n')
    for p in (target/'venv/bin').iterdir():
        if p.is_symlink() or not p.is_file():continue
        try:body=p.read_text()
        except UnicodeError:continue
        if str(args.binary_environment)in body:p.write_text(body.replace(str(args.binary_environment),str(target/'venv')))
    result=dict(status='ASSEMBLED_NOT_NATIVE_REQUALIFIED',binary_rebuild=False,GPU_launched=False,
        source_pins=PINS,official_class_sha256=LORA_SHA,patch_sha256=PATCH_SHA,
        retained_binary_dependency=str(args.binary_environment),source_files=[dict(path=str(p),sha256=sha(p))for p in [providers[0].with_name('evo2_lora.py'),*[peft/n for n in ['base.py','lora.py','adapter_wrapper.py','lora_layers.py','module_matcher.py','utils.py','walk_utils.py']]]])
    (target/'REPRODUCTION.json').write_text(json.dumps(result,indent=2)+'\n');return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    for name in ['binary-environment','bionemo-source','bridge-source','core-source','official-lora','patch','environment-lock','binary-manifest']:p.add_argument('--'+name,type=Path,required=True)
    group=p.add_mutually_exclusive_group();group.add_argument('--dry-run',action='store_true',default=True);group.add_argument('--assemble',action='store_true')
    args=p.parse_args(argv)
    if args.assemble:args.dry_run=False
    print(json.dumps(build(args)))
if __name__=='__main__':main()
