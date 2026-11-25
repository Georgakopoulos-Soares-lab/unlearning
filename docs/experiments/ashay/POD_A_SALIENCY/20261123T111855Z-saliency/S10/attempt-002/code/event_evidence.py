"""Versioned aggregate-event extraction; never loads model or dataset payloads."""
from pathlib import Path
import os,sys,json,csv,struct,hashlib,gzip,io,collections,math,time
import google_crc32c
from tensorboard.backend.event_processing.event_file_loader import LegacyEventFileLoader
from tensorboard.compat.tensorflow_stub import pywrap_tensorflow
from tensorboard.compat.proto import event_pb2

FIELDS=['observation_id','source_id','source_sha256','event_order','value_order','tag','value','step','wall_time','axis','split','run_identity','duplicate_step','restart_segment']
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_name(p.name+'.partial');q.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');q.replace(p)
def mask(b):
 c=google_crc32c.value(b);return ((c>>15)|(c<<17)&0xffffffff)+0xa282ead8&0xffffffff
def records(p):
 with Path(p).open('rb') as f:
  order=0
  while True:
   offset=f.tell();h=f.read(8)
   if not h:return
   if len(h)!=8:raise ValueError('TRUNCATED_LENGTH at '+str(offset))
   n=struct.unpack('<Q',h)[0];assert n<=16*1024**2,'UNBOUNDED_RECORD'
   c=f.read(4)
   if len(c)!=4:raise ValueError('TRUNCATED_LENGTH_CRC at '+str(offset))
   if struct.unpack('<I',c)[0]!=mask(h):raise ValueError('LENGTH_CRC at '+str(offset))
   b=f.read(n);c=f.read(4)
   if len(b)!=n or len(c)!=4:raise ValueError('TRUNCATED_PAYLOAD at '+str(offset))
   if struct.unpack('<I',c)[0]!=mask(b):raise ValueError('DATA_CRC at '+str(offset))
   order+=1;yield order,offset,b
def varint(b,i):
 v=0;s=0
 while True:
  assert i<len(b) and s<70,'MALFORMED_VARINT';c=b[i];i+=1;v|=(c&127)<<s
  if not c&128:return v,i
  s+=7
def wire(b):
 i=0
 while i<len(b):
  k,i=varint(b,i);n,t=k>>3,k&7;assert n>0
  if t==0:v,i=varint(b,i)
  elif t in (1,5):size=8 if t==1 else 4;v=b[i:i+size];i+=size;assert len(v)==size
  elif t==2:size,i=varint(b,i);v=b[i:i+size];i+=size;assert len(v)==size
  else:raise ValueError('UNSUPPORTED_WIRE_TYPE')
  yield n,t,v
def decode(b):
 wall=0.;step=0;summary=[];other=[]
 for n,t,v in wire(b):
  if n==1 and t==1:wall=struct.unpack('<d',v)[0]
  elif n==2 and t==0:step=v-(1<<64) if v>=1<<63 else v
  elif n==5 and t==2:
   for sn,st,sv in wire(v):
    if sn!=1 or st!=2:continue
    tag='';value=None
    for vn,vt,vv in wire(sv):
     if vn==1 and vt==2:tag=vv.decode('utf-8')
     elif vn==2 and vt==5:value=struct.unpack('<f',vv)[0]
     elif vn in (3,4,5,6,8):other.append({'kind':'NON_SIMPLE_VALUE','field':vn,'tag':tag})
    if value is not None:summary.append((tag,value))
  else:other.append({'field':n,'wire_type':t})
 return wall,step,summary,other
def axis(tag):return 'samples' if 'vs samples' in tag.lower() else 'steps'
def split(tag):
 if 'validation' in tag.lower():return 'validation_label_only'
 if any(t in tag.lower() for t in ['forget loss','retain loss','maxent loss']):return 'training_label_only'
 return 'unresolved'
