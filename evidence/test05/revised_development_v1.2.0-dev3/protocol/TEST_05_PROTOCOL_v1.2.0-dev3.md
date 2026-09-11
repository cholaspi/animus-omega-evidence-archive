# Animus Omega Test 05
## Revised Development Protocol v1.2.0-dev3

Status: DEVELOPMENT ONLY
Confirmation: FORBIDDEN
Interpretation: Bounded software experiment on implemented worlds only

This protocol does not test consciousness, subjective experience, love, meditation, physical cosmology, or whether our universe is a simulation.

A supported result applies only to the implemented finite models and this exact frozen protocol.

"Not supported" does not mean "disproved."
"Ready for review" does not mean "confirmed," "accepted," or "published."

==================================================
1. ASSIGNMENT
==================================================

Inspect the existing Test 05 repository, preserve the earlier pilot, implement this revised protocol, run it using development seeds only, independently validate the evidence, and produce a development report.

Do not:

- Use reserved confirmatory seeds
- Modify frozen evidence from earlier tests
- Overwrite the Test 05 pilot
- Hardcode expected outcomes
- Branch simulation behavior on arm names or IDs
- Change thresholds after execution begins
- Weaken acceptance criteria after seeing results
- Run confirmation automatically
- Claim that the complete Animus Omega conjecture is confirmed or disproved

A failed development result is acceptable and must be preserved.

==================================================
2. PRIOR PILOT
==================================================

Before changing or running anything:

1. Determine whether the previous Test 05 execution is active, completed, failed, or aborted.
2. If active, either:
   - allow it to finish unchanged, or
   - stop it safely and label it `aborted_pilot`.
3. Preserve its source, configuration, evidence, logs, and result.
4. Seal it read-only as:
   `superseded_development_pilot`
5. Record this reason exactly:
   `protocol improvements were specified before accepting its conclusions.`
6. Record:
   - pilot protocol version
   - pilot result path
   - pilot status
   - pilot source hash
   - pilot configuration hash
   - pilot evidence digest
7. Do not rescore the pilot using this revised protocol.

The revised run must have a separate directory, protocol version, configuration hash, result, and evidence digest.

==================================================
3. RESEARCH QUESTIONS
==================================================

Test 05 has separate component questions.

05A: Reciprocal closure

Does information derived from the ending causally and necessarily participate in constructing the next beginning?

05B-loss: Genuine information loss

Is the dump operation non-injective over the frozen finite microstate domain?

05B-sem: Semantic continuity

After genuine loss, do frozen semantic obligations remain satisfied?

05B-leak: Leakage audit

Does the candidate preserve meaning through legitimate causal state, rather than cached answers, labels, or access to discarded information?

05C: Observer boundary

Can a frozen bounded observer distinguish boundary observations from phase-matched interior observations?

05C-pos: Observer positive control

Can a full-state observer detect the boundary?

05-ledger: Ledger causality

Does the narrative ledger causally affect reconstruction or permitted future behavior?

05-faults: Fault controls

Do declared data mutations produce their preregistered failures?

05D: Resource advantage

At matched semantic fidelity, does the candidate use less peak canonical memory than every eligible baseline?

05E: Integrated result

Does the same candidate system satisfy every required component?

==================================================
4. ALLOWED RESULT STATUSES
==================================================

Component statuses:

- supported
- unsupported
- inconclusive
- ineligible
- invalid
- not_applicable

Integrated statuses:

- supported
- not_supported
- inconclusive
- invalid

Report every component independently.

The integrated result may be `supported` only if every required gate is supported. Component successes remain visible when the integrated result is not supported.

==================================================
5. DEVELOPMENT SEEDS
==================================================

Use only:

Friendly family:

- 13001
- 13002
- 13003

Adversarial family:

- 14001
- 14002
- 14003

Before execution, verify that these seeds:

- were not used by the pilot
- are not reserved confirmatory seeds
- are not tuning seeds
- are not prohibited by an existing seed registry

If any seed is unavailable, stop before tick zero and request a revised seed assignment. Do not substitute a seed silently.

Seeds and execution IDs are different.

For each adversarial seed, run:

- unfaulted baseline
- identity substitution
- obligation deletion
- contradictory ledger
- missing provenance
- stale event
- duplicate event
- causal reorder
- no-ledger control
- random reconstruction control

Each execution must record:

- seed
- execution ID
- mutation ID
- before hash
- after hash
- mutated fields
- predicted failure
- observed failure

If a reserved seed is requested, refuse execution and write a reserved-seed rejection record.

