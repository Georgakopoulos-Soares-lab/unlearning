"""Independent loss accounting and CPU reconstruction/refitting of saved probes."""
import csv
import ast
import math
from pathlib import Path
import warnings

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

from .validation_data import (TASKS,LAYERS,C_GRID,ValidationError,require,read_json,
                             read_jsonl,verify_provenance,verify_dataset)
from .identity import BACKEND_SPEC
from .validation_data import text_sha
import json


def finite_number(value,label):
    require(type(value) in (int,float) and math.isfinite(value),f'Nonfinite/malformed {label}')
    return float(value)


def positive_int(value,label):
    require(type(value) is int and value>0,f'Nonpositive/noninteger {label}')
    return value


def independent_losses(rows):
    """Does not import or call the producer's aggregate() function."""
    require(bool(rows),'No per-example losses')
    for row in rows:
        require(finite_number(row.get('nll_sum'),'summed NLL')>=0,'Negative summed NLL')
        positive_int(row.get('n_tokens'),'target count')
    total_loss=math.fsum(float(row['nll_sum']) for row in rows)
    total_tokens=sum(row['n_tokens'] for row in rows)
    nll=total_loss/total_tokens
    try:
        perplexity=math.exp(nll);overflow=not math.isfinite(perplexity)
    except OverflowError:
        perplexity,overflow=None,True
    return dict(nll_sum=total_loss,n_tokens=total_tokens,n_examples=len(rows),corpus_nll=nll,
                perplexity=None if overflow else perplexity,perplexity_overflow=overflow)


def verify_loss_summary(recorded,measured,label):
    require(isinstance(recorded,dict),f'Missing loss summary: {label}')
    for key in ['n_tokens','n_examples']:
        require(type(recorded.get(key)) is int and recorded[key]==measured[key],f'Loss count mismatch: {label}/{key}')
    require(finite_number(recorded.get('corpus_nll'),label)==measured['corpus_nll'],f'Corpus NLL mismatch: {label}')
    require(recorded.get('perplexity_overflow') is measured['perplexity_overflow'],'Perplexity overflow mismatch: '+label)
    require(recorded.get('perplexity')==measured['perplexity'],'Perplexity mismatch: '+label)


def arrays(path,expected_keys):
    try:
        with np.load(path,allow_pickle=False) as source:
            require(set(source.files)==set(expected_keys),f'Missing/unexpected NPZ fields: {path}')
            result={key:source[key].copy() for key in source.files}
    except (OSError,ValueError,KeyError) as exc:
        raise ValidationError(f'Invalid required NPZ {path}: {exc}') from exc
    for key,value in result.items():
        if key!='cache_key':
            require(np.issubdtype(value.dtype,np.number) and np.isfinite(value).all(),f'Nonfinite/malformed array: {path}/{key}')
    return result


def auroc(labels,probabilities,classes):
    if len(classes)==2:
        require(np.array_equal(classes,np.array([0,1])),'Unexpected binary class mapping')
        return float(roc_auc_score(labels,probabilities[:,1]))
    return float(roc_auc_score(labels,probabilities,labels=classes,multi_class='ovr',average='macro'))


def candidate_rows(rows,task,n_train,n_dev):
    require(isinstance(rows,list) and len(rows)==6,f'Missing/extra probe candidates: {task}')
    keys=[]
    for row in rows:
        require(isinstance(row,dict),f'Malformed candidate: {task}')
        key=(row.get('layer'),row.get('C'))
        require(row.get('task')==task and key[0] in LAYERS and type(key[1]) in (int,float) and key[1] in C_GRID,f'Unexpected probe task/layer/C: {task}')
        require(type(row.get('selected')) is bool,f'Malformed selection flag: {task}')
        require(0<=finite_number(row.get('validation_auroc'),'candidate AUROC')<=1,f'Invalid candidate AUROC: {task}')
        require(type(row.get('train_count')) is int and row['train_count']==n_train and type(row.get('validation_count')) is int and row['validation_count']==n_dev,f'Candidate record-count mismatch: {task}')
        require(isinstance(row.get('warnings'),list) and all(isinstance(w,str) for w in row['warnings']),f'Malformed candidate warnings: {task}')
        multiclass=task=='gue_splice_reconstructed'
        require(row.get('auroc_definition')==('macro one-vs-rest' if multiclass else 'binary positive class 1'),f'AUROC definition mismatch: {task}')
        require(row.get('positive_class')==(None if multiclass else 1) and row.get('positive_column')==(None if multiclass else 1),f'Positive-class mapping mismatch: {task}')
        keys.append(key)
    require(len(set(keys))==6 and set(keys)=={(layer,c) for layer in LAYERS for c in C_GRID},f'Duplicate/missing candidate coverage: {task}')
    for layer in LAYERS:
        candidates=sorted([r for r in rows if r['layer']==layer],key=lambda r:r['C'])
        selected=[r for r in candidates if r['selected']]
        require(len(selected)==1,f'Exactly one selected probe required: {task}/{layer}')
        require(selected[0] is max(candidates,key=lambda r:r['validation_auroc']),f'Selection/tie rule mismatch: {task}/{layer}')
    return rows