def relevant(tag):return any(t in tag.lower() for t in ['forget','retain','maxent','loss']) and not ('grad' in tag.lower())
def canonical(tag,value,step,wall,order,vi):return json.dumps([order,vi,tag,repr(value),step,repr(wall)],ensure_ascii=False,separators=(',',':')).encode()+b'\n'
def fixture(root):
 root=Path(root);root.mkdir(parents=True,exist_ok=True);p=root/'known.tfevents';e=event_pb2.Event(wall_time=1234.125,step=1500);e.summary.value.add(tag='forget loss validation',simple_value=1.3953843116760254);e.summary.value.add(tag='forget loss validation',simple_value=1.3952388763427734)
 data=e.SerializeToString();h=struct.pack('<Q',len(data));p.write_bytes(h+struct.pack('<I',mask(h))+data+struct.pack('<I',mask(data)))
 maintained=list(LegacyEventFileLoader(str(p)).Load());raw=list(records(p));decoded=decode(raw[0][2]);assert len(maintained)==len(raw)==1 and decoded[1]==1500
 assert decoded[2]==[(v.tag,v.simple_value) for v in maintained[0].summary.value]
 original=pywrap_tensorflow.masked_crc32c
 assert all(original(x)==mask(x) for x in [b'',b'123456789',data,h,bytes(range(256))])
 bad=p.with_name('bad-crc.tfevents');d=bytearray(p.read_bytes());d[-1]^=1;bad.write_bytes(d)
 trunc=p.with_name('truncated.tfevents');trunc.write_bytes(p.read_bytes()[:-2]);failures=[]
 for q in [bad,trunc]:
  try:list(records(q));raise AssertionError('CORRUPTION_NOT_DETECTED')
  except ValueError as x:failures.append(str(x))
 return {'status':'PASS','maintained_reader':'tensorboard LegacyEventFileLoader','independent_decoder':'strict TFRecord framing/compiled CRC32C and standalone protobuf wire decoder','fixtures':['two distinct values same tag/step','exact float32','CRC agreement with maintained CRC implementation','corrupt payload CRC rejected','truncation rejected'],'failures_expected':failures,'CRC_acceleration':'Compiled google_crc32c supplies identical masked CRC algorithm to maintained reader; independent framing still checks every record','numerical_runtime_untouched':True}
