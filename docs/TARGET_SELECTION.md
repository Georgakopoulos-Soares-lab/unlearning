# Target selection — which task to unlearn

Answers [Open Work #1](RESULTS.md#1-requalify-the-target-or-pick-a-different-one). Read
before Stage 1. Provenance labels follow [RESULTS.md](RESULTS.md): `verified` = both arms
in one harness, >=3 seeds, dev-only selection.

**Headline: 27 tasks measured, 1 usable target, and the model this pipeline unlearns
(Evo-1) shows no significant excess on any task tested.**

---

## 1. Qualification: three hurdles

| # | hurdle | test |
|--:|:--|:--|
| **H1** | real excess | `excess = model − max(baselines)` > `2·√(sd²_model + sd²_base)` |
| **H2** | removal matters | `recoverability = max(baselines) / model` is low |
| **H3** | sound split | excess survives re-scoring on a homology-filtered test set |

`max(baselines)` must include a **tuned CNN**. It bound on 21 of 22 tasks; k-mer bound on
one. A k-mer-only floor is not slightly optimistic, it is wrong:

| task | k-mer | CNN | model | excess vs k-mer | excess vs max(base) |
|:--|--:|--:|--:|--:|--:|
| `splice_acceptors` | 0.398 | 0.9514 | 0.9656 | **+0.5679** | **+0.0142** (40x) |
| `human_ensembl_regulatory` | 0.389 | 0.9097 | 0.9082 | +0.5191 | **−0.0015** (sign flip) |
| `4mC A.thaliana` | 0.206 | 0.6607 | 0.6477 | +0.4416 | **−0.0130** (sign flip) |
| `NT_H3K4me3` | 0.205 | 0.5617 | 0.4830 | +0.2776 | **−0.0787** (sign flip) |
| `lncrna.g_max` | 0.143 | 0.3750 | 0.5116 | +0.3685 | +0.1366 (2.7x) |
| `iDHS-EL_DNase_I` | **0.641** | 0.5900 | 0.7054 | +0.0643 | +0.0643 (1.0x) |

On 9 of 22 tasks k-mer-only overstates excess >3x; on 10 it reports a positive excess
where the truth is negative. The CNN score is also **the floor your forget curve stops
at** — below it you are measuring model damage, not removal. One-time cost per task
(~1-2 GPU-h); never re-run during a trajectory.

---

## 2. Which tasks to use

| task | H1 | H2 | H3 | use? |
|:--|:--|:--|:--|:--|
| **`GUE_phage_fragments`** | **+0.0827, ratio 3.19** | 91.5% (marginal) | **PASS** | **YES — primary** |
| `iDHS-EL_DNase_I` | no, ratio 0.72 | 90.9% | **PASS, cleanest** | control only |
| `lncrna.g_max` | +0.0995, ratio **0.79** filtered | **73.3%** (best) | **FAIL** | demo only, caveat stated |
| `lncrna.s_bicolor` | +0.1566, ratio 2.15 | yes | untested | unverified |
| cosmetic tier ×5 | yes, ratio up to 6.10 | **no, 95.6–98.5%** | no | no |
| histone ×8 | **no, excess <= 0** | — | **no, 65–87% retrieval** | no |
| viral ×6 (ViroBench, virus_covid, HVUE) | **no, excess <= 0** | — | HVUE 91–99.9% homologous | no |
| under-powered ×4 | no, ratio < 1 | — | no | no |
| lncRNA siblings ×4 | no / leaked | — | mixed | no |

### All models on the candidate tasks

The excess is **NT-v2-500M-specific, not a property of gLMs**. Dev-selected LR, 3 seeds,
`excess` against the binding baseline, `ratio` = excess / 2·SD:

| model | phage | g_max | s_bicolor | iDHS-EL |
|:--|--:|--:|--:|--:|
| binding baseline | CNN 0.8413 | CNN 0.3653 | CNN 0.4226 | **k-mer** 0.6411 |
| **NT-v2-500M** | **+0.0783 (2.86)** | **+0.1463 (1.13)** | **+0.1566 (2.15)** | +0.0227 (0.23) |
| DNABERT-2 | −0.0192 (−0.64) | +0.0625 (0.51) | +0.0596 (0.90) | **+0.0643 (0.72)** |
| GENA-LM | **−0.1251 (−3.97)** | +0.0459 (0.33) | −0.0517 (−0.45) | +0.0221 (0.23) |
| HyenaDNA | −0.0339 (−1.22) | +0.0048 (0.04) | −0.1069 (−1.32) | −0.0461 (−0.37) |
| Evo-1 probe | in flight | in flight | in flight | **−0.5056 (−1.47)** |
| Evo-1 LoRA | in flight | in flight | in flight | −0.0767 (−0.47) |

**On `phage_fragments`, 3 of 4 gLMs lose to the tuned CNN.** Only NT-v2 is above it, and
it is the only model clearing the gate on any candidate task. On `iDHS-EL` the best model
is DNABERT-2, and there the binding baseline is k-mer rather than the CNN.

So the claim is not "genomic LMs hold erasable capability here" — it is **"NT-v2-500M
does, and three other gLMs plus Evo-1 do not."** That is a narrower and more interesting
result: it points at NT-v2's specific pretraining (multispecies, 500M) rather than at
pretraining in general, and it means any unlearning result on this target is a statement
about one model.

### `GUE_phage_fragments` — the one to use

4,000 bp fragment: bacteriophage or bacterial host? 37,044 train / 4,630 test, 50/50.

**Viral but not dual-use** — phages infect bacteria, not humans/animals/plants; phage ID
is a metagenomics tool. Safe to publish in full. **No task with a misuse pathway
qualified.**

Labels are undocumented upstream (neither GENEB nor the HF card); established by homology
against 358,825 taxonomically labelled viral sequences: label 1 hits **Caudoviricetes
115/124** at identity 1.000 / coverage 1.000 / 4,000 bp; label 0 hits **0/400**. So
**label 1 = phage, label 0 = host**. Hosts: E. coli, *Erwinia amylovora*, *Klebsiella
pneumoniae*, *Pseudomonas aeruginosa*, *Ralstonia solanacearum*.

| arm | score | seeds |
|:--|--:|--:|
| k-mer | 0.6290 | deterministic |
| swept CNN | **0.8413 ± 0.0128** | 5 |
| NT-v2-500M full FT | 0.9196 ± 0.0049 | 3 |
| DNABERT-2 / GENA-LM / HyenaDNA | 0.8221 / 0.7162 / 0.8074 — **all below the CNN** | 3 each |

No GC shortcut (0.471 vs 0.477). Caveats: recoverability **91.5%**; **no in-benchmark
replication exists** (n=1 task); negative-class provenance inferred, not documented.

### `lncrna.g_max` — demo only

lncRNA vs coding mRNA, soybean. Label direction verified by ORF structure (label 0 =
coding: ORF 305 vs 259 bp, ATG-start 0.459 vs 0.256); equal class lengths, so no length
shortcut; a 4-feature ORF baseline reaches only 0.2696, below the CNN, so the excess
survives that missing-comparator check. Fails H3 (§3). Five sibling species were run;
**only 1 of 5 replicates** (`s_bicolor` +0.1566; the rest +0.009 to +0.106, one with seed
SD 0.1996). Species-specific, not a task-family capability.

---

## 3. H3 in practice: filtered re-scoring

Re-score saved predictions on homology-filtered test subsets. No retraining. **A looser
identity threshold removes more rows, so `id>=0.7/c0.3` is the most aggressive filter.**

| filter | phage n | phage excess | ratio | g_max n | g_max excess | ratio |
|:--|--:|--:|--:|--:|--:|--:|
| official | 4630 | +0.0787 | 2.92 | 490 | +0.1463 | 1.13 |
| **id>=0.7/c0.3** | 4266 | **+0.0827** | **3.19** | **341** | **+0.0995** | **0.79** |
| id>=0.8/c0.5 | 4611 | +0.0793 | 2.92 | 387 | +0.1151 | 0.82 |
| id>=0.9/c0.5 | 4618 | +0.0792 | 2.92 | 438 | +0.1482 | 1.11 |

Phage is insensitive — the excess *grows* under the harshest filter. g_max loses 32% and
falls below the gate; filtering *raises* the CNN (0.3653→0.3813) and *lowers* the gLM
(0.5116→0.4809).

**Only 4 of 14 audited splits pass.** Exact duplicates are not the problem — homology is:

| task | exact dup | reachable >=70% | NN-lookup MCC | k-mer floor |
|:--|--:|--:|--:|--:|
| `iDHS-EL_DNase_I` | 0.00% | 1.63% | **0.0000** | 0.641 |
| `phage_fragments` | 0.00% | 7.90% | **0.0796** | 0.629 |
| `lncrna.g_max` | 0.00% | 30.41% | 0.2063 | 0.143 |
| `promoter_all` | 0.14% | 23.67% | — | 0.823 |
| `human_or_worm` | 2.49% | 19.99% | — | 0.882 |
| `NT_H3` | 0.00% | **65.73%** | **0.6851** | 0.656 |
| `NT_H3K4me2` | 0.00% | **66.80%** | — | 0.271 |

`NT_H3`: a lookup reaches **87% of the supervised ceiling**, so the histone tasks measure
retrieval as much as biology. That does not reverse the histone result below (leakage
favours the better memoriser, the CNN) but it is not a generalisation measurement.

Two published splits also fail on duplicates alone: NT-v1 `enhancers` has **100/400 test
rows verbatim in train, all one class** of a balanced 200/200 set (removing them costs
every architecture 0.17–0.21 MCC); HVUE is **91–99.9% homologous on 6/7 tasks with 0.00%
duplicates**. Use `easy-search`, not `easy-cluster` — the latter needs 90% *bidirectional*
coverage and caught **0 of 150** partial-overlap pairs.

---

## 4. Negative results

**Evo-1 — the model Stage 1/2 unlearns — has no significant excess anywhere tested.**
Every other number here is NT-v2/DNABERT-2/GENA-LM/HyenaDNA; Evo-1 was re-measured with
[`geneb_evo_lora.py`](../../genomic-capability-unlearning/scripts/track_b_viral/geneb_evo_lora.py)
(same dev carve, dev-only LR selection, 3 seeds, LoRA r16/a32):

| task | probe excess | LoRA excess |
|:--|--:|--:|
| `human_or_worm` | **−0.6559** | −0.0296 |
| `iDHS-EL_DNase_I` | **−0.5056** | −0.0767 |
| `lncrna.s_lycopersicum` | **−0.2783** | −0.0193 |
| `NT_H3` | **−0.2415** | +0.0207 (ratio **0.45**, not significant) |

Frozen probe negative on all four by −0.24 to −0.66 — and that is the regime Stage 1
localization depends on. Consistent with [RESULTS.md 5d](RESULTS.md#5d-hvue--evo--partial)
(Evo 0.8911 vs full-sequence k-mer 0.8930). Runs on `phage`, `g_max`, `s_bicolor` were
still in flight. `s_bicolor` and `g_max` sat at dev MCC ~0.000 / AUROC ~0.50 at long
context — optimisation failure, **not** a capability measurement.

**Consequence:** either port Stage 1/2 to NT-v2-500M, where excesses exist, or re-scope
to "no removable capability found on this model". Do not localize on a target whose
excess was measured on a different model.

**Viral capabilities have nothing to remove.** ViroBench −0.061 (−0.209 at matched 3.1 kb
context, −0.051 at 20 kb), `virus_covid` −0.049, HVUE Pathogenecity −0.038…−0.095. Only
positive: HVUE Host_Tropism strict +0.058 on **96** clean rows.

**Histone: a swept CNN beats all four gLMs on 8 of 9** (NT-v2 0/9, DNABERT-2 1/9, GENA-LM
0/9, HyenaDNA 0/9; mean −0.049 to −0.162). Reproduction check: our NT-v2 matches published
NT-MS-500M (+0.0005), DNABERT-2 exceeds published (+0.048), our CNN sits 0.025 below a
plain published WideResNet — so the CNN result is a lower bound. GENA-LM underperforms its
own published number by 0.065; treat GENA-LM-specific claims as provisional.

**The cosmetic tier is real but useless.** promoter_all +0.0312 (ratio 6.10, 96.7%
recoverable), coding_vs_intergenomic +0.0244 (97.3%), human_or_worm +0.0208 (97.8%),
splice_acceptors +0.0142 (98.5%), H3K36me3 +0.0292 (95.6%). All three high-ratio tasks
have a raw GC gap doing the work (0.545/0.612, 0.538/0.402, 0.355/0.388).

**H1 and H2 trade off.** Large excess only occurs where baselines are weak; weak baselines
mean hard, small, noisy tasks. So precise measurements tend to be worthless targets and
valuable targets tend to be imprecise.

---

## 5. Pipeline

Steps 1–2 are cheap and **must** precede model training; reversing the order is how
targets get manufactured.

```bash
# 1. Split audit. A published split is not a clean split.
python phase2/audit_split_homology.py --benchmark-manifest data/manifest.csv \
    --out-json results/split_audit.json --composition-floor <task k-mer> --fail-on-leak

# 2. Baselines -- BOTH. Save predictions; H3 needs them.
python phase2/eval_kmer_baseline.py   --benchmark-manifest data/manifest.csv \
    --out-csv results/kmer.csv
python phase2/baseline_cnn_ceiling.py --benchmark-manifest data/manifest.csv \
    --out-csv results/cnn.csv --refit-seeds 3 --predictions-dir results/preds

# 3. Model arm (save predictions), then the gate.
python phase2/score_target_qualification.py --scores-csv results/arms.csv \
    --out-csv results/qualification.csv

# 4. H3: re-score every arm on the homology-filtered subset. No retraining.
python phase2/rescore_filtered.py --prediction-index results/preds/index.csv \
    --mask "phage:id>=0.7/c0.3:results/hits_id70.m8" \
    --mask "phage:id>=0.9/c0.5:results/hits_id90.m8" \
    --out-csv results/rescored.csv
```

`score_target_qualification.py` prints a **per-model** breakdown against the single
binding baseline whenever more than one model arm is present. Read it: on
`phage_fragments` the winner is +0.0783 while three other gLMs are *below* the CNN, and
reporting only the winner would have implied a class-level result.

CNN search must sweep **kernel size and dilation base**, not just capacity: on 600 bp
splice a ResNet at 9.44M params / 89 bp RF scores 0.336 while a U-Net at 0.26M / global RF
scores 0.951 — **+0.62 MCC at 36x fewer parameters**. Report >=3 seeds and check early
stopping is not truncating them: on phage a patience-6 3-seed refit read 0.8185 ± 0.0533
and **failed** the gate; a converged 5-seed refit read 0.8413 ± 0.0128 and **passed**.

---

## 6. Running a PoC

A PoC on a validated non-hazardous target is publishable. Scope statement: *the method
removes a capability that is model-specific; it is untested on hazardous capabilities
because none with removable excess could be found.*

**Blocker: your damage budget exceeds your target.** [RESULTS.md](RESULTS.md) records best
forgetting at **0.144 GUE AUROC** collateral; the entire removable target is
**+0.08 to +0.15**. Under those conditions a PoC cannot separate "removed the capability"
from "broke the model" — what the `random` non-causal-layer control exists to detect.

1. Lead with `probe_nullspace` — training-free, best selection score already recorded.
2. Success = model falls to `max(baselines)`, not to zero. Below that floor is
   over-removal.
3. Seed-SD gating is inadequate at this effect size; paired-bootstrap over predictions.

---

## 7. Protein models

Same doctrine, different comparators. Use the existing qualification scripts
([phistruct](../phase2/phistruct_qualification.py),
[proteingym](../phase2/proteingym_esm2_qualification.py),
[evomil](../phase2/evomil_esm1b_qualification.py),
[vpf](../phase2/vpf_plm_qualification.py)) plus:

**MSA depth is a hard gate.** 6 of 15 viral ProteinGym MSAs are degenerate below 0.2 bits
per-column entropy — R1AB_SARS2 0.002, **SPIKE_SARS2 0.012**, RDRP_I33A0 0.030, 3x
influenza 0.029–0.078, NRAM_I33A0 0.164. Five more are thin (Neff/N < 0.10). Only three
are healthy. On the degenerate six, conservation is meaningless **and** ESM is at chance
(0.541 vs conservation 0.686 on SPIKE_SARS2), so excess is **undefined, not zero**. Report
per-assay with an Neff column; never aggregate. This concentrates on outbreak pathogens.

**Split scheme decides the conclusion:** ESM-2 beats controls 12/15 modulo, 5/15
contiguous. Pre-declare it.

**Do not compare across assays.** Conservation AUROC on a binding DMS vs a published
escape AUROC is a different phenotype, label and metric. We made this error.

---

## 8. Dead ends — do not redo

| hypothesis | killed by |
|:--|:--|
| advantage lives in the 70–90% homology band | replicated on 1 of 13 tasks |
| pretraining buys data efficiency; excess decays with n | 1 decay, 5 rise, 7 flat; mean Spearman **+0.380** |
| a Markov model beats Evo at viral generation | 84%-influenza artifact; 1.2576 → **1.9560** bits/base when family-balanced |
| conservation beats pLMs 14/16 assays | MSA degeneracy (§7) — the pLM is at chance, not conservation strong |
| excess predicted by task compositionality | Spearman −0.511, **fails Bonferroni**; coefficient sign-flips on removing one task |
| leakage inflates the gLM advantage | direction is task-dependent: exact-duplicate removal *grew* NT-v2's enhancers margin +0.056→+0.080, but homology filtering *shrank* g_max's +0.1463→+0.0995 |

Every mechanism-level hypothesis in this project died; every descriptive measurement held.
