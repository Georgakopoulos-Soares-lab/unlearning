"""Investigate the predeclared single shuffle without selecting another seed."""
from pathlib import Path
import json
import joblib
import numpy as np
from sklearn.metrics import roc_auc_score
from benign_pilot.extension import controls,pipeline,write

run=Path('/workspace/meeting-artifacts/evo2-extension-20261021T0942')
old=Path('/workspace/meeting-artifacts/evo2-20261020T1437')
rows=[json.loads(l) for l in (old/'subset_manifest.jsonl').read_text().splitlines()]
results={}
for task in dict.fromkeys(r['task'] for r in rows):
    selected=[r for r in rows if r['task']==task];y=np.array([r['label'] for r in selected]);tr=np.array([r['split']=='train' for r in selected]);dv=~tr
    shuffled=np.random.default_rng(20261021).permutation(y[tr]);x=controls([r['sequence'] for r in selected])['composition']
    previous=json.loads((run/'cached_cpu'/task/'shuffle_seed20261021.json').read_text())['composition'];model=pipeline(previous['C']);model.fit(x[tr],shuffled)
    probabilities=model.predict_proba(x[dv]);base=joblib.load(run/'cached_cpu'/task/'composition.joblib');basep=base.predict_proba(x[dv])
    score=roc_auc_score(y[dv],probabilities[:,1]) if len(np.unique(y))==2 else roc_auc_score(y[dv],probabilities,multi_class='ovr',average='macro')
    if abs(score-previous['auroc'])>1e-12:raise ValueError('Diagnostic does not reproduce original shuffle')
    joblib.dump(model,run/'cached_cpu'/task/'shuffle_composition.joblib')
    write(run/'cached_cpu'/task/'shuffle_train_labels.json',[dict(id=r['id'],original_label=int(a),shuffled_label=int(b)) for r,a,b in zip([r for r in selected if r['split']=='train'],y[tr],shuffled)])
    results[task]=dict(shuffle_seed=20261021,train_label_agreement=float(np.mean(shuffled==y[tr])),train_label_class_counts={str(c):int(sum(shuffled==c)) for c in np.unique(y)},reproduced_dev_auroc=float(score),coefficient=model[-1].coef_.tolist(),unshuffled_coefficient=base[-1].coef_.tolist(),scaler_mean_matches_unshuffled=bool(np.array_equal(model[0].mean_,base[0].mean_)),probability_correlation_with_unshuffled=float(np.corrcoef(probabilities[:,1],basep[:,1])[0,1]),fit_only_used_shuffled_training_labels=True,dev_labels_used_only_for_reporting=True,interpretation='Four composition features can preserve the ranking of a strong composition signal under a chance-aligned shuffled fit; CV on shuffled labels is near/below chance. One shuffle is not a calibrated null distribution or evidence of leakage.')
write(run/'shuffle_investigation.json',results)
print(json.dumps(results,indent=2))