def extract(root,out):
 root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True);sources=json.loads((root/'inputs/SOURCE_PLAN.json').read_text());results=[]
 # Avoid a pure-Python CRC bottleneck in the maintained fallback reader; fixture establishes equivalence.
 pywrap_tensorflow.masked_crc32c=mask
 for source in sources:
  oid=source['id'];p=root/'sources'/(oid+'.tfevents');receipt=out/(oid+'.json')
  if receipt.exists():
   old=json.loads(receipt.read_text());assert old['source_sha256']==sha(p) and sha(out/old['full_scalar_table'])==old['full_scalar_sha256'] and sha(out/old['relevant_scalar_table'])==old['relevant_scalar_sha256'];results.append(old);continue
  h=sha(p);assert p.stat().st_size==source['bytes'] and h==source['sha256'];allpath=out/(oid+'.scalars.csv.gz');relpath=out/(oid+'.relevant.csv');alltmp=allpath.with_suffix('.partial');reltmp=relpath.with_suffix('.partial');assert not alltmp.exists() and not reltmp.exists()
  counts=collections.Counter();ev=0;scalars=0;roll=hashlib.sha256();seen={};duplicates=[];restart=[];segments=collections.defaultdict(int);last={};validation=[];metadata=[];start=time.monotonic()
  with alltmp.open('xb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0,compresslevel=1) as z,io.TextIOWrapper(z,newline='') as gz,reltmp.open('x',newline='') as rf:
   w=csv.DictWriter(gz,fieldnames=FIELDS);w.writeheader();rw=csv.DictWriter(rf,fieldnames=FIELDS);rw.writeheader()
   for ev,event in enumerate(LegacyEventFileLoader(str(p)).Load(),1):
    if not event.HasField('summary'):
     metadata.append({'event_order':ev,'fields':sorted(f.name for f,v in event.ListFields())});continue
    for vi,v in enumerate(event.summary.value):
     if not v.HasField('simple_value'):raise ValueError('SOURCE_REQUIRES_NON_SIMPLE_SCALAR_DECODER at event '+str(ev))
     tag=v.tag;value=float(v.simple_value);step=int(event.step);wall=float(event.wall_time);key=(tag,step);duplicate=key in seen;segment=segments[tag]
     if tag in last and step<last[tag]:segments[tag]+=1;segment=segments[tag];restart.append({'source_id':oid,'event_order':ev,'tag':tag,'previous_step':last[tag],'step':step,'segment':segment})
     last[tag]=step
     if duplicate:duplicates.append({'source_id':oid,'event_order':ev,'tag':tag,'step':step,'first_event_order':seen[key][0],'first_value':seen[key][1],'value':repr(value),'axis':axis(tag)})
     else:seen[key]=(ev,repr(value))
     row=dict(zip(FIELDS,[h+':'+str(ev)+':'+str(vi),oid,h,ev,vi,tag,repr(value),step,repr(wall),axis(tag),split(tag),'source-file:'+h,duplicate,segment]));w.writerow(row)
     if relevant(tag):rw.writerow(row)
     if 'forget loss validation'==tag:validation.append(row)
     counts[tag]+=1;scalars+=1;roll.update(canonical(tag,value,step,wall,ev,vi))
    if ev%100000==0:print('EXTRACT',oid,ev,round(time.monotonic()-start,1),flush=True)
  # Strict full-file framing independently prevents the maintained reader swallowing a truncated suffix.
  n=0;wire_scalars=0;independent=hashlib.sha256();wire_tags=collections.Counter();other_counts=collections.Counter()
  for n,offset,b in records(p):
   wall,step,values,other=decode(b)
   for vi,(tag,value) in enumerate(values):independent.update(canonical(tag,value,step,wall,n,vi));wire_scalars+=1;wire_tags[tag]+=1
   for item in other:other_counts[str(item)]+=1
  assert ev==n and scalars==wire_scalars and roll.hexdigest()==independent.hexdigest() and counts==wire_tags
  alltmp.rename(allpath);reltmp.rename(relpath)
  result={**source,'status':'FULL_SOURCE_VERIFIED','source_sha256':h,'record_count':ev,'scalar_count':scalars,'maintained_scalar_digest':roll.hexdigest(),'independent_wire_scalar_digest':independent.hexdigest(),'independent_record_count':n,'independent_scalar_count':wire_scalars,'all_record_boundaries_and_two_CRCs_verified':True,'truncated_records':0,'unsupported_scalar_records':0,'tag_counts':dict(sorted(counts.items())),'duplicate_observations':duplicates,'restart_diagnostics':restart,'non_summary_metadata':metadata,'non_scalar_wire_fields':dict(other_counts),'validation_observations':validation,'full_scalar_table':allpath.name,'full_scalar_sha256':sha(allpath),'full_scalar_bytes':allpath.stat().st_size,'relevant_scalar_table':relpath.name,'relevant_scalar_sha256':sha(relpath),'elapsed_seconds':time.monotonic()-start}
  save(receipt,result);results.append(result);print('SOURCE_COMPLETE',oid,ev,scalars,'duplicates',len(duplicates),flush=True)
 save(out/'EXTRACTION_RECEIPT.json',{'status':'PASS','sources':results,'source_files':len(results),'source_bytes':sum(x['bytes'] for x in results),'complete_records':sum(x['record_count'] for x in results),'scalar_observations':sum(x['scalar_count'] for x in results),'duplicate_observations':sum(len(x['duplicate_observations']) for x in results),'all_sources_cross_checked':True})
 return results
if __name__=='__main__':
 if sys.argv[1]=='fixture':save(Path(sys.argv[2])/'PARSER_QUALIFICATION.json',fixture(Path(sys.argv[2])/'parser-fixtures'))
 elif sys.argv[1]=='extract':extract(sys.argv[2],sys.argv[3])
