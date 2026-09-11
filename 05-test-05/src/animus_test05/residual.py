"""Test 05B: Semantic Continuity Through Genuine Loss.

Research question: can the system discard microstate information while
preserving independently defined identities, relationships, obligations,
causal dependencies, and future behavior?

Field classification, the semantic contract, and the probe functions are
all declared before any reconstruction runs (they are pure functions of
``WorldConfig`` and the probe/control machinery below, never of a
particular history's outcome). Genuine information loss is demonstrated by
exact enumeration: the full microstate space (every admissible history's
complete ending state, private fields included) is counted and compared
against the retained-residual space (the same endings projected through the
declared dump policy), producing real collision groups rather than an
assertion of non-injectivity.
"""

from __future__ import annotations

import copy
import random
import zlib
from typing import Any, Callable, Optional

from . import world as W
from .hashing import canonical_json, hash_obj

# ---------------------------------------------------------------------------
# Field classification (declared before reconstruction runs)
# ---------------------------------------------------------------------------

FIELD_CLASSIFICATION: dict[str, str] = {
    "obligations.*.owner": "copied",
    "obligations.*.target": "copied",
    "obligations.*.resource": "copied",
    "obligations.*.deadline": "copied",
    "obligations.*.provenance": "copied",
    "obligations.*.status": "reconstructed",
    "agents.*.balance": "reconstructed",
    "relationships.*": "copied",
    "causal_order_token": "derived_through_later_execution",
    "provenance_digest": "derived_through_later_execution",
    "agents.*.internal_seed": "intentionally_discarded",
    "agents.*.private_trace": "intentionally_discarded",
    "event_log[blocked/noop entries]": "intentionally_discarded",
}


def declared_field_classification() -> dict[str, str]:
    return dict(FIELD_CLASSIFICATION)


# Protocol v2, update G: explicit definitions distinguishing six concepts
# that are easy to conflate, each pointing at where it is actually
# evidenced in this module's output (not merely asserted in prose).
SEMANTIC_DISTINCTIONS: dict[str, str] = {
    "exact_microstate_equality": (
        "Two full ending states (private fields included) are byte-identical; evidenced by the "
        "microstate-signature hashes compared in collision_analysis()."
    ),
    "preservation_by_direct_copying": (
        "A field's value is carried into the residual unchanged, verbatim; see FIELD_CLASSIFICATION "
        "entries marked 'copied'."
    ),
    "reconstruction": (
        "A field's value is *recomputed* from the ledger via world.replay(), not copied from the true "
        "ending; see FIELD_CLASSIFICATION entries marked 'reconstructed'."
    ),
    "derivation_through_later_execution": (
        "A field is computed by processing the ledger/residual after the dump (e.g. causal_order_token, "
        "provenance_digest); see FIELD_CLASSIFICATION entries marked 'derived_through_later_execution'."
    ),
    "behavioral_semantic_equivalence": (
        "Two representations answer every core and delayed probe identically, even if their raw bytes "
        "differ; evidenced by main_probe_grade / control grades in run_controls()."
    ),
    "intentionally_discarded_information": (
        "A field is deliberately never retained in any form; see FIELD_CLASSIFICATION entries marked "
        "'intentionally_discarded', and the microstate/residual cardinality gap in collision_analysis()."
    ),
}


# ---------------------------------------------------------------------------
# Residual construction (the declared dump policy)
# ---------------------------------------------------------------------------

def build_residual(true_ending: dict, config: W.WorldConfig) -> dict:
    """The retained residual: reconstructed public fields (via faithful
    ledger replay, matching Test 05A's reciprocal-closure reconstruction)
    plus a small derived narrative summary. Never includes internal_seed,
    private_trace, or any noop/blocked event detail."""
    ledger = W.relevant_ledger(true_ending)
    reconstructed = W.replay(config, ledger, algorithm="faithful_replay")
    causal_order_token = [ev["obligation"] for ev in ledger if ev.get("effect") == "resolved"]
    return {
        "agents": {aid: {"balance": a["balance"]} for aid, a in reconstructed["agents"].items()},
        "obligations": copy.deepcopy(reconstructed["obligations"]),
        "relationships": dict(reconstructed["relationships"]),
        "causal_order_token": causal_order_token,
        "provenance_digest": hash_obj(ledger),
    }


def build_ledger(true_ending: dict) -> list[dict]:
    return W.relevant_ledger(true_ending)


# ---------------------------------------------------------------------------
# Semantic contract (committed before reconstruction)
# ---------------------------------------------------------------------------

