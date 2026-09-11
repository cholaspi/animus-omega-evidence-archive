# Test 05 development protocol, v1.2.0-dev3

**Status:** development protocol, version `1.2.0-dev3`. Supersedes the
acceptance criteria of `TEST_05_PROTOCOL.md` (the original pilot protocol)
for all future runs. The pilot's own run (`superseded_development_pilot`,
sealed at `evidence/test05/superseded_development_pilot/`) is not
reinterpreted under this revision; it remains evaluated only against the
criteria that existed when it ran. This document is frozen for hashing
purposes (`protocol_hash` in every v1.2.0-dev3 result) as of the commit
recorded in that result's `source_hash`. "Frozen" means fixed for this
development run, not confirmatory: no reserved seed may be executed under
this document, and once the freeze commit is made, no source, protocol,
configuration, threshold, or probe may change before that run executes.

This revision was requested before protocol v1's pilot conclusions were
accepted, specifically to close gaps identified in that pilot's own design:
observer-ladder cherry-picking risk, resource-metric ambiguity, world-family
proliferation, a contract that could in principle be represented by only its
hash, no explicit runtime audit against arm-label leakage into the
simulator, and semantic probes whose instance parameters were all fixed in
advance rather than partly generated from the actual dump.

## A. Gated dashboard

`component_results` now reports seven entries instead of five:
`reciprocal_closure`, `genuine_information_loss`, `semantic_continuity`,
`observer_boundary`, `ledger_causality`, `resource_advantage`,
`integrated_result`. `genuine_information_loss` and `semantic_continuity`
were previously bundled into one 05B status; they are now independently
derived (see `integrated.genuine_information_loss_result` and
`integrated.semantic_continuity_result`) so a genuine-loss finding is never
obscured by an unrelated probe failure or vice versa. `resource_advantage`
is downgraded to `ineligible` whenever `semantic_continuity` is not
`supported`, regardless of what 05D's own internal computation found
(`integrated.resource_advantage_result`) -- these are the *same* functions
the integrated gate table calls, so the dashboard and the gate table can
never silently disagree. An integrated failure never erases or hides a
component's own result: every component above is written to evidence and
reported regardless of `integrated_result.status`.

## B. One primary observer

`observer.py` freezes exactly one bounded-observer claim,
`primary_bounded_observer`: radius-one (own state plus the single ring edge
it participates in), two ticks of memory, its own identity, its direct
relationship, and its current obligation status. It explicitly excludes a
global clock, absolute cycle position, boundary marker, full-state access,
and ledger access. `observer.PRIMARY_OBSERVER_SPEC` is hashed at import
time (`observer._PRIMARY_OBSERVER_SPEC_HASH`), before any world family is
evaluated. Every other rung of the v1 ladder (`radius_one_local`,
`local_short_memory`, `local_relationship_memory`, `local_obligation_history`,
`bounded_longer_memory`) is retained but demoted to
`role=sensitivity_analysis`: reported for context, never an alternate path
to "supported." The full-state observer remains a mandatory
`role=positive_control`; if it fails to detect the boundary the whole 05C
result for that world family is `invalid`. All exact-distribution
machinery (window, phase-matched interior start, TV distance, Bayes-optimal
accuracy, mutual information, likelihood-ratio summary, both frozen
thresholds) is unchanged from v1 and remains exact (full enumeration, no
sampling).

## C. Frozen resource objective

`resource.py`'s primary objective is now **peak canonical bytes at matched
semantic fidelity**, and it alone determines
`resource_advantage`/`pareto.status`. Total byte-ticks is reported as a
secondary objective and deterministic operation count as a diagnostic, but
neither can flip a "supported"/"unsupported" conclusion the primary
objective disagrees with (v1 required dominance on both peak bytes and
byte-ticks together, which risked looking like the metric was chosen after
seeing which one was favorable). Wall-clock duration is measured per arm
but now returned as a *separate* `noncanonical_timing` structure
(`resource.evaluate_world_family` returns `(canonical, noncanonical_timing)`
as a tuple) that is written to disk for transparency but deliberately
excluded from the evidence manifest and therefore from `canonical_digest`,
since it is not reproducible run-to-run even with identical seeds. Every
arm now reports an explicit `resource_breakdown` across ten declared
categories (authoritative state, residual, ledger, event log, observer
buffers, checkpoints, reconstruction buffers, indexes, lookup tables,
retained preprocessing) -- categories an arm does not use are reported as
zero, never omitted.

## D. Two world families

`worlds.py` now declares exactly two families -- `friendly` (3 agents, a
2-obligation chain, no adversarial conditions) and `adversarial` (3 agents,
a 3-obligation chain, with identity-substitution and causal-reordering
probes layered on top of the residual-collision/obligation-deletion/
contradiction/stale-event/duplicate-event controls that already apply to
every family) -- replacing v1's seven. Each family carries two
*configurations*: `standard_config` (used by 05A/05B/05D) and
`observer_config` (same agent count and obligation structure, longer
history, used only by 05C so a phase-matched interior window exists). This
is 2 world families and 4 configurations, not "2 world families" doing
double duty as "4 independent" ones, and not "many arms from one template"
miscounted as several families.

