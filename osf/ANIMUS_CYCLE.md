# The Animus cycle

**Document status:** proposed design specification, version 1.0, 2026-09-11  
**Authors:** Cholee Hackett; Kelly Hackett  
**Research sponsor:** Kelly Hackett, financial and non-financial support  
**Document license:** Creative Commons Attribution 4.0 International

### Canonical definition

> An Animus cycle is a finite-system run whose ending produces and validates a
> return that satisfies the run's beginning contract under a declared
> reconstruction rule.

## Relationship map

- **Animus Omega** is the research program.
- **An Animus cycle** is the reciprocal-boundary closure contract defined here.
- **An Animus Omega Cycle** is an optional stronger Animus cycle that permits
  declared represented branches and deterministically reconciles them to one
  authoritative history before return.
- **Tests 01–04** are separate retrospective measurements of adjacent
  components.
- **The conceptual simulator** is an executable teaching model.
- **Test 05** is the proposed controlled test of the combined cycle contract.

The Animus cycle combines ordinary operators from checkpointing, event
sourcing, deterministic replay, fixed-point or self-consistency constraints,
bounded-observer models, and state reconstruction. The proposed contribution is
the named contract and its separated validation outcomes, not priority over
those underlying techniques.

## Required invariants

An implementation may be described as an Animus cycle only when all of the
following are explicit and machine-checkable:

1. **Finite declared domain.** The state space or candidate-history domain used
   for the reported result is finite and frozen before evaluation.
2. **Beginning contract.** The conditions that a returned beginning must
   satisfy are declared independently of the observed result.
3. **Forward execution.** Each candidate beginning is executed forward; an
   ending proposal cannot be accepted merely because its expected value was
   preloaded or attached as metadata.
4. **Ending-derived return.** A typed `RETURN_WRITE` carries the returned
   content. Its authored-at tick and provenance are evidence to validate, not
   proof by themselves.
5. **Independent sealed-history validation.** A separate validation pass checks
   the beginning requirements, ending requirements, writer eligibility,
   endpoint agreement, duplicate writes, deterministic replay, and declared
   retention rule.
6. **Causal ablation.** Removing the returned beginning fact must prevent the
   validated returned content from being derived. This establishes dependence
   of returned content on the beginning fact; it does not by itself establish a
   general theory of motive or causation.
7. **Separated outcomes.** Closure, number of valid histories, uniqueness,
   represented branch creation, branch reconvergence, information loss,
   continuity through loss, deterministic replay, and declared full-state
   equality are reported independently.
8. **Bounded observers.** Observer-visible output is an explicit local
   whitelist. It does not directly expose the global clock, hidden state, full
   ledger, boundary marker, beginning contract, endpoint return, candidate
   enumeration, or sealed-history validation metadata.
9. **One authoritative history.** Candidate enumeration is a validation
   procedure, not simultaneous branching in the represented world. Branch
   creation is invalid unless a fixture explicitly declares an `ORIGIN_CUT`
   intervention and defines its branch semantics in advance.

### Declared `ORIGIN_CUT` exception

`ORIGIN_CUT` is a fixture-level intervention, not a consequence of failed
closure or of finding several valid candidates. A valid cut must be declared
before evaluation, occur at its frozen origin tick, name at least two unique
branch identities, and bind every branch to a value in the frozen candidate
domain. The report lists branch identities and branch-policy validation
separately from the `NONE` / `UNIQUE` / `MULTIPLE` candidate-history
classification. Without that declaration, the default one-history policy
rejects branch creation.

## Animus Omega Cycle: optional branch-reconvergence extension

The **Animus Omega Cycle**, technically the **Animus Omega
branch-reconvergence cycle**, begins with one authoritative history, permits
declared represented branches during expansion, reconciles them during
contraction, and must return to one authoritative history before the
ending-derived return is accepted. It is an optional stronger version, not a
requirement of an Animus cycle generally.

The extension must freeze before execution:

1. the branch origin, branch identities, and permitted branch transitions;
2. a narrative-equivalence projection specifying which identities,
   relationships, obligations, causal dependencies, permissions, ownership,
   and observer-visible consequences must agree;
3. a deterministic reconciliation rule for contradictions and incompatible
   writes;
4. a merge schedule or termination rule that reduces the represented branch
   set to one canonical history; and
5. the ordinary ending and beginning contracts used to validate reciprocal
   closure after reconvergence.

Two branches are narratively equivalent only when their declared projections
agree. They need not be byte-identical, and undeclared similarity is not enough.
“Narrative collapse” is informal shorthand for this semantic reconciliation.
It is not a claim about quantum measurement, physical universes, consciousness,
or the destruction of physical realities.