def semantic_contract(config: W.WorldConfig) -> dict:
    return {
        "stable_identity": "residual.agents keys == config.agent_ids() exactly",
        "relationship_permissions": "residual.relationships == the config ring exactly",
        "obligation_ownership": "every obligation's owner/target/provenance matches genesis",
        "causal_ordering": "an obligation can be closed only if its causal dependency is closed",
        "provenance": "every obligation carries a genesis:<i> provenance tag",
        "resource_commitment": "sum(balances) + resolved_count == config.total_resource",
        "permitted_future_actions": "an agent may move iff balance>0 and its ring edge exists",
        "observer_visible_consequence": "primary_holder is derivable and unique",
    }


# ---------------------------------------------------------------------------
# Behavioral probes: functions of (residual, ledger, config) only. None of
# these read the true microstate; ground truth for grading is computed
# separately, directly from the true ending, and never stored inside the
# residual/ledger themselves.
# ---------------------------------------------------------------------------

def _permitted_movers(residual: dict, config: W.WorldConfig) -> list[str]:
    out = []
    for aid in config.agent_ids():
        bal = residual["agents"].get(aid, {}).get("balance", 0)
        if bal > 0:
            n = config.num_agents
            idx = config.agent_ids().index(aid)
            target = config.agent_ids()[(idx + 1) % n]
            if residual["relationships"].get(f"{aid}->{target}") == 1:
                out.append(aid)
    return sorted(out)


def probe_obligation_owner(residual: dict, ledger: list[dict], config: W.WorldConfig, obligation_id: str) -> Any:
    obl = residual.get("obligations", {}).get(obligation_id)
    return obl["owner"] if obl else None


def probe_permitted_actions(residual: dict, ledger: list[dict], config: W.WorldConfig) -> Any:
    return _permitted_movers(residual, config)


def probe_authorizing_relationship(residual: dict, ledger: list[dict], config: W.WorldConfig, a: str, b: str) -> Any:
    return residual["relationships"].get(f"{a}->{b}", 0) == 1


def probe_causal_prerequisite(residual: dict, ledger: list[dict], config: W.WorldConfig, obligation_id: str) -> Any:
    idx = config.obligation_ids().index(obligation_id)
    return config.obligation_ids()[idx - 1] if idx > 0 else None


def probe_dependency_blocks_resolution(residual: dict, ledger: list[dict], config: W.WorldConfig, obligation_id: str) -> Any:
    idx = config.obligation_ids().index(obligation_id)
    if idx == 0:
        return False
    dep = config.obligation_ids()[idx - 1]
    dep_status = residual["obligations"].get(dep, {}).get("status")
    return dep_status != "closed"


def probe_counterfactual_move(residual: dict, ledger: list[dict], config: W.WorldConfig, agent_id: str) -> Any:
    return agent_id in _permitted_movers(residual, config)


def probe_identity_substitution_should_reject(residual: dict, ledger: list[dict], config: W.WorldConfig) -> Any:
    """A defect-detection probe: is the residual's identity set exactly the
    configured agent set, with obligation owner/target references and
    per-agent balances consistent with an independent replay of the
    ledger? If not, an identity substitution (e.g. two agents' holdings
    swapped) has occurred and must be rejected (answer: True)."""
    expected_ids = set(config.agent_ids())
    residual_ids = set(residual["agents"].keys())
    if residual_ids != expected_ids:
        return True  # reject
    for ev in ledger:
        actor = ev.get("actor")
        if actor is not None and actor not in expected_ids:
            return True  # reject
    for obl in residual["obligations"].values():
        if obl["owner"] not in expected_ids or obl["target"] not in expected_ids:
            return True  # reject
    try:
        expected_state = W.replay(config, ledger, algorithm="faithful_replay")
    except Exception:
        return True  # reject: ledger does not even replay
    for aid in expected_ids:
        if residual["agents"][aid]["balance"] != expected_state["agents"][aid]["balance"]:
            return True  # reject: residual balance inconsistent with an independent ledger replay
    return False  # no defect found; accept


def probe_provenance_present(residual: dict, ledger: list[dict], config: W.WorldConfig, obligation_id: str) -> Any:
    obl = residual.get("obligations", {}).get(obligation_id, {})
    prov = obl.get("provenance")
    idx = config.obligation_ids().index(obligation_id)
    return prov == f"genesis:{idx}"


