"""Read-only, standard-library validation of the B05 PLAN_ONLY package.

This validates design/metadata, never grants execution permission. No model,
array, pickle, CUDA, scientific-stack or subprocess import/launch is supported.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import itertools
import json
from pathlib import Path
import sys

TASKS = ('emp_H3','gue_prom_300_all','gue_prom_core_all',
         'gue_splice_reconstructed','gue_tf_0','gue_mouse_0')
SEEDS = (42,17,1234)
REPS = tuple('decoder_layer_'+str(i) for i in range(25))+('final_norm',)
DOCS = Path('docs/experiments/ashay/POD_B')

class PlanError(ValueError):
    pass

def require(ok, message):
    if not ok:
        raise PlanError(message)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def resolve_file(root, relative):
    p = Path(relative)
    require(not p.is_absolute() and '..' not in p.parts, 'UNSAFE_PACKAGE_PATH')
    result = root/p
    require(result.is_file() and not result.is_symlink(), 'MISSING_OR_SYMLINK_FILE')
    require(result.resolve().is_relative_to(root), 'OUTSIDE_PACKAGE_ROOT')
    require(result.suffix in ('.json','.jsonl','.csv','.md','.py','.sha256'), 'NOT_METADATA')
    require(result.stat().st_size <= 16_000_000, 'METADATA_SIZE_LIMIT')
    return result

def validate(root: Path, manifest: Path | None=None, require_executable=False):
    root = root.resolve()
    require(not require_executable, 'PLAN_ONLY_NOT_EXECUTABLE: obtain separate B04/calibration/B06 approvals')
    manifest = manifest or root/DOCS/'B05_PACKAGE_MANIFEST.json'
    require(manifest.resolve().is_relative_to(root), 'OUTSIDE_PACKAGE_ROOT')
    package = json.loads(manifest.read_text())
    require(package.get('schema')=='POD_B.B05.package.v1' and package.get('mode')=='PLAN_ONLY','WRONG_PACKAGE_MODE')
    require(package.get('production_authorized') is False and package.get('next_stage_authorized') is False,'PACKAGE_NOT_AUTHORIZED')
    seen=set()
    for row in package['files']:
        require(row['path'] not in seen,'DUPLICATE_PACKAGE_FILE');seen.add(row['path'])
        p=resolve_file(root,row['path'])
        require(p.stat().st_size==row['bytes'] and digest(p)==row['sha256'],'PACKAGE_HASH_MISMATCH: '+row['path'])
    def load(n):
        require(str(DOCS/n) in seen,'UNSEALED_REQUIRED_FILE: '+n)
        return json.loads((root/DOCS/n).read_text())
    def rows(n):
        require(str(DOCS/n) in seen,'UNSEALED_REQUIRED_FILE: '+n)
        with (root/DOCS/n).open(newline='') as f:return list(csv.DictReader(f))
    protocol=load('PROTOCOL_FROZEN.json');execution=load('EXECUTION_PLAN.json');calibration=load('CALIBRATION_PLAN.json')
    for obj in (protocol,execution,calibration):
        for flag in ('production_ready','production_authorized','next_stage_authorized'):
            require(obj.get(flag) is False,'PLAN_ONLY_FLAG: '+flag)
    require(protocol['mode']==execution['mode']=='PLAN_ONLY','WRONG_PLAN_MODE')
    require(protocol['model_identity_complete'] is False and protocol['route_qualified'] is False,'UNQUALIFIED_SCIENCE_PROMOTION')
    require(protocol['channel_eligibility']==dict(features=0,fixed_base_transfer=0,LM=0),'UNQUALIFIED_CHANNEL')
    require(not execution['executable_units'] and not execution['launch_commands'],'PLAN_ONLY_NOT_EXECUTABLE')
    require(not execution['currently_eligible_model_ids'] and execution['selected_option'] is None,'UNQUALIFIED_SELECTED_SCOPE')
    require(calibration['authorized'] is False and not calibration['qualified_checkpoint_ids'] and not calibration['bound_units'] and not calibration['executable_units'] and not calibration['commands'],'CALIBRATION_NOT_AUTHORIZED')
    require(calibration['passes_per_representative']==dict(cold=1,warm=1) and set(calibration['inputs']['task_counts'])==set(TASKS) and set(calibration['inputs']['task_counts'].values())=={64},'CALIBRATION_TRAINING_POPULATION')
    require(calibration['proposed_ceilings']['occupied_GPU_seconds']==900 and calibration['proposed_ceilings']['CPU_benchmark_wall_seconds']==1800 and calibration['proposed_ceilings']['authorization'] is False,'CALIBRATION_BUDGET_NOT_GRANTED')
    require(calibration['maximum_representatives']==3 and calibration['maximum_rows_per_representative']==384 and calibration['maximum_extract_passes']==6,'CALIBRATION_LIMITS')
    require(len(calibration['CPU_probe_search_units'])==6 and sum(x['candidate_fold_fits']+x['final_fits'] for x in calibration['CPU_probe_search_units'])==84,'CALIBRATION_CPU_COUNTS')
    for field,value in execution['required_current_digests'].items():
        names={'protocol_sha256':'PROTOCOL_FROZEN.json','comparison_families_sha256':'COMPARISON_FAMILIES.json','coverage_plan_sha256':'COVERAGE_PLAN.csv','coverage_options_sha256':'B05_COVERAGE_OPTIONS.json','calibration_plan_sha256':'CALIBRATION_PLAN.json','B04_qualification_sha256':'CHECKPOINT_QUALIFICATION.jsonl','B04_identity_resolution_sha256':'B04_IDENTITY_RESOLUTION.json'}
        require(digest(root/DOCS/names[field])==value,'EXECUTION_DEPENDENCY_HASH: '+field)
    side=(root/DOCS/'PROTOCOL_FROZEN.sha256').read_text().split()
    require(side==[digest(root/DOCS/'PROTOCOL_FROZEN.json'),'PROTOCOL_FROZEN.json'],'PROTOCOL_SERIALIZATION_HASH')
    require(protocol['representation_contract']['keys']==list(REPS) and protocol['representation_contract']['physical_batch_size']==8,'REPRESENTATION_CONTRACT')
    require(protocol['probe']['CV_seeds']==list(SEEDS) and protocol['probe']['C_grid']==[.1,1.,10.] and protocol['probe']['max_iter_attempts']==[2000,10000],'PROBE_POLICY')
    require(protocol['uncertainty']['draw_attempts']==2000 and protocol['uncertainty']['seed']==20261103 and 'attempted' in protocol['uncertainty']['draw_semantics'],'BOOTSTRAP_ATTEMPT_POLICY')
    cohorts=load('B05_COHORTS_AND_FOLDS.json');tasks={x['task']:x for x in cohorts['tasks']}
    require(set(tasks)==set(TASKS) and cohorts['rows']==22645,'TASK_POPULATIONS')
    require(sum(x['train']+x['dev']+x['previously_analyzed_test']for x in tasks.values())==22645,'ROW_COUNTS')
    for t,x in tasks.items():
        require((x['train'],x['dev'],x['previously_analyzed_test'])==((11971,1497,1497) if t=='emp_H3' else(1024,512,0)),'SPLIT_COUNTS')
        require(x['classes']==([0,1,2] if t=='gue_splice_reconstructed' else[0,1]),'NUMERIC_CLASSES')
        require([f['seed']for f in x['folds']]==list(SEEDS),'FOLD_SEEDS')
        require(all(f['fold_count']==(3 if t=='emp_H3' else 5)for f in x['folds']),'FOLD_PARTITIONS')
    require(sum(f['fold_count']for x in tasks.values()for f in x['folds'])==84,'FOLD_TOTAL')
    coverage=rows('COVERAGE_PLAN.csv');ids={x['checkpoint_id']for x in coverage}
    expected={s+'/iter_'+str(t).zfill(7)for s in ('base','maxent')for t in range(100,1801,100)}
    require(ids==expected and len(coverage)==36 and len({x['unit_id']for x in coverage})==36,'MODEL_IDS')
    require({j:sum(x['job_id']==j for x in coverage)for j in ('11760341','11776574','11803647')}=={'11760341':18,'11776574':16,'11803647':2},'JOB_FAMILY_COUNTS')
    for x in coverage:
        expected_family=('base_all','11760341')if x['series']=='base'else(('maxent_initial','11776574')if int(x['step'])<=1600 else('maxent_restart','11803647'))
        require((x['family'],x['job_id'])==expected_family,'EXACT_JOB_FAMILY_MAPPING')
        require(x['model_identity_complete']==x['route_qualified']==x['executable']==x['next_stage_authorized']=='False','BLOCKED_ROW_NOT_EXECUTABLE')
        require(x['per_checkpoint_gate_status']=='BLOCKED_IDENTITY_ROUTE' and all(x[k]=='BLOCKED'for k in ('feature_status','fixed_base_status','LM_status')),'BLOCKED_CHANNELS')
        require(x['actual_full_state_fingerprint']=='' and x['actual_full_state_fingerprint_reason'],'UNKNOWN_FINGERPRINT_MUST_REMAIN_NULL')
        require(x['series']!='maxent' or x['maxent_restart_side']==('PRE_OR_AT1600'if int(x['step'])<=1600 else'POST_RESTART1700'),'RESTART_SIDE')
    matrix={tuple(x)for x in itertools.product(ids,TASKS,REPS,SEEDS,('independent_refit','fixed_base'))}
    require(len(matrix)==33696,'NORMALIZED_FULL_UNIT_KEYS')
    options=load('B05_COVERAGE_OPTIONS.json')
    require(not options['executable_units'] and not options['currently_eligible_model_ids'],'OPTIONS_NOT_EXECUTABLE')
    for option in options['options']:
        key=option['option_id'];n={'full':36,'balanced':14,'core':8}[key]
        chosen={x['checkpoint_id']for x in coverage if x[key]=='True'}
        require(chosen==set(option['model_ids']) and len(chosen)==n,'OPTION_MEMBERSHIP')
        steps={'full':list(range(100,1801,100)),'balanced':[100,500,1000,1400,1600,1700,1800],'core':[100,1600,1700,1800]}[key]
        exact={series+'/iter_'+str(t).zfill(7)for series in('base','maxent')for t in steps}
        require(chosen==exact and option['common_steps']==steps,'OPTION_LOST_PREDECLARED_RESTART_OR_STEPS')
        require(option['conditional_GPU_estimates']['total_B06_GPU_seconds']is None and option['conditional_CPU_estimates']['total_CPU_wall_seconds']is None,'UNKNOWN_TOTAL_IS_NOT_ZERO')
        require(option['final_refit_heads']==n*468 and option['CV_candidate_fold_fits']==n*6552 and option['nominal_estimator_fits']==n*7020,'FIT_COUNTS')
        require(option['raw_feature_bytes']==n*22645*26*1920*4,'STORAGE_ARITHMETIC')
        require(option['LM_population_outputs']==n*13 and option['LM_evaluation_outputs']==n*7,'LM_NO_LAYER_SEED_MULTIPLIER')
        require(not option['executable_units'] and option['currently_eligible_final_heads']==0,'OPTION_NOT_EXECUTABLE')
        for pair in option['adjacent_pairs']:
            require(pair['left']in chosen and pair['right']in chosen and int(pair['left'][-7:])-int(pair['right'][-7:])==100,'SPARSE_GAP_NOT_ADJACENT')
        for budget in option['conditional_GPU_estimates']['budget_scenarios']:
            require(budget['authorization'] is False and abs(budget['max_total_seconds_per_model']*n-budget['future_phase_GPU_envelope_seconds'])<1e-8,'BUDGET_NOT_NEW_AUTHORIZATION')
    heads=rows('B05_FIXED_BASE_READOUTS.csv');reuse=rows('REUSE_MATRIX.csv')
    base={(x['task'],x['representation'],x['cv_seed']):x for x in reuse if x['kind']=='head'and x['source_model']=='historical_base_iter1'}
    require(len(heads)==len(base)==468 and len({(x['task'],x['representation'],x['cv_seed'])for x in heads})==468,'FIXED_BASE_UNIQUE_KEYS')
    for x in heads:
        old=base[x['task'],x['representation'],x['cv_seed']]
        require(x['reference_model']=='historical_base_iter1' and x['scaler_refit_allowed']==x['head_refit_allowed']=='False','UNCHANGED_SCALER_AND_HEAD')
        for new,key in [('artifact_sha256','sha256'),('scaler_fingerprint','scaler_fingerprint'),('head_fingerprint','head_fingerprint'),('relative_path','relative_path'),('class_order','class_order')]:require(x[new]==old[key],'SCALER_HEAD_PAIR_DRIFT')
        fold=next(f for f in tasks[x['task']]['folds']if str(f['seed'])==x['cv_seed'])
        require(x['fold_sha256']==fold['sha256'],'READOUT_FOLD_MISMATCH')
    controls=load('B05_SEQUENCE_CONTROLS.json');require(controls['count']==36 and controls['new_fits']==0,'CONTROLS_SHARED_NOT_MULTIPLIED')
    families=load('COMPARISON_FAMILIES.json');require(len(families['families'])==7 and not families['current_executable_contrasts'],'COMPARISON_SCOPE')
    forecast=load('B05_RESOURCE_FORECAST.json');require(forecast['PLAN_ONLY_GPU_authorization_seconds']==0 and forecast['B04_accounting']['used_GPU_seconds']==1675.5146971674585 and forecast['B04_accounting']['copied_into_B05']is False,'NO_B04_BUDGET_RESET_TRANSFER')
    require(forecast['options']==options['options'],'RESOURCE_OPTION_JOIN')
    require(forecast['uncertainty_work']['class_score_rank_sorts_per_model']==1404 and forecast['extraction_batch_arithmetic']['physical_batches_per_model']==2831,'BATCH_AND_SORT_COUNTS')
    require(forecast['B04_accounting']['remaining_aggregate_arithmetic_seconds']==9000-1675.5146971674585,'BUDGET_CONSERVATION')
    require(forecast['wall']['total_seconds']is None and forecast['wall']['future_forward_deadline_utc']is None,'UNKNOWN_COSTS_NOT_ZERO_OR_NEW_CLOCK')
    return dict(status='PASS',mode='PLAN_ONLY',package_files_verified=len(seen),models=36,normalized_refit_and_transfer_units=len(matrix),final_refit_units=16848,eligible_models=0,executable_units=0,scientific_stack_imported=any(n in sys.modules for n in ('torch','numpy','sklearn','bionemo')),GPU_operations=0)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',required=True,type=Path)
    p.add_argument('--manifest',type=Path)
    p.add_argument('--require-executable',action='store_true',help='Always rejects PLAN_ONLY; never launches anything')
    a=p.parse_args(argv)
    try:result=validate(a.root,a.manifest,a.require_executable)
    except (PlanError,KeyError,ValueError,OSError)as e:
        print(json.dumps(dict(status='REJECTED',reason=str(e)),sort_keys=True));return 2
    print(json.dumps(result,sort_keys=True));return 0

if __name__=='__main__':
    raise SystemExit(main())