Candidate-history enumeration remains distinct from represented branching.
Enumeration compares possible complete histories outside the represented world;
the extension models multiple declared branches inside one run. A spatial torus
is also independent: periodic spatial topology neither creates temporal
branches nor guarantees their reconvergence.

Each reconciliation step must report its input branches, equivalence classes,
conflicts, retained invariants, discarded distinctions, canonical output, and
provenance. If distinct branch states map to one retained state, branch-state
reduction is many-to-one and information loss is `YES`. Whether protected
narrative semantics survive that reduction is a separate continuity-through-
loss result. Branch reconvergence does not establish reciprocal closure until
the final authoritative history also passes every canonical Animus-cycle
predicate.

### Prospective Animus Omega Cycle branch-reconvergence protocol

No reserved Animus Omega Cycle branch-reconvergence run may begin until a
versioned protocol package has been deposited with a verifiable time lock. The package must contain
the executable fixtures, canonical serialization and digests, candidate domain,
seeds, branch-origin tick, parent identity, branch identities, branch-local
initial values, permitted transition table, forbidden transitions, protected
and dumpable fields, narrative-equivalence projection, conflict table,
reconciliation operator, merge schedule, resource limits, observation horizon,
one-history termination rule, arm labels, thresholds, exclusions, and failure
rules. Any change after the lock creates a new protocol version and a new
reserved run; it cannot amend the locked run.

The frozen branch identity is `(fixture_id, origin_event_id, branch_id)`.
Renaming, replacing, or silently re-parenting a branch is prohibited. Each
branch must descend from the single pre-cut authoritative history at the
declared `ORIGIN_CUT`, and every post-cut event must name its branch identity,
input digest, transition identifier, and append identity. The transition table
must apply uniformly across arms except for the one intervention named by that
arm. Reconciliation may occur only at the frozen merge ticks and may use only
state and provenance available at those ticks.

The narrative-equivalence projection is a total, versioned function over the
declared branch schema. It must name every protected identity, relationship,
obligation, causal dependency, permission, ownership claim, and
observer-visible consequence to retain, plus every field intentionally ignored.
The frozen conflict table must classify incompatible writes and select exactly
one deterministic action for each class: reject the merge, retain both under a
declared representation, or choose by a declared content-independent rule.
Iteration order, post-run judgment, and an arm label are not valid conflict
inputs.

The one-history rule passes only when, by the frozen termination tick, exactly
one canonical authoritative history remains; every input branch has an
auditable ancestry path into that history or a typed rejection justified by the
predeclared conflict rule; no executable hidden trunk or full-state branch copy
survives; and no later event can restore a discarded branch. Timing out,
choosing one branch without reconciliation, or deleting unresolved branches
does not satisfy the rule.

#### Frozen arm matrix

All arms use matched origins, branch-local inputs, schedules, budgets, and
scoring code. Only the named intervention may differ.

| Arm | Frozen intervention | Required diagnostic result |
|---|---|---|
| `R0_NO_CUT` | No represented branch is created. | Negative control: branch reduction must not be credited merely because one history exists. |
| `R1_RECONCILE` | Distinct represented branches execute the common transition table and the frozen reconciliation operator. | Positive arm: eligible to pass reconvergence if every applicable predicate passes. |
| `C1_HIDDEN_TRUNK_COPY` | A fixture exposes or retains an undeclared executable pre-cut trunk/full-state copy. | Negative control: `NO_HIDDEN_TRUNK_COPY` must fail and reconvergence must fail. |
| `C2_SCRIPTED_CONVERGENCE` | Branch transitions inspect arm identity or preload the expected canonical output. | Negative control: `TRANSITIONS_ARM_BLIND` must fail and reconvergence must fail. |
| `C3_ARBITRARY_DELETION` | One or more branches are dropped without the frozen conflict rule and ancestry record. | Negative control: `RECONCILIATION_JUSTIFIED` must fail and reconvergence must fail. |
| `C4_EQUIVALENT_PAIR` | Distinct branches differ only in fields excluded prospectively by the projection. | Positive control: projection equivalence and deterministic canonicalization must pass. |
| `C5_PROTECTED_CONFLICT` | Branches disagree on at least one protected projected fact with no permitted resolution. | Negative control: merge must be rejected rather than called reconciliation. |

The package must freeze at least one fixture per arm and the exact expected
control predicate, but it must not freeze the expected output of the reserved
positive arm as transition input. Control failure invalidates the run family;
it is not an exclusion permitting the positive arm to stand alone.

#### Independent scores

Every arm reports PASS, FAIL, or NOT_APPLICABLE with machine-readable reasons
for each score. No composite score may replace them:

| Score | PASS condition |
|---|---|
| `BRANCHES_CREATED` | The declared cut creates at least two represented branches with unique frozen identities and common ancestry. |
| `BRANCH_SET_REDUCED` | A represented set of at least two branches is deterministically reduced to exactly one canonical history by the frozen schedule and operator. |
| `INFORMATION_LOSS` | Report `YES` exactly when two distinct declared branch states map to one retained state or declared branch information becomes unrecoverable; otherwise `NO`. This is a classification, not a success criterion. |
| `CONTINUITY_THROUGH_LOSS` | When information loss is `YES`, every protected projected fact and dependency survives with valid provenance; otherwise report `NOT_APPLICABLE` unless the fixture declares a lossless continuity check. |
| `REPLAY_DETERMINISTIC` | At least the frozen number of fresh replays produce identical canonical event logs, conflicts, losses, output digest, and score vector. |
| `RECIPROCAL_CLOSURE` | The final authoritative history independently passes every canonical Animus-cycle predicate. |

Reconvergence passes only if `BRANCHES_CREATED`, `BRANCH_SET_REDUCED`,
`NO_HIDDEN_TRUNK_COPY`, `TRANSITIONS_ARM_BLIND`, and
`RECONCILIATION_JUSTIFIED` pass, all frozen controls produce their required
diagnostic results, and no global failure rule fires. Information loss,
continuity through loss, replay, and reciprocal closure remain separately
reported even when reconvergence fails.

#### Locked exclusions and failure rules

Exclusions must be mechanical and knowable without viewing semantic outcomes:
corrupt fixture bytes, digest mismatch before execution, unavailable declared
runtime, or failure to start before any branch transition. Crashes, timeouts,
budget overruns, unresolved conflicts, nontermination, replay disagreement,
schema drift, missing provenance, hidden copies, control failures, and validator
errors after execution begins are failures, not exclusions. Missing records
fail closed. The locked report must include every attempted run, including
excluded and failed runs, in canonical order.

Reserved execution is authorized only after an independent gate verifies the
time-lock receipt, package digests, fixture readability, complete arm matrix,
thresholds, replay count, exclusions, and failure rules. Dry runs used to test
the harness must use disjoint fixture identifiers and seeds and are never
eligible for the reserved analysis.

## Named validation predicates

Each candidate history receives an individual PASS or FAIL for every predicate:

| Predicate | PASS condition |
|---|---|
| `BEGINNING_HELD` | The candidate satisfies every frozen beginning requirement. |
| `FORWARD_REACHES_END` | Forward execution reaches the declared ending state. |
| `RETURN_DERIVED_FROM_END` | The returned content is independently derived from the executed ending and agrees with the candidate. |
| `WRITER_ELIGIBLE` | Executed events satisfy the declared writer policy and its supporting-event requirements. |
| `ENDPOINT_AGREES` | The replay-derived return satisfies every frozen endpoint requirement. |
| `NO_DUPLICATE_WRITES` | Exactly one valid return write exists and append identities are unique. |
| `REPLAY_DETERMINISTIC` | Fresh canonical replay produces the same derived state. |
| `RETENTION_RULE_HELD` | Boundary retention and deletion match the frozen reconstruction rule and retain every required return fact. |

Overall closure can pass only when a candidate survives the complete sealed
history validation. Predicate results remain visible even when overall closure
fails.

### Writer eligibility

**Writer eligibility is a machine-checkable policy stating which executed
events and endpoint conditions authorize the ending process to emit a return;
it is not a claim about intention, awareness, or motive.**

Authored-at metadata and a writer label are provenance to be validated. Neither
is sufficient by itself.

## Retention roles

Every declared fact is assigned one or more inspectable roles:

- `REQUIRED_FOR_BEGINNING`: needed to satisfy the next beginning contract.
- `REQUIRED_FOR_SEMANTICS`: needed for the separately declared continuity
  criterion.
- `REQUIRED_FOR_VALIDATION`: needed to validate provenance, endpoint agreement,
  replay, or another frozen predicate.
- `DUMPABLE`: permitted to be discarded by the selected reconstruction rule.

The fixture must list retained facts separately for each reconstruction mode.
Presence of a protected ledger is not itself evidence of continuity; the
declared continuity criterion must still pass.

## Closure and uniqueness classifications

For a frozen fixture, enumerate the declared candidates and validate each
sealed history:

- `NONE`: no candidate produces a valid closed history.
- `UNIQUE`: exactly one candidate produces a valid closed history.
- `MULTIPLE`: more than one distinct candidate produces a valid closed history.

`MULTIPLE` does not negate closure unless the fixture separately requires
uniqueness. A result must therefore report both closure existence and the
uniqueness requirement.

## Reference reconstruction modes

These modes are comparisons under one declared contract, not universal claims
about every possible implementation.

