"""Render measured H3 follow-up tables and standalone scientific figures."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from .h3_followup import write

LABELS={'original_mlp':'Original MLP','evo2_norm':'Evo2 logistic','composition':'Composition logistic','4mer':'4-mer logistic'}


def interval(v,digits=4):
    return f"{v['estimate']:.{digits}f} [{v['low']:.{digits}f}, {v['high']:.{digits}f}]"


def main(run,docs):
    started=time.perf_counter();cpu_start=time.process_time();docs.mkdir(parents=True,exist_ok=True)
    verification=json.loads((run/'verification.json').read_text())
    if not verification['passed']:raise ValueError('Verification required')
    cfg=json.loads((run/'protocol.json').read_text());original=Path(cfg['original_run'])
    uncertainty=json.loads((run/'uncertainty.json').read_text());supp=json.loads((run/'supplemental_metrics.json').read_text())
    exposure=json.loads((run/'training_exposure.json').read_text());original_metrics=json.loads((original/'metrics.json').read_text())
    seeds=json.loads((run/'seed_results.json').read_text());selection=json.loads((original/'selection.json').read_text())
    execution=json.loads((run/'study_execution_identity.json').read_text());seed_execution=json.loads((run/'seed_execution_identity.json').read_text())
    figdir=run/'figures';figdir.mkdir(exist_ok=True);plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    names=['original_mlp','evo2_norm','composition','4mer'];positions=np.arange(4);colors=['#626262','#2465a8','#bd7532','#29844c']
    fig,axes=plt.subplots(1,3,figsize=(12,4.8),sharey=True)
    for ax,key,title in zip(axes,['auroc','accuracy','balanced_accuracy'],['Test AUROC','Test accuracy','Test balanced accuracy']):
        for i,n in enumerate(names):
            v=uncertainty['test']['models'][n][key]
            ax.errorbar(v['estimate'],i,xerr=[[v['estimate']-v['low']],[v['high']-v['estimate']]],fmt='o',color=colors[i],capsize=4)
        ax.set_title(title);ax.set_xlim(.5,1);ax.grid(axis='x',alpha=.25)
    axes[0].set_yticks(positions,[LABELS[n] for n in names]);axes[0].invert_yaxis()
    fig.suptitle('Same 1,497 H3 test sequences; fixed fitted classifiers',fontsize=12)
    fig.text(.5,.015,'2,000 whole-sequence resamples; pointwise 95% intervals; post-hoc exploratory',ha='center',fontsize=9)
    fig.tight_layout(rect=[0,.055,1,.94]);fig.savefig(figdir/'performance.png',dpi=180);fig.savefig(figdir/'performance.pdf');plt.close(fig)
    contrasts=uncertainty['test']['paired_auroc_differences'];fig,ax=plt.subplots(figsize=(8.2,3.5))
    labels=['Evo2 logistic − composition','Evo2 logistic − 4-mer','Original MLP − Evo2 logistic']
    for i,(key,label) in enumerate(zip(contrasts,labels)):
        v=contrasts[key];ax.errorbar(v['estimate'],i,xerr=[[v['estimate']-v['low']],[v['high']-v['estimate']]],fmt='o',capsize=4,color='#2465a8')
    ax.axvline(0,color='black',lw=.8);ax.set_yticks(np.arange(3),labels);ax.invert_yaxis();ax.set_xlabel('Paired test AUROC difference (left readout minus right readout)');ax.grid(axis='x',alpha=.25)
    ax.set_title('Conditional, pointwise exploratory 95% paired intervals');fig.tight_layout();fig.savefig(figdir/'paired_differences.png',dpi=180);fig.savefig(figdir/'paired_differences.pdf');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4.5));steps=[r['step'] for r in exposure['summaries']]
    axes[0].plot(steps,[100*r['fraction_seen'] for r in exposure['summaries']],marker='o',color='#2465a8')
    axes[0].scatter([250],[100*exposure['summaries'][4]['fraction_seen']],color='#c27728',zorder=4)
    axes[0].set(xlabel='Head training step',ylabel='Available training rows seen (%)',title='Reconstructed unique gradient exposure',ylim=(0,22))
    axes[0].annotate('Selected: 1,842 / 11,971 rows',xy=(250,15.39),xytext=(90,20),arrowprops={'arrowstyle':'->'},fontsize=9)
    trajectory=selection['candidates'];right=axes[1];twin=right.twinx()
    p1=right.plot(steps,[r['dev']['auroc'] for r in trajectory],color='#2465a8',marker='o',label='Dev AUROC')
    p2=twin.plot(steps,[r['dev']['classification_cross_entropy'] for r in trajectory],color='#bd7532',marker='s',label='Dev classification CE')
    right.axvline(250,color='gray',ls='--',lw=.8);right.set(xlabel='Head training step',ylabel='Dev AUROC',title='Original checkpoint selection trajectory');twin.set_ylabel('Dev classification cross-entropy')
    right.legend(p1+p2,[p.get_label() for p in p1+p2],loc='lower right',fontsize=8)
    fig.tight_layout();fig.savefig(figdir/'exposure_trajectory.png',dpi=180);fig.savefig(figdir/'exposure_trajectory.pdf');plt.close(fig)
    lines=['# Benign H3 follow-up results','',
'The 4-mer logistic control outperformed the cached final-normalized Evo2 logistic probe on the supplied test split: AUROC 0.8955 versus 0.8469. The original MLP remains unchanged at 0.8318. This is a post-hoc exploratory study on a test result already known when the supplement was designed, not a new confirmatory benchmark.','',
'## Table 1 — unchanged original MLP, with new conditional uncertainty','',
'| Split | Rows | AUROC [95% interval] | Accuracy [95% interval] | Balanced accuracy [95% interval] | Causal NLL [95% interval] | LM perplexity [95% interval] |',
'|---|---:|---|---|---|---|---|']
    for split in ['dev','test']:
        u=uncertainty[split];m=u['models']['original_mlp']
        lines.append(f"| {split} | 1497 | {interval(m['auroc'])} | {interval(m['accuracy'])} | {interval(m['balanced_accuracy'])} | {interval(u['causal_nll'])} | {interval(u['lm_perplexity'])} |")
    lines += ['',
'The selected step-250 head received 2,000 draws from **1,842 unique rows (15.39%)**, not all 11,971 available training rows. At step 300 the unique count was 2,181. All 14,965 rows had frozen features extracted; 11,971 training rows were scored for original training metrics. Those facts do not imply full gradient exposure. See TRAINING_EXPOSURE.md for counts/classes at all six checkpoints and an addendum to the historical wording. The head has 3,696,002 parameters. Limited exposure is a protocol limitation, not an established causal explanation of its score.','',
'## Table 2 — same-row supplemental readouts','',
'| Split | Readout (selected C) | AUROC [95% interval] | Average precision | Accuracy | Balanced accuracy | Classification CE |',
'|---|---|---|---:|---:|---:|---:|']
    for split in ['dev','test']:
        for name in cfg['conditions']:
            m=supp[name]['splits'][split];u=uncertainty[split]['models'][name]
            lines.append(f"| {split} | {LABELS[name]} ({supp[name]['selected_C']:g}) | {interval(u['auroc'])} | {m['average_precision']:.4f} | {m['accuracy']:.4f} | {m['balanced_accuracy']:.4f} | {m['classification_cross_entropy']:.4f} |")
    lines+=['',
'Class1 prevalence / majority baseline is 0.5090 on dev and 0.5043 on test. Numeric labels are retained; biological meanings are not guessed. Full sensitivity, specificity, confusion matrices, all accuracy/balanced-accuracy intervals and classification losses are in supplemental_metrics.json, original_metrics.json and uncertainty.json. The composition baseline uses four canonical-base frequencies; 4-mers use normalized overlapping forward-strand counts without RC aggregation. All three logistic pipelines use balanced L2 regression, three identical exact/RC-grouped stratified training folds, fold-local StandardScaler, C=0.1/1/10 with smaller-C ties, and all-train refitting. Solver/seed/tolerance/limits were frozen before scoring. All 27 CV fits and three refits converged without a retry. The Evo2 fit retains float32 cached features/coefficients; sequence controls use float64.','',
'| Paired test AUROC contrast | Difference [95% interval] |','|---|---|']
    for key,v in uncertainty['test']['paired_auroc_differences'].items():lines.append(f"| {key} | {interval(v)} |")
    lines+=['',
'Every contrast used identical sampled sequence IDs, seed 20261027, 2,000 resamples; none lacked a class. Intervals are percentile, pointwise and unadjusted for multiple exploratory comparisons. Exact/RC groups are all singletons; no biological groups were available, so these intervals do not account for homology or other unknown dependencies. They condition on the fitted readouts and split and exclude fitting/selection uncertainty. Causal NLL resamples entire sequence loss/count pairs; it never treats nucleotide targets as independent. LM NLL/perplexity are reused unchanged for every readout, and classifier CE is kept separate.','',
'The Evo2 probe’s positive difference from composition suggests additional predictive information under this protocol. Its negative difference from the 4-mer control does not establish absent model information or biological mechanism. The original-MLP/readout difference combines changes in architecture, exposure and selection procedure; it does not isolate any one cause. Do not rank this test result against the old block-7 dev score as a model effect.','',
'## Bounded MLP seed sensitivity','',
'| Seed | Selected step | Unique training rows at selection | Dev AUROC | Test AUROC | Test accuracy | Test balanced accuracy |',
'|---|---:|---:|---:|---:|---:|---:|',
'| 42 (original) | 250 | 1842 | 0.820656 | 0.831817 | 0.702739 | 0.701179 |']
    for seed in ['17','1234']:
        r=seeds[seed];m=r['metrics'];lines.append(f"| {seed} | {r['selected_step']} | {r['unique_rows_seen_at_selected']} | {m['dev']['auroc']:.6f} | {m['test']['auroc']:.6f} | {m['test']['accuracy']:.6f} | {m['test']['balanced_accuracy']:.6f} |")
    lines+=['',
'Only the two prespecified additional seeds were run, under a hashed amendment before their test scoring. Every seed is reported; none replaces the original primary result. Their observed test AUROC range is 0.8210–0.8406. Three seeds are not a precise estimate of all training uncertainty.','',
'## Table 3 — readiness for comparison with Sayyed','',
'| Evidence category | Status | Practical conclusion |',
'|---|---|---|',
'| Numeric class1 AUROC, MLP definition, actual 300-step/batch8/initial-LR1e-3 settings | VERIFIED MATCH | Specification overlap; not full numerical equivalence. |',
'| Padding/backend/precision, effective LR curve, checkpoint250 vs300, threshold tie handling | VERIFIED DIFFERENCE | Historical aggregate-score subtraction would mix protocols. |',
'| Exact split identities, converted base/parent lineage, tokenizer bytes, normalization location, trained head/load audit | UNAVAILABLE | Direct matched H3 comparison is not ready. |','',
'COMPARABILITY.md contains the complete item-by-item matrix. Pinned bionemo head is b90fc1853d1d3be79922a98a2649c91c89716637. Historical H3 logs resolve base iteration1 and head iteration300; these files, tokenizer assets and BioNeMo runtime are not available here. No GPU compatibility check, large conversion or build was launched. Missing-head warnings during base loading do not alone prove head-overlay failure; the actual head/load audit is required. The shell continuation error is preserved as executed evidence, and no MaxEnt result is relabeled GradDiff.','',
'## Verification, recovery and next experiment','',
'Five focused accounting tests passed. Independent verification reconstructed all three loaded pipelines and both added-seed heads exactly, checked 2,994 aligned evaluation IDs, fold membership/training-only scaling and selection, independently recomputed AUROC/AP/confusion/CE, and reproduced all 2,000 paired resamples per split via weighted-rank accounting. Maximum bootstrap numeric discrepancy was 4.44e-16. Float32 versus float64 classification-CE differences are explicitly recorded under dtype-based tolerance; no model was refit or metric definition changed in response to test scores. This is saved-artifact verification, not a new backbone reproduction.','',
'The highest-value next experiment is a predeclared training-only token/representation/logit parity check after obtaining Sayyed’s hash-pinned converted base iteration1, trained head iteration300, tokenizer/run_config, conversion/loader lineage and split-ID tables. Until then this independent H3 reference supports within-protocol readout/control comparisons, not an unlearning effect or completion of the broader project.','',
f"Core classifier/bootstrap execution commit: {execution['execution_commit']}. Seed execution commit: {seed_execution['execution_commit']}. Exact code/input/protocol hashes are in the run. Original run is read-only. Run directory: {run}. Packaged source and final documentation delivery commits are recorded separately at delivery. Remote private backup is pending replacement securely configured credentials; the exposed chat token was not reused.",'',
'![Test performance and conditional intervals](figures/performance.png)','',
'![Paired test AUROC differences](figures/paired_differences.png)','',
'![Original exposure and dev trajectory](figures/exposure_trajectory.png)']
    report='\n'.join(lines)+'\n';(run/'FOLLOWUP_RESULTS.md').write_text(report);(docs/'FOLLOWUP_RESULTS.md').write_text(report)
    handoff=f'''# H3 follow-up handoff

1. **Measured:** original selected head unchanged; three training-only-CV-selected logistic readouts on identical dev/test rows; two fixed additional MLP seeds; whole-sequence paired uncertainty.
2. **New evidence:** selected original head saw1,842 unique training rows; 4-mers outperform the final-normalized Evo2 logistic probe under this protocol, while Evo2 exceeds composition; original MLP seed sensitivity is reported without selecting a winner.
3. **Supported:** performance depends on readout/training procedure. Additional predictive information relative to composition is conditional on this protocol. No causal biological understanding, unlearning effect, or broad project completion is established.
4. **Uncertain:** biological grouping/homology, unseen deployment distribution, training/selection uncertainty, dataset/converted-backbone/tokenizer parity with BioNeMo. Known test scores make the supplement post-hoc exploratory.
5. **Direct Sayyed comparison ready?** No. Current results are an independent original-backend reference.
6. **Needed:** immutable converted base iteration1 and trained H3 head iteration300 weights/checksums; run_config/tokenizer/loader/environment/parent conversion provenance; exact split-ID/sequence-hash/label tables; sampler/selection record. Agree normalization hook, padding, precision, LR curve and decision rule.
7. **Highest-value next experiment:** bounded, predeclared training-only token/hidden-state/logit/head parity check once those files are accessible, before a matched benchmark comparison.

Original input run: {original} (read-only). Follow-up: {run}. Python: /workspace/venvs/sayyed-base-runtime/bin/python. Branch: experiments-ashay-sayyed-base-v1.

Reproducible CPU entry point from /workspace/wt-sayyed-base (use a fresh output directory for new execution):

```
/workspace/venvs/sayyed-base-runtime/bin/python -m scripts.sayyed.h3_followup freeze --original {original} --run /workspace/meeting-artifacts/NEW_H3_FOLLOWUP
/workspace/venvs/sayyed-base-runtime/bin/python -m scripts.sayyed.h3_followup exposure --run /workspace/meeting-artifacts/NEW_H3_FOLLOWUP
OPENBLAS_NUM_THREADS=4 OMP_NUM_THREADS=4 /workspace/venvs/sayyed-base-runtime/bin/python -m scripts.sayyed.h3_followup fit --run /workspace/meeting-artifacts/NEW_H3_FOLLOWUP
/workspace/venvs/sayyed-base-runtime/bin/python -m scripts.sayyed.h3_followup bootstrap --run /workspace/meeting-artifacts/NEW_H3_FOLLOWUP
/workspace/venvs/sayyed-base-runtime/bin/python -m scripts.sayyed.verify_h3_followup --run /workspace/meeting-artifacts/NEW_H3_FOLLOWUP
```

Create the new output directory first. Reusing completed follow-up artifacts requires only the verifier, not refitting or bootstrap regeneration. Optional seed stage must first freeze its amendment; never expand beyond17/1234.

No additional GPU work was performed; shared ledger868.753177/7200 seconds remains inactive. No experiment job remains after delivery. Private remote backup remains pending replacement securely configured HF credentials. Do not reuse the exposed chat token. The complete local archive, checksum and source/delivery receipts are recorded separately; preserve the original verified backup.
'''
    (run/'HANDOFF.md').write_text(handoff);(docs/'HANDOFF.md').write_text(handoff)
    for name in ['supplemental_metrics.json','original_metrics.json','uncertainty.json','seed_results.json','verification.json','fit_timing.json','bootstrap_timing.json','seed_timing.json','verification_timing.json','study_execution_identity.json','seed_execution_identity.json']:
        shutil.copyfile(run/name,docs/name)
    shutil.copytree(figdir,docs/'figures',dirs_exist_ok=True)
    write(run/'report_timing.json',dict(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu_start))
    print('REPORT_COMPLETE',docs/'FOLLOWUP_RESULTS.md')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--docs',type=Path,required=True);a=p.parse_args();main(a.run,a.docs)
