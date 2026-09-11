"""Test 05, section 7: frozen companion specifications.

Each function below exports a real, accurate description of what the
implementation actually does -- never an aspirational schema that overstates
what is operationally wired into the simulator. Where a section-8-style
schema lists more fields than the operational ``FrozenContract`` currently
carries, both the full documented schema and the operationally-implemented
subset are recorded, and the gap is called out explicitly (see
``beginning_contract_schema``) rather than glossed over.

Every function returns a plain JSON-able dict; the caller (``run.py``) is
responsible for writing each one to ``protocol/`` or ``config/`` with a
canonical-JSON hash, and for building the resulting companion-file manifest.
"""

from __future__ import annotations

from . import boundary as B
from . import execution_matrix as EM
from . import observer as O
from . import residual as R
from . import resource as RS
from . import seeds as S
from . import world as W
from .worlds import all_world_families


def observer_specification() -> dict:
    return {
        "primary_observer_spec": O.PRIMARY_OBSERVER_SPEC,
        "primary_observer_spec_hash": O._PRIMARY_OBSERVER_SPEC_HASH,
        "window_ticks": O.WINDOW,
        "sensitivity_ladder": [
            {"observer_id": oid, "description": desc, "role": role}
            for oid, desc, _fn, role in O.OBSERVER_LADDER
        ],
        "thresholds": {
            "indistinguishability_tv": O.INDISTINGUISHABILITY_TV_THRESHOLD,
            "indistinguishability_accuracy": O.INDISTINGUISHABILITY_ACCURACY_THRESHOLD,
            "positive_control_tv": O.POSITIVE_CONTROL_TV_THRESHOLD,
            "positive_control_accuracy": O.POSITIVE_CONTROL_ACCURACY_THRESHOLD,
            "min_matched_observations_per_class": O.MIN_MATCHED_OBSERVATIONS_PER_CLASS,
            "min_matching_coverage": O.MIN_MATCHING_COVERAGE,
        },
        "null_model": "histories uniformly likely over the full enumerated admissible-history space (exact, no sampling)",
    }


def physics_configuration() -> dict:
    out = {}
    for wf in all_world_families():
        out[wf.family_id] = {
            "standard_config": wf.standard_config.to_dict(),
            "standard_config_hash": wf.standard_config.config_hash(),
            "observer_config": wf.observer_config.to_dict(),
            "observer_config_hash": wf.observer_config.config_hash(),
            "action_alphabet": list(W.ACTIONS),
            "relevant_actions": list(W.RELEVANT_ACTIONS),
            "irrelevant_actions": list(W.IRRELEVANT_ACTIONS),
            "loss_profile": wf.loss_profile,
            "adversarial_conditions": list(wf.adversarial),
        }
    return out


def beginning_contract_schema() -> dict:
    return {
        "operationally_implemented_fields": {
            "total_conserved_invariant": "int; sum(balances)+resolved_count must equal this",
            "min_resolutions": "int; resolved_count must be >= this for contract satisfaction",
        },
        "note_on_operational_scope": (
            "FrozenContract carries exactly the two fields above, which are sufficient to drive every "
            "05A necessity/specificity intervention arm and the contract-consumption check. The fuller "
            "field list below (protocol section 8's 'minimum contract contents') is documented for "
            "completeness and future extension; most of those fields are already implicitly fixed "
            "elsewhere in this protocol version (e.g. the world-family ID and physics-config hash are "
            "recorded per world family in physics_configuration(), the observer-spec hash in "
            "observer_specification(), the semantic-probe IDs in semantic_probe_specification()) but are "
            "not yet folded into the FrozenContract object J actually consumes. This is a declared scope "
            "limitation, not a silent gap: see the development report's Limitations section."
        ),
        "documented_full_schema_fields": [
            "protocol_version", "world_family_id", "physics_configuration_hash",
            "identity_table_commitment", "relationship_schema", "obligation_schema",
            "causal_order_rules", "locked_beginning_payload_schema", "dump_operator",
            "residual_schema", "ledger_schema", "observer_specification_hash",
            "resource_objective_id", "declared_causal_path", "intentionally_discarded_fields",
            "irrelevant_fields", "frozen_semantic_probe_ids", "delayed_probe_generator_hash",
        ],
        "immutability_mechanism": "FrozenContract (__slots__, __setattr__/__delattr__ raise TypeError); consumed flag set exactly once by execute_J",
        "committed_at_tick": -1,
    }


def causal_path_specification() -> dict:
    return {
        "stages": ["intermediate_action", "later_state", "ending_state", "return_value", "reconstruction"],
        "description": (
            "boundary.serialize_causal_path records these five stages for a history anchored at an "
            "intervention tick; boundary.diff_causal_paths compares two such records stage-by-stage so a "
            "'relevant' intervention can be shown to actually modify executed data (sensitivity) and an "
            "'irrelevant' one shown not to (specificity), rather than inferring this from the closure "
            "outcome alone."
        ),
    }


