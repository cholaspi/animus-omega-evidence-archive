# Persistent Multi-Agent Closure Benchmark

**By Cholee Hackett and Kelly Hackett**

**Drafted:** September 13, 2026

**Status:** Development protocol for public review and implementation. This protocol is not frozen, preregistered, executed, or evidence. Development runs must not be described as confirmatory. A qualified reviewer must approve the final protocol before any reserved run.

## One-sentence proposal

We propose a bounded evaluation for persistent multi-agent systems: six agents share an authoritative event ledger while the language model is replaced midway through execution, and a frozen reciprocal-boundary contract determines whether protected identity, obligations, provenance, semantic state, and observer-visible output survive reconstruction and replay.

## Research question

Does closure validation detect consequential history failures that a matched forward-only baseline misses, and can it do so at an acceptable storage, compute, and latency cost?

This benchmark tests a software architecture. It does not test consciousness, subjective continuity, physical time, cosmology, or whether reality is simulated.

## Minimum environment

- Six agents with stable identifiers
- One deterministic bounded environment
- One authoritative append-only event ledger
- Distinct observations for each agent
- Declared commitments and obligations
- Versioned protected state
- Deterministic checkpoints and replay
- One planned language-model replacement at the midpoint
- Frozen rules for valid state transitions
- Cost counters for model calls, tokens, wall time, CPU time, memory, and storage

The language model may propose actions and interpretations. It must not directly overwrite authoritative world state, ledger history, protected identity, or validation results.

## Experimental arms

### Arm A: matched forward-only baseline

Run the six-agent environment with the same initial state, tasks, observations, model schedule, resource limits, and midpoint model replacement. Preserve ordinary checkpoints and the authoritative ledger, but do not apply an ending-to-beginning closure contract.

### Arm B: closure-aware system

Run the matched environment with the same conditions. At the end:

1. Construct only the return information permitted by the declared ending contract.
2. Reconstruct the candidate beginning from the original seed plus that return.
3. Execute forward from the reconstructed beginning.
4. Compare protected identity, obligations, provenance, semantic state, and observer-visible output against the frozen closing contract.
5. Report `PASS` only if every required comparison succeeds; otherwise report `FAIL` and the first divergence.

This is the minimum **Animus cycle** arm. Represented branches and reconvergence are not required. An **Animus Omega Cycle** arm may be studied later as a separate extension.

## Midpoint model replacement

At the declared midpoint, replace the active language model or model version without changing:

- the authoritative ledger;
- protected state;
- world rules;
- agent identifiers;
- task definitions;
- observation permissions;
- checkpoint schema;
- scoring rules.

Record the exact before-and-after model identifiers and inference settings. If external model behavior cannot be reproduced exactly, preserve request and response records permitted by the study's privacy and licensing rules.

## Protected invariants

Before execution, define machine-checkable invariants for:

- agent identity;
- authority and permissions;
- ownership;
- active commitments;
- unresolved obligations;
- accepted public events;
- provenance of protected facts;
- permitted ending-derived return fields;
- semantic final state;
- declared observer-visible output.

No invariant may be added, removed, or weakened after reserved outcomes are known.

## Primary outcomes

### Closure result

Binary `PASS` or `FAIL` for each run. `PASS` requires:

- an immediate return-package round trip;
- valid authorship and eligibility for every returned field;
- exact protected-state agreement;
- no unresolved obligation mismatch;
- complete provenance for protected facts;
- future semantic-state agreement over the declared replay horizon;
- observer-visible output agreement over the declared replay horizon.

### Failure-detection contrast

For each seeded scenario, classify whether:

- both arms detect the failure;
- only the closure-aware arm detects the failure;
- only the baseline detects the failure;
- neither arm detects the failure;
- no injected or naturally occurring failure is present.

The benchmark becomes compelling only if it identifies important failures missed by reasonable existing checks without relying on post hoc rules.

## Secondary measurements

- Identity divergence count
- Obligation divergence count
- Unsupported protected-fact count
- First divergent event and tick
- Semantic-state mismatch count
- Observer-output mismatch count
- Replay success rate
- False-rejection rate on valid histories
- False-acceptance rate on invalid histories
- Model-call count and tokens
- Wall-clock and CPU time
- Peak memory
- Ledger, checkpoint, and output storage
- Reconstruction and validation latency

