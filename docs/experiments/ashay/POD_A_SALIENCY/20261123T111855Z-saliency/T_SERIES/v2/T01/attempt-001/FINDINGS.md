# Supplied Drive inventory and future-use audit

**The supplied folder contains checkpoints and forget-related logs, but this review identified only configuration references to the forget dataset; no actual forget-data payload was identified.** The same applies to retain data. Nine large checkpoint containers remain uninspected, so this is not a proof that their opaque contents contain no data.

## Scope and observed inventory

Root: [saliency_sweep](https://drive.google.com/drive/folders/1axy9YloRhDgylh_PkKYHTYnZF6wMZaM9). Observed 2026-11-25T08:24:46.263Z through 2026-11-25T08:30:56.836Z. This is a time-bounded observed inventory, not an atomic snapshot. All 43 folders have terminal provider pages; 148 unique objects comprise 105 files and 43 folders. Ten end-window rechecks found no change in the reviewed root/endpoint-child metadata. No shortcuts, pagination errors, cycles or repeated tokens occurred.

Even exhausted accessible listings cannot rule out files hidden from the authenticated account.

| Artifact | Unique objects | Interpretation |
|---|---:|---|
| Actual forget payload identified | 0 | References only; no uploaded-payload manifest |
| Actual retain payload identified | 0 | References only; no uploaded-payload manifest |
| Mixed/unknown dataset payload candidate identified | 0 | Nine model containers remain opaque; do not infer a full content count |
| Run configurations with dataset references | 9 | Each documents forget and retain roles as producer paths |
| Model shard containers | 9 | Each 15,516,878,934 bytes; model-index filename bindings, not current-byte audits |
| Event logs | 9 | Corrected S10 extraction inherited; scientifically unqualified |
| Training/common state containers | 26 | 17 train-state and 9 common ZIPs structurally inspected without unpickling |
| Checkpoint storage indexes | 9 | Model storage indexes, not dataset manifests |
| Other configurations | 18 | 9 checkpoint-backend and 9 tokenizer configurations |
| Tokenizer model assets | 9 | WordLevel model/vocabulary schema, not dataset rows |
| Progress and latest-step documents | 16 | 8 each; not scientific aggregate results |
| Standalone aggregate result/report/code or generic archive files | 0 | Logs still contain source observations; those are not absent |
| Folders | 43 | Source organization preserved |

The current roster of 148 stable IDs equals historical S01, with no added or missing IDs. Fresh exhausted accessible listing is a new observation; S01/S10/S11 receipts remain unchanged. All nine known endpoint folders and current config hashes match the frozen endpoint roster. This does not establish the original assignment’s exhaustive intended inventory.

## Dataset references and their resolution

All nine run configs have the same four producer-host target references. They do not contain an uploaded dataset object ID or a payload-membership manifest. Their declared provider class name does not prove the implemented objective. Each exact source/key and every occurrence is recorded in [DATASET_REFERENCE_MAP.csv](DATASET_REFERENCE_MAP.csv).

| Documented role | Reference | Exact current-Pod check |
|---|---|---|
| RETAIN | `/projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_h3_fasta_splits/preprocessed_emp_h3` | NOT_PRESENT_AT_EXACT_PATH_ON_CURRENT_POD |
| FORGET | `/projects/MENTISLab/unlearning/data/evo2/HVUE_v2/preprocessed_hvue_human_host_tropism` | NOT_PRESENT_AT_EXACT_PATH_ON_CURRENT_POD |
| FORGET | `/projects/MENTISLab/unlearning/evo2_unlearn_pipeline/forget_data_config.yaml` | NOT_PRESENT_AT_EXACT_PATH_ON_CURRENT_POD |
| RETAIN | `/projects/MENTISLab/unlearning/evo2_unlearn_pipeline/training_data_config_emp_h3.yaml` | NOT_PRESENT_AT_EXACT_PATH_ON_CURRENT_POD |

A missing exact path on this Pod says nothing about that path on the producer’s machine. No biological payload rows, splits or labels were inspected, constructed or evaluated. Dataset byte readability and scientific suitability remain untested. No external dataset Drive/repository target was linked by the reviewed dataset declarations; none was crawled.

Decisive examples: [candidate06 config](https://drive.google.com/file/d/1jlXGtSzAPA2yO0AopTo9T3tBPNJMA87V/view), [candidate01 config](https://drive.google.com/file/d/1Fdkz67Q9l_tvUnf_SyfjIW4-wDbMqPpp/view), [noise5 step2000 config](https://drive.google.com/file/d/177xFYrj7E-mFasbHYQUh6JJYmBzKvrvB/view), [noise5 step2151 config](https://drive.google.com/file/d/1UqzaMQMZpgiWaFLs-7teepf81WACESEd/view). The two noise5 configs have equal bytes while their checkpoint content identities remain distinct. Both reinit5 histories and duplicated step1500 observations remain preserved in corrected S10.

## What verification means here

Evidence levels describe the basis of a classification, not confidence probabilities:

| Evidence level | Meaning |
|---|---|
| NAME_ONLY | A filename proposes a classification; role and contents are unverified. |
| METADATA_SUPPORTED | Provider metadata or inspected structural schema supports the artifact classification. |
| DOCUMENTED_ROLE | An exact documentary source explicitly assigns the role or context; payload membership and scientific suitability remain separate. |
| IDENTITY_BOUND_TO_MANIFEST | An inspected index binds a named member to the observed object. For the large shards here, this is a storage-filename/sibling-object-ID binding, not a newly verified shard checksum. |
| CONFLICTED | Available sources disagree on the proposed classification or role. |
| UNRESOLVED | The available evidence cannot support a classification or role. |

Verified here: complete accessible direct-child pagination; stable-ID/path/parent-edge accounting; exact bytes/SHA256 for87 small non-sequence files totaling2,099,503 bytes; explicit documentary role review of every config; inert ZIP-member and pickle-opcode inspection; model-storage filename-to-object bindings; reference/path checks; current-versus-historical roster/config reconciliation. Provider checksum/revision/version fields were not exposed and remain null. Provider MD5 was never relabeled SHA256.

Not verified here: raw biological contents, actual dataset byte access, producing biological cohort correctness, scientific metric semantics, checkpoint invocation bindings, new uncertainty/comparison eligibility, current large-shard bytes or member lists, model replay, clean-runtime recreation, recovery, external delivery or collaborator acceptance. Corrected S10’s nine-log extraction and existing retain scientific release are inherited, not rerun.

87 small files were read as52 non-sequence text/JSON/YAML assets,26 small ZIP state containers and9 inert pickle storage indexes. No pickle/torch object deserialization, imported repository code, new model execution, event decoding or large model shard transfer occurred. A ZIP member list identifies structure only, not the truth of every serialized field.

## Future-use boundaries

| Stage | Usable now under later stage authorization | Still unestablished |
|---|---|---|
| T02 | Nine config source hashes,36 reference occurrences/four targets, exact documentary keys | Actual cohort/version/preprocessing/split identities or dataset presence |
| T03 | Nine endpoint folders,9storage indexes,26state structures and exact log/config IDs | Exact invocation/content association from equal steps, names or folders |
| T04 | Declared provider/settings and original-tag source references | Producing implementation, scientific loss semantics and actual denominator |
| T05 | Deduplicated missing-payload/manifest/binding requests and T00 dependencies | A sent message, confirmed owner or collaborator agreement |
| T06–T09 | Version-bound source candidates and explicit missingness | Scientific admission or passing those stages in advance |
| T12–T13 | Existing released retain tables/atlas and corrected source-only log traces | New qualified forget results, selective unlearning or original completion |
| T15–T16 | Exact source locators, byte/version limits and access dependencies | Fresh recovery, delivery or scientific closure |

The [future-use matrix](FUTURE_USE_MATRIX.csv) covers every catalog item, source-only log reuse, later candidate qualification and the separate inherited retain release. No generic READY state is used. Raw dataset evaluation/training/optimization is NOT_ASSESSED_BY_THIS_AUDIT. Finding a dataset later will not promote scientific status automatically.

## Next actions and unresolved scope

- **No identified delivered forget/retain payload or payload manifest:** Obtain exact aggregate cohort/dataset manifest identities and documented payload locator from producing team; no raw data transfer requested. Boundary: T02/T05.
- **Nine large model containers uninspected:** Use existing trustworthy model manifest or producer-generated member/index sidecar if a stronger content-absence claim is needed; do not download139GB to classify. Boundary: T03 metadata scope only.
- **Exact scientific log/checkpoint/cohort/metric binding absent:** Preserve existing logs; obtain invocation/content and producing-implementation/denominator metadata per existing dependency register. Boundary: T03/T04/T05 then separately authorized T06/T07.
- **Original requested inventory boundary unknown:** Obtain attributed scope/exhaustiveness statement; accessible enumeration does not substitute for original assignment definition. Boundary: T05 coordination.
- **Future scientific layerwise coverage:** Request genuine existing qualified aggregate records or explicit nonexistence confirmation; no raw evaluation automatically authorized. Boundary: T05–T08 after separate authorization.

Keep the [sealed T00 register](../../CONTINUATION_REGISTER.json) unchanged. [T01_ADDITION.json](T01_ADDITION.json) records current evidence and scoped dependency updates without treating accessible listing exhaustion as original requested-scope completion. Later T06–T09 must retain the versioned S10/S11 future-intake gates. R2 excluded; Pod B separate; no-deadline amendment retained.

## Local package and terminal boundary

[Catalog JSONL](DRIVE_CATALOG.jsonl) · [Catalog CSV](DRIVE_CATALOG.csv) · [Folder coverage](FOLDER_COVERAGE.json) · [Future-use matrix](FUTURE_USE_MATRIX.csv) · [Dataset reference map](DATASET_REFERENCE_MAP.csv) · [Audit receipt](AUDIT_RECEIPT.json) · [Handoff](SESSION_HANDOFF.md). Full source bytes and sanitized transport/listing responses are private local control artifacts; no credentials or temporary signed locators are durable source IDs.

This package is local only. No commits, pushes, uploads, messages, Drive renames/moves/sharing changes, scientific evaluation or later-stage execution. Historical research and the sealed T00 snapshot remain unchanged. Original retain-and-forget request remains PARTIAL.

STOP_AFTER_T01_INVENTORY_AND_FUTURE_USE_HANDOFF
