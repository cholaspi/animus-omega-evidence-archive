# Animus Omega simulator specification

**Status:** implemented conceptual specification. This is a buildable pattern, not a result of
the completed tests. It does not claim that the physical universe, a mind, or
 consciousness uses this architecture.

The browser simulator explicitly reports a `RETURN_WRITE` handshake. It is
not Test 05 evidence (and must not be described as such). The display is an
executable toy model, not a physical-time, cosmology, consciousness, or
resource-advantage claim.

## RETURN_WRITE handshake

The fixture separates seed-supplied facts, beginning requirements,
return-supplied requirements, temporal obligations, endpoint requirements,
and writer policies. A finite frozen candidate domain is enumerated in
canonical order. Each candidate is applied hypothetically at the beginning,
forward execution derives an ending proposal from that returned content and
explicit writer-eligibility predicates, and an independent sealed-history
validator checks typed events. The implemented ablation demonstrates that the
beginning fact determines the returned content; it does not establish a general
theory of motive or causation. Closure and
uniqueness are separate: histories are classified `NONE`, `UNIQUE`, or
`MULTIPLE`; uniqueness is required only when the fixture says so.

Events carry an effective tick, authored-at tick, provenance, and append
identity. Authored-at metadata is provenance, never proof of ending authorship.
Each reconstruction mode enumerates candidates independently. Reciprocal
closure is reported separately from information loss and semantic continuity
through loss. Observer projection is an explicit whitelist of at most two
frames and does not expose ticks, phases, endpoints, provenance, contracts,
ledgers, candidate data, or handshake metadata. Byte/resource values shown in
the UI are illustrative serialized sizes, never benchmark evidence.

## Purpose and boundary

The simulator studies whether a bounded executable can preserve a specified
world payload while it splits work and reunites work. An optional mode discards
lower-level detail to test continuity through loss. The
payload is operational: identities, relationships, obligations, unresolved
events, and plot phase. “Narrative” means state and dependency bookkeeping,
not subjective experience.

The **Animus Omega Cycle** is the public name for the stronger proposed
branch-reconvergence version; its technical subtype is the **Animus Omega
branch-reconvergence cycle**. The browser includes a separate deterministic
teaching trace that illustrates this proposed architecture; this built-in trace
is not experimental evidence and does not show that an independent run achieved
reconvergence. The cycle begins with one
authoritative history, permits declared represented branches during expansion,
and reconciles them under a frozen narrative-equivalence projection during
contraction until one canonical history remains. “Narrative collapse” means
this deterministic semantic reconciliation; it is not a physical, quantum, or
consciousness claim. Candidate enumeration and observer threads do not count as
represented timelines.

The teaching trace is separate from the trunk closure run. Its stages show one
authoritative history expanding to four declared branches, grouping under a
frozen narrative-equivalence projection, contracting within equivalence classes,
and ending at one canonical history. Every merge audit lists retained invariants,
discarded distinctions, conflicts, and provenance. Its scorecard reports branch
reduction, information loss, continuity through loss, and reciprocal closure as
four separate fields; reciprocal closure is deliberately not evaluated by this
trace.

The proposed narrative-closure boundary is an **untested internal constraint**:
an ending-to-beginning pathway must supply the conditions required by the
beginning, while the boundary remains an event in one continuous simulated
history. This is not a physical time loop, backwards causation, consciousness,
or evidence about the universe.

## State model

### Trunk

The trunk is the sole authoritative state:

- a monotonic world clock and configuration;
- entity and identity store;
- relation ledger (edges, obligations, ownership, and provenance);
- unresolved-event and causal-dependency ledger;
- plot-state ledger, including open arcs and required next-scene conditions;
- resource accounting and versioned schema.

Threads never commit directly to the trunk. Every mutation is an event with
source thread, logical time, input version, and deterministic conflict
metadata.

### Observer and region threads

At split, the scheduler creates observer, region, or inhabitant threads. Each
receives a versioned partial view and a bounded working buffer. A thread may
read only its view, emit proposed events, and maintain local microstate. It
does not receive an implicit full copy of the world. Views must identify their
omissions and stale reads.

### Protected narrative ledger

The protected ledger is the minimum state that may not be silently dropped:
stable identity mappings; relation edges and their provenance; obligations and
promises; unresolved events; plot phase and open dependencies; and the
conditions marked as required for a future scene or closure boundary. Each
entry has a schema version, owner, last authoritative update, and retention
reason. A dump may reject an entry only through an explicit, recorded policy.

### Dump

`dump(thread_state, policy)` produces a residual plus an audit record. It may
either preserve state losslessly or unload inactive microstate or summarize it.
Information loss is not required for cyclic operation. A lossy mode must report
discarded fields, retained fields, transforms, and reconstruction assumptions. Dump cost
includes serialization, summary computation, storage, I/O, and information
loss. A successful dump is not proof of fidelity.

### Merge and still

`merge(residuals, trunk_version)` synchronizes threads at a barrier, validates
versions, orders events deterministically, applies the declared conflict rule,
updates the trunk, and records discarded detail. The default conflict rule is
“reject ambiguous writes”; alternatives require a versioned specification.

