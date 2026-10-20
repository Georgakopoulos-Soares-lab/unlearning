"""Train-only scaling and validation selection, adapted from undo train_probes."""
import warnings

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler


def fit_probes(features, labels, splits):
    train, validation = splits == 'train', splits == 'validation'
    classes = sorted(set(labels[train]))
    if len(classes) < 2 or set(labels[validation]) != set(classes):
        raise ValueError('Train and validation require the same nontrivial label schema')
    if not np.isfinite(features).all():
        raise ValueError('Nonfinite probe features')
    scaler = StandardScaler().fit(features[train])
    x_train, x_val = scaler.transform(features[train]), scaler.transform(features[validation])
    candidates, fitted = [], []
    for c in [0.1, 1., 10.]:
        classifier = LogisticRegression(C=c, solver='lbfgs', class_weight='balanced', max_iter=2000, random_state=42)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            classifier.fit(x_train, labels[train])
        if len(classes) == 2:
            if classes != [0, 1]:
                raise ValueError('Binary tasks require documented positive class 1')
            positive_index = np.flatnonzero(classifier.classes_ == 1).item()
            score = roc_auc_score(labels[validation], classifier.predict_proba(x_val)[:, positive_index])
        else:
            positive_index = None
            score = roc_auc_score(labels[validation], classifier.predict_proba(x_val),
                                  labels=classifier.classes_, multi_class='ovr', average='macro')
        candidates.append(dict(C=c, validation_auroc=float(score), warnings=[str(w.message) for w in caught],
                               positive_class=1 if len(classes)==2 else None, positive_column=positive_index,
                               auroc_definition='binary positive class 1' if len(classes)==2 else 'macro one-vs-rest'))
        fitted.append(classifier)
    best = max(range(len(candidates)), key=lambda i: candidates[i]['validation_auroc'])
    # Candidate order resolves exact ties in favor of smaller C.
    return candidates, best, scaler, fitted[best]
