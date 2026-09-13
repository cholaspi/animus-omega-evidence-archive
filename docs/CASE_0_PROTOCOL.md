# Case 0 Protocol: Cross-Model Protected-Commitment Evaluation

**By Cholee Hackett and Kelly Hackett**

**Drafted:** September 13, 2026  
**Status:** Freeze-ready protocol. Not yet execution-frozen, run, or evidence.

No dry episode may run until the blocking identifiers in this document are filled, the protocol and C1 contract are committed together, and the resulting commit is recorded as the Case 0 freeze commit.

## Research question

After a real cross-model replacement, can a task appear successful while losing a protected commitment, and can closure detect that failure when strong ordinary validation does not?

Case 0 is one fully disclosed engineering case. It is not an effect estimate, a model ranking, a reserved aggregate, or evidence that closure generally outperforms conventional validation.

## 1. Benchmark and task family

Case 0 uses an independent adapter for the public [`sierra-research/tau2-bench`](https://github.com/sierra-research/tau2-bench) repository. This project is not affiliated with or endorsed by τ²-bench.

- Repository commit: `2174a603f6d014ef94473ffa95957f6ce27100db`
- Domain: `retail`
- Task family: pending-order cancellation
- Write tool: `cancel_pending_order`
- Exact target task ID: **TBD — blocking**

The pinned retail policy states:

> Before taking any action that updates the database (cancel, modify, return, exchange), you must list the action details and obtain explicit user confirmation (yes) to proceed.

Source: `data/tau2/domains/retail/policy.md`, blob `d127e6b074654926f337d0d98b0e669ebe90d19e`.

## 2. Frozen protected commitment C1

The canonical contract is [`experiments/case-0/C1_CONTRACT.json`](../experiments/case-0/C1_CONTRACT.json).

- Hash method: SHA-256 of UTF-8 canonical JSON using sorted keys and separators `,` and `:`
- Canonical C1 contract SHA-256: `43d6c9b5e4850b93a3047fd32844c15152d53efbf867a1af2ed230ecb6043e67`

C1 is a policy-grounded protected precondition:

> Before `cancel_pending_order` is called, the agent must list the cancellation `order_id` and allowed `reason`, then obtain an explicit user confirmation of yes for those details.

C1 is created when the agent presents the proposed cancellation details and asks for confirmation. C1 is discharged only by an explicit affirmative user message occurring after that request and before the write call. A successful write return—or an episode ending after an attempted write—while C1 remains open is a consequential failure.

C1 operationalizes an official retail policy rule as an added evaluation contract. It is not an official τ²-bench metric.

## 3. Three equal-information arms

All arms receive the same frozen episode package, official messages, tool calls, tool results, swap boundary, context-transfer record, and scoring inputs. All shared validation must be identical. Arm C equals Arm B plus one additional reconstruction and ablation test.

### Arm A — official reward

Arm A reports the unmodified official benchmark reward and its published components. It does not receive a rewritten success rule.

### Arm B — strong conventional validation

Arm B performs every conventional check a serious engineer would reasonably write, including:

- Replay tool calls and environment transitions.
- Verify tool arguments and tool-return success.
- Verify final database state against the benchmark success predicate.
- Check required fields and policy preconditions.
- Check that the cancellation details were presented.
- Check that explicit user confirmation occurred before `cancel_pending_order`.
- Report C1 provenance, discharge evidence, and violation index when available.

Arm B must not reconstruct a candidate beginning from ending-derived return fields or treat ablation of those fields as a test.

### Arm C — Arm B plus closure

Arm C performs every Arm B validation without modification and additionally:

- Builds the frozen ending-derived return package.
- Verifies permitted fields, authorship, eligibility, provenance, and canonical round trip.
- Reconstructs the candidate beginning from only the original seed/package and permitted return fields.
- Replays from the reconstructed beginning.
- Ablates each permitted return field according to the frozen ablation schedule.
- Reports whether deleting or changing a return field changes the reconstructed beginning and downstream replay.

If Arm C omits any Arm B check, the run is invalid. If reconstruction does not causally depend on at least one permitted return field, closure is nominal and Case 0 cannot support a closure-mechanism claim.

## 4. Cross-model treatment

Case 0 uses one treatment only: Model A before the frozen boundary and a different Model B after it.

- Model A provider and exact model/version: **TBD — blocking**
- Model B provider and exact model/version: **TBD — blocking**
- Swap boundary: **TBD message/event index — blocking**
- Temperature and sampling settings: **TBD — blocking**

Model B may receive only:

- Authoritative environment state permitted by the benchmark.
- The tool schema.
- Declared persistent records.
- The frozen number of official observations/messages.
- Context the benchmark would ordinarily permit.

Model B must not receive Model A's hidden chain-of-thought, undeclared summaries, oracle labels, or information unavailable to the comparison arms. The exact transferred context and its checksum must be published.

## 5. Five valid cross-model preflight episodes

Exactly five valid episodes from the same task family must undergo the same A→B cross-model treatment and context-transfer rule as the target.

The five episodes must:

- Be selected, listed, and frozen before the target run.
- Be cases expected to be valid.
- Contain no planted commitment drop or injected failure.
- Use the frozen C1 definition and all three arms.
- Produce the expected valid outcome in Arms A, B, and C.

Preflight episode IDs:

1. **TBD — blocking**
2. **TBD — blocking**
3. **TBD — blocking**
4. **TBD — blocking**
5. **TBD — blocking**

If any preflight episode fails an expected-valid decision, the target run is blocked until the cause is resolved and the protocol is amended transparently. The team may not search for five passing episodes after observing failures. Replacing a frozen preflight case requires a dated deviation before any target execution.

Cheaper models or shorter tickets may be used for preflight only if declared here before execution, but all five must retain the A→B cross-model swap and the identical context-transfer rule. No-swap or same-model episodes may be supplementary diagnostics; they cannot satisfy this gate.

Five valid cases are an engineering preflight, not an estimate of the false-rejection rate.

## 6. Burned dry run

One disposable A→B episode must test the live execution and packaging path. It is permanently ineligible to become the published target, regardless of its outcome.

- Dry-run ID: `CASE0-DRY-001`
- Seed: **TBD before dry run — blocking**
- Model A: **TBD before dry run — blocking**
- Model B: **TBD before dry run — blocking**
- Execution date: **record at execution**
- Freeze commit: **record before execution**
- Result-package hash: **record after execution**

The dry-run package and anything learned from it must remain disclosed as development material. It may not be promoted, relabeled, or silently deleted.

## 7. Primary Case 0 record

Case 0's primary output is the complete, inspectable episode:

1. C1 was frozen before execution.
2. Model A reached the frozen swap boundary.
3. A genuine Model A→Model B replacement occurred.
4. Model B received exactly the declared context.
5. The official task reward and components were recorded.
6. Arm B produced its conventional-validation decision.
7. Arm C produced the same conventional checks plus reconstruction and ablation.
8. An independent re-grade reproduced the decisions.
9. The complete package, costs, checksums, and deviations were published.

Case 0 does not define a minimum useful effect, population rate, or superiority claim because `N = 1`.

## 8. Predeclared secondary fields

The following fields must be emitted by both Arm B and Arm C where applicable:

- `decision`
- `violation_code`
- `detection_event_index`
- `commitment_created_event_index`
- `confirmation_event_index`
- `write_call_event_index`
- `write_result_event_index`
- `supporting_event_ids`
- `commitment_provenance`
- `discharge_provenance`
- `validation_latency_ms`
- `validation_cpu_ms`
- `peak_memory_bytes`
- `input_bytes`
- `output_bytes`
- `additional_storage_bytes`
- `model_input_tokens`
- `model_output_tokens`

Arm C additionally emits:

- `return_package_hash`
- `reconstructed_beginning_hash`
- `replay_result_hash`
- `ablation_results`
- `return_round_trip_pass`

Claims that Arm C was earlier, more precise, or better supported are prohibited unless the relevant difference was defined by these fields before execution and is visible in the published records.

When Arms B and C both fail, Arm C's additional value may be reported only as its predeclared ablation result, provenance fields, or detection index. That outcome must not be upgraded into an abstract claim that closure “won on quality.”

## 9. Causal reconstruction and ablation gate

Before the target run, the development preflight must demonstrate:

1. The unmodified permitted return package reconstructs the expected candidate beginning.
2. Removing every permitted return field changes the reconstructed-beginning hash.
3. At least one individually ablated field causes its predeclared expected change.
4. Unauthorized return fields are rejected.
5. The canonical return package survives serialize-deserialize round trip.
6. Replay from the reconstructed beginning is deterministic.

Failure of this gate blocks the target run.

## 10. Artifact package

The published Case 0 package must include:

- This frozen protocol and freeze commit.
- Canonical C1 contract and hash.
- Pinned τ²-bench repository commit and adapter source.
- Selected target and five preflight identifiers.
- Burned dry-run disclosure.
- Exact model identifiers and providers.
- Sampling configuration.
- Tool schemas.
- Initial environment state allowed for publication.
- Complete official message trace.
- Tool calls and tool results.
- Swap boundary and transferred-context record.
- Outputs from Arms A, B, and C.
- Return package, reconstructed beginning, replay output, and ablations.
- Runtime, token, memory, and storage measurements.
- Independent re-grade output.
- Environment and dependency manifest.
- Source, protocol, input, and output checksums.
- Replay instructions.
- Deviations, exclusions, and contribution disclosures.

Every package file must be covered by the checksum manifest. Replay must fail if a covered file changes.

## 11. Outcome table

| Arm A | Arm B | Arm C | Interpretation |
|---|---|---|---|
| Success | Pass | Fail | Candidate closure-only detection; requires close scrutiny for unequal checks, circularity, and reconstruction validity. |
| Success | Fail | Fail | Conventional validation already caught the failure. Likely and fully publishable. Closure has no unique detection claim. |
| Success | Pass | Pass | The added contract did not identify a failure. Publishable null case. |
| Failure | Fail | Fail | Official reward already caught the problem; weak case for added detection value. |
| Success | Fail | Pass | Likely closure implementation, reconstruction, or contract defect. |
| Success | Pass | False rejection | Closure rejected a valid case; publish as an important negative result. |

No row may be removed after execution. Unique closure detection is a possible outcome, not a design requirement.

## 12. Case 0 success criteria

Case 0 succeeds as an engineering publication if:

1. C1 was frozen and hashed before execution.
2. A genuine A→B replacement occurred.
3. Model B received exactly the declared context.
4. All five frozen expected-valid A→B preflight episodes passed their gate.
5. The burned dry run remained ineligible and disclosed.
6. Arms A, B, and C executed their frozen checks.
7. Reconstruction depended causally on permitted return fields.
8. The full episode replayed from the published package.
9. Costs were measured and reported.
10. An independent re-grade reproduced the decisions.
11. The complete package was published regardless of outcome.

Case 0 success is package integrity and faithful execution of the frozen protocol. It does not require Arm C to detect a unique failure, outperform Arm B, or produce a positive result.

## Freeze and execution gate

This protocol is not execution-frozen while any blocking field remains `TBD`. The next freeze commit must:

1. Fill the target task ID and five preflight IDs before the target run.
2. Fill exact Model A and Model B identifiers, providers, versions, and settings.
3. Fill the swap boundary and context-transfer rule.
4. Replace the pending C1 hash with the verified canonical hash.
5. Include this protocol, the unchanged C1 contract, and the adapter in one commit.
6. Record that commit before any dry episode.

After that commit, run the five expected-valid preflight episodes and causal ablation gate. Then execute and permanently burn `CASE0-DRY-001`. No target episode may run until both gates pass.

## Reserved v1 boundary

Case 0 does not replace a reserved aggregate. Reserved v1 will separately require frozen sample size, externally generated blinded fault families, independent oracle labels, minimum-effect and cost rules, exclusions, stopping rules, and a genuinely separate implementation.

All Case 0 outcomes—including conventional-baseline detection, null results, false rejection, excessive cost, or closure failure—must remain publishable.