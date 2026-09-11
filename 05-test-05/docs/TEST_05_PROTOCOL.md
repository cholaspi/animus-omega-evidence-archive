# Test 05 development protocol

**Status:** development protocol. This document is frozen for the purposes
of hashing (`protocol_hash` in every Test 05 result), but "frozen" here
means "fixed for this development run," not "confirmatory." No reserved
seed may be executed under this document. A confirmatory protocol, if one is
ever written, will be a separate, separately reviewed document with its own
frozen manifest, matching `seeds.RESERVED_PROTOCOL_HASH_REQUIRED`.

## Scope

Test 05 studies, in a small, exactly-enumerable deterministic simulation,
whether a single implemented system can jointly demonstrate:

1. Reciprocal ending-to-beginning closure (05A).
2. Genuine information loss with preserved semantic continuity (05B).
3. Observer-boundary indistinguishability for a specified bounded observer,
   validated by a positive control (05C).
4. A fidelity-matched computational advantage over comparable baselines
   (05D).
5. All of the above, gated together, in the same system (05E).

A supported result is evidence about this implemented model and this
protocol only. It does not establish consciousness, subjective continuity,
physical cosmology, unrestricted predestination, or that the physical
universe follows this structure.

## World model

Defined in `src/animus_test05/world.py`. A world is: a ring of `num_agents`
agents holding a conserved resource pool; a chain of `num_obligations`
obligations with a strict causal-dependency order; a relationship ledger
(the ring's transfer permissions); and a per-agent private nuisance field
(`internal_seed` / `private_trace`) that is genuinely irrelevant to every
public/semantic quantity. The action alphabet is
`{move, resolve, noop_x, noop_y}`; `move` and `resolve` are causally
relevant to every public quantity, `noop_x`/`noop_y` are causally
irrelevant (they only churn the private nuisance field). Histories are
fixed-length tuples over this alphabet and are exactly enumerated
(`itertools.product`) rather than sampled, whenever the resulting space is
computationally tractable.

## World families

`src/animus_test05/worlds.py` declares seven world families for 05A/05B/05D
(varying agent count, obligation-chain length, reconstruction algorithm,
ledger capacity, and two adversarial conditions -- identity substitution and
causal reordering) and two dedicated, smaller world families for 05C
(observer boundary detection needs a longer history to contain a
phase-matched interior window, which makes exact enumeration expensive, so
05C restricts agent count to keep runtime tractable). No world family
encodes an expected outcome, arm label, or closure status in its
definition.

## Seeds

`src/animus_test05/seeds.py` declares disjoint development and reserved
confirmatory seed bands per sub-test (05A: 55000-55019 / 56000-56019, 05B:
55100-55119 / 56100-56119, 05C: 55200-55219 / 56200-56219, 05D:
55300-55319 / 56300-56319, 05E: 55400-55419 / 56400-56419). Development
seeds are used only for the randomized elements of the protocol (arm 3's
random-agent draw, control 12's random reconstructed payload); the world
mechanics themselves are deterministic given a history. Reserved seeds
cannot be executed by the development entrypoint;
`seeds.confirm_reserved_execution` additionally requires a frozen protocol
document whose hash matches a pinned constant that is deliberately
unsatisfiable until a human freezes a real confirmatory protocol in a
reviewed change.

## Test 05A: reciprocal boundary necessity

`locked_beginning_contract(config)` is a pure function of `WorldConfig`
only, so it is committed before any history executes. The boundary
transition `execute_J(reconstructed_state, ledger, return_value, config)`
builds the next beginning's public fields from its three data inputs, using
a `TrackedReturnValue` wrapper to record which return-value fields are
actually read (so a value that is computed but never propagated to the
output can be detected). `contract_satisfied` is a structural check using
only the values present in the constructed next-beginning (conservation,
well-formed fields, minimum-resolutions requirement); `exact_closure`
additionally compares against the true ending's independently computed
ground truth. All 12 required intervention arms, plus an ignored-return-
value control, are implemented as perturbations of J's inputs relative to a
naturally-closing reference history per world family (arms 6/7 additionally
re-execute a one-tick-mutated history). Every admissible history is
enumerated and classified as closing or non-closing.

## Test 05B: semantic continuity through genuine loss

Field classification (copied / reconstructed / derived through later
execution / intentionally discarded) is declared in
`residual.FIELD_CLASSIFICATION` before any reconstruction runs. The residual
retains reconstructed public fields plus a derived narrative summary
(`causal_order_token`, `provenance_digest`); it never retains
`internal_seed`, `private_trace`, or noop/blocked event detail. Genuine
information loss is demonstrated by exact enumeration: every admissible
history's full ending state is hashed as a microstate signature, and the
declared residual is hashed separately, so collision groups (multiple
microstates mapping to one residual) are counted exactly rather than
asserted. Eight behavioral probes are graded against ground truth computed
independently from the true microstate. Thirteen required controls are
executed and graded with the same probes; a leakage audit scans the
residual and ledger for banned meta-keys (expected answers, arm labels,
closure status, etc.).

## Test 05C: observer boundary detection

The observer ladder (six classes, from a radius-one local observer to a
full-state positive control), the window size (2 ticks), the boundary/
interior window positions (phase-matched by `tick mod num_agents`), the null
model (histories uniformly likely over the full enumerated space), and both
thresholds are frozen as module-level constants in `observer.py`:
`INDISTINGUISHABILITY_TV_THRESHOLD = 0.05` for the five bounded classes and
`POSITIVE_CONTROL_TV_THRESHOLD = 0.20` for the full-state positive control.
Because every observer world family is exactly enumerated, P(observation |
boundary) and P(observation | interior) are exact histograms, not samples,
so no sampling-uncertainty procedure applies. Total variation distance,
Bayes-optimal accuracy, mutual information, and a likelihood-ratio summary
are reported for every observer class in every world family.

## Test 05D: fidelity-matched resource comparison

Ten baseline architectures plus the proposed residual+ledger architecture
are each measured for peak canonical bytes, total byte-ticks, and a
deterministic operation count (dump/reconstruction/merge/sync/observer-
update), using real `len(canonical_json(...))` byte counts rather than
estimates. Every arm is graded against the same 05B semantic-probe battery;
only arms that pass every probe are eligible for the resource-advantage
comparison. The proposed architecture is compared against every other
eligible baseline; "supported" requires strictly dominating at least one
baseline on both peak bytes and byte-ticks, with no undeclared total
regression (losing to a baseline on every axis without a documented
non-comparability caveat, such as the scripted-replay baseline's exemption
from the loss requirement).

## Test 05E: integrated evaluation

`integrated.evaluate` reads the already-computed 05A-05D component results
and applies the strict gating rules from the protocol (13 named gates). It
performs no simulation of its own. The integrated conclusion is
"supported" only if every gate passes; otherwise "not_supported", which is
never converted to "disproved."

## Validation

`validator.py` independently recomputes every conclusion from the raw
evidence files (never trusting a cached `status` field) and additionally
checks: every referenced evidence file exists and hashes match, no reserved
seed appears anywhere in the run manifest, and a deliberately corrupted copy
of the evidence is correctly rejected.
