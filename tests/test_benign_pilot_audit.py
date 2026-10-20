"""Synthetic audit regressions; no optional model imports or GPU execution."""
import copy
import csv
import importlib.util
import json
from pathlib import Path
import shutil
import sys

import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from benign_pilot import run
from benign_pilot.data import prepare, overlap_report
from benign_pilot.identity import CHECKPOINT_SHA256, execution_provenance, cache_key, checkpoint_identity
from benign_pilot.metrics import aggregate
from benign_pilot.probes import fit_probes
from benign_pilot.validation import validate_saved, ValidationError, independent_losses
from benign_pilot.validation_data import read_json, text_sha, file_sha256, TASKS, LAYERS


def dump(path,value):
    path.write_text(json.dumps(value,indent=2))


def context():
    return dict(manifest_sha256='manifest',config_sha256='config',checkpoint_sha256='checkpoint',
                source_hashes={'source':'original'},packages={'package':'1'},backend_files={'backend':'hash'},source_commit='1'*40)


def test_provenance_collection_does_not_write(monkeypatch,tmp_path):
    original=b'{"original": "execution"}\n'
    (tmp_path/'run_manifest.json').write_bytes(original)
    (tmp_path/'subset_manifest.jsonl').write_text('synthetic\n')
    monkeypatch.setattr(run,'checkpoint_identity',lambda path:CHECKPOINT_SHA256)
    monkeypatch.setattr(run,'backend_identity',lambda:{'synthetic':'hash'})
    monkeypatch.setattr(run,'git',lambda *args:'2'*40)
    monkeypatch.setattr(run.importlib.metadata,'version',lambda name:'synthetic')
    monkeypatch.setattr(run.torch.cuda,'get_device_name',lambda:'synthetic')
    monkeypatch.setattr(run.torch.cuda,'get_device_capability',lambda:(9,0))
    candidate=run.provenance({'precision':'synthetic'},tmp_path,'synthetic checkpoint')
    assert candidate['source_commit']=='2'*40
    assert (tmp_path/'run_manifest.json').read_bytes()==original


def test_rejected_resume_preserves_execution_before_model_load(monkeypatch,tmp_path):
    original=context();dump(tmp_path/'run_manifest.json',original)
    dump(tmp_path/'smoke_provenance.json',original);dump(tmp_path/'model_smoke_results.json',{})
    dump(tmp_path/'config.json',{});dump(tmp_path/'status.json',{'stage':'original_complete'})
    before={p.name:p.read_bytes() for p in tmp_path.iterdir()}
    candidate=copy.deepcopy(original);candidate['source_hashes']['source']='changed'
    monkeypatch.setattr(run,'guard',lambda config:None)
    monkeypatch.setattr(run,'provenance',lambda *args:candidate)
    monkeypatch.setattr(run,'load_model',lambda *args:pytest.fail('Incompatible resume reached model load'))
    monkeypatch.setattr(sys,'argv',['pilot','pilot','--run-dir',str(tmp_path),'--config',str(tmp_path/'config.json')])
    with pytest.raises(ValueError,match='provenance mismatch'):
        run.main()
    assert {name:(tmp_path/name).read_bytes() for name in before}==before
    attempt=read_json(next((tmp_path/'resume_attempts').glob('*.json')))
    assert not attempt['accepted'] and attempt['original_inference_source_commit']=='1'*40


def test_compatible_resume_retains_original_source_commit(tmp_path):
    original=context();dump(tmp_path/'run_manifest.json',original)
    before=(tmp_path/'run_manifest.json').read_bytes()
    candidate=dict(original,source_commit='2'*40)
    execution_provenance(tmp_path,candidate,'smoke')
    assert (tmp_path/'run_manifest.json').read_bytes()==before
    attempt=read_json(next((tmp_path/'resume_attempts').glob('*.json')))
    assert attempt['accepted'] and attempt['candidate']['source_commit']=='2'*40


