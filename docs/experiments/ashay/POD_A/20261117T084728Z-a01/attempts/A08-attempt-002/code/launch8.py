from common8 import *
def launch(name,script,args,identity='SOURCE_IDENTITY.json'):
 guard();assert identity in ['SOURCE_IDENTITY.json','CONTRAST_SOURCE_IDENTITY.json'];j={'stage':'A08','candidate':'R5','kind':'CPU','prompt_commit':cfg['prompt_commit'],'coverage_plan_sha256':cfg['coverage_plan_sha256'],'source_identity_file':identity,'source_identity_sha256':sha(C/identity),'script_sha256':sha(A/'code'/script),'argv':[cfg['cpu_venv']+'/bin/python',str(A/'code'/script),*args]};p=C/'jobs'/(name+'.json');assert not p.exists();put(p,j);return subprocess.run([cfg['tools_venv']+'/bin/python',str(A/'code/worker8.py'),str(p)],check=True)
if __name__=='__main__':launch(sys.argv[1],sys.argv[2],sys.argv[3:])
