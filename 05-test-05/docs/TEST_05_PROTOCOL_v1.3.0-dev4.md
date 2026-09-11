# Animus Omega Test 05
## Revised Development Protocol v1.3.0-dev4

Status: DEVELOPMENT ONLY
Confirmation: FORBIDDEN
Interpretation: Bounded software experiment on implemented worlds only

This protocol does not test consciousness, subjective experience, love, meditation, physical cosmology, or whether our universe is a simulation.

A supported result applies only to the implemented finite models and this exact frozen protocol.

"Not supported" does not mean "disproved."
"Ready for review" does not mean "confirmed," "accepted," or "published."

v1.2.0-dev3 is preserved unchanged at `evidence/test05/revised_development_v1.2.0-dev3/`, classified in all future reporting as: **informative development run, invalid for protocol acceptance** (reason: the overall not_supported direction remained informative, but the run did not fully comply with its own frozen protocol -- the runtime contract omitted mandatory section-8 fields and the integrated evaluator omitted 2 of the 16 required section-17 gates). Its own post-run audit is preserved unchanged at `evidence/test05/reviews/POST_RUN_AUDIT_v1.2.0-dev3.md`. Neither is rescored, regenerated, or altered by this protocol version.

==================================================
0. AMENDMENTS FROM v1.2.0-dev3
==================================================

This version makes the following corrections, identified by the post-run audit of v1.2.0-dev3 and this protocol's own explicit review. Every amendment is a correction to the IMPLEMENTATION or CONFIGURATION; no acceptance criterion is weakened and no threshold is loosened to obtain a pass.

1. The beginning contract (section 8) now carries all 18 mandatory fields, not 2. `boundary.locked_beginning_contract(config, protocol_version)` builds every field; `execute_J` additionally echoes `world_family_id` and `protocol_version` into the next beginning, and `contract_satisfied` independently verifies both round-trip -- proof J actually reads more of the contract than the 2 operational fields v1.2.0-dev3 propagated. (Note: section 8's field list has 18 distinct named items, not 17 as v1.2.0-dev3's development-report shorthand miscounted; this is corrected here.)
2. The validator now checks every mandatory contract field's presence, Python type, and (where independently derivable) frozen value against its own recomputation from other frozen sources, plus evidence that J actually consumed the fuller content -- not merely that the schema is documented alongside a narrower runtime object.
3. `integrated.evaluate()` is rewritten as an explicit, one-gate-per-required-property structure: exactly 16 named gates, one per section 17 item, each fed by all six component results (boundary, residual, observer, resource, expansion, execution_matrix).
4. Two of those 16 gates -- `expansion_and_contraction` and `fault_control_validity` -- are REAL gates reading `expansion_result` and `execution_matrix_result` directly. v1.2.0-dev3 never wired either component into the integrated gate table at all; two same-topic, different-content gates occupied their slots instead.
5. No gate in this version stands in for a different required property by name resemblance alone. Every gate name in `runs/integrated_gates.json` corresponds exactly to the section-17 item it gates.
6. A protocol-to-code gate registry (`protocol/gate_registry.json`) lists, for every one of the 16 gates: its governing protocol clause, its evidence source path, its generator-side evaluator, and its independent validator check.
7. The independent validator derives the integrated status with its OWN separate implementation (`validator._independent_integrated_evaluation` and its 16 `_independent_gate_*` functions) and does NOT call or reuse `integrated.evaluate()`. A defect in the production evaluator can no longer silently reproduce itself in the "independent" derivation.
8. New corruption tests remove each of the 16 gates individually, flip each gate's boolean individually, remove each of the 18 mandatory contract fields individually, and prove that integrated `supported` is structurally impossible while any required gate fails.
9. World-family dimensions are corrected (friendly: 3 agents/1 obligation/history_length 5; adversarial: 4 agents/2 obligations/history_length 6) so the section-16 expansion/contraction inequality is mathematically achievable AND actually witnessed by an exhaustively-enumerated history, verified empirically before freeze, not merely by ceiling arithmetic.
10. `expansion.preflight_feasibility_check()` actually runs the exhaustive search against every family's configured dimensions before freeze; `run.freeze()` calls it and raises `RuntimeError` (refusing to freeze) if any family's configured maximum represented-world size cannot satisfy the inequality.
11-12. The two causal_reorder mismatches from v1.2.0-dev3 were investigated mechanically (see `execution_matrix._causally_significant_reorder`'s docstring): the swap-pair selection accepted any "earlier index" pair rather than an immediately-dependent pair, so a non-adjacent pair (e.g. o0/o2 in a 3-chain) could leave the real gating dependency (o1) untouched, producing an inert reorder. This was an implementation defect, fixed by requiring the swapped pair be an immediate dependency -- not a weakened prediction. The same mechanical investigation, applied to a newly-observed `duplicate_event` mismatch under the corrected world dimensions, found the same class of defect (`ledger_obj[0]` is not guaranteed detectable if it is a "move" whose preconditions still hold when reprocessed) and fixed it the same way (`_duplicate_a_resolve_entry`, which duplicates a "resolve" entry -- unconditionally detectable via "already_closed" -- rather than entry 0 unconditionally). Both fixes are verified empirically: 0 mismatches across both families under the new dimensions and seeds.
13. The primary observer definition and thresholds (section 14) are unchanged from v1.2.0-dev3. Observer access was not reduced in response to it detecting the boundary.
14-15. The three regression baselines' resource advantage over the proposed architecture is analyzed (see the development report's resource-baseline analysis), not removed, and the primary metric (peak canonical bytes) is unchanged.
16-17. A two-stage digest replaces the single canonical_digest concept: stage 1 (`canonical_digest`, documented as the "evidence_digest") covers the frozen protocol, configuration, source identity, and every raw/component evidence value -- everything `execute()` produces. Stage 2 (`assessment_digest`, in `hashes/digest_manifest.json`) covers stage 1 plus the independently-derived integrated determination, the validator's own validation report, and the final evidence manifest. Both digests and their exact coverage are recorded in the development report.
18-19. New development seeds are used (friendly: 17001-17003; adversarial: 18001-18003), verified disjoint from every prior protocol version's development seeds, the pilot's seeds, tuning seeds, and the reserved confirmatory bands. No reserved or confirmatory seed is used.
20. Failures are preserved; the run stops after independent validation, without running confirmation.

