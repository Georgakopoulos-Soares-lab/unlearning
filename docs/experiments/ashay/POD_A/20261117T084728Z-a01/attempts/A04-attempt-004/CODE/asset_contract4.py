"""Small acquisition boundaries, independent of SDK/GPU state."""
from pathlib import Path,PurePosixPath
import hashlib,re
def safe_relative(value):
 p=PurePosixPath(value)
 if not value or p.is_absolute() or '..' in p.parts or '\\' in value or str(p)!=value:raise ValueError('Unsafe/noncanonical asset path')
 return p
def immutable_revision(value):
 if not re.fullmatch('[0-9a-f]{40}',value):raise ValueError('Full immutable revision required')
 return value
def verify_file(path,size,digest,provider_md5=None):
 p=Path(path)
 if p.is_symlink() or p.stat().st_size!=size:raise ValueError('Asset size/link mismatch')
 h=hashlib.sha256();m=hashlib.md5()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(32*1024**2),b''):h.update(block);m.update(block)
 if h.hexdigest()!=digest or provider_md5 is not None and m.hexdigest()!=provider_md5:raise ValueError('Full asset digest mismatch')
 return {'sha256':h.hexdigest(),'md5':m.hexdigest(),'bytes':size}
def runtime_relative(native):
 safe_relative(native)
 if native not in ['metadata.json','tokenizer/tokenizer_config.json','common.pt','train_state.pt','tokenizer/tokenizer.json','run_config.yaml','.metadata','__0_0.distcp']:raise ValueError('Unselected native asset')
 return Path(native).name