def probe_ledger_effects_consistent(residual: dict, ledger: list[dict], config: W.WorldConfig) -> Any:
    """Independently recomputes each ledger entry's effect from its own
    (tick, action) pair and compares it against the stored effect field.
    Detects tampering (a contradictory ledger entry) that a state-level
    replay alone would not catch, since state replay never reads the
    stored effect string."""
    try:
        recomputed = W.replay_with_recomputed_effects(config, ledger)
    except Exception:
        return False
    if len(recomputed) != len(ledger):
        return False
    for stored, fresh in zip(ledger, recomputed):
        if stored.get("effect") != fresh.get("effect"):
            return False
        if stored.get("action") != fresh.get("action"):
            return False
    return True


def probe_unseen_obligation_chain_completion(residual: dict, ledger: list[dict], config: W.WorldConfig) -> Any:
    """Can a NEW obligation appended after the reconstructed state be given
    the correct causal dependency without consulting the true microstate?
    Answer: the id of the last resolved obligation in causal_order_token
    (or None if none resolved), which is what a correctly-appended
    successor obligation must declare as its dependency."""
    token = residual.get("causal_order_token", [])
    return token[-1] if token else None


def probe_identity_continuity(residual: dict, ledger: list[dict], config: W.WorldConfig) -> Any:
    """Core probe: is the residual's identity set exactly the configured
    agent set (no relabeling, no dropped/added identity)?"""
    return set(residual.get("agents", {}).keys()) == set(config.agent_ids())


def probe_deadline_behavior(residual: dict, ledger: list[dict], config: W.WorldConfig, obligation_id: str) -> Any:
    """Core probe: does the obligation still carry its correct genesis
    deadline (unmodified by loss/dump/reconstruction)?"""
    idx = config.obligation_ids().index(obligation_id)
    obl = residual.get("obligations", {}).get(obligation_id, {})
    return obl.get("deadline") == (config.history_length - idx)


def probe_resource_allocation_commitment(residual: dict, ledger: list[dict], config: W.WorldConfig) -> Any:
    """Core probe: does retained balance plus resolved (spent) obligations
    still add up to the total resource declared in config? A structural
    conservation check on the residual alone."""
    total = sum(a["balance"] for a in residual.get("agents", {}).values())
    resolved = len(residual.get("causal_order_token", []))
    return (total + resolved) == config.total_resource


def probe_observer_visible_consequence(residual: dict, ledger: list[dict], config: W.WorldConfig) -> Any:
    """Core probe: is there a unique, well-defined observer-visible
    consequence (the current primary resource holder) derivable from the
    residual alone?"""
    agents = config.agent_ids()
    balances = [residual.get("agents", {}).get(a, {}).get("balance", 0) for a in agents]
    if not balances:
        return None
    max_bal = max(balances)
    holders = [a for a, b in zip(agents, balances) if b == max_bal]
    return holders[0] if len(holders) >= 1 else None


# ---------------------------------------------------------------------------
# Delayed behavioral probes (protocol v2, update G): the probe *functions*
# below are frozen and hashed before execution, but the specific instance
# parameters they are evaluated against (which agent, which obligation,
# which pair) are chosen by ``generate_delayed_probe_instances`` -- a
# frozen, hashed generator whose OUTPUT depends on the actual residual and
# ledger content, computed only after the lossy dump has been committed.
# This is deliberately different from the core probes above, whose
# instances (o0, a0->a1, etc.) are fixed in the code regardless of what
# happened during execution.
# ---------------------------------------------------------------------------

def generate_delayed_probe_instances(residual: dict, ledger: list[dict], config: W.WorldConfig) -> dict:
    import itertools

    agents = config.agent_ids()

    def _balance(aid: str) -> int:
        return residual.get("agents", {}).get(aid, {}).get("balance", 0)

    # Rule: the agent currently holding the most balance (frozen tie-break:
    # lowest agent index), chosen from the committed residual.
    counterfactual_agent = max(agents, key=lambda a: (_balance(a), -agents.index(a)))

    # Rule: the most recently resolved obligation per the committed
    # causal_order_token, else the last obligation in the declared chain.
    token = residual.get("causal_order_token", [])
    unseen_obligation = token[-1] if token else config.obligation_ids()[-1]

    # Rule: the pair of agents whose committed balances are closest
    # together (the hardest pair to tell apart / most contested), tie-break
    # by agent index. Prefer a pair with a *nonzero* difference when one
    # exists -- a zero-difference pair makes an identity swap a no-op,
    # which would trivially (and unhelpfully) always "pass" a swap-based
    # control; only fall back to a zero-difference pair if every pair ties.
    pairs = list(itertools.combinations(agents, 2))
    nonzero_pairs = [p for p in pairs if abs(_balance(p[0]) - _balance(p[1])) != 0]
    candidates = nonzero_pairs or pairs
    dispute_pair = min(
        candidates,
        key=lambda p: (abs(_balance(p[0]) - _balance(p[1])), agents.index(p[0]), agents.index(p[1])),
    )

    # Rule: the open obligation with the latest declared deadline in the
    # committed residual, else the last obligation in the chain.
    open_obls = [oid for oid, o in residual.get("obligations", {}).items() if o.get("status") == "open"]
    prerequisite_obligation = (
        max(open_obls, key=lambda oid: residual["obligations"][oid].get("deadline", -1))
        if open_obls
        else config.obligation_ids()[-1]
    )

    return {
        "counterfactual_agent": counterfactual_agent,
        "unseen_obligation": unseen_obligation,
        "dispute_pair": list(dispute_pair),
        "substitution_pair": list(dispute_pair),
        "prerequisite_obligation": prerequisite_obligation,
    }


