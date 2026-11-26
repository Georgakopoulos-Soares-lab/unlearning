"""Independent bounded T00 acceptance route: primary bytes, decisions and challenges.

This checker does not import the contract generator and runs no scientific work.
"""
from pathlib import Path
import json, hashlib, subprocess, copy, math, datetime, os

P=Path(__file__).resolve().parents[2]
R=Path('/workspace/pod-a-saliency/research-POD_A_SALIENCY')
C=Path('/workspace/pod-a-saliency/control/20261123T111855Z-saliency/T_SERIES/v2/T00/attempt-001')
ANCHOR='a4bb5b0305591ccc0b57db752bf0d4f1f2f6f89e'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a,cwd=R):return subprocess.check_output(['git',*a],cwd=cwd,timeout=15).decode().strip()
reg=read(P/'CONTINUATION_REGISTER.json')
sources={x['id']:x for x in reg['source_register']}
def src(i):return read(R/sources[i]['path'])
checks=[]
def check(name,condition,detail):
    assert condition, name+': '+detail
    checks.append({'check':name,'status':'PASS','detail':detail})
check('01_v2_stage_meanings',reg['plan_version']=='v2_T00_T16' and
      [s['id'] for s in reg['stages']]==['T'+str(i).zfill(2) for i in range(17)] and
      'cohort' in reg['stages'][2]['title'] and 'binding' in reg['stages'][3]['title'] and
      'Metric' not in reg['stages'][3]['title'], 'Exact17stage v2 map, not prior8stage proposal')
total=0
for s in reg['source_register']:
    if s['id'] in ['PROMPT','PLAN']:continue
    path=R/s['path']
    assert sha(path)==s['sha256'] and path.stat().st_size==s['bytes']
    assert git('rev-parse',ANCHOR+':'+s['path'])==s['git_blob_id']
    assert git('hash-object',str(path))==s['git_blob_id']
    total+=s['bytes']
assert sha(P/'T00/attempt-001/PROMPT.md')==sources['PROMPT']['sha256']
check('02_exact_predecessors',all('SRC'+str(i).zfill(2) in sources for i in range(1,20)),
      '19 exact source paths compared independently to Git blob/SHA256; eight required predecessors available')
check('03_scoped_precedence',src('SRC16')['verified_units']==0 and
      src('SRC09')['status']=='VERIFIED' and src('SRC09')['S07_producer_status_unchanged']=='COMPLETE_UNVERIFIED' and
      src('SRC10')['status']=='COMPLETE' and src('SRC11')['verified_units']==48924 and
      src('SRC17')['verified_units']==9 and len(reg['source_precedence'])==4,
      'Read actual producer/release/corrected receipts; no timestamp-only/controller invalidation')
Q={x['id']:x for x in reg['questions']};D={x['id']:x for x in reg['dependencies']}
S={x['id']:x for x in reg['stages']};roles={x['id'] for x in reg['roles']}
A={x['id'] for x in reg['prospective_artifact_register']}
CP={x['id'] for x in reg['qualification_policy']['claim_family_policies']}
FP={x['id'] for x in reg['deliverable_contract']['figure_families']}
CMP={x['id'] for x in reg['qualification_policy']['comparison_family_policies']}
check('04_required_questions',set(Q)=={'Q'+str(i).zfill(2) for i in range(1,12)} and all(
      all(x[k] for k in ['wording','obligation_class','scope_basis','scientific_unit','evidence_requirements','current_answer_state','source_ids','responsible_role','deciding_stages','permitted_conclusion','completion_consequence']) for x in Q.values()),
      'Each original/claim-dependent question has evidence, role, unit, deciding stage and closure consequence')
policy=reg['completion_policy']; coverage=reg['coverage_policy']
check('05_no_silent_reduction',policy['scope_amendments']==[] and policy['missingness_can_reduce_scope'] is False and
      not reg['required_scope_definition_complete'] and policy['current_original_request']=='PARTIAL' and
      len(policy['original_scope_all_required'])==8,
      'No scope amendment inferred from missingness; eight conjunctive scientific completion requirements')
