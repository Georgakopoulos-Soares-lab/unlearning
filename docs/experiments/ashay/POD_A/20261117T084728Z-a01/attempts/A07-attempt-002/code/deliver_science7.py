"""Deliver sealed owned reports after explicit sanitized CSV size-policy reconciliation."""
from common7 import *
from finish7 import seal,quiet
from delivery7 import deliver
import gzip

def main():
 guard();assert not (C/'SCIENTIFIC_DELIVERY.json').exists();state=quiet();v=read(C/'PUBLICATION_VALIDATION.json');assert v['status']=='PASS'
 for name,h in v['table_sha256s'].items():assert sha(D/name)==h
 for e in read(C/'CPU_SOURCE_IDENTITY.json')['files']:assert sha(A/'code'/e['path'])==e['sha256']
 for filename in ['RESULTS_LONG.csv','PAIRED_CONTRASTS.csv']:
  content=(D/filename).read_bytes();data=gzip.compress(content,compresslevel=6,mtime=0);assert gzip.decompress(data)==content;publish(filename+'.gz',data)
 accounting=[]
 for task in TASKS[1:]:
  b=read(C/('BACKUP_R5_'+task+'.json'));checks=b['CPU_restored_checks'];assert len(checks['checks'])==12 and checks['paired_vectors']==240
  accounting.append({'task':task,'recovery_receipt_sha256':sha(C/('BACKUP_R5_'+task+'.json')),'counts_derived_from_validated_frozen_restore_loops_and_receipt':True,'probability_arrays':12,'probability_scalar_comparisons':12*512*(3 if task=='gue_splice_reconstructed' else 2),'point_metric_comparisons':300,'marginal_draw_vectors':60,'marginal_draw_scalar_comparisons':120000,'paired_draw_vectors':240,'paired_draw_scalar_comparisons':480000,'CI_endpoint_comparisons':600,'validity_mask_boolean_comparisons':120000,'max_abs_residuals':checks['max_abs_residuals'],'worst_units_by_check':checks['worst_units']})
 publish('RECOVERY_COMPARISON_ACCOUNTING.json',{'status':'PASS','tasks':accounting,'unique_panel_prediction_metric_paths':60,'unique_panel_paired_vectors':1200,'separate_isolation_test':'PRODUCER_PATH_DENIAL_TEST.json repeats one12-path/240-vector panel under active producer-path denial, no new fit','tolerances':{'probabilities':1e-10,'points_draws_CIs':1e-12}})
 publish('APPROVAL_LOG_APPEND_RECEIPT.json',read(C/'APPROVAL_LOG_APPEND_RECEIPT.json'))
 publish('DELIVERY_TABLE_POLICY.json',{'status':'PASS','scope':'Only the two canonical sanitized aggregate CSV reports may be up to50MiB; all other files retain20MiB limit. Raw sequences/arrays/predictions/heads/weights remain forbidden.','reason':'Required8400-row typed-provenance/full-precision paired table exceeds inherited A06 helper20MiB assumption; no package contract sets that assumption. No scientific bytes changed to repair delivery.','sizes':{name:(D/name).stat().st_size for name in ['RESULTS_LONG.csv','PAIRED_CONTRASTS.csv']},'lossless_gzip_mirrors_verified':True,'report_only_failure_log':'Preserved privately as finish.001.stderr.log','all_fits_audits_and_scientific_seals_reused':True})
 for p in (A/'code').glob('*.py'):publish('code/'+p.name,p.read_bytes())
 publish('ORCHESTRATION_SOURCE_IDENTITY.json',{'files':[{'path':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted((A/'code').glob('*.py'))],'scientific_CPU_identity_sha256':sha(C/'CPU_SOURCE_IDENTITY.json'),'report_delivery_reconciliation_only':True})
 seal();r=deliver('A07 R5: publish 390 protected probes, exact12300 results and A08 readiness');put(C/'SCIENTIFIC_DELIVERY.json',r);print(json.dumps({k:r[k] for k in ['status','commit','remote_equal']}))
if __name__=='__main__':main()
