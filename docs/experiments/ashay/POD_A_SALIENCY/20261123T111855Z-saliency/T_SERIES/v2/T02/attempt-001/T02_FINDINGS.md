# T02 dataset provenance and readiness assessment

**T02_BLOCKED_EXTERNAL.** The intended forget input is documented only by the producer-path label `HVUE_v2/preprocessed_hvue_human_host_tropism`; no exact dataset version, accessible intended root, authoritative member manifest or split identity has been established. All resolvable local documentary work is finished, but the mandatory success conditions are not met.

## What is and is not identified

All 36 dataset references in the nine established source configurations are accounted for. They resolve into four distinct literal paths and two **declaration groups**, not two proven dataset versions or nine independent datasets. Dataset payloads, membership counts and version identities remain unknown. No similarly named replacement was substituted.

| Declared role | Configured dataset root | Dataset-definition reference | Actual version/location |
|---|---|---|---|
| FORGET | `/projects/MENTISLab/unlearning/data/evo2/HVUE_v2/preprocessed_hvue_human_host_tropism` | `/projects/MENTISLab/unlearning/evo2_unlearn_pipeline/forget_data_config.yaml` | Unresolved; exact paths absent on this Pod, producer host not established |
| RETAIN | `/projects/MENTISLab/unlearning/data/evo2/GUE_benchmark/emp_h3_fasta_splits/preprocessed_emp_h3` | `/projects/MENTISLab/unlearning/evo2_unlearn_pipeline/training_data_config_emp_h3.yaml` | Unresolved; exact paths absent on this Pod, producer host not established |

Four targeted `lstat` checks returned ENOENT on the current Pod. This is not evidence that the dataset is absent on the producer’s system. The exact producing source directory/config basenames were not found in the bounded local research checkout check. Unrelated historical benchmark-log paths were not opened or used as substitutes. No new Drive crawl or credential discovery was needed.

## Expected-versus-observed membership

Expected dataset file/shard counts are **null**, because no authoritative producer membership manifest is available. Intended observed-member counts are also **null**, because intended versions/locations are unresolved. T01 identified zero dataset payload objects in its reviewed accessible scope; that is not an expected-membership denominator.

The membership table contains 16 **evidence-component obligations**, eight per declaration group: produced root, independent expected manifest, dataset definition, preprocessing code, preprocessing configuration/rules, training manifest, validation manifest, and test applicability plus a manifest if applicable. These are not 16 inferred dataset files. All remain unsatisfied; merely listing them does not pass completeness.

## Nine previously unopened containers

All nine exact T01 container IDs have a source-backed disposition: **model-only established for their bound historical checkpoint versions**, including optimizer and RNG state. Existing S03 payload manifests/local admission records bind original Drive IDs to native digests. Current local five-field stat tuples match those digest bindings. Exact cached T01 storage-index bytes also match the bound manifests.

Inert opcode inspection identifies 1,126 storage records per native file. Their model/optimizer/RNG namespaces and contiguous offsets account for all 15,516,878,934 bytes, without gaps, overlap or an unindexed tail. No model payload body, biological sequence, tensor value or executable pickle object was read or loaded in T02. This resolves the material container search question at those identified versions; it is not a fresh checksum/access assertion for current remote Drive bytes.

| Alias | Original Drive container ID | Bound native SHA256 | Disposition |
|---|---|---|---|
| candidate_01 | `1XnC0R7878FreDHU-8sEqMA0nSByPzHxl` | `c8a192778f7ae900855dbdc3c63d2c98bc365fdc8f52618ae591ca7074df9c14` | MODEL_ONLY_ESTABLISHED |
| candidate_02 | `1FQLKbttrWtvFAz24gw7Cm5altap8N8zs` | `8f9997a04f912ba15c424c63e400f5ec8170e21d9a68f63f01c6d42af9446c12` | MODEL_ONLY_ESTABLISHED |
| candidate_03 | `1PboRcLdyJLUmMuVYASAl9He9_NSO49v-` | `0d37cf4228cc25c944af08f7a0c01becf4656287545e9d5666dcd6e90f34f5bc` | MODEL_ONLY_ESTABLISHED |
| candidate_04 | `16iWRqR0FY7E53ZxQDSNpaFNRb-kf5DZN` | `fea5369e5afec0dd127401242806034378eb26d97e6901453117aebca752fb98` | MODEL_ONLY_ESTABLISHED |
| candidate_05 | `1GrVgqmcJSkKuTmKyo16qKnElNCo7R-BA` | `9ab6de9d027ad45ac938a6f579e95a1c88d4fc8f0fab2772f50c2a2461d056b6` | MODEL_ONLY_ESTABLISHED |
| candidate_06 | `13CcTIOJddLsqFofAgPclNiEdMQBzqjMc` | `6ee66eb6c031054cfa2c6cd8a2bdf68703c736343a4da74b2cd3b48d3662f2d3` | MODEL_ONLY_ESTABLISHED |
| candidate_07 | `1sVeovPvaolpF9nRFftf3I8Dx_eB22C8V` | `7864d1f568113d13815d482391d56a30865c2056246602d56503897512b8879c` | MODEL_ONLY_ESTABLISHED |
| candidate_08 | `1sV-lAtlGAW1HIfdIkc-nwLdxMjdh_UJM` | `6966bdf46414c917a909c89f876991c88157462f640e06dbb4a8d102ba7f9acd` | MODEL_ONLY_ESTABLISHED |
| candidate_09 | `1wM_z3sjetS0ijTAWSoEOdWPHwAC19N9a` | `0462c321ceb3d2030bd865a7b9c8c427ad8e2286a827d33b486bad95846235da` | MODEL_ONLY_ESTABLISHED |