`still` is a merge with new event intake paused: threads drain or cancel
according to policy, residuals are committed, and the trunk emits a quiet
checkpoint. Stillness is an engineering state, not a claim about meditation,
love, or physics.

### Animus Omega Cycle (optional branch reconvergence)

When the Animus Omega Cycle extension is enabled, every branch has a declared
origin and unique identity. The frozen narrative-equivalence projection identifies the protected
identities, relations, obligations, causal dependencies, permissions,
ownership, and observer-visible consequences that must agree. Reconciliation
proceeds in declared stages, records conflicts and provenance, and must end with
one authoritative history before reconstruction and return.

The run reports branch counts and equivalence classes at every stage. Mapping
distinct branch states to one retained state is information loss even when all
protected narrative invariants survive. Branch-state reduction, continuity
through loss, and reciprocal closure are therefore separate outcomes.

The Animus Omega Cycle teaching trace illustrates this contract, but a reserved
branch-reconvergence experiment requires a separate, prospectively locked
protocol package. Before execution that package freezes:

- canonical fixtures and digests, branch origins and immutable identities;
- branch-local initial state, permitted and forbidden transition tables, and
  arm-blind transition code;
- the total narrative-equivalence projection, including protected and ignored
  fields;
- conflict classes and their deterministic, content-independent dispositions;
- merge ticks, resource limits, observation horizon, and the exact one-history
  termination rule;
- matched positive and negative controls, thresholds, replay count, exclusions,
  and fail-closed rules.

The minimum control set includes: no cut, to prevent credit for an always-single
history; a valid equivalent pair; an undeclared hidden trunk/full-state copy;
scripted convergence that reads an arm label or expected output; arbitrary
branch deletion; and an unresolvable protected-field conflict. Control arms use
the same scheduler, budgets, validator, and scoring implementation as the
positive arm except for their named intervention. A failed control invalidates
the run family.

The experimental report must score branch creation, branch-set reduction,
information loss (`YES` or `NO`), continuity through loss, deterministic replay,
and reciprocal closure independently. Reconvergence additionally requires no
hidden executable trunk copy, arm-blind transitions, justified deterministic
reconciliation, complete ancestry, and exactly one authoritative history at the
frozen termination tick. Selecting a survivor, timing out, or deleting an
unresolved branch is not reconciliation.

Reserved fixtures and seeds must be disjoint from harness dry runs. Once the
protocol package is time-locked, any change to fixtures, projection, code,
thresholds, schedule, exclusions, or failure rules creates a new protocol and
new reserved run. Only pre-execution corruption, digest mismatch, unavailable
declared runtime, or failure before the first branch transition may be excluded.
Post-start crashes, timeouts, budget overruns, unresolved conflicts, replay
disagreement, missing provenance, control failures, and validator errors count
as failures. The reserved run starts only after an independent gate verifies
the receipt, digests, complete arm matrix, and all frozen decision rules.

## Cost model

Every run reports wall-clock time separately from semantic outcomes and
accounts for thread CPU, memory and retained context, view construction,
serialization, dump storage, merge/barrier time, reconstruction, conflict
resolution, and discarded information. Resource comparisons must define the
budget and task fidelity in advance. A torus, compression, or state reuse
does not remove compute, storage, or thermodynamic costs.

## Invariants and acceptance checks

1. Only the trunk can authoritatively advance world time or protected-ledger
   entries.
2. Every committed event has deterministic provenance and is applied once.
3. Split/merge preserves identity keys and ledger referential integrity.
4. No protected entry disappears without a typed loss record and policy.
5. Conflicting writes are rejected or resolved by the frozen rule, never by
   iteration order.
6. Replay from an identical trunk, residual set, configuration, and seed is
   identical within the declared semantic state and observation horizon.
7. Dump and merge are auditable: input/output digests, costs, losses, and
   conflicts are recorded.
8. Narrative closure, if implemented, must satisfy both forward causal
   continuity and the explicit return constraint; it is not inferred from a
   cycle alone.
9. A branch-reconvergence result is ineligible unless its prospective protocol
   package passed the time-lock gate before any reserved branch transition.
10. Branch reduction, information loss, continuity through loss, deterministic
    replay, and reciprocal closure are never collapsed into one success label.

## Failure modes

Test and report at least: stale-view writes; duplicate or lost events; broken
identity joins; contradictory relations; unresolved merge conflicts; ledger
overflow; summary hallucination or under-specification; reconstruction drift;
unbounded thread or buffer growth; deadlock at the barrier; nondeterministic
ordering; hidden full-world copies; resource-budget overruns; and a closure
boundary that exposes a seam or fails to supply its declared initial
conditions. Failure is informative and must not be relabeled as fidelity.

## Evidence boundary

The public record describes this architecture as a proposed synthesis. Tests
01–04 are separate operational studies; they do not validate the combined
simulator, its narrative closure, comparative fidelity, information creation,
or a physical-universe claim.