facts=src('SRC05');roster=src('SRC13');known=reg['known_endpoint_roster']
check('06_nine_exact_endpoints',len(known)==len(roster)==9 and
      len({x['content_sha256'] for x in known})==9 and all(
          all(x[k]==roster[x['alias']][k] for k in roster[x['alias']]) for x in known) and
      reg['inventory_completeness']['requested_endpoint_total'] is None,
      'Every alias/content/label/step checked against exact registry; exhaustiveness separately unresolved')
endpoint={x['alias']:x for x in known}
dup=reg['duplicate_observations']
check('07_endpoint_and_duplicate_roles',endpoint['candidate_04']['step']==2000 and endpoint['candidate_05']['step']==2151 and
      endpoint['candidate_04']['content_sha256']!=endpoint['candidate_05']['content_sha256'] and
      dup['reinit5_A_step1500_original_values']==facts['reinit5_duplicate_original_values']==['1.3953843116760254','1.3952388763427734'] and
      dup['selection_or_average_permitted'] is False and dup['reinit5_B_training_last_step']==1439,
      'Both noise5 tensors and reinit5 values/history remain distinct')
counts=reg['baseline_counts']['retain']
check('08_typed_retain_bookkeeping',counts==facts['coverage'] and
      9*6*26*3==counts['refitted_heads']==counts['unchanged_base_applications']==4212 and
      2*4212==counts['prediction_paths']==8424 and 5*8424==counts['classifier_metric_records']==42120 and
      counts['LM_units']==54+54==108 and counts['LM_metric_records']==216 and
      sum(counts['contrast_families'].values())==48924 and sum(counts['deferred_families'].values())==42228 and
      src('SRC11')['verified_units']==counts['admitted_S09_contrasts'],
      'Arithmetic and actual released receipts agree; records/CV seeds not called intervention replicates')
forget=reg['baseline_counts']['forget']
check('09_unknown_denominators',coverage['actual_unique_examples'] is None and coverage['actual_valid_target_count'] is None and
      coverage['required_forget_cell_count'] is None and coverage['required_forget_coverage_universe'] is None and
      not coverage['illustration_is_required_forget_denominator'] and
      forget['sources']==9 and forget['validation_forget_loss_step_observations']==23 and forget['forget_validation_loss_and_ppl_both_axes_records']==92,
      'Unknown totals remain null with reasons;23observations are not92independent evaluations')
qp=reg['qualification_policy']
check('10_separate_qualification',all(qp.get(k) for k in ['source_verification','point','interval','comparison']) and
      qp['interval_required_for_absolute_point'] is False and qp['reference_required_for_absolute_point'] is False and
      qp['qualification_ledger']==qp['eligible_comparison_ledger']==qp['new_claim_ledger']==[] and
      Q['Q06']['obligation_class']==Q['Q08']['obligation_class']=='REQUIRED_FOR_CLAIM',
      'No T00 admission; point/interval/comparison gates distinct and conditional')
check('11_genuine_layerwise_requirement',coverage['qualified_layerwise_forget_observations']==0 and
      forget['layerwise_forget_performance_observations']==0 and Q['Q07']['obligation_class']=='REQUIRED_ORIGINAL' and
      'gradient' in qp['layerwise'] and 'D11' in D and len(reg['deliverable_contract']['figure_families'])==6,
      'Layerwise request remains mandatory; global loss/gradientnorms cannot fill it')
state=reg['separate_states']
check('12_independent_states',state['T00_execution']=='COMPLETE' and state['delivery']=='DRAFT' and
      state['collaborator_acceptance'] is None and policy['current_original_request']=='PARTIAL' and
      policy['current_final_closure_verdict'] is None and 'new_forget_interval_qualification' in state and
      'report_review_release' in state and 'recovery' in state,
      'Stage, scientific scope, report, recovery, delivery and feedback cannot imply one another')
check('13_sufficient_dependencies',all(all(d.get(k) for k in [
      'category','missing','existing_source_ids_checked','scientific_consequence','minimum_sufficient_response',
      'acceptable_evidence_types','affected_stage_ids','affected_artifact_ids','responsible_role','state',
      'last_material_update','next_useful_action','independent_work_possible','conclusion_unavailable_if_never_resolved'])
      and d['ownership_confirmed'] is False for d in D.values()),
      'Every dependency has checked sources, sufficient response, affected scope and independent work; no accepted owner invented')
