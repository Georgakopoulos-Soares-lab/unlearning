"""Pure validation for frozen planning and future gates. No stage execution."""
import hashlib,json
from pathlib import Path
import numpy as np
def require(ok,why):
 if not ok:raise ValueError(why)
def paired_rows(left,right):
 for k in ['ids','labels','groups','classes']:
  require(np.array_equal(left[k],right[k]),'Unpaired '+k)
 require(len(set(left['ids']))==len(left['ids']),'Duplicate example identity')
def probabilities(p,classes,expected):
 require(np.array_equal(classes,expected),'Class columns inverted')
 require(p.shape[1]==len(classes) and np.isfinite(p).all() and np.all(p>=0) and np.all(p<=1),'Invalid probabilities')
 require(np.allclose(p.sum(1),1,rtol=0,atol=1e-12),'Probability rows do not sum to1')
def next_gate(candidate,completed):
 sequence=['H3_EXTRACTION','H3_78_REFITS','H3_78_FIXED','H3_INDEPENDENT_AUDIT','H3_SEALED','OTHER_FIVE_EXTRACTION']
 prefix=candidate+'/'
 for step in sequence:
  if prefix+step not in completed:return prefix+step
 return candidate+'/A06_EXTRACTION_SEALED'
def eligible_contrast(target,reference):
 if any(a in ['R2','R5'] for a in [target,reference]):return False
 if 'R3' in [target,reference] and any(a in ['R4','R6'] for a in [target,reference]):return False
 return True
def lm_corpus(losses,counts,real):
 losses=np.asarray(losses)[real].astype(np.float64);counts=np.asarray(counts)[real].astype(np.float64)
 require(np.all(counts>0) and np.isfinite(losses).all(),'Invalid LM sufficient statistics')
 return losses.sum()/counts.sum()
def paired_draw_difference(left,right,draws):
 require(left.shape==right.shape,'Different populations')
 return (left[draws]-right[draws]).mean(1)
def output_path(path,root):
 p=Path(path).resolve();r=Path(root).resolve();require(p.is_relative_to(r) and p!=r,'Historical/unowned write path');return p
def validate_plan(plan,rows):
 heads=[r for r in rows if r['unit_kind']=='final_head'];require(len(heads)==3276,'Shrunk head universe')
 require(len({r['unit_id'] for r in rows})==len(rows),'Duplicate unit identity')
 for alias in ['base','R1','R2','R3','R4','R5','R6']:require(sum(r['checkpoint']==alias for r in heads)==468,'Uneven endpoint universe')
 require(sum(r['status']=='REUSED_VALIDATED' for r in heads)==1404,'Historical reuse wrong')
 require(sum(r['status']=='ELIGIBLE' for r in heads)==936,'Qualified proposal wrong')
 require(sum(r['unit_kind']=='control_head' for r in rows)==36,'Control multiplication')
 require(len(plan['new_proposed_units'])==936,'Missing executable proposal')
 require(sum(u['owning_stage']=='A06' for u in plan['new_proposed_units'])==156,'H3 gate coverage wrong')
 for u in plan['new_proposed_units']:
  if u['owning_stage']=='A07':require(any('H3_GATE_SEALED' in p for p in u['prerequisites']),'H3 bypass')
 return {'status':'PASS','full_heads':len(heads),'proposed':936,'H3_heads_A06':156,'remaining_heads_A07':780,'controls':36,'all_rows':len(rows)}
