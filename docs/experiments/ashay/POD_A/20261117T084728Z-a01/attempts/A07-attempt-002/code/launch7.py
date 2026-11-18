from common7 import *
import sys

def launch(name,script,args):
 guard();j={'stage':'A07','candidate':'R5','kind':'CPU','prompt_commit':cfg['prompt_commit'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'source_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'script_sha256':sha(A/'code'/script),'argv':[cfg['cpu_venv']+'/bin/python',str(A/'code'/script),*args]};p=C/'jobs'/(name+'.json');assert not p.exists();put(p,j);return subprocess.run([cfg['tools_venv']+'/bin/python',str(A/'code/worker7.py'),str(p)],check=True)
if __name__=='__main__':launch(sys.argv[1],sys.argv[2],sys.argv[3:])