def test_identity_failure_records_attempt_without_replacing_provenance(tmp_path,monkeypatch):
    dump(tmp_path/'run_manifest.json',context());before=(tmp_path/'run_manifest.json').read_bytes()
    def reject(*args):
        raise ValueError('synthetic checkpoint identity failure')
    monkeypatch.setattr(run,'provenance',reject)
    with pytest.raises(ValueError,match='identity failure'):
        run.prepare_execution_context({},tmp_path,'synthetic','pilot')
    assert (tmp_path/'run_manifest.json').read_bytes()==before
    attempt=read_json(next((tmp_path/'resume_attempts').glob('*.json')))
    assert not attempt['accepted'] and attempt['original_execution_manifest_sha256']==file_sha256(tmp_path/'run_manifest.json')


def test_checkpoint_identity_rejects_wrong_bytes_before_loader(tmp_path,monkeypatch):
    checkpoint=tmp_path/'wrong.pt';checkpoint.write_bytes(b'synthetic wrong weights')
    with pytest.raises(ValueError,match='checkpoint checksum mismatch'):
        checkpoint_identity(checkpoint)
    with pytest.raises(ValueError,match='checkpoint checksum mismatch'):
        run.load_model({},tmp_path,str(checkpoint))


def test_overlap_blocks_ordinary_completion_and_report(tmp_path):
    rows=[]
    for split,seqs in [('train',['ACGA','AGGA']),('validation',['TCGT','TCCT'])]:
        for label,sequence in enumerate(seqs):
            rows.append(dict(task='gue_emp_h3',id=f'synthetic-{split}-{label}',split=split,label=label,sequence=sequence,full_sequence=sequence))
    dump(tmp_path/'data_provenance.json',{'gue_emp_h3':{'overlap':overlap_report(rows)}})
    (tmp_path/'subset_manifest.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    config={'tasks':{'gue_emp_h3':'EMP/H3'},'layers':LAYERS}
    blocked=run.pilot(config,tmp_path,None,rows,context())
    assert blocked==['gue_emp_h3'] and not (tmp_path/'gue_emp_h3/complete.json').exists()
    # Even a pre-existing ordinary completion cannot appear unqualified in a report.
    (tmp_path/'gue_emp_h3').mkdir();dump(tmp_path/'gue_emp_h3/complete.json',{'task':'gue_emp_h3'})
    run.report(config,tmp_path)
    report=(tmp_path/'SUMMARY.md').read_text()
    assert 'Completed tasks: 0/1' in report and 'BLOCKED_OVERLAP' in report


def test_overlap_gate_continues_clean_tasks(tmp_path,monkeypatch):
    import torch
    rows=[]
    for task,sequences in [('gue_emp_h3',['ACGA','AGGA','TCGT','TCCT']),('gue_prom_300_all',['AAAA','CCCC','AAAC','CCCA'])]:
        for i,sequence in enumerate(sequences):
            rows.append(dict(task=task,id=f'synthetic-{task}-{i}',split='train' if i<2 else 'validation',label=i%2,sequence=sequence,full_sequence=sequence))
    dump(tmp_path/'data_provenance.json',{task:{'overlap':overlap_report([r for r in rows if r['task']==task])} for task in ['gue_emp_h3','gue_prom_300_all']})
    (tmp_path/'subset_manifest.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
    scored=[]
    def synthetic_infer(model,items,layers):
        scored.extend(r['task'] for r in items)
        return [dict(id=r['id'],task=r['task'],split=r['split'],n_tokens=3,nll_sum=3.) for r in items],{layer:torch.tensor([[float(r['label']),1.-r['label']] for r in items]) for layer in layers}
    monkeypatch.setattr(run,'infer',synthetic_infer)
    monkeypatch.setattr(torch.cuda,'synchronize',lambda:None);monkeypatch.setattr(torch.cuda,'reset_peak_memory_stats',lambda:None);monkeypatch.setattr(torch.cuda,'max_memory_allocated',lambda:0)
    blocked=run.pilot({'tasks':{task:TASKS[task] for task in ['gue_emp_h3','gue_prom_300_all']},'layers':LAYERS},tmp_path,None,rows,context())
    assert blocked==['gue_emp_h3'] and scored==['gue_prom_300_all']*4
    assert read_json(tmp_path/'gue_prom_300_all/complete.json')['eligibility']['eligible']


@pytest.fixture(scope='module')
def saved_fixture(tmp_path_factory):
    import zipfile
    root=tmp_path_factory.mktemp('synthetic_saved_core');run_dir=root/'run';run_dir.mkdir()
    config=json.loads((Path(__file__).resolve().parents[1]/'configs/benign_pilot.json').read_text())
    config.update(train_size=6,validation_size=3,data_source_revision='synthetic audit fixture')
    archive=root/'synthetic.zip';rng=np.random.default_rng(42)
    with zipfile.ZipFile(archive,'w') as z:
        for task,directory in TASKS.items():
            for split,count in [('train',6),('dev',3)]:
                rows=['sequence,label']
                for index in range(count):
                    sequence=''.join(rng.choice(list('ACGT'),size=24))
                    rows.append(f'{sequence},{index%len(config["label_schemas"][task])}')
                z.writestr('GUE/'+directory+'/'+split+'.csv','\n'.join(rows)+'\n')
            z.writestr('GUE/'+directory+'/test.csv','NEVER OPEN THIS SYNTHETIC TEST MEMBER')
    config['data_archive_sha256']=file_sha256(archive)
    prepare(config,archive,run_dir);dump(run_dir/'config.json',config)
    manifest=[json.loads(line) for line in (run_dir/'subset_manifest.jsonl').read_text().splitlines()]
    snapshot=run_dir/'source-at-run/benign_pilot';snapshot.mkdir(parents=True)
    (snapshot/'probes.py').write_text('# synthetic source snapshot fixture\n')
    trusted=read_json(Path(__file__).resolve().parents[1]/'configs/evo2_backend_identity.json')
    ctx=dict(config=config,config_sha256=text_sha(json.dumps(config,sort_keys=True)),manifest_sha256=file_sha256(run_dir/'subset_manifest.jsonl'),checkpoint_sha256=CHECKPOINT_SHA256,
             source_commit='1'*40,source_hashes={'benign_pilot/probes.py':file_sha256(snapshot/'probes.py')},packages=trusted['packages'],backend_files={'/synthetic/site-packages/'+p:d for p,d in trusted['files'].items()})
    dump(run_dir/'run_manifest.json',ctx);dump(run_dir/'smoke_provenance.json',ctx)
    dump(run_dir/'model_contract.json',{'layers':LAYERS,'config':trusted['model_config'],'config_sha256':trusted['model_config_sha256']})
    all_metrics=[];all_candidates=[];key=cache_key(ctx)
    for task in TASKS:
        directory=run_dir/task;directory.mkdir();selected=[r for r in manifest if r['task']==task]
        labels=np.array([r['label'] for r in selected]);splits=np.array([r['split'] for r in selected])
        features=np.zeros((len(selected),1920),dtype=np.float32)
        features[np.arange(len(selected)),labels]=1
        np.savez_compressed(directory/'features.npz',cache_key=key,**{layer:features for layer in LAYERS})
        candidates=[]
        for layer in LAYERS:
            with threadpool_limits(limits=4):
                scores,best,scaler,classifier=fit_probes(features,labels,splits)
            np.savez(directory/(layer+'.probe.npz'),coef=classifier.coef_,intercept=classifier.intercept_,classes=classifier.classes_,mean=scaler.mean_,scale=scaler.scale_)
            candidates += [dict(task=task,layer=layer,**score,selected=i==best,train_count=6,validation_count=3) for i,score in enumerate(scores)]
        metrics=[dict(id=r['id'],task=task,split=r['split'],n_tokens=23,nll_sum=23.) for r in selected]
        (directory/'per_example_metrics.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in metrics))
        dump(directory/'probe_results.json',candidates)
        dump(directory/'complete.json',dict(task=task,cache_key=key,validation_selected=True,probes=candidates,nll={s:aggregate([r for r in metrics if r['split']==s]) for s in ['train','validation']}))
        all_metrics.extend(metrics);all_candidates.extend(candidates)
    (run_dir/'per_example_metrics.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in all_metrics))
    with (run_dir/'baseline_probe_results.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(all_candidates[0]),lineterminator='\n');writer.writeheader();writer.writerows(all_candidates)
    return run_dir,archive


def test_complete_synthetic_saved_artifacts_pass_without_gpu(saved_fixture):
    with threadpool_limits(limits=4):
        result=validate_saved(*saved_fixture,expected_source_commit='1'*40)
    assert result['all_passed'] and len(result['checks'])==6 and len(result['candidate_checks'])==18


@pytest.mark.parametrize('mutation,match',[
    ('missing_probes','probe candidates'),('missing_layer','probe candidates'),('duplicate_selection','selected probe'),
    ('duplicate_candidate','candidate coverage'),('record_alignment','record alignment'),('wrong_label','label mismatch'),
    ('invalid_provenance','Manifest hash'),('both_stored_keys_wrong','actual provenance'),('nonfinite_features','Nonfinite'),
    ('feature_dimensions','dimension mismatch'),('missing_task','artifact directories'),('empty_tasks','all three'),
])
def test_corrupted_artifacts_cannot_pass(saved_fixture,tmp_path,mutation,match):
    original,archive=saved_fixture;run_dir=tmp_path/'mutant';shutil.copytree(original,run_dir)
    directory=run_dir/'gue_emp_h3';complete=read_json(directory/'complete.json')
    if mutation=='missing_probes':complete['probes']=[]
    elif mutation=='missing_layer':complete['probes']=[r for r in complete['probes'] if r['layer']=='blocks.7']
    elif mutation=='duplicate_selection':complete['probes'][1]['selected']=True
    elif mutation=='duplicate_candidate':complete['probes'][1]=copy.deepcopy(complete['probes'][0])
    elif mutation in ['record_alignment','wrong_label']:
        p=directory/'per_example_metrics.jsonl';rows=[json.loads(x) for x in p.read_text().splitlines()]
        if mutation=='record_alignment':rows[0]['split']='validation'
        else:rows[0]['label']=99
        p.write_text(''.join(json.dumps(r)+'\n' for r in rows))
    elif mutation=='invalid_provenance':
        p=run_dir/'run_manifest.json';value=read_json(p);value['manifest_sha256']='0'*64;dump(p,value)
    elif mutation in ['both_stored_keys_wrong','nonfinite_features','feature_dimensions']:
        p=directory/'features.npz'
        with np.load(p) as source:values={key:source[key].copy() for key in source.files}
        if mutation=='both_stored_keys_wrong':values['cache_key']=np.array('same-but-wrong');complete['cache_key']='same-but-wrong'
        elif mutation=='nonfinite_features':values['blocks.7'][0,0]=np.nan
        else:values['blocks.7']=values['blocks.7'][:,:10]
        np.savez(p,**values)
    elif mutation=='missing_task':shutil.rmtree(run_dir/'gue_prom_300_all')
    elif mutation=='empty_tasks':
        p=run_dir/'config.json';value=read_json(p);value['tasks']={};dump(p,value)
    dump(directory/'complete.json',complete)
    with pytest.raises(ValidationError,match=match):
        validate_saved(run_dir,archive)


def test_independent_losses_does_not_call_producer(monkeypatch):
    import benign_pilot.metrics
    monkeypatch.setattr(benign_pilot.metrics,'aggregate',lambda *args:pytest.fail('Producer aggregate called'))
    assert independent_losses([dict(nll_sum=2.,n_tokens=1),dict(nll_sum=4.,n_tokens=3)])['corpus_nll']==1.5


def test_finite_classifier_disagreement_is_qualified(saved_fixture,tmp_path):
    original,archive=saved_fixture;directory=tmp_path/'shifted';shutil.copytree(original,directory)
    path=directory/'gue_emp_h3/blocks.7.probe.npz'
    with np.load(path,allow_pickle=False) as source:values={key:source[key].copy() for key in source.files}
    values['intercept']+=2.
    np.savez(path,**values)
    with threadpool_limits(limits=4):result=validate_saved(directory,archive)
    assert not result['all_passed']
    assert result['refit_qualifications']
    check=next(row for row in result['checks'] if row['task']=='gue_emp_h3' and row['layer']=='blocks.7')
    assert check['exact_auroc_match']  # AUROC alone cannot detect this corruption.
    assert check['refit']['maximum_probability_difference']>0
    assert 'saved_probabilities' in check['refit'] and 'refit_probabilities' in check['refit']


def test_validator_requires_separate_output_directory(tmp_path):
    spec=importlib.util.spec_from_file_location('validator',Path(__file__).resolve().parents[1]/'scripts/validate_benign_pilot_results.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    with pytest.raises(ValueError,match='outside the input'):
        module.validate(tmp_path,tmp_path)