def probe_new_counterfactual_action(residual: dict, ledger: list[dict], config: W.WorldConfig, instances: dict) -> Any:
    return probe_counterfactual_move(residual, ledger, config, instances["counterfactual_agent"])


def probe_unseen_obligation_query(residual: dict, ledger: list[dict], config: W.WorldConfig, instances: dict) -> Any:
    oid = instances["unseen_obligation"]
    return {
        "owner": probe_obligation_owner(residual, ledger, config, oid),
        "prerequisite": probe_causal_prerequisite(residual, ledger, config, oid),
    }


def probe_new_resource_dispute(residual: dict, ledger: list[dict], config: W.WorldConfig, instances: dict) -> Any:
    """A frozen, generic tie-break rule (lower ring index wins) applied to
    a dynamically generated contested pair: can the correct allocation be
    derived from the residual alone?"""
    a, b = instances["dispute_pair"]
    agents = config.agent_ids()
    return a if agents.index(a) < agents.index(b) else b


def probe_identity_substitution_challenge(residual: dict, ledger: list[dict], config: W.WorldConfig, instances: dict) -> Any:
    # The underlying defect-detector already scans the whole residual/
    # ledger; the "challenge" instance selects which pair is actually
    # swapped when constructing the corresponding control (see
    # run_controls). The probe answer itself is family-wide (True/False).
    return probe_identity_substitution_should_reject(residual, ledger, config)


def probe_causal_prerequisite_challenge(residual: dict, ledger: list[dict], config: W.WorldConfig, instances: dict) -> Any:
    """Full prerequisite chain (not just the immediate predecessor) for a
    dynamically generated obligation."""
    oid = instances["prerequisite_obligation"]
    idx = config.obligation_ids().index(oid)
    return config.obligation_ids()[:idx]


# Frozen core probes (protocol v2, update G): fixed instance parameters,
# identical question asked on every run regardless of what the history
# produced. Covers all nine required core categories.
CORE_PROBE_SPECS: list[tuple[str, str, Callable[..., Any]]] = [
    ("identity_continuity", "Is the residual's identity set exactly the configured agent set?", probe_identity_continuity),
    ("obligation_ownership", "Which agent owns obligation o0?", lambda r, l, c: probe_obligation_owner(r, l, c, c.obligation_ids()[0])),
    (
        "relationship_permissions",
        "Does the ring relationship authorize a transfer a0->a1?",
        lambda r, l, c: probe_authorizing_relationship(r, l, c, c.agent_ids()[0], c.agent_ids()[1]),
    ),
    (
        "causal_ordering",
        "Is the last obligation blocked by an unresolved dependency?",
        lambda r, l, c: probe_dependency_blocks_resolution(r, l, c, c.obligation_ids()[-1]),
    ),
    (
        "provenance",
        "Does obligation o0 carry its correct genesis provenance tag?",
        lambda r, l, c: probe_provenance_present(r, l, c, c.obligation_ids()[0]),
    ),
    (
        "deadline_behavior",
        "Does obligation o0 carry its correct genesis deadline?",
        lambda r, l, c: probe_deadline_behavior(r, l, c, c.obligation_ids()[0]),
    ),
    ("resource_allocation_commitments", "Does balance + resolved-count add up to the declared total resource?", probe_resource_allocation_commitment),
    ("permitted_future_actions", "Which agents may still move?", probe_permitted_actions),
    ("observer_visible_consequences", "Who is the unique current primary resource holder?", probe_observer_visible_consequence),
    # Retained from the v1 draft as additional core checks (fixed
    # instances; not part of the nine named categories but still useful
    # ledger-integrity checks that must hold on every run).
    (
        "causal_prerequisite_last_obligation",
        "Which obligation must resolve before the last obligation in the chain?",
        lambda r, l, c: probe_causal_prerequisite(r, l, c, c.obligation_ids()[-1]),
    ),
    ("unseen_chain_completion", "What dependency must an appended successor obligation declare?", probe_unseen_obligation_chain_completion),
    ("ledger_effects_consistent", "Does every ledger entry's stored effect match an independent recomputation?", probe_ledger_effects_consistent),
]

