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
            "protocol_version": "str; the exact frozen protocol version this contract was built under",
            "world_family_id": "str; config.world_id -- echoed into next_beginning and cross-checked by contract_satisfied",
            "physics_configuration_hash": "str; config.config_hash()",
            "identity_table_commitment": "str; hash of the frozen agent-id list",
            "relationship_schema": "str; description of the fixed ring-relationship structure",
            "obligation_schema": "str; description of the obligation dict's fixed field set",
            "causal_order_rules": "str; description of the obligation dependency chain rule",
            "locked_beginning_payload_schema": "list[str]; exactly the keys execute_J's next_beginning output carries",
            "dump_operator": "str; the identifier of the frozen dump function (residual.build_residual)",
            "residual_schema": "list[str]; the top-level keys of a residual.build_residual() output",
            "ledger_schema": "list[str]; the possible keys of a relevant-ledger entry",
            "observer_specification_hash": "str; observer._PRIMARY_OBSERVER_SPEC_HASH",
            "resource_objective_id": "str; resource.RESOURCE_OBJECTIVE_ID",
            "declared_causal_path": "list[str]; the 5 stages boundary.serialize_causal_path records",
            "intentionally_discarded_fields": "list[str]; residual.FIELD_CLASSIFICATION entries marked 'intentionally_discarded'",
            "irrelevant_fields": "list[str]; in this model, coincides with intentionally_discarded_fields (see note below)",
            "frozen_semantic_probe_ids": "list[str]; residual.REQUIRED_CORE_PROBE_IDS (the 9 required core probes)",
            "delayed_probe_generator_hash": "str; residual._GENERATOR_SOURCE_HASH",
            "total_conserved_invariant": "int; sum(balances)+resolved_count must equal this (operational, pre-v1.3.0-dev4)",
            "min_resolutions": "int; resolved_count must be >= this for contract satisfaction (operational, pre-v1.3.0-dev4)",
        },
        "note_on_naming": (
            "Section 8's 'minimum contract contents' names 18 distinct fields (protocol_version through "
            "delayed_probe_generator_hash), not 17 as earlier development-report shorthand miscounted. All "
            "18 are implemented above, plus the 2 pre-existing operational fields "
            "(total_conserved_invariant, min_resolutions) that contract_satisfied() checks next_beginning "
            "against -- 20 fields total."
        ),
        "note_on_irrelevant_vs_discarded": (
            "irrelevant_fields and intentionally_discarded_fields are declared as separate section-8 items "
            "but coincide in this bounded model: the only fields the IRRELEVANT_ACTIONS (noop_x/noop_y) "
            "touch (internal_seed, private_trace) are also the only fields intentionally never retained in "
            "the residual. This is recorded explicitly rather than left as an unexplained duplication."
        ),
        "protocol_v1_3_0_dev4_change": (
            "v1.2.0-dev3's FrozenContract carried only 2 of these fields (total_conserved_invariant, "
            "min_resolutions). Protocol v1.3.0-dev4 threads the full field set through: "
            "boundary.locked_beginning_contract(config, protocol_version) now builds all fields listed "
            "above, and execute_J additionally echoes world_family_id and protocol_version into "
            "next_beginning, with contract_satisfied() independently verifying both round-trip -- proof J "
            "actually reads more of the contract than just the 2 operational fields, not merely that the "
            "fuller schema is documented alongside a narrower runtime object."
        ),
        "immutability_mechanism": "FrozenContract (__slots__, __setattr__/__delattr__ raise TypeError); consumed flag set exactly once by execute_J",
        "committed_at_tick": -1,
    }