def field_classification_manifest() -> dict:
    return {
        "classification": R.declared_field_classification(),
        "categories": ["copied", "reconstructed", "derived_through_later_execution", "intentionally_discarded"],
        "semantic_distinctions": R.SEMANTIC_DISTINCTIONS,
    }


def delayed_probe_generator() -> dict:
    return {
        "generator_source_hash": R._GENERATOR_SOURCE_HASH,
        "delayed_probe_ids": [p[0] for p in R.DELAYED_PROBE_SPECS],
        "instance_generation_rules": {
            "counterfactual_agent": "agent currently holding the most balance in the committed residual (tie: lowest index)",
            "unseen_obligation": "most recently resolved obligation per causal_order_token, else the last obligation in the chain",
            "dispute_pair": "pair of agents with the closest (preferring nonzero) balance difference in the committed residual",
            "substitution_pair": "same rule as dispute_pair",
            "prerequisite_obligation": "open obligation with the latest declared deadline in the committed residual",
            "urgent_obligation": "open obligation with the earliest declared deadline in the committed residual",
            "authorization_pair": "the counterfactual_agent and its direct ring successor",
        },
        "committed_after_dump": True,
    }


def fault_predictions() -> dict:
    return EM.FAULT_PREDICTIONS


def mutation_definitions() -> dict:
    return {mid: {"description": spec["description"]} for mid, spec in EM.FAULT_PREDICTIONS.items()}


def semantic_probe_specification() -> dict:
    return {
        "required_core_probe_ids": list(R.REQUIRED_CORE_PROBE_IDS),
        "core_probe_descriptions": {pid: desc for pid, desc, _fn in R.CORE_PROBE_SPECS},
        "delayed_probe_ids": [p[0] for p in R.DELAYED_PROBE_SPECS],
        "delayed_probe_descriptions": {pid: desc for pid, desc, _fn in R.DELAYED_PROBE_SPECS},
        "additional_core_checks": [
            pid for pid, _d, _f in R.CORE_PROBE_SPECS if pid not in R.REQUIRED_CORE_PROBE_IDS
        ],
        "banned_leakage_keys": sorted(R.BANNED_KEYS),
    }


def byte_accounting_specification() -> dict:
    return {
        "categories": list(RS.RESOURCE_CATEGORIES),
        "primary_objective": "peak_canonical_bytes",
        "secondary_objective": "total_byte_ticks",
        "diagnostic": "total_operation_count",
        "noncanonical_diagnostic": "wall_clock_seconds (excluded from canonical_digest)",
        "state_machine_replicas": RS.STATE_MACHINE_REPLICAS,
    }


def resource_objective() -> dict:
    return {
        "objective_id": "peak_canonical_bytes_v1",
        "primary": "peak_canonical_bytes",
        "secondary": "total_byte_ticks",
        "diagnostic": "total_operation_count",
        "noncanonical_diagnostic": "wall_clock_seconds",
        "support_rule": "strictly lower peak_canonical_bytes than every eligible baseline, in both world families",
    }


def seed_list() -> dict:
    return {
        "development_seeds": S.PROTOCOL_V3_DEVELOPMENT_SEEDS,
        "eligibility": S.check_v3_seed_eligibility(),
        "reserved_bands": {k: [v.start, v.stop] for k, v in S.RESERVED_CONFIRMATORY_SEED_BANDS.items()},
    }


def baseline_definitions() -> dict:
    return {
        "required_baselines": [
            "complete_checkpointing", "snapshot_plus_event_log", "always_expanded_lossless",
            "open_chain_execution", "general_purpose_lossless_compression",
            "general_purpose_lossy_compression_matched_fidelity", "lossy_execution_without_ledger",
            "no_loss_cyclic_execution", "scripted_cyclic_replay", "state_machine_replication",
        ],
        "focal_arm": "proposed_architecture_residual_plus_ledger",
    }


COMPANION_SPEC_BUILDERS = {
    "observer_spec.json": observer_specification,
    "physics_config.json": physics_configuration,
    "beginning_contract_schema.json": beginning_contract_schema,
    "causal_path_specification.json": causal_path_specification,
    "field_classification_manifest.json": field_classification_manifest,
    "delayed_probe_generator.json": delayed_probe_generator,
    "fault_predictions.json": fault_predictions,
    "mutation_definitions.json": mutation_definitions,
    "semantic_probe_specification.json": semantic_probe_specification,
    "byte_accounting_specification.json": byte_accounting_specification,
    "resource_objective.json": resource_objective,
    "seed_list.json": seed_list,
    "baseline_definitions.json": baseline_definitions,
}
