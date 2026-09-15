# Contributing to Animus Omega

Animus Omega is a finite simulation and evidence project. Contributions must
keep mechanisms, measurements, and interpretation separate.

## Current build priority

New builders should first read
[Animus Omega for Builders: Start Here](docs/BUILDERS_START_HERE.md) to decide
whether reciprocal closure fits their problem before proposing implementation
work.

The current collaboration target is the
[Persistent Multi-Agent Closure Benchmark](https://github.com/cholaspi/animus-omega-evidence-archive/blob/main/docs/PERSISTENT_MULTI_AGENT_CLOSURE_BENCHMARK.md):
six agents, one authoritative ledger, a planned language-model replacement,
matched forward-only and closure-aware arms, independent replay, measured
fidelity and divergence, and complete resource accounting.

Development does not wait for collaborators. Public contributions are most
useful when they strengthen the protocol, deterministic harness, ledger,
model-swap adapter, fixtures, metrics, replay independence, cost accounting,
or replication. The protocol is still a development draft and must receive
independent review before any reserved execution.

## Roles

- **Maintainer:** owns scope, release decisions, and the claims ledger.
- **Protocol owner:** freezes questions, endpoints, seeds, exclusions, and
  deviations before execution.
- **Implementer:** changes code and supplies tests and provenance.
- **Reviewer:** checks correctness, reproducibility, and claim boundaries
  without reviewing their own change.
- **Data steward:** checks manifests, checksums, schemas, and retention.
- **Documentation editor:** keeps public prose synchronized with evidence.
- **Human accountable contributor:** named on every contribution and
  responsible for its contents, including AI-assisted work.

One person may hold several roles, but a review must remain independent where
practical.

## Reproducibility

Record the exact commit or file set, environment, command, configuration,
random seeds, runtime, hardware-relevant assumptions, outputs, and checksums.
Freeze confirmatory inputs before reserved seeds are opened. Development runs
are not confirmatory evidence. Preserve failed and aborted attempts, deviations,
and burned seeds. Do not overwrite an executed manifest or silently rerun a
one-attempt protocol. For the persistent-closure development harness, use only
the disclosed seeds in
`persistent_closure_benchmark/outputs/DEV_MANIFEST.json`; no reserved seeds
are allocated to the development harness.

## Issues, proposals, and review

Use the public
[Animus Omega evidence archive issue tracker](https://github.com/cholaspi/animus-omega-evidence-archive/issues)
for proposals and contribution records. Do not include private information in
an issue. Use the repository's issue and pull-request workflow.

Open an issue for a bug, evidence correction, documentation gap, or proposed
experiment. An experiment proposal must state the question, endpoint,
controls, resource budget, stopping/exclusion rules, seed policy, provenance
plan, and falsification condition. Link the issue to the pull request.
Small documentation fixes may go directly to review; protocol or claim
changes require maintainer approval before execution.

Pull requests must explain changed files, include tests or a reason tests do
not apply, and include reproducibility evidence. Reviewers should inspect
boundary cases, deterministic ordering, data provenance, and whether wording
overclaims. Do not merge generated outputs without their source and manifest.

## Attribution and license

Retain existing copyright and provenance notices. The project publication is
CC BY 4.0 unless a file states otherwise; contributors must have permission
to submit code, text, data, and media under the applicable license. Credit
substantial contributions in release notes and the contributor record.
Citation, acknowledgment, and authorship are distinct; authorship requires
substantial intellectual contribution and accountability.

## Claim boundaries

Write only what the evidence supports. Tests 01–04 are separate studies.
Test 01 validates a method and calibrates a threshold; it has no confirmatory
effect. Test 02 is exact only within its enumerated finite domain. Test 03 is
unsupported (Q<0 in 0/20 bundles; mean Q=0.6826707925423762). Test 04
Revision 2 supports exact replay only in its fixed deterministic model,
60/60 arms, seeds 43000–43019, checkpoints 37/113/251, and horizon 4096;
Revision 1 was aborted and supplies no evidence. Never infer physical
recurrence, consciousness, subjective continuity, entropy removal, resource
advantage, or universe-scale validity.

Do not claim endorsement, affiliation, shared formalism, or agreement with
Klee Irwin, Donald Hoffman, or Tom Campbell. If public themes are mentioned,
say they independently motivated this project only.


## Persistent closure benchmark implementation boundary

The Python implementation in `persistent_closure_benchmark/` is a
development-only deterministic harness. Contributions may improve its ledger,
schemas, fixtures, replay worker, or resource accounting, but must retain the
six stable IDs, matched arms, disclosed fixture list, and explicit
`development` status unless a protocol revision is documented. Do not call the
script in confirmatory mode (none exists), introduce reserved seeds, edit
frozen checkpoint evidence, or describe the sample output as proof that closure
is generally effective. A pull request changing an invariant, fixture,
divergence ordering, model-swap schedule, or resource definition must update
the protocol and source manifest and receive independent review.
