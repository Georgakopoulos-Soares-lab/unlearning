"""Evidence-only GradDiff qualification; no weights, inference, training or test discovery."""
from pathlib import Path
import json,hashlib,collections,time,datetime,subprocess,csv
R=Path('/workspace/meeting-artifacts/benign-graddiff-qualification-v1');OLD=Path('/workspace/meeting-artifacts/multiretain-layers-v1');D=Path('/workspace/wt-benign-followup/docs/experiments/ashay/graddiff-qualification-v1')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 start=time.monotonic();cpu=time.process_time();D.mkdir(parents=True,exist_ok=True);table=[]
 for group in ['H3','other_five']:
  p=OLD/'manifests'/(group+'.jsonl');rows=[json.loads(x) for x in p.read_text().splitlines()]
  for task in sorted({r['task'] for r in rows}):
   rr=[r for r in rows if r['task']==task];by={s:{r['exact_rc_group'] for r in rr if r['split']==s} for s in {r['split'] for r in rr}};counts=collections.Counter(r['split'] for r in rr);labels=sorted({r['label'] for r in rr});overlap={a+'/'+b:len(by[a]&by[b]) for a in by for b in by if a<b};assert not any(overlap.values());assert labels==([0,1,2] if 'splice' in task else [0,1]);explicitgroups=sum(r.get('group_id') is not None for r in rr)
   table.append(dict(task=task,manifest=str(p),manifest_sha256=sha(p),counts=dict(counts),labels=labels,biological_group_rows=explicitgroups,exact_rc_cross_split_overlap=overlap,fields=sorted(set().union(*(set(r) for r in rr)))))
 assert len(table)==6
 candidates=[dict(name='original',iteration_folder='1b9MrHwGulAVDayu3UvCsSiSYpvkNTLC5',shard_id='1oBQiCUpr-MxIKLtbigdzwO4gXk_Qktbf',config_id='15aoYOQA9g10NRZHcLPdnCpc1eAzzqE1U',config_sha256='22e5b44e7107b72e1f6ec7cdee050acbf927d26932d35647075df3f91614f645',learning_rate=1e-5),dict(name='v2',iteration_folder='11qL_Sz5vVpMmRUZeoaZWol4VwsCLc7UP',shard_id='1yXV12bpH2nb6It2fobGZlDofnMrJRmJh',config_id='1N7gdktjwSiI3kz3_E_Eywoz5Ivaxw5cX',config_sha256='62d1e10e446e306e182cdc02f9a4bb38683cb0946a420b4af1bb0455a030fae3',learning_rate=1e-4)]
 for c in candidates:c.update(status='DEFERRED_AMBIGUOUS_INTENDED_CHECKPOINT',iteration=1000,shard_bytes=15516878934,shard_sha256=None,shard_hash_reason='Not downloaded; provider metadata did not return requested hashes',train_state_sha256='5ba9c56284f31a8d8ca829d56da8ff7752e78d1d2527ac63b70c282b8d70c95f',tokenizer_sha256='d8b5392d4795e3011b648b7e79a1e2f563cfa508200196d30d6dcbb0292d0803',consumed_train_samples=128000,consumed_valid_samples=898560,recorded_parent='/projects/MENTISLab/unlearning/checkpoints/evo2_1b_base_mbridge',retain='training_data_config_emp_h3.yaml / preprocessed_emp_h3',method_evidence='GradDiffDualDatasetProvider in serialized config; exact executed objective revision/coefficients/cap not pinned',architecture='Hyena1bModelProvider,25blocks,1920hidden,vocab512,BF16,torch_dist',strict_loading='NOT_ATTEMPTED; weight completeness/distinctness and native strict loading not established',selection_confirmation=None)
 registry=dict(status='QUALIFICATION_COMPLETE_EVALUATION_DEFERRED',candidates=candidates,base_correction='1n1ZfbP_OOucoEQhsuk5PsKeKMJu0ZYzj is base_mbridge, step1/consumed_train0, Mock provider/null paths, config b648cfd2fb11797ade835e82f6dd4c3e7abd0d4256ae4360bd67796d00f198c9; not combined retain',multi_retain='DEFERRED_NOT_IDENTIFIED',noise='No qualified supplied candidate identified in inspected metadata; not proof none exists',eligible_checkpoint_selected=None)
 (R/'CHECKPOINT_REGISTRY_V9.json').write_text(json.dumps(registry,indent=2));(R/'DATA_EVIDENCE_AUDIT.json').write_text(json.dumps(table,indent=2))
 text='''# Checkpoint eligibility — benign GradDiff follow-up

Status: metadata audit complete; GradDiff evaluation **deferred pending intended-checkpoint identification**. No weights downloaded, GPU inference or new fits. Completed base/MaxEnt caches and matched controls remain unchanged. This explicitly restores the original pretrained-versus-GradDiff question: MaxEnt results are not GradDiff results.

| Candidate | Iteration folder ID | Shard ID | Bytes | LR | Config SHA256 |
|---|---|---|---:|---:|---|
'''
 for c in candidates:text+=f"| {c['name']} | {c['iteration_folder']} | {c['shard_id']} | {c['shard_bytes']} | {c['learning_rate']} | {c['config_sha256']} |\n"
 text+='''
Both configs declare Hyena1bModelProvider/25blocks/1920hidden/vocab512, BF16 and torch_dist. Both tokenizers downloaded (10,649bytes each) hash d8b5392d4795e3011b648b7e79a1e2f563cfa508200196d30d6dcbb0292d0803, matching the qualified MaxEnt tokenizer. A valid native fixed-physical8 route exists in the completed project, but no candidate weights have passed strict loading or the unchanged training-only numerical/masking/repeatability gate. Folder listing of a single shard is not proof of completeness/loadability; equal sizes do not prove equal weights. Provider metadata did not return requested shard checksums. These are explicitly unknown, not invented.

The two train_state.pt files are byte-identical (3,461bytes, SHA2565ba9c56284f31a8d8ca829d56da8ff7752e78d1d2527ac63b70c282b8d70c95f). Safe CPU weights_only loading records step1000, consumed_train_samples128000, consumed_valid_samples898560, skipped0, do_testfalse. Separate progress logs identify jobs11293002 (Oct22) and11313850 (Oct23), each reporting0.13 billion tokens (rounded operational accounting, not an exact retain-token/exposure manifest). Their config differences are LR/minLR and logging/load/save paths; neither says which checkpoint corrects the reported mistakes. No score-based candidate selection occurred.

Both configs contain GradDiffDualDatasetProvider and explicit H3-only retain config/data paths, not a combined mixture. They record base_mbridge as pretrained_checkpoint by path, without parent-shard hashes/conversion revision or a checkpoint-bound objective implementation revision. The current bionemo branch snapshot b90fc1853d1d3be79922a98a2649c91c89716637 has an Evo2 GradDiff forward implementation and custom objective fields; it is reference code, not proof that either checkpoint executed it. Those extra objective fields are absent from the saved configs, whose model forward_step_fn is the standard hyena route; the actual supplied training invocation/custom callback needs provenance. No intervention code was executed. Evo-1 implementation/results were not transplanted.

Historical benign head config (Drive1SQtOb3npKroFN8Mt8PVZkx92mLv9YrOM) is a two-class Hyena1bClassifierProvider and references the original GradDiff path. It identifies a historical readout source but does not resolve whether that backbone is the corrected intended delivery. Its51,806,899byte classifier shard was not treated as a full backbone or loaded. Hazardous evaluation contents were not read.

Base correction independently checked: folder1n1ZfbP_OOucoEQhsuk5PsKeKMJu0ZYzj is evo2_1b_base_mbridge; latest state step1/consumed_train_samples0. Its config hash b648cfd2fb11797ade835e82f6dd4c3e7abd0d4256ae4360bd67796d00f198c9 declares MockEvo2DatasetProvider with null paths. It is not multi-retain evidence. A zero-consumed conversion state does not prove no upstream pretraining.

Root/results metadata was refreshed, including the two GradDiff runs, base, MaxEnt and benign official classifier directories. No qualified combined-retain or supplied-noise arm was identified. LoRA/training directories were not promoted to eligible noise or combined-retain checkpoints. This is a statement about inspected evidence, not global absence.

Next gate after a precise identity answer: freeze chosen exact shard/config/tokenizer and method metadata; download/hash shards; strict native loading; unchanged fixed8 training-only smoke; H3 first then remaining five cohorts,26representations/3CVseeds/refit+fixed-base, reuse all compatible completed base/MaxEnt caches, separate causal LM accounting and full saved-output audits. GPU authorization is uncapped within scope but usage is0 seconds here. No speculative training infrastructure was built.
'''
 (D/'CHECKPOINT_ELIGIBILITY.md').write_text(text)
 request='''Unsent checkpoint-identification request (do not send automatically): Which is the corrected intended Evo2 GradDiff checkpoint for the benign comparison: original iter1000 shard1oBQiCUpr-MxIKLtbigdzwO4gXk_Qktbf (LR1e-5, folder1b9MrHwGulAVDayu3UvCsSiSYpvkNTLC5), or v2 iter1000 shard1yXV12bpH2nb6It2fobGZlDofnMrJRmJh (LR1e-4, folder11qL_Sz5vVpMmRUZeoaZWol4VwsCLc7UP), or a replacement? Please identify the exact corrected shard/hash and executed code revision/launch objective settings, with its parent/retain exposure record; both existing configs currently name H3-only retention.\n'''
 (D/'UNSENT_REQUEST.md').write_text(request)
 data='''# Data evidence gaps

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
'''
 (D/'DATA_EVIDENCE_GAPS.md').write_text(data)
 files={str(p.relative_to(R)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in R.rglob('*') if p.is_file()}
 (R/'EVIDENCE_INDEX.json').write_text(json.dumps(files,indent=2))
 status=dict(status='COMPLETE',evaluation_status='DEFERRED_AMBIGUOUS_CHECKPOINT',GPU_seconds=0,new_fits=0,metadata_audit_cpu_seconds=time.process_time()-cpu,metadata_audit_wall_seconds=time.monotonic()-start,accounting_scope='This CPU audit execution only; connector inspection/setup timing not exhaustively instrumented',completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),no_untouched_test_access=True)
 (R/'AUDIT_COMPLETE.json').write_text(json.dumps(status,indent=2))
 for name in ['CHECKPOINT_REGISTRY_V9.json','DATA_EVIDENCE_AUDIT.json','AUDIT_COMPLETE.json','EVIDENCE_INDEX.json']:(D/name).write_bytes((R/name).read_bytes())
 print(json.dumps(status))
if __name__=='__main__':main()
