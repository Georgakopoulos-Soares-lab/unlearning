"""Matched train-only-CV controls; no optional model imports or test data access."""
import argparse
from collections import defaultdict
import itertools
import json
from pathlib import Path
import warnings

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score, balanced_accuracy_score, matthews_corrcoef
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import digest, prepare, eligibility_for_run


def write(path, obj):
    path = Path(path)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')
    tmp.replace(path)


def controls(sequences):
    words = {''.join(k): i for i, k in enumerate(itertools.product('ACGT', repeat=4))}
    comp, kmers = [], []
    for seq in sequences:
        c = np.array([seq.count(b) for b in 'ACGT'], dtype=float)
        k = np.zeros(256)
        for i in range(len(seq)-3):
            word = seq[i:i+4]
            if word in words:
                k[words[word]] += 1
        if not c.sum() or not k.sum():
            raise ValueError('No canonical bases or 4-mer windows')
        comp.append(c/c.sum()); kmers.append(k/k.sum())
    return {'composition': np.array(comp), '4mer': np.array(kmers)}


def groups(rows):
    # Union supplied biological groups and both full/prefix exact/RC identities.
    parent = list(range(len(rows)))
    def root(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    seen = {}
    for i, r in enumerate(rows):
        s = r['sequence']; canonical = min(s, s.translate(str.maketrans('ACGTN','TGCAN'))[::-1])
        keys = [('prefix', digest(canonical)), ('full', r.get('full_sequence_rc_sha256', r['full_sequence_sha256']))]
        if r.get('group_id') is not None:
            keys.append(('biological', str(r['group_id'])))
        for key in keys:
            if key in seen:
                parent[root(i)] = root(seen[key])
            else:
                seen[key] = i
    return np.array([str(root(i)) for i in range(len(rows))])


def auc(y, probabilities, classes):
    if len(classes) == 2:
        if list(classes) != [0,1]:
            raise ValueError('Unqualified binary positive class')
        return float(roc_auc_score(y, probabilities[:,1]))
    return float(roc_auc_score(y, probabilities, labels=classes, multi_class='ovr', average='macro'))


def fold_indices(y, group):
    folds = list(StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42).split(np.zeros(len(y)), y, group))
    for a,b in folds:
        if set(group[a]) & set(group[b]) or set(y[a]) != set(y) or set(y[b]) != set(y):
            raise ValueError('Invalid grouped training fold')
    return folds


def pipeline(c):
    return make_pipeline(StandardScaler(), LogisticRegression(C=c, class_weight='balanced', solver='lbfgs', max_iter=2000, random_state=42))


def fit(x, y, train, dev, folds, fit_labels=None):
    yt = y[train] if fit_labels is None else fit_labels
    classes = np.unique(y[train]); candidates = []
    for c in [.1,1.,10.]:
        scores, messages = [], []
        for a,b in folds:
            model = pipeline(c)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always'); model.fit(x[train][a], yt[a])
            messages.extend(str(w.message) for w in caught)
            scores.append(auc(yt[b], model.predict_proba(x[train][b]), classes))
        candidates.append(dict(C=c, fold_auroc=scores, mean_fold_auroc=float(np.mean(scores)), warnings=messages))
    chosen = max(candidates, key=lambda c:c['mean_fold_auroc'])
    model = pipeline(chosen['C'])
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always'); model.fit(x[train], yt)
    p = model.predict_proba(x[dev]); pred = model.predict(x[dev])
    return model, p, dict(C=chosen['C'], candidates=candidates, refit_warnings=[str(w.message) for w in caught],
        converged=not caught and all(not c['warnings'] for c in candidates),
        auroc=auc(y[dev], p, classes), accuracy=float(accuracy_score(y[dev],pred)),
        balanced_accuracy=float(balanced_accuracy_score(y[dev],pred)), mcc=float(matthews_corrcoef(y[dev],pred)))


CONTRASTS = [('blocks.7','4mer'),('blocks.15','4mer'),('norm','4mer'),('blocks.7','blocks.15'),('4mer','composition')]


def bootstrap(y, predictions, group, n=2000):
    classes = np.unique(y); units = np.unique(group); members = [np.flatnonzero(group==g) for g in units]
    rng = np.random.default_rng(20261021)
    pairs = [(a,b) for a,b in CONTRASTS if a in predictions and b in predictions]
    samples = {a+' minus '+b: [] for a,b in pairs}; rejected=0
    for _ in range(n):
        idx=np.concatenate([members[i] for i in rng.integers(len(units), size=len(units))])
        if len(np.unique(y[idx])) != len(classes):
            rejected+=1; continue
        scores={k:auc(y[idx],p[idx],classes) for k,p in predictions.items()}
        for a,b in pairs:
            samples[a+' minus '+b].append(scores[a]-scores[b])
    return {key:dict(difference=auc(y,predictions[a],classes)-auc(y,predictions[b],classes),
        low=float(np.percentile(samples[key],2.5)),high=float(np.percentile(samples[key],97.5)),
        valid_replicates=len(samples[key]),missing_class_replicates=rejected,replicates=n,
        scope='pointwise exploratory, conditional on fitted models; duplicate/available-group bootstrap; unknown biological dependence')
        for a,b in pairs for key in [a+' minus '+b]}