This is a versioned refinement of T01’s “unopened in this audit” state, not a rewrite of T01. Model manifests do not become dataset manifests, and excluding these containers does not establish the expected dataset inventory.

## Roles, preprocessing and splits

The nine exact configs explicitly assign a forget path and a retain path in their dataset blocks. That supports configured roles in nine contexts. It does not bind actual dataset versions, training exposure, train/validation membership or the actual evaluated cohort. The provider class name and directory label do not establish the producing implementation or objective.

Required source-release, preprocessing implementation/configuration, inclusion/exclusion criteria, produced-artifact and split-manifest links are unavailable. Test applicability itself is unresolved; it was not silently marked NOT_APPLICABLE. Actual invocation association remains T03 work, while the missing split identities remain a T02 blocker. Existing qualified benign evaluation cohorts remain usable at their own scope and are not substituted for the producer’s training retain directory.

## Mandatory acceptance verdict

The current invocation explicitly tightens T02 acceptance. T00/T01 keep their narrower valid receipts. The 12 Appendix A conditions are represented by 13 conjunctive gates, because expected membership and affirmative required-member presence are checked separately.

| Gate | Requirement | Verdict | Evidence or missing condition |
|---|---|---|---|
| C01 | required_reference_scope_established | PASS | All 36 direct dataset references within nine exact T01 configs have recorded dispositions and source/key/context identities. |
| C02 | all_required_references_resolved | UNKNOWN | Four exact producer-host paths lack an intended concrete target/version binding. ENOENT here does not settle producer-host presence. |
| C03 | expected_dataset_membership_established | UNKNOWN | No authoritative dataset expected-component manifest or equivalent producer inventory is available. |
| C04 | all_required_components_present | UNKNOWN | Expected member universe is unknown; no complete intended dataset bundle or required component presence can be affirmed. |
| C05 | relevant_container_uncertainty_resolved | PASS | All nine exact checkpoint versions are source-bound model/optimizer/RNG artifacts, with1,126 index segments per file covering15,516,878,934 bytes contiguously and unchanged local stat bindings. No shard bodies opened. |
| C06 | required_role_assignments_supported | UNKNOWN | Configured forget/retain roles are documented for nine contexts, but actual required dataset-version/split membership roles are not bound. |
| C07 | required_version_and_preprocessing_provenance_supported | UNKNOWN | Source release, producing preprocessing code/configuration, inclusion/exclusion rules and produced output identities remain unsupported. |
| C08 | required_split_identities_supported | UNKNOWN | Producer train/validation membership identities and test applicability are unresolved. Invocation association remains separately T03. |
| C09 | required_use_availability_sufficient | FAIL | U02,U04,U07 lack mandatory dataset identity/provenance/membership/availability evidence; four other review uses are eligible. |
| C10 | no_unresolved_consequential_conflicts | PASS | Paired apparent conflicts are resolved by source scope/temporal distinction or explicit T02 amendment; no accepted provenance assertion masks a contradiction. |
| C11 | downstream_input_contract_verified | PASS | Seven required use contracts remain frozen/nonvacuous, with exact sources, eligibility, unmet evidence and prohibited inferences. |
| C12 | independent_checks_passed | PASS | Certified only by the separate source-first verifier and20predeclared challenges plus gate controls; receipt seals actual execution. |
| C13 | handoff_package_verified | PASS | Certified only after separate-directory metadata-input/package verification; source-byte restoration is not scientific reproduction. |

**Six PASS, one FAIL, six UNKNOWN.** Unknown does not pass. C09 fails because three frozen required uses lack evidence, even though four documentary review uses are eligible. No requirement or use was dropped to manufacture readiness. No unresolved consequential contradiction is concealed; missing evidence is tracked separately from conflict. Verification/package PASS refers only to the actual checks in the sealed verification/receipt, not scientific or dataset availability success.

## Downstream inputs