==================================================
1. ASSIGNMENT
==================================================

Inspect the existing Test 05 repository, preserve the earlier pilot AND the v1.2.0-dev3 revised run, implement this further-revised protocol, run it using development seeds only, independently validate the evidence, and produce a development report.

Do not:

- Use reserved confirmatory seeds
- Modify frozen evidence from earlier tests or protocol versions
- Overwrite the Test 05 pilot or the v1.2.0-dev3 run
- Hardcode expected outcomes
- Branch simulation behavior on arm names or IDs
- Change thresholds after execution begins
- Weaken acceptance criteria after seeing results
- Run confirmation automatically
- Claim that the complete Animus Omega conjecture is confirmed or disproved

A failed development result is acceptable and must be preserved.

==================================================
2. PRIOR RUNS
==================================================

Before changing or running anything:

1. Confirm the pilot (`superseded_development_pilot`) and v1.2.0-dev3 (`revised_development_v1.2.0-dev3`, plus its post-run audit) remain byte-identical to their sealed state.
2. Classify v1.2.0-dev3 in all future reporting exactly as: informative development run, invalid for protocol acceptance (see section 0's amendment list for the reason).
3. Do not rescore either prior run using this protocol.

This revised run must have a separate directory, protocol version, configuration hash, result, and evidence digest: `revised_development_v1.3.0-dev4/`.

==================================================
3. RESEARCH QUESTIONS
==================================================

Unchanged from v1.2.0-dev3: 05A reciprocal closure, 05B-loss genuine information loss, 05B-sem semantic continuity, 05B-leak leakage audit, 05C observer boundary (+ 05C-pos positive control), 05-ledger ledger causality, 05-faults fault controls, 05D resource advantage, 05E integrated result.

==================================================
4. ALLOWED RESULT STATUSES
==================================================

Unchanged from v1.2.0-dev3:

Component statuses: supported, unsupported, inconclusive, ineligible, invalid, not_applicable.

Integrated statuses: supported, not_supported, inconclusive, invalid.

Report every component independently. The integrated result may be `supported` only if every one of the 16 required gates is supported. Component successes remain visible when the integrated result is not supported.

==================================================
5. DEVELOPMENT SEEDS
==================================================

Use only:

Friendly family: 17001, 17002, 17003
Adversarial family: 18001, 18002, 18003

Before execution, verify that these seeds: were not used by the pilot; were not used by v1.2.0-dev3; are not reserved confirmatory seeds; are not tuning seeds; are not prohibited by an existing seed registry (`seeds.check_v4_seed_eligibility`).

If any seed is unavailable, stop before tick zero and request a revised seed assignment. Do not substitute a seed silently.

For each adversarial seed, run the full 10-execution fault matrix (unchanged mutation set): unfaulted baseline, identity substitution, obligation deletion, contradictory ledger, missing provenance, stale event, duplicate event, causal reorder, no-ledger control, random reconstruction control.

Each execution must record: seed, execution ID, mutation ID, before hash, after hash, mutated fields, predicted failure, observed failure.

If a reserved seed is requested, refuse execution and write a reserved-seed rejection record.

==================================================
6. WORLD FAMILIES
==================================================

Use exactly two world families for this development run. Dimensions are corrected from v1.2.0-dev3 (amendment 9) so the section-16 expansion/contraction inequality is achievable:

### Family 1: Friendly obligation world

3 agents, 1 obligation, total_resource 3, history_length 5 (standard) / 7 (observer). R(genesis)=2; required R(t1)>=4; provable ceiling 4 -- tight but achievable, and empirically confirmed witnessed by an enumerated history before freeze.

### Family 2: Adversarial collision world

4 agents, 2 obligations, total_resource 4, history_length 6 (standard) / 9 (observer). R(genesis)=3; required R(t1)>=6; provable ceiling 6 -- tight but achievable and empirically confirmed. Exactly 2 obligations so causal_reorder has a real, immediately-dependent resolve pair.

Do not describe separate arms or seeds from one template as independent world families.

Prefer exact enumeration. If an action-history space exceeds one million histories, mark exhaustion inconclusive or reduce the model before protocol freeze. Do not quietly replace enumeration with sampling. (Both families' standard_config enumeration spaces -- 1,024 and 4,096 histories respectively -- and observer_config spaces -- 16,384 and 262,144 -- are far under this bound.)

==================================================
7. PROTOCOL FREEZE
==================================================

Before tick zero, create, serialize, and hash everything v1.2.0-dev3 required, plus (amendments 6, 10):

- protocol-to-code gate registry
- expansion/contraction feasibility proof

`run.freeze()` refuses to run (raises `RuntimeError`) if the expansion/contraction feasibility check fails for any world family (amendment 10) -- a mechanical, non-bypassable preflight gate, not merely a documented check.

Use canonical JSON (sorted keys, UTF-8, deterministic numeric representation, one trailing newline). The evidence directory must contain only protocol and configuration material before tick zero. No simulation result may be used to alter a frozen file.

==================================================
8. BEGINNING CONTRACT
==================================================

Before tick zero: build the beginning contract; serialize it to canonical bytes; write its SHA-256 digest; record `committed_at_tick = -1`; make it immutable during execution; pass the actual contract object into the boundary transition; use the hash only to verify commitment and immutability.

Minimum contract contents (18 distinct fields; amendment 1 corrects v1.2.0-dev3's mislabeling of this list as 17 and its implementation of only 2):

- protocol version
- world-family ID
- physics-configuration hash
- identity-table commitment
- relationship schema
- obligation schema
- causal-order rules
- locked beginning payload schema
- dump operator
- residual schema
- ledger schema
- observer-specification hash
- resource-objective ID
- declared causal path
- intentionally discarded fields
- irrelevant fields
- frozen semantic-probe IDs
- delayed-probe generator hash

All 18 are implemented in `boundary.locked_beginning_contract(config, protocol_version)`. `execute_J` reads and echoes `world_family_id` and `protocol_version` (in addition to `min_resolutions`) into the next beginning; `contract_satisfied` independently verifies all three round-trip, proof J actually consumed more than the 2 pre-v1.3.0-dev4 operational fields.

Required transition (unchanged):

S_next = J(reconstructed_state, ledger, return_value_from_ending, beginning_contract)

The validator must reject everything v1.2.0-dev3 required, plus (amendment 2): a mandatory contract field missing, wrongly typed, or (where independently derivable) not matching its frozen value from another module's own frozen content; and a beginning contract for which J's output shows no evidence of having consumed the fuller field set.

Distinguish: exact microstate equality; satisfaction of the beginning contract; semantic equivalence; illegal direct copying.

==================================================
9. SIMULATOR ISOLATION
==================================================

Unchanged from v1.2.0-dev3. The simulator may receive only: world state, action history, ledger, beginning contract, physics configuration, return value or null. It must not receive: report-layer arm name, expected result, `should_close`, `fault_control`, expected status, integrated-support expectation, integer ID that encodes expected behavior.

Interventions must operate on actual data: construct baseline input; apply a declared mutation; record the mutation path and before/after hashes; execute the simulator using only the resulting data; attach human-readable names later in the report layer.

Add a source and runtime audit for label-driven behavior.

==================================================
10. TEST 05A: RECIPROCAL CLOSURE
==================================================

Unchanged from v1.2.0-dev3 (all 12 arms, both families' support requirements, and the "report the first mismatching field and transition" rule), except that the beginning contract each arm commits now carries the full 18-field content (section 8).

==================================================
11. TEST 05B: LOSS AND SEMANTIC CONTINUITY
==================================================

Unchanged from v1.2.0-dev3: field classification into copied/reconstructed/derived-later/intentionally-discarded; genuine-loss requirements; the 9 frozen core semantic probes (9 of 9 required); the 8 delayed behavioral probes (8 of 8 required, generated only after the lossy dump is committed).

==================================================
12. LEAKAGE AUDIT
==================================================

Unchanged from v1.2.0-dev3.

==================================================
13. LEDGER CAUSALITY AND FAULT CONTROLS
==================================================

Unchanged from v1.2.0-dev3, except (amendments 11-12): the causal_reorder and duplicate_event mutation mechanisms are corrected so their swap/duplication target is unconditionally detectable (an immediately-dependent resolve pair; a resolve entry rather than entry 0), not merely usually detectable. Every required fault must still produce its frozen predicted rejection or semantic failure, with no exceptions carved out after the fact.

==================================================
14. TEST 05C: OBSERVER BOUNDARY
==================================================

Unchanged from v1.2.0-dev3 in every particular: the primary bounded observer's definition, the exact statistics reported, phase matching, the primary support threshold (TV<=0.05 and accuracy<=0.55), the sensitivity ladder, and the positive control (TV>=0.25 or accuracy>=0.75). Amendment 13: observer access is not reduced merely because it detected the boundary in v1.2.0-dev3; any future change to this section requires a documented mechanistic justification, not a result-driven one.

==================================================
15. TEST 05D: RESOURCE COMPARISON
==================================================

Unchanged from v1.2.0-dev3: only semantically eligible arms may enter the comparison; the frozen objectives (primary: peak canonical bytes; secondary: total canonical byte-ticks; diagnostic: operation count; noncanonical diagnostic: wall-clock, excluded from the canonical digest); the same 10 required baselines; full byte accounting across all 10 declared categories; the strict support rule (peak canonical bytes strictly lower than every eligible baseline in both families, with byte-ticks never rescuing a primary-metric loss).

Amendments 14-15: the three baselines that beat the candidate on peak bytes in v1.2.0-dev3 (general-purpose lossless compression, general-purpose lossy compression at matched fidelity, scripted cyclic replay) are analyzed for why, in the development report, rather than removed or redefined away. No baseline is dropped and no primary metric is changed to manufacture a pass.

==================================================
16. EXPANSION AND CONTRACTION
==================================================

Unchanged definition: R(t) = live entities + live represented-region cells. Support requires t0 < t1 < t2 with R(t1) >= 2*R(t0) and R(t2) <= R(t0)+1, for the candidate in both families. Amendment 9-10: world-family dimensions are corrected so this is mathematically achievable, and `expansion.preflight_feasibility_check` mechanically confirms at least one enumerated history actually exhibits the pattern before freeze -- refusing to freeze otherwise.

==================================================
17. INTEGRATED RESULT
==================================================

The same candidate system must demonstrate all 16 properties from v1.2.0-dev3's list, unchanged:

1. Required expansion and contraction
2. Beginning contract committed before tick zero
3. Ending-derived return value
4. Executed J transition
5. At least one closing history
6. At least one non-closing history
7. Causal endpoint sensitivity
8. Genuine information loss
9. Semantic continuity on all core probes
10. Semantic continuity on all delayed probes
11. Clean leakage audit
12. Ledger causality
13. Valid fault controls
14. Primary observer indistinguishability
15. Full-state observer boundary detection
16. Fidelity-matched resource advantage

Amendments 3-6: each of these 16 items is now gated by its OWN named gate (`integrated.evaluate()` returns exactly 16 gate entries), fed by real evidence from all six components (boundary, residual, observer, resource, expansion, execution_matrix). No gate stands in for a different item by name resemblance. A protocol-to-code gate registry documents, per gate, its governing clause, evidence source, evaluator, and validator check.

Integrated result rules (unchanged): missing canonical evidence -> invalid; prohibited leakage -> semantic result invalid; failed positive control -> observer result invalid; missing frozen observer threshold -> observer result inconclusive; semantic failure -> resource result ineligible; ignored return value -> reciprocal closure unsupported; any unsupported required gate -> integrated result not supported; any inconclusive required gate -> integrated result inconclusive unless another required gate is already unsupported; any invalid required gate -> integrated result invalid; every required gate supported -> integrated result supported.

Do not use "disproved" as a result status.

==================================================
18. INDEPENDENT VALIDATOR
==================================================

Create a separate validator process that recomputes conclusions from raw evidence. It must not trust summary statuses.

Amendment 7: the validator's integrated-status derivation must be a structurally separate implementation from the generator's `integrated.evaluate()` -- it must not call or import that function's gate-evaluation logic. Each of the 16 gates gets its own independently-written validator function.

The validator must reject everything v1.2.0-dev3 required, plus: a mandatory beginning-contract field missing, wrongly typed, or not matching an independently-derivable frozen value; any of the 16 integrated gates individually removed or flipped without the integrated status changing accordingly; integrated `supported` reported while any of the 16 gates is not `ok`.

Create at least one corruption fixture for every rejection class, including (amendment 8): removing each of the 16 gates individually, flipping each gate's boolean individually, removing each of the 18 mandatory contract fields individually, and a fixture proving integrated `supported` is impossible while any required gate fails.

The validator must return a nonzero exit code for corrupted evidence and zero only for structurally valid evidence. A zero exit code does not mean the conjecture was supported.

==================================================
19. RESULT FORMAT
==================================================

The canonical result must include everything v1.2.0-dev3 required, plus:

- the protocol-to-code gate registry hash
- the expansion/contraction feasibility proof
- stage-1 evidence digest (`canonical_digest`) and its exact coverage
- stage-2 assessment digest (`assessment_digest`, filled in only by the validator) and its exact coverage

The integrated status must begin as `pending` or remain absent until the validator derives it. Do not initialize it as supported or not supported.

==================================================
20. REQUIRED DIRECTORY STRUCTURE
==================================================

evidence/test05/
  superseded_development_pilot/
  revised_development_v1.2.0-dev3/  (preserved unchanged; classified informative/invalid-for-acceptance)
  reviews/  (preserved unchanged; contains the v1.2.0-dev3 post-run audit and its classification record)
  revised_development_v1.3.0-dev4/
    protocol/
    config/
    worlds/
    runs/
    results/
    hashes/
    validator/
    report/

Never overwrite a sealed directory.

==================================================
21. EXECUTION ORDER
==================================================

1. Confirm the pilot and v1.2.0-dev3 remain untouched.
2. Classify v1.2.0-dev3 per section 0/2.
3. Implement corrections 1-15 (contract, validator, gate registry, independent derivation, corruption tests, world dimensions, feasibility preflight, causal-reorder/duplicate-event investigation, observer unchanged, resource-baseline analysis).
4. Implement the two-stage digest.
5. Run unit tests before protocol freeze.
6. Run validator corruption tests before protocol freeze.
7. Correct implementation defects found before the freeze.
8. Produce the final protocol, configuration, and gate-registry hashes.
9. Verify the expansion/contraction feasibility proof passes for every world family.
10. Verify that the evidence directory contains no run evidence.
11. Verify that the simulator accepts no report labels.
12. Verify that reserved seeds remain untouched.
13. Produce a preflight report per section 22a and stop until it is reviewed.
14. Freeze the protocol.
15. Execute seeds 17001-17003 and 18001-18003.
16. Do not modify frozen code, protocol, configuration, thresholds, or probes during execution.
17. If execution fails, preserve the failure.
18. Run the independent validator.
19. Produce the component dashboard.
20. Produce the Markdown development report, recording both digests and their exact coverage.
21. Stop without running confirmation.

If a defect is discovered after tick zero: preserve the affected run; mark it invalid or aborted; do not patch it in place; create a new protocol version before rerunning.

==================================================
22. FINAL HANDOFF REPORT
==================================================

At completion, report everything v1.2.0-dev3's list required, plus: the gate registry; the independent-validator architecture (confirming it does not reuse the production evaluator); the expansion feasibility proof; the causal-reorder/duplicate-event investigation outcome; the observer-protocol status (unchanged, with reason); the resource-baseline analysis; both digests and their exact coverage.

Do not call the result accepted, confirmed, or published.

==================================================
22a. PREFLIGHT REPORT (BEFORE TICK ZERO)
==================================================

Before tick zero, provide a preflight report showing: v1.2.0-dev3 remains untouched; the new protocol version; the new seed set; all 18 contract fields implemented; the complete protocol-to-code gate registry; the independent validator architecture; the expansion feasibility proof; the causal-reorder/duplicate-event investigation outcome; the observer protocol status; the resource-baseline analysis; corruption-test results; the completed freeze checklist.

Do not begin v1.3.0-dev4 tick zero until every preflight requirement passes.

==================================================
23. FREEZE CHECKLIST
==================================================

Do not execute tick zero until all are true:

[ ] v1.2.0-dev3 and its post-run audit confirmed untouched
[ ] v1.2.0-dev3 classified (informative development run, invalid for protocol acceptance)
[ ] Revised protocol stored and hashed
[ ] Observer specification stored and hashed
[ ] Physics configuration stored and hashed
[ ] Beginning-contract schema stored and hashed (all 18 fields documented as operationally implemented)
[ ] Beginning contracts committed (all 18 fields present, typed, and frozen-value-checked)
[ ] Causal-path specification stored and hashed
[ ] Field-classification manifest stored and hashed
[ ] Delayed-probe generator stored and hashed
[ ] Fault predictions stored and hashed
[ ] Mutation definitions stored and hashed
[ ] Semantic probes stored and hashed
[ ] Byte-accounting specification stored and hashed
[ ] Resource objective fixed to peak canonical bytes
[ ] Protocol-to-code gate registry stored and hashed
[ ] Expansion/contraction feasibility proof stored, hashed, and confirmed feasible for every world family
[ ] Seed list fixed (17001-17003 / 18001-18003)
[ ] Seeds checked against pilot, v1.2.0-dev3, tuning, and reserved registries
[ ] Simulator receives no report labels or expected outcomes
[ ] Unit tests pass
[ ] Validator corruption tests pass (including per-gate and per-contract-field removal/flip fixtures)
[ ] Revised evidence directory contains no execution evidence
[ ] Confirmation path remains disabled

When every item passes, provide the preflight report (section 22a) for review. Only once every preflight requirement passes may the revised development experiment run once, be validated, preserved, reported, and stopped.
