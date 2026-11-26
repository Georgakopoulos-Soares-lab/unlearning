"""Compact documentary acceptance rules. Never qualifies scientific results."""
CRITERIA=tuple('C'+str(i).zfill(2) for i in range(1,14))
USES=tuple('U'+str(i).zfill(2) for i in range(1,8))
def classify_documentary_case(case):
    """Contract challenges only: explicit facts produce bounded decisions."""
    k=case['kind'];x=case['facts']
    if k=='target':return {'resolved':bool(x['exists'] and x['intended_version_bound'])}
    if k=='membership':return {'complete':bool(x['authoritative_expected'] and x['all_required_present'])}
    if k=='aliases':return {'distinct_datasets':len(set(x['stable_content_ids']))}
    if k=='artifact':return {'is_dataset_payload':x['artifact_type']=='DATA_PAYLOAD' and x['documented_payload_binding']}
    if k=='container':return {'excludable':bool(x['role_established'] and x['scope_exclusion_evidence'])}
    if k=='byte_access':return {'bytes_established':bool(x['identity_bound_byte_receipt'] and x['temporal_scope_applies'])}
    if k=='cohort':return {'actual_cohort_verified':bool(x['split_manifest_bound'] and x['invocation_bound'])}
    if k=='conflict':return {'claim_eligible':not x['unresolved_material_conflict']}
    if k=='metadata':return {'metadata_eligible':bool(x['metadata_identity_bound']), 'scientifically_qualified':bool(x['separate_scientific_release'])}
    if k=='uses':return {'readiness_valid':bool(x['required_use_ids']) and set(x['required_use_ids'])==set(x['observed_use_ids']) and x['all_required_satisfied']}
    if k=='exemption':return {'exemption_valid':not x['inherently_mandatory'] and bool(x['source_backed_reason'])}
    if k=='optional':return {'required_work_preserved':bool(x['required_inputs_valid'] and x['exclusion_source_backed'])}
    if k=='correction':return {'version_required':x['bytes_changed'],'invalidate_scope':x['dependent_ids'] if x['bytes_changed'] else []}
    raise ValueError('Unknown challenge kind')
def verdict(criteria,uses,unresolved_conflicts=0,internal_defects=()):
    defects=list(internal_defects)
    if set(criteria)!=set(CRITERIA):defects.append('Mandatory criterion dropped or invented')
    if set(uses)!=set(USES) or not uses:defects.append('Frozen required-use scope dropped or vacuous')
    if any(v not in ['PASS','FAIL','UNKNOWN'] for v in criteria.values()):defects.append('Mandatory criterion exempted without authority')
    all_uses=bool(uses) and all(v=='ELIGIBLE' for v in uses.values())
    if criteria.get('C09')=='PASS' and not all_uses:defects.append('Availability PASS contradicts required-use evidence')
    if defects:return 'T02_BLOCKED_INTERNAL'
    if all(v=='PASS' for v in criteria.values()) and all_uses and unresolved_conflicts==0:return 'T02_REQUIREMENTS_MET'
    return 'T02_BLOCKED_EXTERNAL'
