"""Build meeting tables directly from saved outputs, never extrapolate missing cells."""
import csv
import json
from pathlib import Path
import shutil

RUN=Path('/workspace/meeting-artifacts/evo2-extension-20261021T0942')
DOC=Path('docs/experiments/ashay/extension')

def load(p):return json.loads(p.read_text())

def main():
    tasks=load(RUN/'config.json')['tasks'];lines=['# Evo2 frozen benign extension: meeting results','','Expanded protocol: 1024 official train / 512 official dev examples per GUE task. Selection: five fixed grouped training-only CV folds; balanced L2 logistic regression, fold-local scaling, C=.1/1/10. AUROC uses numeric class1 for binary tasks and macro OVR for splice. No untouched test data.','', '| Task | Evidence | Composition | 4-mer | Block7 | Block15 | Final RMSNorm | Dev NLL | Dev perplexity |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
    table=[];contrasts=[]
    for task in tasks:
        matched=RUN/'expanded_matched'/task/'metrics.json';cpu=RUN/'expanded_cpu'/task/'metrics.json';gpu=RUN/task/'extraction_complete.json'
        m=load(matched) if matched.exists() else load(cpu) if cpu.exists() else {};g=load(gpu) if gpu.exists() else None
        status='NEW_GPU_COMPLETE + NEW_CPU_COMPLETE' if g and matched.exists() else 'NEW_CPU_COMPLETE; GPU NOT_RUN'
        values=[f"{m[k]['auroc']:.4f}" if k in m else 'NOT_RUN' for k in ['composition','4mer','blocks.7','blocks.15','norm']]
        nll=g['nll']['validation'] if g else {}
        lines.append('| '+ ' | '.join([task,status,*values,f"{nll['corpus_nll']:.6f}" if nll else 'NOT_RUN',f"{nll['perplexity']:.6f}" if nll else 'NOT_RUN'])+' |')
        for method,result in m.items():table.append(dict(task=task,method=method,status=status,**{k:result[k] for k in ['auroc','accuracy','balanced_accuracy','mcc','C','converged']}))
        p=matched.parent/'contrasts.json'
        if p.exists():
            for name,v in load(p).items():contrasts.append(dict(task=task,contrast=name,**v))
    if (RUN/'anchor.json').exists():
        a=load(RUN/'anchor.json');lines+=['','Historical identity anchors: '+str(len(a['anchors']))+' examples; all passed='+str(a['all_passed'])+'. Every original layer feature and per-example NLL delta was exactly zero. This checks six selected anchors, not independent regeneration of all historical features.']
    lines+=['','## Counts and causal likelihood','','| Task | Train/dev class counts | Train/dev targets | Train NLL | Dev NLL | Train perplexity | Dev perplexity |','|---|---|---|---:|---:|---:|---:|']
    for task in tasks:
        counts=RUN/'expanded_cpu'/task/'counts.json';gpu=RUN/task/'extraction_complete.json'
        c=load(counts) if counts.exists() else {}
        if gpu.exists():
            g=load(gpu)['nll'];a=g['train'];b=g['validation']
            lines.append(f"| {task} | {c.get('train_classes')}/{c.get('dev_classes')} | {a['n_tokens']}/{b['n_tokens']} | {a['corpus_nll']:.6f} | {b['corpus_nll']:.6f} | {a['perplexity']:.6f} | {b['perplexity']:.6f} |")
        else:lines.append(f"| {task} | {c.get('train_classes')}/{c.get('dev_classes')} | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN | NOT_RUN |")
    lines+=['','## Primary paired dev contrasts','','Block7 minus 4-mer AUROC, 2000 paired bootstrap replicates. Intervals are pointwise exploratory and conditional on fitted models, exclude fitting/selection uncertainty and simultaneous coverage. Exact/RC duplicate groups used; no biological groups supplied. Unknown dependence remains. Missing-class resamples excluded and counted in saved contrasts.json.','','| Task | Difference | 95% interval |','|---|---:|---|']
    for r in contrasts:
        if r['contrast']=='blocks.7 minus 4mer':lines.append(f"| {r['task']} | {r['difference']:+.4f} | [{r['low']:+.4f}, {r['high']:+.4f}] |")
    lines+=['','## Cached historical-row comparison','','NEW_CPU_COMPLETE: both saved representations refit under NEW training-only selection. These rows/features inherit original manifest-order/producer/provenance association, since old arrays lack embedded IDs. This is not GPU reproduction. Original dev-selected scores are preserved separately.','','| Task (256/128) | Composition | 4-mer | Block7 | Block15 | Block7–4mer interval |','|---|---:|---:|---:|---:|---|']
    for p in sorted((RUN/'cached_cpu').glob('*/metrics.json')):
        m=load(p);c=load(p.parent/'contrasts.json')['blocks.7 minus 4mer']
        lines.append('| '+ ' | '.join([p.parent.name,*[f"{m[k]['auroc']:.4f}" for k in ['composition','4mer','blocks.7','blocks.15']],f"{c['difference']:+.4f} [{c['low']:+.4f}, {c['high']:+.4f}]"])+' |')
    # Preserve every matched-C result rather than claiming separate replications.
    historical=list(csv.DictReader((Path('/workspace/meeting-artifacts/evo2-20261020T1437')/'baseline_probe_results.csv').open()))
    sensitivity=[]
    for task in sorted(set(r['task'] for r in historical)):
        for c in [.1,1.,10.]:
            values={r['layer']:float(r['validation_auroc']) for r in historical if r['task']==task and float(r['C'])==c}
            sensitivity.append(dict(task=task,C=c,block7=values['blocks.7'],block15=values['blocks.15'],difference=values['blocks.7']-values['blocks.15']))
    lines+=['','## Evidence and interpretation','','HISTORICAL_REUSED: original three-task NLL and dev-selected probe evidence remains unchanged. The historical C-grid has block7 > block15 at all three C values for each of the three tasks (nine correlated comparisons, not independent replications); see historical_c_sensitivity.csv.','','The cached-row matched comparison shows a small uncertain block7 advantage over 4-mer on H3, and larger positive advantages on promoter and splice. Block7-minus-block15 cached intervals include zero on all three tasks; the direction alone does not establish a reliable layer advantage. 4-mer underperforms composition on cached splice, so a more elaborate simple feature is not uniformly better. The one fixed shuffled-training-label diagnostic repeats selection; it is a sanity check, not a formal test. H3 composition gave a suspiciously high 0.8112 shuffled-label dev AUROC despite shuffled-label mean CV 0.4483. The investigation independently reproduced that fit using only the same shuffled train labels (52.34% agreement with originals), recorded small coefficients, and found 0.9304 probability correlation with the ordinary composition fit. This is consistent with chance alignment to a low-dimensional composition signal, not proof of leakage or its absence. No alternative seed was searched; shuffled labels/model and investigation are saved. Full metrics include chosen C, every fold/candidate AUROC, convergence warnings, class counts, fixed-threshold accuracy/balanced accuracy/MCC, fitted pipelines and ID-aligned dev probabilities.','','All original 256/128 rows are included in their corresponding expanded subsets. Differences in sample size or selection policy are not model effects. Numeric biological class mappings and tf/0/mouse/0 exact experiment aliases remain unverified; see TASK_QUALIFICATION.md. Source task definitions are known, but no biological meaning is inferred from integer IDs. No biological groups/homology independence is established. Cross-task NLL does not rank task capability. Simple controls outperforming a probe would not establish no model information, biological mechanism, or leakage.','','## Explicit outstanding work','','| Requested item | Status |','|---|---|','| vGUE viral genome identification | BLOCKED: labeled immutable task table, source/group/split/license metadata and full-genome protocol missing |','| vGUE viral-read identification | BLOCKED: labeled read/source-genome manifest, generation/split/license metadata missing |','| Corrected GradDiff comparison | BLOCKED: immutable corrected checkpoint, parent/loader/tokenizer/conversion/exposure handoff absent |','','Aris Step1 is incomplete while viral tasks remain blocked. No GradDiff/unlearning or hazardous-knowledge removal result is claimed. Broader retain training is NOT_RUN and requires a subsequent team decision.','','Next recommended experiment: obtain the corrected checkpoint handoff and exposure manifests; establish compatible base/post backend and evaluate both fixed base probes and separately train-CV-refitted probes on these same eligible rows, with paired token-weighted NLL and AUROC changes. Team questions: exact viral identification dataset tables/source groups and genome protocol; authoritative numeric class map and TF aliases; corrected checkpoint owner/iteration; qualified training exposure; agreed preservation margins.','','## Verbal update (not sent)','','We added train-only matched controls to the old pilot and expanded the six benign GUE tasks. The old-row results show that the probe advantage depends on the task: it is uncertain for H3 and clearer for promoter and splice; layer differences remain uncertain. These are exploratory official-dev measurements, with reused examples and incomplete biological grouping. Viral identification is still blocked on qualified data, and the corrected GradDiff checkpoint handoff is still needed. No unlearning claim is supported.','','Artifact root: '+str(RUN)+'. CPU source timing limitations are recorded in cpu_execution_identity.json; later delivery commits must not be relabeled as execution. Saved figures: baseline_controls.png, paired_differences.png and cached_paired_differences.png. Complete predictions/probes/CV scores are in expanded_matched/<task>; per-example likelihoods and identity-bearing features are in <task>. Source hashes and execution revision: extraction_identity.json when GPU extraction exists; later documentation commits are separate. Prompt receipt pins v5.txt at d158a3666c72a212c6c1cbc5b9c264f3c6dd3687, SHA256 0688904d96748076127f5ad9842cc35ca7ad39a4ebfc6fcdae1fbbda8c7c3ad4. Old HF backup remains verified; NEW supplement status belongs in backup_receipt.json and must not be confused with it.']
    text='\n'.join(lines)+'\n';(DOC/'MEETING_RESULTS.md').write_text(text);(RUN/'MEETING_RESULTS.md').write_text(text)
    for name,rows in [('classification_metrics.csv',table),('paired_contrasts.csv',contrasts),('historical_c_sensitivity.csv',sensitivity)]:
        if rows:
            for target in [RUN/name,DOC/name]:
                with target.open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    # Original-grid source values copied unchanged, separate from CV refits.
    (RUN/'SPOKEN_UPDATE.txt').write_text(lines[-4] if False else 'See MEETING_RESULTS.md verbal update; no message sent.\n')
    if table:
        import matplotlib;matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        methods=['composition','4mer','blocks.7','blocks.15','norm'];tasklist=list(tasks)
        fig,ax=plt.subplots(figsize=(11,5));import numpy as np
        for j,method in enumerate(methods):
            vals=[next((r['auroc'] for r in table if r['task']==t and r['method']==method),float('nan')) for t in tasklist]
            ax.bar(np.arange(len(tasklist))+(j-2)*.15,vals,width=.15,label=method)
        ax.set_xticks(np.arange(len(tasklist)),[t.removeprefix('gue_') for t in tasklist],rotation=20);ax.set_ylabel('Official-dev AUROC');ax.set_ylim(0,1);ax.legend(ncol=5);ax.set_title('Frozen Evo2 and matched controls: training-only CV selection');fig.tight_layout();fig.savefig(RUN/'baseline_controls.png',dpi=180);plt.close(fig)
        primary=[r for r in contrasts if r['contrast']=='blocks.7 minus 4mer']
        if primary:
            fig,ax=plt.subplots(figsize=(9,4));x=np.arange(len(primary));v=np.array([r['difference'] for r in primary]);lo=np.array([r['low'] for r in primary]);hi=np.array([r['high'] for r in primary]);ax.errorbar(x,v,yerr=[v-lo,hi-v],fmt='o',capsize=4);ax.axhline(0,color='gray');ax.set_xticks(x,[r['task'].removeprefix('gue_') for r in primary],rotation=20);ax.set_ylabel('Block7 minus 4-mer AUROC');ax.set_title('Pointwise exploratory 95% paired intervals; fitted models fixed');fig.tight_layout();fig.savefig(RUN/'paired_differences.png',dpi=180);plt.close(fig)

if __name__=='__main__':main()
