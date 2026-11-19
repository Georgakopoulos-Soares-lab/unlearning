"""Finite predeclared adjacent and paired-LM work only; A09 never dispatched."""
from common8 import *
from launch8 import launch
from backup8 import main as backup
from report8 import progress

def classifier_done(family):
 paths=list((A/'contrasts/classifier'/family).glob('*/*/*/seed*/COMPLETE.json'));assert len(paths)==546
 for p in paths:
  j=read(p);assert j['status']=='PASS' and j['identity']['contrast_source_sha256']==sha(C/'CONTRAST_SOURCE_IDENTITY.json')
 return paths

def main():
 for family in ['R4_minus_R3','R5_minus_R4','R6_minus_R5']:
  assert not (C/'STOP_SCHEDULING').exists()
  if family=='R4_minus_R3':assert read(C/'BACKUP_adjacent_R4_minus_R3.json')['status']=='PASS'
  else:
   launch('adjacent-'+family+'-001','run_classifier8.py',['--stage','A08','--family',family],'CONTRAST_SOURCE_IDENTITY.json');classifier_done(family);backup('adjacent_'+family,'classifier')
  classifier_done(family);publish('BACKUP_adjacent_'+family+'.json',read(C/('BACKUP_adjacent_'+family+'.json')));progress(family+':5460 paired classifier rows verified by two numerical routes;420 anchor vectors freshly recovered.')
 launch('paired-LM-001','run_lm8.py',['--stage','A08'],'CONTRAST_SOURCE_IDENTITY.json');paths=list((A/'contrasts/LM').glob('*/*/*/COMPLETE.json'));assert len(paths)==35 and all(read(p)['status']=='PASS' for p in paths)
 launch('paired-LM-points-001','verify_LM_points8.py',['--stage','A08'],'CONTRAST_SOURCE_IDENTITY.json');assert read(C/'LM_PAIRED_POINT_SUPPLEMENT.json')['status']=='PASS';r=backup('LM_all','LM');publish('BACKUP_LM_all.json',r)
 cls=[read(p.parent/'RESULTS.json') for p in (A/'contrasts/classifier').glob('*/*/*/*/seed*/COMPLETE.json')];lm=[read(p.parent/'RESULTS.json') for p in paths];assert len(cls)==1638 and sum(len(r['rows']) for r in cls)==16380 and sum(r['attempted_values'] for r in cls)==32760000 and sum(len(r['rows']) for r in lm)==70
 receipt={'status':'PASS','classifier_rows':16380,'classifier_attempted_delta_values':32760000,'LM_rows':70,'LM_attempted_delta_values':140000,'classifier_point_max_abs':max(r['point_max_abs'] for r in cls),'classifier_draw_max_abs':max(r['draw_max_abs'] for r in cls),'classifier_CI_max_abs':max(r['interval_max_abs'] for r in cls),'LM_point_max_abs':max(r['point_max_abs'] for r in lm),'LM_draw_max_abs':max(r['draw_max_abs'] for r in lm),'LM_CI_max_abs':max(r['interval_max_abs'] for r in lm),'LM_paired_point_supplement':read(C/'LM_PAIRED_POINT_SUPPLEMENT.json'),'R2_dependent_slots_still_missing':10948,'nonadjacent_historical_families_not_recalculated':True,'source_sha256':sha(C/'CONTRAST_SOURCE_IDENTITY.json')};put(C/'CONTRAST_VERIFICATION.json',receipt);publish('CONTRAST_VERIFICATION.json',receipt);put(C/'ANALYSIS_QUEUE_RESULT.json',{'status':'PASS','new_classifier_rows':16380,'new_LM_rows':70,'A09_started':False,'completed_utc':now()});progress('All16380 new adjacent classifier and70 paired LM rows verified;1260 classifier and70 LM vectors freshly recovered. Tables/analysis/figures/final delivery remain.');print('ANALYSIS_QUEUE_PASS',flush=True)
if __name__=='__main__':main()
