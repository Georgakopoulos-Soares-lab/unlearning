"""Add exact declaration-source rows and measured audit timings, no effect values."""
from common5 import *
def main():
 guard()
 with (D3/'EXPOSURE_AUDIT.csv').open() as f:old={(e['stage'],e['task']):e for e in csv.DictReader(f)}
 with (D/'INCLUSION_EXPOSURE_PLAN.csv').open() as f:rows=list(csv.DictReader(f))
 for e in rows:
  source=old.get((e['candidate'],e['task']));e['observed_selected_config_declares_family']=source['config_declares_family'] if source else 'UNKNOWN_NO_ADMITTED_R2';e['first_observed_selected_config_declaration']=source['first_observed_selected_config_declaration'] if source else 'UNKNOWN_NO_ADMITTED_R2';e['config_sha256']=source['config_sha256'] if source else '';e['config_locator']=source['config_locator'] if source else 'NO_ADMITTED_R2';e['source_row_sha256']=digest(source) if source else '';e['actual_parent_evidence']=source['actual_parent'] if source else 'UNKNOWN';e['executed_objective_evidence']=source['executed_objective'] if source else 'UNKNOWN';e['actual_benign_retain_row_manifest']=source['actual_benign_retain_row_manifest'] if source else 'NOT_SUPPLIED'
 table('INCLUSION_EXPOSURE_PLAN.csv',rows)
 r=read(D/'THROUGHPUT_FORECAST.json');a=read(D8/'AUDIT_REFIT_RECEIPT.json');seconds=sum(e['wall_seconds'] for e in a['units']);r['measured_A08_60_full_CV_audit_refit_unit_wall_sum_seconds_not_elapsed']=seconds;r['R5_30_full_CV_other_five_refit_linear_unit_wall_sum_seconds']=seconds/2;r['R5_30_full_CV_other_five_refit_planning_unit_wall_range_seconds']=[seconds/4,seconds*1.5];r['audit_timing_basis']='Prior60 independently full-CV refit units/960 initial solver calls; R5 other-five30/480, H3six/60 separate. Unit-wall sum differs from pipeline elapsed. Metadata timings only; no audit refit repeated.';publish('THROUGHPUT_FORECAST.json',r)
 publish('CONTROL_NAME_ALIASES.json',{'historical_control_name':'4mer','canonical_report_name':'kmer4','mapping_kind':'TYPED_NAME_ALIAS_NO_VALUE_OR_FEATURE_CHANGE','definition':'Normalized forward4mer frequencies; no reverse-complement collapse','source':{'path':str((D3/'CONTROL_REUSE_INDEX.json').relative_to(W)),'sha256':sha(D3/'CONTROL_REUSE_INDEX.json')},'new_control_refits':0})
 for name in ['keys5.py','common5.py','metadata_contract5.py','refine5.py']:publish('code/'+name,(A/'code'/name).read_bytes())
 no_science_imports();print('PASS: exact config declaration metadata and audit timing sources added')
if __name__=='__main__':main()