==================================================
6. WORLD FAMILIES
==================================================

Use exactly two world families for this development run.

### Family 1: Friendly obligation world

Required characteristics:

- Three agents
- Four or more represented cells
- Explicit identities
- Explicit relationships
- Acyclic obligation ownership
- Explicit causal prerequisites
- Expansion stage
- Contraction stage
- Many-to-one dump
- Exhaustively enumerable histories and microstates

### Family 2: Adversarial collision world

Use the same general size class so exact analysis remains feasible.

Required characteristics:

- Residual collisions
- Identity-substitution opportunities
- Obligation-deletion opportunities
- Contradictory ledger entries
- Missing provenance
- Stale events
- Duplicate events
- Causal reorderings
- Unfaulted baseline in addition to fault executions

Do not describe separate arms or seeds from one template as independent world families.

Prefer exact enumeration. If an action-history space exceeds one million histories, mark exhaustion inconclusive or reduce the model before protocol freeze. Do not quietly replace enumeration with sampling.

==================================================
7. PROTOCOL FREEZE
==================================================

Before tick zero, create, serialize, and hash:

- this protocol
- observer specification
- physics configuration
- beginning-contract schema
- beginning contract for each family
- causal-path specification
- field-classification manifest
- delayed-probe generator source
- fault predictions
- mutation definitions
- semantic probe specification
- canonical byte-accounting specification
- resource objective
- seed list
- baseline definitions

Use canonical JSON:

- sorted keys
- UTF-8
- deterministic numeric representation
- one trailing newline

The evidence directory must contain only protocol and configuration material before tick zero.

No simulation result may be used to alter a frozen file.

==================================================
8. BEGINNING CONTRACT
==================================================

Before tick zero:

1. Build the beginning contract.
2. Serialize it to canonical bytes.
3. Write its SHA-256 digest.
4. Record `committed_at_tick = -1`.
5. Make it immutable during execution.
6. Pass the actual contract object into the boundary transition.
7. Use the hash only to verify commitment and immutability.

Minimum contract contents:

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

Required transition:

S_next = J(
    reconstructed_state,
    ledger,
    return_value_from_ending,
    beginning_contract
)

The validator must reject:

- contract creation after tick zero
- contract modification after execution begins
- a transition that does not read contract fields
- a return value that is computed but ignored
- direct copying of the original beginning
- hidden lookup of the original beginning
- reconstruction using discarded source state

Distinguish:

- exact microstate equality
- satisfaction of the beginning contract
- semantic equivalence
- illegal direct copying

==================================================
9. SIMULATOR ISOLATION
==================================================

The simulator may receive only:

- world state
- action history
- ledger
- beginning contract
- physics configuration
- return value or null

It must not receive:

- report-layer arm name
- expected result
- `should_close`
- `fault_control`
- expected status
- integrated-support expectation
- integer ID that encodes expected behavior

Interventions must operate on actual data:

1. Construct baseline input.
2. Apply a declared mutation.
3. Record the mutation path and before/after hashes.
4. Execute the simulator using only the resulting data.
5. Attach human-readable names later in the report layer.

Add a source and runtime audit for label-driven behavior.

==================================================
10. TEST 05A: RECIPROCAL CLOSURE
==================================================

Freeze this causal pathway:

intermediate action
→ later state
→ ending state
→ ending-derived return value
→ reconstruction or merge
→ J
→ next beginning

Enumerate all admissible histories where feasible.

Required baseline and necessity interventions:

1. Correct return value
2. Missing return value
3. Deterministically randomized return value
4. Incompatible return from another history
5. One-symbol mutation of a contract-relevant endpoint component
6. Causally relevant intermediate-action mutation
7. Corrupted ledger
8. Corrupted reconstruction
9. Bypassed return transition
10. Beginning construction without endpoint information
11. Open-chain control without J

Required specificity interventions:

1. Irrelevant intermediate mutation
2. Intentionally discarded irrelevant-detail mutation

Apply irrelevant-detail mutations before the dump and run the complete pathway. Do not apply them only after the information has become inaccessible.

### Deterministic random return

Generate replacement bytes from a SHA-256 counter stream derived from:

- protocol hash
- family ID
- seed
- history hash
- mutation ID
- counter

### Swapped return

The donor return must differ on at least one contract-relevant field. Record the field before execution.

If no incompatible donor exists, mark this intervention `not_applicable`. Do not count a semantically equivalent swap as a failed necessity intervention.

### 05A support requirements

Report each family separately.

A family supports reciprocal closure only if:

