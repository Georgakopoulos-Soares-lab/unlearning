# Data evidence gaps

This audit uses only the existing authorized benign manifests and preserved source qualifications; no split changes or untouched test members. Earlier task qualification (docs/experiments/ashay/extension/TASK_QUALIFICATION.md) records the GUE paper AppendixB.2 and DNABERT2 README commit f25bed9ee20db966dff39e5c1571249d04e36404. It is historical source evidence, not a newly inferred code-to-class mapping.

| Current exact identity | Supported task description | Numeric mapping / alias limitation |
|---|---|---|
| emp_H3 | Yeast histone-H3 mark prediction | Numeric0/1 verified; biological positive mapping not proven by integer IDs |
| gue_prom_300_all | Human promoter/TSS window -249,+50 | Numeric0/1; do not equate proposed “promoter4” with this alias |
| gue_prom_core_all | Human core-promoter/TSS window -34,+35 | Numeric0/1; coordinate convention from task source, not recovered sample loci |
| gue_splice_reconstructed | Reconstructed donor/acceptor/nonsplice task | Numeric0/1/2; exact code-to-biological-class map unresolved |
| gue_tf_0 | Human TF binding: ChIP peaks vs length/GC-matched negatives | Numeric0/1; wgEncodeEH000552 association is size-based only, not a verified alias map |
| gue_mouse_0 | Mouse TF binding: peaks vs dinucleotide-shuffled negatives | Numeric0/1; Ch12Nrf2Iggrab association is size-based only |

H3 uses11971train/1497dev/1497test; each other task1024train/512officialdev. H3 dev/test and other dev are exploratory reused populations. AUROC positive remains numerical class1, not an asserted biological meaning; splice remains sorted-class macroOVR. Source field definitions and independent counts/group checks are in DATA_EVIDENCE_AUDIT.json.

No source-genome, locus, homology-cluster or biological group membership is supplied by these cohort manifests. other_five group_id values are all null; exact_rc_group is a sequence-derived grouping, not biological metadata. Cross-split exact/RC overlap is zero in all6current cohorts; one within-split splice duplicate group is preserved in prior qualification. Neither zero exact overlap nor missing group columns proves independence. No fabricated homology groups or changed splits.

Exposure: both GradDiff configs point to preprocessed_emp_h3 and training_data_config_emp_h3.yaml, with no per-row identity/exposure manifest. Historical repository config at b90fc... lists H3train,validation,test prefixes with weight1 by split, not a three-task retain mixture. A listed test prefix is not proof of training on test: state do_testfalse, and consumed validation counts do not identify which rows or retain/forget shares were exposed. Actual loader revision, packing/sampling, unique rows, sequence lengths, per-stream processed tokens and any overlap with these evaluation cohorts remain unresolved. The base zero-consumed Mock conversion state is not upstream exposure proof. Collaborator parent confirmation is retained separately from missing shard-hash lineage.

The proposed incremental plan (broaden H3 with promoter/human-TF components under comparable token budgets) is a proposal. Transcript aliases “ENG H3, promoter4, humanTF0” and their proportions remain unqualified. Supplied candidate artifacts record H3 only. No causal attribution to retain diversity or algorithm is justified without actual corrected method/parent/exposure/budget records. Benign checkpoint comparison can be descriptive once checkpoint identity is unambiguous; these metadata gaps must remain visible.
