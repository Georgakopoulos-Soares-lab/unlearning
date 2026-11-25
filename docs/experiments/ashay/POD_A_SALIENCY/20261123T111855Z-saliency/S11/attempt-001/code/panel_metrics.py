"""Saved-output audit metrics using pairwise comparisons, independent of producer ranks."""
import numpy as np


def metrics(y, probabilities, classes, weights):
    """Compute weighted metrics via pairwise wins and score-threshold indicators."""
    p = np.asarray(probabilities, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    if p.shape != (len(y), len(classes)) or not np.isfinite(p).all():
        raise ValueError('Invalid probability matrix')
    if np.any((p < 0) | (p > 1)) or not np.allclose(p.sum(axis=1), 1, atol=1e-12, rtol=0):
        raise ValueError('Invalid probability support or normalization')
    supports = np.array([w[:, y == c].sum(axis=1) for c in classes]).T
    valid = np.all(supports > 0, axis=1)
    prediction = (classes[(p[:, 1] >= .5).astype(int)] if len(classes) == 2
                  else classes[np.argmax(p, axis=1)])
    correct = prediction == y
    result = dict(accuracy=w[:, correct].sum(axis=1) / w.sum(axis=1))
    with np.errstate(divide='ignore', invalid='ignore'):
        result['balanced_accuracy'] = np.array([
            w[:, correct & (y == c)].sum(axis=1)/supports[:, i]
            for i, c in enumerate(classes)]).mean(axis=0)
    aurocs, average_precisions = [], []
    for i, c in enumerate(classes):
        if len(classes) == 2 and i == 0:
            continue
        positive, negative = y == c, y != c
        wp, wn = w[:, positive], w[:, negative]
        ps, ns = p[positive, i], p[negative, i]
        wins = (ps[:, None] > ns[None, :]).astype(np.float64)
        wins += .5 * (ps[:, None] == ns[None, :])
        with np.errstate(divide='ignore', invalid='ignore'):
            aurocs.append(((wp @ wins) * wn).sum(axis=1)/(wp.sum(axis=1)*wn.sum(axis=1)))
        # At each positive score, count all weighted positives/examples at least that score.
        at_least = (p[:, i, None] >= ps[None, :]).astype(np.float64)
        denominator = w @ at_least
        numerator = wp @ at_least[positive]
        precision = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=denominator > 0)
        with np.errstate(divide='ignore', invalid='ignore'):
            average_precisions.append((precision*wp).sum(axis=1)/wp.sum(axis=1))
    result['auroc'] = np.array(aurocs).mean(axis=0)
    result['average_precision'] = np.array(average_precisions).mean(axis=0)
    columns = np.array([{c:i for i, c in enumerate(classes)}[v] for v in y])
    true_probability = p[np.arange(len(y)), columns]
    row_loss = -np.log(np.minimum(1-np.finfo(np.float64).eps,
                                  np.maximum(np.finfo(np.float64).eps, true_probability)))
    result['classification_cross_entropy'] = (w @ row_loss) / w.sum(axis=1)
    for value in result.values():
        value[~valid] = np.nan
    return result, valid


def reconstruct(model, features):
    """Apply saved scaler/coefficients directly without sklearn prediction methods."""
    scaler, head = model[0], model[-1]
    standardized = features.copy()
    standardized -= scaler.mean_
    standardized /= scaler.scale_
    score = standardized @ head.coef_.T + head.intercept_
    if len(head.classes_) == 2:
        from scipy.special import expit
        positive = expit(score[:, 0])
        return np.column_stack([1-positive, positive])
    score -= score.max(axis=1, keepdims=True)
    exponential = np.exp(score)
    return exponential / exponential.sum(axis=1, keepdims=True)