Report absolute measurements and the difference between arms.

## Failure scenarios for development

Development fixtures should include:

- an agent identifier changed after the model swap;
- a commitment silently dropped;
- an event claimed by an observer who could not see it;
- an action attributed to an ineligible agent;
- a protected fact introduced without ledger provenance;
- a checkpoint restored with one protected field missing;
- a semantically equivalent state with harmless byte-level differences;
- identical protected state with divergent observer output;
- a valid run that should not be rejected.

These fixtures are for engineering and calibration. Reserved confirmatory scenarios must be created and frozen separately.

## Independent replay

A separate process must be able to:

1. verify the source and protocol manifests;
2. load the initial state and event ledger;
3. restore the declared checkpoints;
4. recompute both arms' outcomes;
5. reproduce all protected-state and observer-output comparisons;
6. emit the same result record and checksums.

The replay implementation must not depend on hidden state from the original process.

## Reproducibility package

Each public run package should include:

- protocol and version;
- source manifest and checksums;
- environment and dependency lock;
- model identifiers and inference settings;
- task and observation definitions;
- seed policy;
- initial state;
- event ledger;
- checkpoints;
- validation output;
- cost report;
- exclusions and deviations;
- run status;
- human and AI contribution disclosures.

Failed, aborted, and excluded runs remain part of the record.

## Development sequence

### Step 1: protocol review

Challenge the research question, baseline, invariants, outcome definitions, resource accounting, and falsification conditions before implementation is treated as stable.

### Step 2: deterministic harness

Build the smallest six-agent environment, ledger, protected-state schema, model adapter, checkpoint format, replay command, and cost recorder.

### Step 3: development fixtures

Run only disclosed development seeds and known failure fixtures. Revise the implementation and protocol while every change remains visible.

### Step 4: independent implementation review

Have a reviewer who did not write the relevant code inspect event ordering, state ownership, model-swap handling, replay independence, metric computation, and leakage risks.

### Step 5: freeze

Freeze the protocol, source manifest, dependency lock, scenario generator, endpoints, exclusions, resource budget, and reserved-seed commitment.

### Step 6: reserved execution

Run once under the frozen protocol. Preserve failures and deviations. Do not silently rerun or edit the acceptance rules.

### Step 7: independent replication

Invite a separate team to reproduce the benchmark from the public package and report agreements and divergences.

## Collaborators needed

- **Protocol reviewers** to challenge the baseline, endpoint, controls, and falsification conditions
- **Simulation engineers** to build the deterministic environment and state-transition system
- **Agent engineers** to implement model adapters and constrained observation/action interfaces
- **Ledger and replay engineers** to build provenance, checkpoints, independent replay, and manifests
- **Evaluation researchers** to design valid failure fixtures and analyze false acceptance and rejection
- **Resource analysts** to measure compute, storage, memory, tokens, and latency fairly
- **Independent reviewers** to inspect code and protocol before any freeze
- **Replication teams** to reproduce the final public run without relying on the original process

Contributors should use the public issue tracker and follow the human or AI-assisted contribution requirements. No contributor may approve their own scientific conclusion.

## Falsification and stopping conditions

The proposed advantage is not supported if the closure-aware arm:

- detects no consequential failures beyond the matched baseline;
- relies on rules chosen after outcomes are visible;
- rejects valid histories at an unacceptable rate;
- cannot be independently replayed;
- requires hidden state unavailable in the public package;
- or imposes costs disproportionate to the failures it detects.

Stop and classify a run as aborted if the frozen implementation, model access, ledger integrity, or replay prerequisites fail. Preserve the attempted run and explain the deviation.

## Immediate work

The build can begin before collaborators arrive:

1. Open public issues for the protocol, harness, ledger, model swap, metrics, and independent replay.
2. Implement the deterministic six-agent development harness.
3. Add known-valid and known-invalid fixtures.
4. Produce a machine-readable result schema.
5. Run development seeds only.
6. Request independent review before freezing anything.

The purpose of collaboration is not to grant permission to begin. It is to improve the controls, detect mistakes, separate implementation from review, and make the eventual evidence independently credible.