def gate_registry() -> list[dict]:
    """Protocol v1.3.0-dev4, correction 6: the protocol-to-code gate
    registry -- for every one of the 16 required section-17 gates, its
    governing protocol clause, its evidence source, the generator-side
    evaluator that computes it, and the (separate, non-reusing) validator
    check that independently re-derives it. Frozen and hashed before tick
    zero like every other companion file."""
    return [
        {"gate": "expansion_and_contraction", "protocol_clause": "section 16", "evidence_source": "runs/expansion/<family>.json", "evaluator": "integrated.expansion_and_contraction_result", "validator_check": "_independent_gate_expansion_and_contraction"},
        {"gate": "beginning_contract_committed", "protocol_clause": "section 8, points 1-6", "evidence_source": "runs/boundary/<family>.json:beginning_commitment", "evaluator": "integrated.evaluate (inline)", "validator_check": "_independent_gate_beginning_contract_committed"},
        {"gate": "ending_derived_return_value", "protocol_clause": "section 10, required transition", "evidence_source": "runs/boundary/<family>.json:arms[01_correct_return_value]", "evaluator": "integrated.evaluate (inline)", "validator_check": "_independent_gate_ending_derived_return_value"},
        {"gate": "executed_transition", "protocol_clause": "section 8, required transition", "evidence_source": "runs/boundary/<family>.json:arms", "evaluator": "integrated.evaluate (inline)", "validator_check": "_independent_gate_executed_transition"},
        {"gate": "at_least_one_closing_history", "protocol_clause": "section 10, support requirement 1", "evidence_source": "runs/boundary/<family>.json:support_checks", "evaluator": "integrated.evaluate (inline)", "validator_check": "_independent_gate_closing_histories"},
        {"gate": "at_least_one_non_closing_history", "protocol_clause": "section 10, support requirement 2", "evidence_source": "runs/boundary/<family>.json:support_checks", "evaluator": "integrated.evaluate (inline)", "validator_check": "_independent_gate_closing_histories"},
        {"gate": "causal_endpoint_sensitivity", "protocol_clause": "section 10, support requirements 4-5", "evidence_source": "runs/boundary/<family>.json:support_checks", "evaluator": "integrated.evaluate (inline)", "validator_check": "_independent_gate_causal_endpoint_sensitivity"},
        {"gate": "genuine_information_loss", "protocol_clause": "section 11", "evidence_source": "runs/residual/<family>.json:support_checks.non_injective_loss_demonstrated", "evaluator": "integrated.genuine_information_loss_result", "validator_check": "_independent_gate_genuine_information_loss"},
        {"gate": "semantic_continuity_core_probes", "protocol_clause": "section 11, section 17 item 9", "evidence_source": "runs/residual/<family>.json:main_probe_grade.scoring.required_core", "evaluator": "integrated.semantic_continuity_core_result", "validator_check": "_independent_gate_semantic_continuity_core"},
        {"gate": "semantic_continuity_delayed_probes", "protocol_clause": "section 11, section 17 item 10", "evidence_source": "runs/residual/<family>.json:main_probe_grade.scoring.delayed", "evaluator": "integrated.semantic_continuity_delayed_result", "validator_check": "_independent_gate_semantic_continuity_delayed"},
        {"gate": "clean_leakage_audit", "protocol_clause": "section 12", "evidence_source": "runs/residual/<family>.json:support_checks.leakage_audit_clean,positive_controls_pass", "evaluator": "integrated.clean_leakage_audit_result", "validator_check": "_independent_gate_clean_leakage_audit"},
        {"gate": "ledger_causality", "protocol_clause": "section 13, part 1", "evidence_source": "runs/residual/<family>.json:controls; runs/boundary/<family>.json:arms[08_...]", "evaluator": "integrated.ledger_causality_result", "validator_check": "_independent_gate_ledger_causality"},
        {"gate": "fault_control_validity", "protocol_clause": "section 13, part 2", "evidence_source": "runs/execution_matrix/<family>.json:all_predictions_matched", "evaluator": "integrated.fault_control_validity_result", "validator_check": "_independent_gate_fault_control_validity"},
        {"gate": "primary_observer_indistinguishability", "protocol_clause": "section 14, 'Primary support threshold'", "evidence_source": "runs/observer/<family>.json:status", "evaluator": "integrated.evaluate (inline)", "validator_check": "_independent_gate_primary_observer"},
        {"gate": "full_state_observer_boundary_detection", "protocol_clause": "section 14, 'Positive control'", "evidence_source": "runs/observer/<family>.json:positive_control_result.conclusion", "evaluator": "integrated.evaluate (inline)", "validator_check": "_independent_gate_positive_control"},
        {"gate": "fidelity_matched_resource_advantage", "protocol_clause": "section 15, point 4", "evidence_source": "runs/resource/<family>.json:pareto.status", "evaluator": "integrated.resource_advantage_result", "validator_check": "_independent_gate_resource_advantage"},
    ]


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
        "development_seeds": S.PROTOCOL_V4_DEVELOPMENT_SEEDS,
        "eligibility": S.check_v4_seed_eligibility(),
        "reserved_bands": {k: [v.start, v.stop] for k, v in S.RESERVED_CONFIRMATORY_SEED_BANDS.items()},
    }


def expansion_feasibility_proof() -> dict:
    """Protocol v1.3.0-dev4, correction 10: frozen, pre-tick-zero record of
    the expansion/contraction feasibility check for every world family's
    configured dimensions -- the same check run.freeze() runs and refuses
    to freeze on failure, recorded here as a companion file so the proof
    itself is part of the frozen, hashed evidence, not just a runtime
    assertion."""
    from . import expansion as E

    return E.preflight_feasibility_check(all_world_families())


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
    "gate_registry.json": gate_registry,
    "expansion_feasibility_proof.json": expansion_feasibility_proof,
}