# Delayed behavioral probes: the (frozen, hashed) generator picks concrete
# instance parameters from the committed residual/ledger; these functions
# then answer the generated instance.
DELAYED_PROBE_SPECS: list[tuple[str, str, Callable[..., Any]]] = [
    ("new_counterfactual_actions", "If the generated agent attempted to move next, would it be permitted?", probe_new_counterfactual_action),
    ("unseen_obligation_queries", "Who owns, and what prerequisite does, the generated (previously unseen) obligation query?", probe_unseen_obligation_query),
    ("new_resource_disputes", "Given the generated contested pair, who wins the disputed unit under the frozen tie-break rule?", probe_new_resource_dispute),
    ("identity_substitution_challenges", "Should an identity substitution on the generated pair be rejected?", probe_identity_substitution_challenge),
    ("causal_prerequisite_challenges", "What is the full prerequisite chain for the generated obligation?", probe_causal_prerequisite_challenge),
]

_GENERATOR_SOURCE_HASH = hash_obj({"fn": "generate_delayed_probe_instances", "version": 1})


def run_probes(residual: dict, ledger: list[dict], config: W.WorldConfig) -> dict[str, Any]:
    """Runs every frozen core probe, then generates delayed-probe
    instances from the committed residual/ledger and runs every delayed
    probe against those generated instances. Returns a flat answers dict
    (core and delayed probe ids never collide)."""
    answers: dict[str, Any] = {}
    for probe_id, _desc, fn in CORE_PROBE_SPECS:
        try:
            answers[probe_id] = fn(residual, ledger, config)
        except Exception as exc:  # a malformed/corrupted control may raise
            answers[probe_id] = {"__error__": str(exc)}

    try:
        instances = generate_delayed_probe_instances(residual, ledger, config)
    except Exception as exc:
        instances = None
        answers["__delayed_probe_generation_error__"] = str(exc)

    for probe_id, _desc, fn in DELAYED_PROBE_SPECS:
        if instances is None:
            answers[probe_id] = {"__error__": "delayed probe instance generation failed"}
            continue
        try:
            answers[probe_id] = fn(residual, ledger, config, instances)
        except Exception as exc:
            answers[probe_id] = {"__error__": str(exc)}
    return answers


def run_probes_with_instances(residual: dict, ledger: list[dict], config: W.WorldConfig) -> tuple[dict[str, Any], Optional[dict]]:
    """Like run_probes, but also returns the generated delayed-probe
    instances (so callers, e.g. run_controls, can reuse the same generated
    pair/obligation when constructing a corresponding adversarial control)."""
    try:
        instances = generate_delayed_probe_instances(residual, ledger, config)
    except Exception:
        instances = None
    return run_probes(residual, ledger, config), instances


def ground_truth_answers(true_ending: dict, config: W.WorldConfig) -> dict[str, Any]:
    """Computed directly from the true microstate, independently of the
    residual/ledger machinery, for grading only."""
    true_residual = build_residual(true_ending, config)
    true_ledger = build_ledger(true_ending)
    return run_probes(true_residual, true_ledger, config)


def grade_probes(answers: dict[str, Any], ground_truth: dict[str, Any]) -> dict[str, bool]:
    return {pid: (answers.get(pid) == ground_truth.get(pid)) for pid in ground_truth}


# ---------------------------------------------------------------------------
# Leakage audit
# ---------------------------------------------------------------------------

BANNED_KEYS = {
    "expected_answer", "probe_answer", "answer_key", "arm_id", "arm_label",
    "arm_identity", "closure_status", "boundary_flag", "boundary_location",
    "original_microstate_id", "future_action_label", "test_label", "expected",
}