| Use | Stage | Purpose | Eligibility | Remaining conditions |
|---|---|---|---|
| U01 | T03 | Exact nine run configs as documentary proposed-association inputs | ELIGIBLE | Exact cached documentary inputs available; later-stage authorization still required |
| U02 | T03 | Dataset/version and cohort identities as concrete association-review inputs | BLOCKED | Producer-bound dataset identity/version; Split/cohort manifest identity |
| U03 | T04 | Declared dataset provider and validation settings as source assertions | ELIGIBLE | Exact cached documentary inputs available; later-stage authorization still required |
| U04 | T04 | Producing dataset definition/preprocessing and split records as semantics-review context | BLOCKED | Exact producing dataset YAML; Release/preprocessing implementation/config identities; Required split metadata |
| U05 | T05 | Focused deduplicated unsent producer dependency request | ELIGIBLE | Exact cached documentary inputs available; later-stage authorization still required |
| U06 | T03 | Container provenance/exclusion evidence as association-review input | ELIGIBLE | Exact cached documentary inputs available; later-stage authorization still required |
| U07 | T03/T04 | Expected component and availability records as documentary review inputs | BLOCKED | Authoritative expected-member manifest; Supported observed identities/presence and appropriate existing byte-access receipts |

All eligible uses are documentary: inspecting proposed associations, declared settings, container provenance, or a focused request. None establishes a T03 association verdict, T04 metric meaning, T07 scientific qualification, T08 layerwise result or permission to evaluate raw biological data. Old acquisition receipts were not recast as proof of present remote access.

## Unsent producer request — exact missing evidence only

Proposed coordination contact: Sayyed, unconfirmed. Technical owners remain OWNER_UNASSIGNED; producing data/pipeline/evaluation roles are proposed, not accepted. Do not resend existing logs or send raw sequences, per-example losses, labels or predictions.

- **DEP_TARGETS — Producer-bound exact dataset roots and definition-config objects/versions for both configured roles:** Stable source locators plus immutable revision or supported content digest, linked explicitly to the four literal producer paths and nine config contexts. Owner: OWNER_UNASSIGNED; producing data/pipeline team proposed.
- **DEP_MEMBERS — Authoritative expected dataset membership and appropriate availability receipts:** Producer-origin manifest identifying exact required components, versions, sizes/checksums where available, intended completeness and existing identity-bound acquisition/access evidence; no raw sequences. Owner: OWNER_UNASSIGNED; producing data team proposed.
- **DEP_PROVENANCE — Actual version/role and source→preprocessing→artifact provenance:** Exact producing dataset YAMLs, source release/revision, preprocessing implementation/config, inclusion/exclusion rules and produced-artifact identity; identify missing/nonexistent records explicitly. Owner: OWNER_UNASSIGNED; producing pipeline/data team proposed.
- **DEP_SPLITS — Required split/cohort identities and explicit test applicability:** Versioned train/validation membership manifest identities; test manifest only if applicable, otherwise attributed scope reason; existing overlap-check receipts and their limits. Actual invocation joins remain T03. Owner: OWNER_UNASSIGNED; dataset/evaluation owner proposed.

This is an unsent artifact for later T05 consolidation, not a collaborator message. Explicitly identify missing/nonexistent producer records rather than reconstructing undocumented preprocessing or raw biological measurements.

## Verification, limits and resumption

A separate source-first checker reads exact configuration blocks, source identities, index fields, memberships, eligibility and the completion predicate. The minimum ten adversarial cases, six additional scope/completeness challenges and four positive controls are frozen before execution; synthetic fixtures are separate from real evidence. The small package is checked from a separate local directory with declared metadata inputs and no producer-tree fallback. Read the actual [verification](T02_VERIFICATION.json) and [receipt](T02_RECEIPT.json) for outcomes and operational repair history.

Full declared input snapshots remain in private local control. The package check restores metadata decisions only; it does not repeat S11 recovery, scientific computation, producer evaluation, remote dataset access or model reconstruction. No raw biological record, new model shard, event log or new scientific aggregate was acquired.

[Canonical evidence](T02_EVIDENCE.json) · [Reference map](DATASET_REFERENCE_MAP.csv) · [Membership reconciliation](MEMBERSHIP_RECONCILIATION.csv) · [Downstream matrix](DOWNSTREAM_USE_MATRIX.csv) · [Requirements freeze](REQUIREMENTS_FROZEN.json) · [Handoff](SESSION_HANDOFF.md).

Next useful action: obtain the exact producer documents above. Resume only affected blocked units with new evidence, a new version/attempt and targeted checks. Eligible documentary inputs may support separately authorized T03/T04/T05 work; no automatic T03 launch. Historical S10 correction, S11 report, all sealed T00/T01 artifacts, original POD_A and no-deadline amendment remain unchanged. No commit, push, publication, sharing change, message, observer, scheduler, shutdown or resize.

STOP_AFTER_T02_HANDOFF — ORIGINAL RETAIN-AND-FORGET REQUEST REMAINS PARTIAL