def evaluate(rows, features, out, shuffle=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    ids=[r['id'] for r in rows]
    if len(set(ids)) != len(ids): raise ValueError('Duplicate IDs')
    y=np.array([r['label'] for r in rows]); splits=np.array([r['split'] for r in rows]);tr=splits=='train';dv=splits=='validation';g=groups(rows)
    if set(g[tr]) & set(g[dv]): raise ValueError('Cross-split groups')
    folds=fold_indices(y[tr],g[tr]); write(out/'folds.json',[[[ids[np.flatnonzero(tr)[i]] for i in a],[ids[np.flatnonzero(tr)[i]] for i in b]] for a,b in folds])
    methods=controls([r['sequence'] for r in rows]);methods.update(features)
    predictions={}; result={}
    for name,x in methods.items():
        if x.shape[0]!=len(rows) or not np.isfinite(x).all(): raise ValueError('Feature alignment/nonfinite failure')
        model,p,metrics=fit(x,y,tr,dv,folds);predictions[name]=p;result[name]=metrics
        joblib.dump(model,out/(name+'.joblib'))
        print(out.name,name,metrics['auroc'],flush=True)
        write(out/'metrics.partial.json',result)
    write(out/'metrics.json',result)
    write(out/'contrasts.json',bootstrap(y[dv],predictions,g[dv]))
    write(out/'counts.json',dict(train=int(tr.sum()),dev=int(dv.sum()),train_classes={str(c):int(sum(y[tr]==c)) for c in np.unique(y)},dev_classes={str(c):int(sum(y[dv]==c)) for c in np.unique(y)},biological_group_rows=sum(r.get('group_id') is not None for r in rows)))
    with (out/'predictions.jsonl').open('w') as f:
        for j,i in enumerate(np.flatnonzero(dv)):
            f.write(json.dumps(dict(id=ids[i],label=int(y[i]),split='validation',sequence_sha256=rows[i]['scored_prefix_sha256'],probabilities={k:p[j].tolist() for k,p in predictions.items()}))+'\n')
    if shuffle:
        shuffled=np.random.default_rng(20261021).permutation(y[tr]);diagnostics={}
        # Same predetermined folds; selection repeated on shuffled train labels.
        for name in ['composition','4mer']:
            _,_,diagnostics[name]=fit(methods[name],y,tr,dv,folds,shuffled)
        write(out/'shuffle_seed20261021.json',diagnostics)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','cached','expanded']);p.add_argument('--run-dir',required=True);a=p.parse_args();run=Path(a.run_dir);run.mkdir(exist_ok=True,parents=True)
    config=json.loads(Path('configs/benign_extension.json').read_text())
    if a.stage=='prepare':
        import hashlib
        archive='/workspace/data/gue/GUE.zip'
        with open(archive,'rb') as f: h=hashlib.file_digest(f,'sha256').hexdigest()
        if h!=config['data_archive_sha256']: raise ValueError('Archive hash mismatch')
        write(run/'config.json',config);write(run/'data_preparation.json',prepare(config,archive,run))
        rows=[json.loads(l) for l in (run/'subset_manifest.jsonl').read_text().splitlines()];write(run/'eligibility.json',eligibility_for_run(config,run,rows))
        old=[json.loads(l) for l in Path('/workspace/meeting-artifacts/evo2-20261020T1437/subset_manifest.jsonl').read_text().splitlines()]; oldids={r['id'] for r in old}
        write(run/'historical_overlap.json',{t:{s:sum(r['id'] in oldids for r in rows if r['task']==t and r['split']==s) for s in ['train','validation']} for t in config['tasks']})
    elif a.stage=='cached':
        old=Path('/workspace/meeting-artifacts/evo2-20261020T1437');rows=[json.loads(l) for l in (old/'subset_manifest.jsonl').read_text().splitlines()]
        for task in dict.fromkeys(r['task'] for r in rows):
            selected=[r for r in rows if r['task']==task]; saved=np.load(old/task/'features.npz',allow_pickle=False)
            evaluate(selected,{k:saved[k] for k in ['blocks.7','blocks.15']},run/'cached_cpu'/task,shuffle=True)
    else:
        rows=[json.loads(l) for l in (run/'subset_manifest.jsonl').read_text().splitlines()];eligible=json.loads((run/'eligibility.json').read_text())
        for task in config['tasks']:
            if not eligible[task]['eligible']:continue
            selected=[r for r in rows if r['task']==task];path=run/task/'features.npz';features={}
            if path.exists():
                saved=np.load(path,allow_pickle=False)
                if saved['ids'].tolist()!=[r['id'] for r in selected] or saved['labels'].tolist()!=[r['label'] for r in selected]:raise ValueError('Saved feature identity mismatch')
                features={k:saved[k] for k in config['layers']}
            evaluate(selected,features,run/('expanded_matched' if features else 'expanded_cpu')/task)

if __name__=='__main__':main()