def validate_saved(run,archive,source_root=None,expected_source_commit=None):
    run=Path(run);config=read_json(run/'config.json')
    require(config.get('tasks')==TASKS,'Expected all three configured core tasks')
    require(config.get('layers')==LAYERS,'Expected both configured intermediate layers')
    require(config.get('seed')==42 and config.get('max_length')==512 and config.get('batch_size')==1,'Unexpected scientific protocol')
    positive_int(config.get('train_size'),'configured train size');positive_int(config.get('validation_size'),'configured dev size')
    manifest=read_jsonl(run/'subset_manifest.jsonl');ids=[r.get('id') for r in manifest]
    require(all(isinstance(x,str) and x for x in ids) and len(set(ids))==len(ids),'Missing/duplicate selected IDs')
    require({r.get('task') for r in manifest}==set(TASKS),'Missing/unexpected manifest tasks')
    require(all(r.get('split') in ['train','validation'] and type(r.get('label')) is int and type(r.get('original_row_index')) is int for r in manifest),'Malformed manifest split/label/row alignment')
    for row in manifest:
        positive_int(row.get('original_length'),'original sequence length');positive_int(row.get('scored_length'),'scored sequence length')
        require(type(row.get('truncated')) is bool and type(row.get('ambiguous_bases_scored')) is int and row['ambiguous_bases_scored']>=0,'Malformed truncation/ambiguity metadata')
    context,key=verify_provenance(run,config,source_root,expected_source_commit)
    data=verify_dataset(run,config,manifest,archive)
    contract=read_json(run/'model_contract.json')
    require(contract.get('layers')==LAYERS and contract.get('config',{}).get('hidden_size')==1920 and contract['config'].get('num_layers')==25,'Wrong representation/model dimensions')
    trusted=read_json(BACKEND_SPEC)
    require(contract.get('config_sha256')==trusted['model_config_sha256'] and text_sha(json.dumps(contract['config'],sort_keys=True))==trusted['model_config_sha256'],'Recorded architecture differs from pinned official configuration')
    require({p.name for p in run.glob('gue_*') if p.is_dir()}==set(TASKS),'Missing/unexpected task artifact directories')
    checks,losses,candidate_checks,all_metrics,all_candidates=[],{},[],[],[]
    discrepancies=[];qualifications=[]
    for task in TASKS:
        directory=run/task;complete=read_json(directory/'complete.json')
        require(complete.get('task')==task and complete.get('validation_selected') is True,f'Completion task/selection mismatch: {task}')
        require(complete.get('cache_key')==key,f'Completion key does not match actual provenance: {task}')
        selected_rows=[r for r in manifest if r['task']==task];metrics=read_jsonl(directory/'per_example_metrics.jsonl')
        require(len(metrics)==len(selected_rows),f'Per-example record count mismatch: {task}')
        for metric,row in zip(metrics,selected_rows):
            require(all(metric.get(field)==row[field] for field in ['id','task','split']),f'Metric/manifest record alignment mismatch: {task}')
            if 'label' in metric:
                require(type(metric['label']) is int and metric['label']==row['label'],f'Metric label mismatch: {task}')
            require(metric.get('n_tokens')==row['scored_length']-1,f'Causal-target count mismatch: {task}/{row["id"]}')
        summaries={}
        for split in ['train','validation']:
            summaries[split]=independent_losses([r for r in metrics if r['split']==split])
            verify_loss_summary(complete.get('nll',{}).get(split),summaries[split],task+'/'+split)
        losses[task]=summaries
        features=arrays(directory/'features.npz',['cache_key',*LAYERS])
        require(features['cache_key'].shape==() and features['cache_key'].item()==key,f'Feature key does not match actual provenance: {task}')
        for layer in LAYERS:
            require(features[layer].shape==(len(selected_rows),1920),f'Feature record/dimension mismatch: {task}/{layer}')
        labels=np.array([r['label'] for r in selected_rows]);train=np.array([r['split']=='train' for r in selected_rows]);dev=~train
        require(int(train.sum())==data[task]['train_count'] and int(dev.sum())==data[task]['validation_count'],'Feature/split association mismatch')
        classes=np.array(config['label_schemas'][task])
        require(np.array_equal(np.unique(labels[train]),classes) and np.array_equal(np.unique(labels[dev]),classes),f'Missing classes: {task}')
        candidates=candidate_rows(complete.get('probes'),task,int(train.sum()),int(dev.sum()))
        require(read_json(directory/'probe_results.json')==candidates,f'Candidate-file disagreement: {task}')
        all_candidates.extend(candidates);all_metrics.extend(metrics)
        require({p.name for p in directory.glob('*.probe.npz')}=={l+'.probe.npz' for l in LAYERS},f'Missing/unexpected saved classifier files: {task}')
        for layer in LAYERS:
            saved=arrays(directory/(layer+'.probe.npz'),['coef','intercept','classes','mean','scale'])
            k=1 if len(classes)==2 else len(classes)
            require(saved['coef'].shape==(k,1920) and saved['intercept'].shape==(k,) and saved['mean'].shape==(1920,) and saved['scale'].shape==(1920,),f'Classifier dimension mismatch: {task}/{layer}')
            require(np.issubdtype(saved['classes'].dtype,np.integer) and np.array_equal(saved['classes'],classes) and (saved['scale']>0).all(),f'Classifier class/scaling mismatch: {task}/{layer}')
            chosen=next(r for r in candidates if r['layer']==layer and r['selected'])
            scaler=StandardScaler();scaler.mean_,scaler.scale_=saved['mean'],saved['scale'];scaler.n_features_in_=1920
            classifier=LogisticRegression(C=chosen['C'],solver='lbfgs',class_weight='balanced',max_iter=2000,random_state=42)
            classifier.coef_,classifier.intercept_,classifier.classes_=saved['coef'],saved['intercept'],saved['classes'];classifier.n_features_in_=1920
            probabilities=classifier.predict_proba(scaler.transform(features[layer][dev]))
            require(np.isfinite(probabilities).all(),f'Nonfinite saved predictions: {task}/{layer}')
            score=auroc(labels[dev],probabilities,classes)
            if score!=chosen['validation_auroc']:
                discrepancies.append(f'Saved classifier AUROC differs: {task}/{layer}: {score} vs {chosen["validation_auroc"]}')
            fresh_scaler=StandardScaler().fit(features[layer][train])
            x_train=fresh_scaler.transform(features[layer][train]);x_dev=fresh_scaler.transform(features[layer][dev]);selected_refit=None
            for candidate in sorted([r for r in candidates if r['layer']==layer],key=lambda r:r['C']):
                refit=LogisticRegression(C=candidate['C'],solver='lbfgs',class_weight='balanced',max_iter=2000,random_state=42)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always');refit.fit(x_train,labels[train])
                refit_prob=refit.predict_proba(x_dev)
                require(np.isfinite(refit_prob).all(),f'Nonfinite refitted predictions: {task}/{layer}')
                refit_score=auroc(labels[dev],refit_prob,refit.classes_);delta=refit_score-candidate['validation_auroc']
                candidate_checks.append(dict(task=task,layer=layer,C=candidate['C'],recorded_auroc=candidate['validation_auroc'],refit_auroc=refit_score,auroc_difference=delta,selected=candidate['selected'],warnings=[str(w.message) for w in caught]))
                if delta!=0:
                    discrepancies.append(f'Candidate refit AUROC differs: {task}/{layer}/C={candidate["C"]}: {delta}')
                if candidate['selected']:
                    selected_refit=dict(refit_auroc=refit_score,maximum_probability_difference=float(np.max(np.abs(refit_prob-probabilities))),maximum_coefficient_difference=float(np.max(np.abs(refit.coef_-saved['coef']))),
                        maximum_intercept_difference=float(np.max(np.abs(refit.intercept_-saved['intercept']))),
                        maximum_scaler_mean_difference=float(np.max(np.abs(fresh_scaler.mean_-saved['mean']))),maximum_scaler_scale_difference=float(np.max(np.abs(fresh_scaler.scale_-saved['scale']))),
                        predicted_labels_equal=bool(np.array_equal(refit.predict(x_dev),classifier.predict(scaler.transform(features[layer][dev])))))
                    if any(value!=0 for name,value in selected_refit.items() if name.startswith('maximum_')) or not selected_refit['predicted_labels_equal']:
                        qualifications.append(f'Saved/refit numerical disagreement: {task}/{layer}; no acceptance tolerance was invented')
                        selected_refit.update(saved_probabilities=probabilities.tolist(),refit_probabilities=refit_prob.tolist(),
                            saved_coefficients=saved['coef'].tolist(),refit_coefficients=refit.coef_.tolist(),
                            saved_intercepts=saved['intercept'].tolist(),refit_intercepts=refit.intercept_.tolist(),
                            saved_scaler_mean=saved['mean'].tolist(),refit_scaler_mean=fresh_scaler.mean_.tolist(),
                            saved_scaler_scale=saved['scale'].tolist(),refit_scaler_scale=fresh_scaler.scale_.tolist())
            checks.append(dict(task=task,layer=layer,selected_C=chosen['C'],recorded_auroc=chosen['validation_auroc'],reconstructed_auroc=score,exact_auroc_match=score==chosen['validation_auroc'],refit=selected_refit))
    require(len(checks)==6 and len(candidate_checks)==18,'Incomplete six-probe/18-candidate verification')
    combined=read_jsonl(run/'per_example_metrics.jsonl');combined_ids=[r.get('id') for r in combined]
    require(all(isinstance(x,str) for x in combined_ids) and len(combined)==len(manifest) and len(set(combined_ids))==len(manifest),'Combined metric count/ID mismatch')
    require({r['id']:r for r in combined}=={r['id']:r for r in all_metrics},'Combined/per-task metric disagreement')
    with (run/'baseline_probe_results.csv').open(newline='') as stream:csv_rows=list(csv.DictReader(stream))
    require(len(csv_rows)==18,'Combined candidate CSV must contain all 18 rows')
    wanted={(r['task'],r['layer'],float(r['C'])):r for r in all_candidates};seen=set()
    for row in csv_rows:
        row_key=(row.get('task'),row.get('layer'),float(row.get('C','nan')))
        require(row_key in wanted and row_key not in seen,'Duplicate/unexpected combined candidate row')
        seen.add(row_key);expected=wanted[row_key]
        require(float(row['validation_auroc'])==expected['validation_auroc'] and row['selected']==str(expected['selected']),'Combined candidate score/selection mismatch')
        require(int(row['train_count'])==expected['train_count'] and int(row['validation_count'])==expected['validation_count'],'Combined candidate record-count mismatch')
        require(row.get('auroc_definition')==expected['auroc_definition'] and row.get('positive_class')==('' if expected['positive_class'] is None else str(expected['positive_class'])) and row.get('positive_column')==('' if expected['positive_column'] is None else str(expected['positive_column'])),'Combined candidate class/definition mismatch')
        require(ast.literal_eval(row['warnings'])==expected['warnings'],'Combined candidate warning mismatch')
    return dict(all_passed=not discrepancies and not qualifications,structural_checks_passed=True,scientific_discrepancies=discrepancies,refit_qualifications=qualifications,samples_verified=len(manifest),inference_source_commit=context['source_commit'],data=data,losses=losses,checks=checks,candidate_checks=candidate_checks,
                limitations=['Saved-artifact consistency and CPU classifier refits only; GPU feature extraction was not independently reproduced.',
                'Original feature NPZs contain no row IDs/labels; association uses manifest order, producer source and recomputed keys, not independently regenerated embeddings.',
                'Validation-selected small pilot; BioNeMo/GradDiff checkpoint compatibility is not established.'])