check('14_local_invalidation',len(reg['change_invalidation'])==7 and all(
      x['preserve'] and x['route'] and 'invalidate' in x for x in reg['change_invalidation']) and
      qp['evidence_chain']==['source_version','interpretation_or_qualification_decision','eligible_record_or_comparison','claim','display_or_report_artifact'],
      'Seven explicit change routes preserve independent evidence and sealed prior editions')
prose=(P/'CONTINUATION_CONTRACT.md').read_text()
def row_exists(parts):return ('| '+' | '.join(parts)+' |') in prose
check('15_readable_tables_match',all(row_exists([x['id'],x['wording'],x['obligation_class'],x['current_answer_state'],', '.join(x['deciding_stages']),'; '.join(x['evidence_requirements']),x['completion_consequence']]) for x in Q.values()) and
      all(f"| {e['alias']} | {e['supplied_method_label']} | {e['nominal_fraction']:g} | {e['step']} | `{e['content_sha256']}` |" in prose for e in known) and
      all(d['minimum_sufficient_response'] in prose for d in D.values()) and all(s['acceptance_rule'] in prose for s in S.values()),
      'Human question, endpoint, dependency and stage tables checked directly against canonical values')
for x in Q.values():
    assert set(x['source_ids'])<=sources.keys() and set(x['dependency_ids'])<=D.keys()
    assert set(x['deciding_stages'])<=S.keys() and x['responsible_role'] in roles
for x in D.values():
    assert set(x['existing_source_ids_checked'])<=sources.keys() and set(x['affected_question_ids'])<=Q.keys()
    assert set(x['affected_claim_ids'])<=CP and set(x['affected_comparison_ids'])<=CMP
    assert set(x['affected_figure_ids'])<=FP and set(x['affected_artifact_ids'])<=A and set(x['affected_stage_ids'])<=S.keys()
for x in S.values():
    assert set(x['question_ids'])<=Q.keys() and set(x['input_source_ids'])<=sources.keys()
    assert set(x['required_predecessor_stages'])<=S.keys() and set(x['prospective_input_artifact_ids'])<=A
    assert set(x['output_artifact_ids'])<=A and all(x[k] for k in ['decisions','acceptance_rule','blocked_case_behavior','handoff'])
check('16_foreign_keys_and_empty_future_ledgers',True,'All question/source/dependency/role/stage/artifact/claim/comparison/figure references resolve; future artifact IDs explicitly prospective')
before=read(C/'BEFORE_STATE.json')
assert git('rev-parse','HEAD')==ANCHOR==before['HEAD']
assert git('rev-parse','POD_A')==before['original_POD_A_tip']
assert git('diff','--name-only','HEAD')==''
untracked=git('ls-files','--others','--exclude-standard').splitlines()
prefix=str(P.relative_to(R))+'/'
check('17_owned_paths_and_history',all(x.startswith(prefix) for x in untracked) and
      git('diff','--cached','--name-only')=='' and git('branch','--show-current')=='POD_A_SALIENCY',
      'Only new owned continuation paths; HEAD/originalPOD_A/index/tracked history unchanged')
check('18_terminal_boundary',all(s['status']=='NOT_STARTED' and not s['execution_authorized_in_this_invocation'] for s in reg['stages'][1:]) and
      reg['authorization']['commits_pushes_uploads_messages_authorized'] is False and
      reg['interruption_recovery']['scientific_transfer_bytes']==0 and reg['scope_boundaries']['no_deadline_amendment'],
      'T01–T16 unexecuted, no messages/publication/scientific work or deadline introduced')