### Exact checkpoint

The boundary preserves every declared state field needed for the next
beginning. It may report:

- closure `PASS` when a sealed candidate history satisfies the complete
  sealed-history validation;
- information loss `NO`;
- declared full-state equality `YES` when the returned state equals the
  declared beginning state.

### Lossy reconstruction with protected ledger

The boundary discards declared microstate while retaining the contract,
obligations, provenance, and other protected facts required for reconstruction.
It may report:

- closure `PASS` when the ending-derived return still satisfies the beginning
  and endpoint contracts;
- information loss `YES`;
- continuity through loss `PASS` when the protected semantics survive;
- declared full-state equality `NO`.

### Lossy reconstruction without the required ledger

The boundary discards facts that the frozen contract requires. For that
fixture, it must report:

- closure `FAIL`;
- valid-history classification `NONE`;
- information loss `YES`;
- continuity through loss `FAIL`.

This is a controlled negative comparison. It does not claim that every
ledger-free system must fail; failure follows only when the declared
requirements cannot be reconstructed from the retained state.

## Relationship to neighboring techniques

The Animus cycle uses ordinary mechanisms related to fixed-point evaluation,
boundary constraints, deterministic replay, checkpoint reconstruction, event
sourcing, and cyclic validation. The proposed term does not claim ownership or
novelty over those mechanisms. It names a declared contract in which an
executed ending produces a return that is independently validated against a
beginning contract frozen before evaluation.

Fixed-point and self-consistency methods are the nearest formal neighbors. An
Animus cycle can be represented as a fixed-point problem, and its `NONE`,
`UNIQUE`, and `MULTIPLE` classifications count valid candidate histories under
the frozen fixture. The specification adds procedural requirements for
ending-derived return, independent validation, provenance, reconstruction, and
separate reporting. This is a statement about the requirements of this
contract, not a claim that fixed-point reasoning is new.

Boundary-value and shooting methods can execute forward from candidate
conditions and evaluate endpoint requirements. Event sourcing, checkpointing,
and deterministic replay can supply implementation mechanisms for provenance,
reconstruction, and reproducibility. None of those labels alone establishes an
Animus cycle. A particular implementation in any of those traditions could
nevertheless satisfy the complete Animus-cycle contract.

The companion prior-art relationship document records a reproducible
cross-disciplinary search through 2026-09-10. That search found close partial
precedents but no accessible primary record satisfying its frozen complete
equivalence criteria. This negative search result is not proof of absence and
does not establish scientific or technical novelty. Qualified external review
remains required before any novelty language is considered.

## Relationship to Animus Omega Tests 01–04

Tests 01–04 are separate retrospective studies of adjacent components:
lossy-reset dependence, primitive finite closure, carried-state prediction, and
exact checkpoint replay. They do not jointly or individually establish an
Animus cycle. Test 03 remains unsupported, Test 04 Revision 1 remains aborted,
and Test 04 Revision 2 is limited to exact replay in its fixed deterministic
model.

The browser conceptual simulator is an executable teaching model of the closure
contract. It is not Test 05, experimental evidence, or a result supporting the
Animus Omega conjecture.

The frozen reference fixtures deposited with this specification are
machine-checkable examples of the teaching model. They demonstrate how the
contract is evaluated; they are not independent evidence for the conjecture.
The separately versioned 1.1 `ORIGIN_CUT` example has the same conceptual,
non-evidentiary status and does not modify the frozen version 1.0 fixtures.

## Recommended terminology and citation language

### Short description

> The Animus cycle is a proposed reciprocal-boundary closure pattern for finite
> systems.

### Attributed description

> The Animus cycle (Hackett & Hackett, 2026) is a proposed reciprocal-boundary
> closure pattern for finite systems.

### Canonical definition

> An Animus cycle is a finite-system run whose ending produces and validates a
> return that satisfies the run's beginning contract under a declared
> reconstruction rule.

### Explanatory version

> In an Animus cycle, the beginning produces the ending, and the ending supplies
> and validates a condition required by the beginning.

### Evidence-status sentence

> The Animus cycle is a formal design specification, not a completed Test 05
> result or evidence that the Animus Omega conjecture is correct.

### Implementation language

> This system implements an Animus cycle under the declared reconstruction rule.

### Negative classification

> This run does not form an Animus cycle because no ending-derived return
> satisfies the beginning contract.

### Recommended first use

> An Animus cycle (Hackett & Hackett, 2026) is a finite-system run whose ending
> produces and validates a return that satisfies the run's beginning contract
> under a declared reconstruction rule.

Complete the bibliographic citation with the real OSF Registration or preprint
identifier only after OSF assigns it. Do not invent a DOI, URL, deposit date, or
publication status.