## E. Strengthened beginning commitment

`boundary.FrozenContract` is an immutable object (data + content hash +
a `consumed` flag) constructed once per attempted transition, strictly
before that transition's history executes. `execute_J` now takes the
actual `FrozenContract` object (not a bare hash) and calls `.consume()` on
it, folding a value from its data (`declared_min_resolutions`) into the
constructed next-beginning -- proof the transition used the real contract,
not merely its hash. `contract_satisfied` first checks `contract.consumed`
(a transition that bypassed `execute_J` entirely, as arms 11/12 do by
design, fails here first) and then checks that the propagated
`declared_min_resolutions` matches the contract's own data. Every world
family's evidence includes a `beginning_commitment` record (the contract's
data, its hash, and a note that it was constructed before any history in
that family was enumerated or executed).

## F. No arm labels in simulator inputs

`label_audit.py` provides a runtime audit,
`audit_no_label_leakage()`, that inspects the actual parameter names (via
`inspect.signature`) of every registered simulator-core function
(`world.step`, `world.replay`, `world._apply_action_effect`,
`world.run_history`, `world.relevant_ledger`, `world.return_value_of`,
`boundary.execute_J`, `boundary.contract_satisfied`,
`boundary.exact_closure`) against a list of forbidden substrings (arm id/
name/label/index, expected, should_close, fault flags, integrated-support
expectations, closure status). None of these functions take such a
parameter; arm ids and human-readable descriptions are attached only by the
report-layer helper `_run_arm`, strictly after the simulator core above has
already produced its result.

## G. Core vs. delayed semantic probes

`residual.py` splits the eight v1 probes (plus two new ones,
`identity_continuity` and one merged into `resource_allocation_commitments`)
into nine **frozen core probes** (identity continuity, obligation
ownership, relationship permissions, causal ordering, provenance, deadline
behavior, resource-allocation commitments, permitted future actions,
observer-visible consequences) with fixed instance parameters, and five
**delayed behavioral probes** (new counterfactual actions, previously
unseen obligation queries, new resource disputes, identity-substitution
challenges, causal-prerequisite challenges) whose concrete instance
parameters -- which agent, which obligation, which pair -- are chosen by
`generate_delayed_probe_instances`, a frozen, hashed generator function
whose *output* depends on the actual committed residual/ledger content
(e.g. "the agent currently holding the most balance," "the pair of agents
whose balances are closest"), computed only after the lossy dump exists.
The `shuffled_identities` control now swaps the generator's dynamically
chosen pair rather than a hardcoded pair. The leakage audit, and the six
distinctions (`residual.SEMANTIC_DISTINCTIONS`: exact microstate equality,
preservation by direct copying, reconstruction, derivation through later
execution, behavioral semantic equivalence, intentionally discarded
information) are unchanged in substance but now explicitly recorded in
evidence rather than left to prose.

## H. Sensitivity and specificity for causal closure interventions

`boundary.serialize_causal_path` records, for a given history and
intervention tick, the full declared causal path (intermediate action ->
later state -> ending state -> return value -> reconstruction).
`boundary.diff_causal_paths` compares this path for a baseline history
against a mutated one and reports, per stage, whether it actually differs.
Arms 6 (relevant intermediate mutation) and 7 (irrelevant intermediate
mutation) now each carry a `causal_path_diff`, and `evaluate_world_family`
requires (as part of `support_checks`) that the relevant arm's path
actually differs somewhere downstream (sensitivity) and the irrelevant
arm's path does not differ anywhere (specificity) -- not merely that
closure broke or held, but that the underlying executed data moved or
didn't.

## I. Independent validator

`validator.py` (new) independently recomputes every conclusion from raw
evidence files rather than trusting any cached `status` field, and rejects:
missing evidence, modified hashes, forbidden (reserved) seeds, a beginning
contract whose commitment cannot be shown to precede execution, a contract
that was never consumed by the transition it is attached to, an ignored
return value, label-driven branching in the simulator core (via
`label_audit`), a "fake" intervention whose causal-path diff shows no
executed data actually changed, residual/ledger answer leakage, incorrect
microstate/collision counts, invalid observer statistics, a failed
positive control, a fidelity-ineligible arm admitted into the resource
comparison, an omitted resource-breakdown category, and integrated support
claimed despite a failed prerequisite gate. `tests/test_validator_corruption.py`
deliberately corrupts a copy of real evidence for each rejection condition
and asserts the validator actually rejects it.

## Seeds

`seeds.PROTOCOL_V2_DEVELOPMENT_SEED_BANDS` (named `V2` in code, meaning
"the revision after the pilot protocol" -- this is the same revision this
document calls `1.2.0-dev3`; 55000s are the pilot's, kept for provenance;
this revision uses 57000s: 05A 57000-57019, 05B 57100-57119, 05C
57200-57219, 05D 57300-57319, 05E 57400-57419) are disjoint from the
pilot's bands and from the reserved confirmatory bands (58000s), so no seed
is reused across protocol versions and no confirmatory seed is reachable from a
development entrypoint.
