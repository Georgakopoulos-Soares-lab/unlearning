"""Exact tied-score weighted metrics for paired sequence/group bootstraps."""
import numpy as np
from sklearn.metrics import (accuracy_score, average_precision_score,
                             balanced_accuracy_score, confusion_matrix,
                             log_loss, roc_auc_score)

METRICS = ['auroc', 'accuracy', 'balanced_accuracy', 'average_precision',
           'classification_cross_entropy']


def decisions(probabilities, classes):
    return (classes[(probabilities[:, 1] >= .5).astype(int)] if len(classes) == 2
            else classes[probabilities.argmax(1)])


def point_metrics(y, probabilities, classes):
    p = np.asarray(probabilities, dtype=np.float64)
    if (p.shape != (len(y), len(classes)) or not np.isfinite(p).all()
            or np.any((p < 0) | (p > 1)) or not np.allclose(p.sum(1), 1)):
        raise ValueError('Invalid probabilities or class ordering')
    pred = decisions(p, classes)
    binary = len(classes) == 2
    metrics = dict(
        auroc=float(roc_auc_score(y, p[:, 1]) if binary else
                    roc_auc_score(y, p, labels=classes, multi_class='ovr', average='macro')),
        accuracy=float(accuracy_score(y, pred)),
        balanced_accuracy=float(balanced_accuracy_score(y, pred)),
        average_precision=float(average_precision_score(y, p[:, 1]) if binary else
                                np.mean([average_precision_score(y == c, p[:, i])
                                         for i, c in enumerate(classes)])),
        classification_cross_entropy=float(log_loss(y, p, labels=classes)))
    return metrics, dict(n=len(y), classes=classes.tolist(),
                         class_support=[int(np.sum(y == c)) for c in classes],
                         confusion_counts=confusion_matrix(y, pred, labels=classes).tolist(),
                         confusion_axes='rows=true, columns=predicted; declared class order',
                         score_direction='higher probability for declared positive class; numeric class1 in binary',
                         multiclass='AUROC and average precision are macro one-vs-rest; balanced accuracy is macro recall')


def weighted_rank_metrics(binary_y, score, weights):
    """Rows of weights are bootstrap multiplicities; ties are combined exactly."""
    order = np.argsort(score, kind='stable')
    sorted_score = score[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_score)) + 1]
    sorted_weights = np.asarray(weights[:, order], dtype=np.float64)
    positive = np.add.reduceat(sorted_weights * binary_y[order], starts, axis=1)
    negative = np.add.reduceat(sorted_weights * (1 - binary_y[order]), starts, axis=1)
    total_positive, total_negative = positive.sum(1), negative.sum(1)
    with np.errstate(divide='ignore', invalid='ignore'):
        auc = (positive * (negative.cumsum(1) - .5 * negative)).sum(1) / (total_positive * total_negative)
        reverse_positive, reverse_negative = positive[:, ::-1], negative[:, ::-1]
        precision = reverse_positive.cumsum(1) / (reverse_positive + reverse_negative).cumsum(1)
        ap = np.nansum(precision * reverse_positive, axis=1) / total_positive
    invalid = (total_positive == 0) | (total_negative == 0)
    auc[invalid] = np.nan
    ap[invalid] = np.nan
    return auc, ap


def bootstrap_metrics(y, probabilities, classes, weights):
    p = np.asarray(probabilities, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)
    supports = np.stack([weights @ (y == c).astype(float) for c in classes], axis=1)
    valid = np.all(supports > 0, axis=1)
    predicted = decisions(p, classes)
    total = weights.sum(1)
    result = dict(accuracy=(weights @ (predicted == y).astype(float)) / total)
    recall = np.stack([(weights @ ((predicted == y) & (y == c)).astype(float)) / supports[:, i]
                       for i, c in enumerate(classes)], axis=1)
    result['balanced_accuracy'] = recall.mean(1)
    ranked = [weighted_rank_metrics((y == c).astype(float), p[:, i], weights)
              for i, c in enumerate(classes) if len(classes) != 2 or i == 1]
    result['auroc'] = np.mean([x[0] for x in ranked], axis=0)
    result['average_precision'] = np.mean([x[1] for x in ranked], axis=0)
    encoded = np.searchsorted(classes, y)
    # sklearn log_loss clips to the probability dtype's machine epsilon.
    clipped = np.clip(p, np.finfo(np.float64).eps, 1 - np.finfo(np.float64).eps)
    row_loss = -np.log(clipped[np.arange(len(y)), encoded])
    result['classification_cross_entropy'] = (weights @ row_loss) / total
    for value in result.values():
        value[~valid] = np.nan
    return result, valid


def group_resampling(groups, seed=20261103, repetitions=2000):
    names, inverse = np.unique(groups, return_inverse=True)
    draws = np.random.default_rng(seed).integers(len(names), size=(repetitions, len(names)), dtype=np.int32)
    group_weights = np.stack([np.bincount(draw, minlength=len(names)) for draw in draws])
    return names, inverse, draws, group_weights[:, inverse]