1. At least one natural history satisfies the locked beginning contract after J.
2. At least one admissible history does not.
3. Missing, random, incompatible swapped, and endpoint-mutated returns break contract satisfaction.
4. A causally relevant intermediate intervention breaks contract satisfaction.
5. Irrelevant interventions preserve contract satisfaction and frozen semantics.
6. The beginning contract existed before tick zero.
7. J consumed the contract.
8. J consumed endpoint-derived information.
9. Direct-copy and ignored-return detectors did not fire.
10. Required histories were exhaustively enumerated.

Overall 05A is supported only if both families are supported.

Report the first mismatching field and transition for every failed intervention.

==================================================
11. TEST 05B: LOSS AND SEMANTIC CONTINUITY
==================================================

Before execution, classify every state field as exactly one of:

- copied
- reconstructed
- derived later
- intentionally discarded

Copied information must not be described as reconstructed.

### Genuine loss

For each family, calculate exactly:

- number of admissible microstates
- number of distinct residuals
- cardinality reduction
- collision groups
- maximum preimage size
- discarded fields

Genuine loss is supported only if:

- the dump is non-injective
- at least two admissible microstates share a residual
- at least one field is intentionally discarded
- all counts recompute from raw evidence

### Frozen core semantic probes

Use all nine:

1. Identity continuity
2. Obligation ownership
3. Relationship permissions
4. Causal ordering
5. Provenance
6. Deadline behavior
7. Resource allocation
8. Permitted future actions
9. Observer-visible consequences

The unfaulted candidate must pass 9 of 9 in each family. Do not average across probes or families.

Fault executions must fail or be rejected in the direction specified in the frozen fault-prediction file.

### Delayed behavioral probes

Freeze and hash the generator before tick zero. Instantiate probes only after the lossy dump has been committed.

Generate eight legal probes per unfaulted execution, including:

- counterfactual action
- unseen obligation query
- resource dispute
- identity-substitution challenge
- causal-prerequisite challenge

The candidate must pass 8 of 8.

If eight legal probes cannot be generated, mark the semantic experiment invalid.

The generator may inspect the committed pre-dump evidence to construct valid questions and expected answers, but those answers must not be passed to reconstruction or stored in the residual or ledger.

==================================================
12. LEAKAGE AUDIT
==================================================

Legitimate identity, relationship, obligation, provenance, and causal information may be retained. Correct answers may be derived from that information through the generic reconstruction and world-execution process.

That is semantic continuity, not leakage.

Prohibited leakage includes:

- literal probe answers
- probe-ID-to-answer tables
- expected outcomes
- closure status
- report-layer arm names
- boundary markers
- original microstate IDs used as lookup keys
- future action labels
- data created specifically after seeing probe instances
- hidden access to discarded state
- hidden access to the original complete checkpoint
- a probe-specific decoder unavailable to ordinary world execution

The validator must distinguish:

- direct answer storage
- probe-specific encoding
- legitimate retained causal information
- generic reconstruction
- later behavioral derivation

Semantic continuity is invalid if success depends on prohibited leakage.

Do not invalidate a representation merely because legitimate retained information allows correct semantic inference.

==================================================
13. LEDGER CAUSALITY AND FAULT CONTROLS
==================================================

Ledger causality is supported only if:

1. At least one valid ledger difference changes reconstruction or a permitted future action.
2. Removing the ledger causes at least one frozen semantic failure.
3. The valid-ledger candidate passes the corresponding semantic probe.
4. The ledger is consumed by reconstruction or J.
5. Ledger effects arise from content, not a "ledger present" flag.

Fault-control validity is separate.

Every required fault must produce its frozen predicted rejection or semantic failure:

- identity substitution
- obligation deletion
- contradictory ledger
- missing provenance
- stale event
- duplicate event
- causal reorder
- no ledger
- random reconstruction

Report unexpected passes and unexpected failure modes.

==================================================
14. TEST 05C: OBSERVER BOUNDARY
==================================================

### Primary bounded observer

The primary observer has:

- radius-one local-state access
- memory of the previous two ticks
- access to its own identity
- access to direct relationships
- access to current obligations

It does not have:

- global clock
- absolute cycle position
- explicit boundary marker
- full-state access
- unrestricted ledger access
- beginning-contract hash
- return-value bytes
- J internals

This is the only observer used for the primary indistinguishability claim.

Other observer classes are sensitivity analyses.

### Exact statistics

Where tractable, calculate:

P(observation | boundary)

and:

P(observation | phase-matched interior)

Report:

- total variation distance
- Bayes-optimal classification accuracy
- mutual information when the exact joint distribution is available
- number of boundary windows
- number of interior windows
- matching coverage
- unmatched windows
- match multiplicity
- weighting procedure
- distributions before and after matching

### Phase matching

Match interior observations by:

- local occupancy class
- obligation-count bucket
- any additional frozen matching variables in the observer specification

At least 90% of boundary windows must have an eligible phase-matched interior match in each family.

If coverage is below 90%, mark 05C inconclusive.

Do not silently discard unmatched boundary observations.

### Primary support threshold

For each family:

- supported if TV ≤ 0.05 and Bayes-optimal accuracy ≤ 0.55
- unsupported if TV > 0.05 or accuracy > 0.55
- inconclusive if exact enumeration is unavailable and there are fewer than 200 independent matched observations per class
- invalid if the positive control fails

Overall 05C is supported only if both families support it.

### Sensitivity ladder

Report without using these observers to replace the primary claim:

1. Radius one without memory
2. Primary observer
3. Primary observer with eight ticks of memory
4. Primary observer with obligation history
5. Bounded longer-memory observer
6. Full-state observer

### Positive control

The full-state observer must achieve:

- TV ≥ 0.25, or
- Bayes-optimal accuracy ≥ 0.75

Otherwise, mark 05C invalid.

==================================================
15. TEST 05D: RESOURCE COMPARISON
==================================================

Only semantically eligible arms may enter the resource comparison.

### Frozen objectives

Primary:

- peak canonical bytes

Secondary:

- total canonical byte-ticks

Diagnostic:

- deterministic operation count

Noncanonical diagnostic:

- repeated wall-clock duration

Wall-clock timing must not enter the canonical digest.

### Required baselines

1. Complete checkpoint
2. Snapshots plus event logs
3. Always-expanded lossless execution
4. Open-chain execution
5. General-purpose lossless compression
6. General-purpose lossy compression at matched semantic fidelity
7. Lossy execution without the narrative ledger
8. No-loss cyclic execution
9. Scripted cyclic replay
10. State-machine replication, if implemented

A baseline that does not satisfy the same semantic contract is ineligible, not defeated.

### Byte accounting

Count all live and retained memory:

- authoritative state
- residual
- ledger
- event log
- observer buffers
- checkpoints
- temporary reconstruction buffers
- indexes
- lookup tables
- retained preprocessing
- compression metadata
- dictionaries
- model parameters used only by one arm

Prohibit:

- uncounted preprocessing
- reconstruction oracle
- hidden original-state lookup
- easier tasks for the candidate
- omitted temporary buffers
- excluded ledger or observer memory

### Resource support rule

The candidate is supported only if:

1. It passes 9 of 9 core semantic probes.
2. It passes 8 of 8 delayed probes.
3. Every compared baseline is evaluated on the same histories and semantic contract.
4. Its peak canonical bytes are strictly lower than every eligible baseline in both families.

If semantic continuity fails, resource advantage is ineligible.

If the candidate does not beat every eligible baseline, report the complete Pareto table and mark resource advantage unsupported.

Byte-ticks cannot rescue a failure on the frozen primary metric.

==================================================
16. EXPANSION AND CONTRACTION
==================================================

Define represented-world size:

R(t) = live entities + live represented-region cells

Expansion and contraction are supported only if, for the candidate in both families, ticks exist such that:

t0 < t1 < t2

R(t1) ≥ 2 × R(t0)

and:

R(t2) ≤ R(t0) + 1

Report R(t) for every tick.

==================================================
17. INTEGRATED RESULT
==================================================

The same candidate system must demonstrate:

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

Integrated result rules:

- Missing canonical evidence: invalid
- Prohibited leakage: semantic result invalid
- Failed positive control: observer result invalid
- Missing frozen observer threshold: observer result inconclusive
- Semantic failure: resource result ineligible
- Ignored return value: reciprocal closure unsupported
- Any unsupported required gate: integrated result not supported
- Any inconclusive required gate: integrated result inconclusive unless another required gate is already unsupported
- Any invalid required gate: integrated result invalid
- Every required gate supported: integrated result supported

Do not use "disproved" as a result status.

==================================================
18. INDEPENDENT VALIDATOR
==================================================

Create a separate validator process that recomputes conclusions from raw evidence.

It must not trust summary statuses.

The validator must reject:

- missing evidence
- hash mismatch
- forbidden seed
- reserved confirmatory seed
- post-hoc contract
- modified contract
- ignored return value
- direct-copy beginning
- label-driven simulator behavior
- unchanged fake intervention
- incompatible mutation metadata
- incorrect history counts
- incorrect microstate counts
- incorrect collision groups
- probe-answer leakage
- hidden original-state lookup
- incorrect semantic scores
- incorrect observer distributions
- inadequate matching coverage
- failed positive control reported as valid
- ineligible resource arm included as eligible
- omitted required memory category
- incorrect peak-byte total
- integrated support with a failed prerequisite

Create at least one corruption fixture for every rejection class.

The validator must return a nonzero exit code for corrupted evidence and zero only for structurally valid evidence. A zero exit code does not mean the conjecture was supported.

==================================================
19. RESULT FORMAT
==================================================

The canonical result must include:

- test ID
- protocol version
- development status
- run class
- exact pilot superseded
- development seeds
- confirmation that reserved seeds were not used
- world-family results
- reciprocal-closure result
- loss result
- semantic result
- leakage result
- observer result
- positive-control result
- observer sensitivity results
- ledger-causality result
- fault-control result
- fidelity eligibility
- resource result
- expansion/contraction result
- integrated result
- failed gates
- inconclusive gates
- ineligible gates
- invalid gates
- source hash
- protocol hash
- configuration hash
- companion-file hashes
- canonical evidence digest
- evidence manifest
- interpretation
- limitations

The integrated status must begin as `pending` or remain absent until the validator derives it.

Do not initialize it as supported or not supported.

==================================================
20. REQUIRED DIRECTORY STRUCTURE
==================================================

Use a structure equivalent to:

evidence/test05/
  superseded_development_pilot/
  revised_development_v1.2.0-dev3/
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

1. Inspect the repository.
2. Record the true pilot status.
3. Preserve and seal the pilot.
4. Implement missing protocol components.
5. Create every frozen companion file.
6. Run unit tests before protocol freeze.
7. Run validator corruption tests before protocol freeze.
8. Correct implementation defects found before the freeze.
9. Produce the final protocol and configuration hashes.
10. Verify that the evidence directory contains no run evidence.
11. Verify that the simulator accepts no report labels.
12. Verify that reserved seeds remain untouched.
13. Freeze the protocol.
14. Execute seeds 13001-13003 and 14001-14003.
15. Do not modify frozen code, protocol, configuration, thresholds, or probes during execution.
16. If execution fails, preserve the failure.
17. Run the independent validator.
18. Produce the component dashboard.
19. Produce the Markdown development report.
20. Stop without running confirmation.

If a defect is discovered after tick zero:

- preserve the affected run
- mark it invalid or aborted
- do not patch it in place
- create a new protocol version before rerunning

==================================================
22. FINAL HANDOFF REPORT
==================================================

At completion, report:

- repository and branch
- base commit
- files created or changed
- pilot status and evidence digest
- revised protocol version
- frozen companion files
- protocol and configuration hashes
- development seeds used
- confirmation that reserved seeds were untouched
- world families evaluated
- execution matrix
- automated test results
- corruption-test results
- reciprocal-closure result by family
- loss result by family
- semantic-continuity result by family
- delayed-probe result
- leakage-audit result
- observer result by family
- observer matching coverage
- positive-control result
- ledger-causality result
- fault-control result
- fidelity eligibility
- resource comparison
- Pareto table
- expansion/contraction result
- integrated dashboard
- independent-validator result
- canonical evidence path
- canonical digest
- limitations
- whether the result is ready for human review

Do not call the result accepted, confirmed, or published.

==================================================
23. FREEZE CHECKLIST
==================================================

Do not execute tick zero until all are true:

[ ] Pilot preserved and identified by exact digest
[ ] Revised protocol stored and hashed
[ ] Observer specification stored and hashed
[ ] Physics configuration stored and hashed
[ ] Beginning-contract schema stored and hashed
[ ] Beginning contracts committed
[ ] Causal-path specification stored and hashed
[ ] Field-classification manifest stored and hashed
[ ] Delayed-probe generator stored and hashed
[ ] Fault predictions stored and hashed
[ ] Mutation definitions stored and hashed
[ ] Semantic probes stored and hashed
[ ] Byte-accounting specification stored and hashed
[ ] Resource objective fixed to peak canonical bytes
[ ] Seed list fixed
[ ] Seeds checked against pilot and reserved registries
[ ] Simulator receives no report labels or expected outcomes
[ ] Unit tests pass
[ ] Validator corruption tests pass
[ ] Revised evidence directory contains no execution evidence
[ ] Confirmation path remains disabled

When every item passes, run the revised development experiment once, validate it, preserve it, report it, and stop.