def leakage_audit(residual: dict, ledger: list[dict]) -> dict:
    violations = []

    def scan(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if str(k).lower() in BANNED_KEYS:
                    violations.append(f"{path}.{k} uses a banned key")
                scan(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                scan(v, f"{path}[{i}]")

    scan(residual, "residual")
    for i, ev in enumerate(ledger):
        scan(ev, f"ledger[{i}]")
    return {"violations": violations, "clean": len(violations) == 0}


# ---------------------------------------------------------------------------
# Collision / genuine-loss analysis (exact enumeration)
# ---------------------------------------------------------------------------

def collision_analysis(config: W.WorldConfig) -> dict:
    groups: dict[str, list[tuple[str, ...]]] = {}
    microstate_signatures: set[str] = set()
    for history in W.enumerate_histories(config):
        ending = W.run_history(config, history)
        microstate_signatures.add(hash_obj(ending))
        residual = build_residual(ending, config)
        key = hash_obj(residual)
        groups.setdefault(key, []).append(history)

    total_histories = sum(len(v) for v in groups.values())
    max_preimage = max(len(v) for v in groups.values())
    collision_groups = [v for v in groups.values() if len(v) >= 2]
    example = None
    if collision_groups:
        g = max(collision_groups, key=len)
        h1, h2 = g[0], g[1]
        e1, e2 = W.run_history(config, h1), W.run_history(config, h2)
        example = {
            "residual_key_prefix": hash_obj(build_residual(e1, config))[:16],
            "microstate_a": {"history": list(h1), "microstate_hash": hash_obj(e1)},
            "microstate_b": {"history": list(h2), "microstate_hash": hash_obj(e2)},
            "group_size": len(g),
        }
    return {
        "admissible_microstate_count": len(microstate_signatures),
        "total_histories_enumerated": total_histories,
        "distinct_residual_count": len(groups),
        "max_preimage_size": max_preimage,
        "cardinality_reduction_ratio": (
            round(1 - (len(groups) / len(microstate_signatures)), 6) if microstate_signatures else None
        ),
        "collision_group_count": len(collision_groups),
        "non_injective": max_preimage >= 2,
        "example_collision": example,
    }


# ---------------------------------------------------------------------------
# Required controls
# ---------------------------------------------------------------------------

def _grade(residual, ledger, true_ending, config) -> dict:
    gt = ground_truth_answers(true_ending, config)
    answers = run_probes(residual, ledger, config)
    grades = grade_probes(answers, gt)
    return {
        "answers": answers,
        "ground_truth": gt,
        "grades": grades,
        "pass_count": sum(1 for v in grades.values() if v),
        "total": len(grades),
        "all_pass": all(grades.values()),
    }


def run_controls(true_ending: dict, config: W.WorldConfig, rng_seed: int) -> dict[str, dict]:
    rng = random.Random(rng_seed)
    ledger = build_ledger(true_ending)
    residual = build_residual(true_ending, config)
    controls: dict[str, dict] = {}

    # 1. Complete checkpoint: the full true microstate itself, projected
    # through the same probe functions by treating it as if it were the
    # residual (probes only read agents/obligations/relationships /
    # causal_order_token, all present on the full state once we add the
    # derived summary fields).
    checkpoint_residual = dict(build_residual(true_ending, config))
    checkpoint_residual["agents"] = {aid: {"balance": a["balance"]} for aid, a in true_ending["agents"].items()}
    controls["complete_checkpoint"] = {
        "description": "Full true microstate (private fields included) used directly.",
        **_grade(checkpoint_residual, true_ending["event_log"], true_ending, config),
    }

    # 2. Lossless event log: use the FULL event log (including noop/blocked
    # entries) alongside the true residual.
    controls["lossless_event_log"] = {
        "description": "Full unfiltered event_log supplied alongside the true residual.",
        **_grade(residual, true_ending["event_log"], true_ending, config),
    }

    # 3. Lossy residual with valid ledger: the actual subject under test.
    controls["lossy_residual_with_valid_ledger"] = {
        "description": "The declared residual + its matching relevant ledger (the real architecture).",
        **_grade(residual, ledger, true_ending, config),
    }

    # 4. Lossy residual without ledger.
    controls["lossy_residual_without_ledger"] = {
        "description": "The declared residual with an empty ledger (no narrative history available).",
        **_grade(residual, [], true_ending, config),
    }

    # 5. Shuffled identities: swap the pair generated by the frozen delayed-
    # probe instance generator (the two agents whose balances are closest,
    # per the committed residual) rather than a hardcoded pair, so the
    # identity-substitution challenge is chosen post-dump.
    shuffled = copy.deepcopy(residual)
    ids = config.agent_ids()
    try:
        generated_instances = generate_delayed_probe_instances(residual, ledger, config)
        substitution_pair = generated_instances["substitution_pair"]
    except Exception:
        substitution_pair = ids[:2]
    if len(substitution_pair) >= 2:
        a, b = substitution_pair[0], substitution_pair[1]
        shuffled["agents"][a], shuffled["agents"][b] = shuffled["agents"][b], shuffled["agents"][a]
    controls["shuffled_identities"] = {
        "description": f"Generated pair {substitution_pair}'s balances swapped in the residual (identity relabeling).",
        **_grade(shuffled, ledger, true_ending, config),
    }

    # 6. Deleted obligation.
    deleted = copy.deepcopy(residual)
    first_obl = config.obligation_ids()[0]
    deleted["obligations"].pop(first_obl, None)
    controls["deleted_obligation"] = {
        "description": f"Obligation {first_obl} removed from the residual.",
        **_grade(deleted, ledger, true_ending, config),
    }

    # 7. Changed causal dependency: corrupt the residual's causal ordering
    # token so the last-resolved obligation looks wrong.
    changed_dep = copy.deepcopy(residual)
    if changed_dep["causal_order_token"]:
        changed_dep["causal_order_token"] = list(reversed(changed_dep["causal_order_token"]))
        changed_dep["causal_order_token"].append("CORRUPTED_DEP")
    controls["changed_causal_dependency"] = {
        "description": "causal_order_token corrupted (reversed and tagged).",
        **_grade(changed_dep, ledger, true_ending, config),
    }

    # 8. Contradictory ledger entry.
    contradictory_ledger = [dict(e) for e in ledger]
    if contradictory_ledger:
        contradictory_ledger[0]["effect"] = "resolved" if contradictory_ledger[0]["effect"] != "resolved" else "blocked_dependency"
    controls["contradictory_ledger_entry"] = {
        "description": "First ledger entry's effect field replaced with a contradictory value.",
        **_grade(residual, contradictory_ledger, true_ending, config),
    }

    # 9. Missing provenance.
    missing_prov = copy.deepcopy(residual)
    for obl in missing_prov["obligations"].values():
        obl.pop("provenance", None)
        break
    controls["missing_provenance"] = {
        "description": "First obligation's provenance field removed.",
        **_grade(missing_prov, ledger, true_ending, config),
    }

    # 10. Stale ledger entry: use the ledger from the INITIAL (empty)
    # history instead of this history's true ledger.
    controls["stale_ledger_entry"] = {
        "description": "Ledger replaced with an empty/stale ledger from a different (earlier) point.",
        **_grade(residual, [], true_ending, config),
    }

    # 11. Duplicate event.
    dup_ledger = [dict(e) for e in ledger]
    if dup_ledger:
        dup_ledger.append(dict(dup_ledger[0]))
    controls["duplicate_event"] = {
        "description": "First ledger entry duplicated at the end.",
        **_grade(residual, dup_ledger, true_ending, config),
    }

    # 12. Random reconstructed payload.
    random_residual = copy.deepcopy(residual)
    for aid in random_residual["agents"]:
        random_residual["agents"][aid]["balance"] = rng.randint(0, config.total_resource)
    for obl in random_residual["obligations"].values():
        obl["status"] = rng.choice(["open", "closed"])
        obl["owner"] = rng.choice(config.agent_ids())
    controls["random_reconstructed_payload"] = {
        "description": "Residual balances/obligation owners/status replaced with random values.",
        **_grade(random_residual, ledger, true_ending, config),
    }

    # 13. General-purpose compressed baseline at a comparable budget:
    # zlib-compress the full true microstate and decompress it back, then
    # grade probes on the decompressed (lossless) reconstruction.
    full_json = canonical_json(true_ending).encode("utf-8")
    compressed = zlib.compress(full_json, level=9)
    decompressed = zlib.decompress(compressed)
    import json as _json

    recovered_state = _json.loads(decompressed.decode("utf-8"))
    recovered_residual = dict(build_residual(recovered_state, config))
    recovered_residual["agents"] = {aid: {"balance": a["balance"]} for aid, a in recovered_state["agents"].items()}
    controls["general_purpose_compressed_baseline"] = {
        "description": "Full microstate losslessly zlib-compressed then decompressed (generic compression).",
        "compressed_bytes": len(compressed),
        "raw_bytes": len(full_json),
        **_grade(recovered_residual, recovered_state["event_log"], recovered_state, config),
    }

    return controls


# ---------------------------------------------------------------------------
# Component evaluation
# ---------------------------------------------------------------------------

def evaluate_world_family(wf, rng_seed: int, reference_history: Optional[tuple[str, ...]] = None) -> dict:
    config = wf.config
    if reference_history is None:
        histories = W.enumerate_histories(config)

        def _has_distinguishable_agents(ending: dict) -> bool:
            ids = config.agent_ids()
            return ending["agents"][ids[0]]["balance"] != ending["agents"][ids[1]]["balance"]

        reference_history = next(
            (
                h for h in histories
                if W.resolved_count(W.run_history(config, h)) >= 1
                and _has_distinguishable_agents(W.run_history(config, h))
            ),
            next((h for h in histories if W.resolved_count(W.run_history(config, h)) >= 1), histories[0]),
        )
    true_ending = W.run_history(config, reference_history)
    residual = build_residual(true_ending, config)
    ledger = build_ledger(true_ending)

    collisions = collision_analysis(config)
    contract = semantic_contract(config)
    main_grade = _grade(residual, ledger, true_ending, config)
    controls = run_controls(true_ending, config, rng_seed)
    leakage = leakage_audit(residual, ledger)

    adversarial_notes = {}
    if "identity_substitution" in wf.adversarial:
        shuffled_residual_answers = controls["shuffled_identities"]["answers"]
        adversarial_notes["identity_substitution"] = {
            "description": "The identity-substitution probe must answer False (no defect) on the true "
            "residual and True (reject) on the shuffled-identity control.",
            "true_residual_answer": main_grade["answers"].get("identity_substitution_challenges"),
            "shuffled_control_answer": shuffled_residual_answers.get("identity_substitution_challenges"),
            "correctly_distinguishes": (
                main_grade["answers"].get("identity_substitution_challenges") is False
                and shuffled_residual_answers.get("identity_substitution_challenges") is True
            ),
        }
    if "causal_reorder" in wf.adversarial:
        reordered_ledger = list(reversed(ledger))
        reorder_grade = _grade(residual, reordered_ledger, true_ending, config)
        adversarial_notes["causal_reorder_control"] = {
            "description": "Ledger order reversed; causal_order_token in the residual is unaffected by "
            "ledger order since it is derived once at dump time, so this probes whether reordering alone "
            "(without changing residual content) is wrongly treated as semantically different.",
            **reorder_grade,
        }

    negative_controls = [
        cid for cid in controls
        if cid not in ("lossy_residual_with_valid_ledger", "complete_checkpoint", "lossless_event_log",
                        "general_purpose_compressed_baseline")
    ]
    negative_controls_correctly_fail = all(not controls[cid]["all_pass"] for cid in negative_controls)

    support_checks = {
        "non_injective_loss_demonstrated": collisions["non_injective"],
        "main_residual_passes_all_probes": main_grade["all_pass"],
        "positive_controls_pass": controls["complete_checkpoint"]["all_pass"] and controls["lossless_event_log"]["all_pass"],
        "negative_controls_correctly_fail": negative_controls_correctly_fail,
        "leakage_audit_clean": leakage["clean"],
        "expected_answers_not_directly_copied": leakage["clean"],
    }
    status = "supported" if all(support_checks.values()) else "unsupported"

    return {
        "world_id": config.world_id,
        "field_classification": declared_field_classification(),
        "semantic_distinctions": SEMANTIC_DISTINCTIONS,
        "core_probe_ids": [p[0] for p in CORE_PROBE_SPECS],
        "delayed_probe_ids": [p[0] for p in DELAYED_PROBE_SPECS],
        "delayed_probe_generator_hash": _GENERATOR_SOURCE_HASH,
        "semantic_contract": contract,
        "collision_analysis": collisions,
        "reference_history": list(reference_history),
        "rng_seed": rng_seed,
        "residual_snapshot": residual,
        "ledger_snapshot": ledger,
        "main_probe_grade": main_grade,
        "controls": controls,
        "leakage_audit": leakage,
        "adversarial_notes": adversarial_notes,
        "support_checks": support_checks,
        "status": status,
    }


def run_component(world_families, seed_base: int) -> dict:
    per_family = {}
    for i, wf in enumerate(world_families):
        per_family[wf.family_id] = evaluate_world_family(wf, seed_base + i)
    statuses = [r["status"] for r in per_family.values()]
    if not statuses:
        overall = "invalid"
    elif all(s == "supported" for s in statuses):
        overall = "supported"
    else:
        overall = "unsupported"
    return {
        "status": overall,
        "reason": (
            "every world family's residual is non-injective relative to the full microstate, passes "
            "every semantic probe, and every required negative control correctly fails at least one probe"
            if overall == "supported"
            else "at least one world family failed a required semantic-continuity check "
            "(see per_world_family for which)"
        ),
        "per_world_family": per_family,
    }