# Expected answers were specified by PROMPT sections7/15 before these handlers.
# These synthetic metadata fixtures are never scientific observations.
challenges=[
 {'id':'CH01','case':'Stage complete but scientific scope incomplete','input':{'stage_complete':True,'conditions':{k:False for k in policy['original_scope_all_required']}},'expected':{'original_status':'PARTIAL'}},
 {'id':'CH02','case':'One whole-model value copied into26layer slots','input':{'measurement_level':'WHOLE_MODEL','claimed_layer_slots':26,'genuine_hooks':False},'expected':{'layerwise_eligible':False}},
 {'id':'CH03','case':'Same nominal fraction, distinct exact tensors','input':{'endpoints':[{'nominal':0.05,'content':'tensor-A'},{'nominal':0.05,'content':'tensor-B'}]},'expected':{'distinct_endpoints':2}},
 {'id':'CH04','case':'Valid point, reversed interval bounds','input':{'point_qualified':True,'estimate':1.0,'interval':[2.0,0.0]},'expected':{'point_eligible':True,'interval_eligible':False}},
 {'id':'CH05','case':'Matching display labels, incompatible actual cohorts','input':{'display_target':'same','display_reference':'same','actual_target_cohort':'cohort-A','actual_reference_cohort':'cohort-B'},'expected':{'comparison_eligible':False}},
 {'id':'CH06','case':'Unknown source denominator relabeled zero','input':{'source_denominator':None,'proposed_denominator':0},'expected':{'representation_valid':False}},
 {'id':'CH07','case':'Unsent package called delivered','input':{'sent':False,'declared_delivery':'DELIVERED'},'expected':{'delivery_claim_valid':False}},
 {'id':'CH08','case':'Stale producer/controller versus exact independent overlay','input':{'producer_state':'COMPLETE_UNVERIFIED','overlay_matches_source':True,'overlay_release':'VERIFIED'},'expected':{'reuse_state':'VERIFIED','producer_state':'COMPLETE_UNVERIFIED'}}]
def challenge(case,x):
    if case=='CH01':return {'original_status':'COMPLETE_ORIGINAL_SCOPE' if all(x['conditions'].values()) else 'PARTIAL'}
    if case=='CH02':return {'layerwise_eligible':x['measurement_level']=='LAYERWISE_PERFORMANCE' and x['genuine_hooks']}
    if case=='CH03':return {'distinct_endpoints':len({e['content'] for e in x['endpoints']})}
    if case=='CH04':
        lo,hi=x['interval'];valid=x['point_qualified'] and math.isfinite(x['estimate'])
        return {'point_eligible':valid,'interval_eligible':valid and math.isfinite(lo) and math.isfinite(hi) and lo<=hi}
    if case=='CH05':return {'comparison_eligible':x['actual_target_cohort']==x['actual_reference_cohort']}
    if case=='CH06':return {'representation_valid':x['source_denominator']==x['proposed_denominator']}
    if case=='CH07':return {'delivery_claim_valid':x['sent'] or x['declared_delivery'] not in ['DELIVERED','ACCESS_VERIFIED']}
    if case=='CH08':return {'reuse_state':x['overlay_release'] if x['overlay_matches_source'] else 'UNRESOLVED','producer_state':x['producer_state']}
for x in challenges:
    x['observed']=challenge(x['id'],x['input'])
    assert x['observed']==x['expected'],x['id']
    x['status']='PASS'

result={'schema_version':'t00-independent-contract-verification-v1','status':'PASS','research_anchor':ANCHOR,
 'register_sha256':sha(P/'CONTINUATION_REGISTER.json'),'contract_sha256':sha(P/'CONTINUATION_CONTRACT.md'),
 'route':'Separate checker reads canonical register and exact primary files directly; no generator import or numerical replay',
 'source_files_checked':19,'source_bytes_checked':total,'acceptance_checks':checks,'synthetic_decision_challenges':challenges,
 'synthetic_fixtures_are_scientific_evidence':False,'T01_through_T16_executed':False,
 'scientific_admission_or_computation_performed':False,'external_messages_sent':0,'publication_performed':False,
 'limitations':reg['verification_limits'],'pid':os.getpid(),'start_ticks':Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
 'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'checked_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
out=P/'T00/attempt-001/VERIFICATION.json';tmp=out.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2)+'\n');tmp.replace(out)
print('T00_INDEPENDENT_CHECK_PASS',len(checks),'acceptance checks',len(challenges),'synthetic challenges')
