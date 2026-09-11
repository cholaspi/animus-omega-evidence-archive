# Post-Run Audit — Test 05 v1.2.0-dev3 Revised Development Run

**Status: NONCANONICAL REVIEW DOCUMENT.** This file is not part of the sealed
evidence tree, is not covered by `canonical_digest`, and carries no authority
to change any conclusion in the sealed run. Nothing under
`evidence/test05/revised_development_v1.2.0-dev3/` or
`evidence/test05/superseded_development_pilot/` was read-modified, rescored,
regenerated, or replaced to produce this document. All findings below were
obtained by (a) reading the sealed JSON/Markdown evidence as-is and (b)
reading the frozen source at commit `d2a5240b3c5e41deb41fa4242036123e8e707650`
and the frozen protocol document. No code was executed and no new seed —
development or reserved — was run to produce this audit.

**Auditor's bottom line up front:** the sealed run's raw measurements are
sound and internally consistent (confirmed independently below), and its
`not_supported` integrated status is correct for this run's data. But the
*mechanism* that produced that status — `integrated.py`'s `evaluate()`
function, called identically by both the generator and the validator — has a
real, code-level gap: 2 of the 16 required §17 gates are never evaluated at
all, and a same-shaped-but-different check silently occupies each of their
slots. It happened not to matter this time because both omitted properties
were themselves failing. It could matter in a future run. See §9 for the
full classification.

---

## 1. Why `expansion_contraction` is unsupported but not a listed failed gate

**This is real, not a reporting error in the handoff — it is a code gap.**

`integrated_determination.json`'s `gates` array contains a gate named
`expanding_and_contracting_represented_world`. Its `ok` value is `true` in
this run. It is tempting to read this as "the R(t) expansion/contraction
requirement passed." It did not. Reading `src/animus_test05/integrated.py`
lines 153–159:

```python
boundary_families = boundary_result.get("per_world_family", {})
ran_boundary = len(boundary_families) > 0
gates.append(_gate(
    "expanding_and_contracting_represented_world",
    ran_boundary,
    "every 05A world family executes a history (expansion) followed by a J "
    "boundary transition (contraction)",
))
```

This gate checks only that *05A ran at all* (`len(boundary_families) > 0`,
trivially true whenever any family was evaluated). It has nothing to do
with the actual §16 requirement:

> R(t) = live entities + live represented-region cells. Expansion and
> contraction are supported only if ... R(t1) ≥ 2×R(t0) ... and R(t2) ≤
> R(t0) + 1.

That requirement is implemented separately, correctly, in `expansion.py`,
and its result is honestly reported as `unsupported` in both families
(`runs/expansion/{friendly,adversarial}.json`, and in the top-level
`world_family_results` dashboard and `expansion_contraction_result` in the
canonical result). The gap is that `integrated.evaluate()` — the function
that builds the gate table both the generator and the validator use — never
takes `expansion_result` as an argument at all. Confirmed by its signature:

```python
def evaluate(boundary_result, residual_result, observer_result, resource_result) -> dict:
```

`expansion_result` is computed in `run.py` (`expansion.run_component(...)`,
line 242) and written to evidence, but it is **never passed into
`integrated.evaluate()`**, so no gate in the 13-entry `gates` array can ever
reflect it, regardless of its status. `expanding_and_contracting_represented_world`
is a same-topic, wrong-content stand-in that happens to sit in the slot where
§17 item 1 belongs.

**Conclusion:** the omission from `failed_gates` is a genuine code defect in
the gate-evaluation function, not a quirk of the handoff summary. See the
gate matrix in §4 and the classification in §9.

## 2. Why the causal_reorder mismatches are not a listed failed gate

**Same root cause as §1, on the other required gate.**

§13 of the protocol ("LEDGER CAUSALITY AND FAULT CONTROLS") states, after
covering ledger causality:

> Fault-control validity is separate. Every required fault must produce its
> frozen predicted rejection or semantic failure: identity substitution,
> obligation deletion, contradictory ledger, missing provenance, stale
> event, duplicate event, causal reorder, no ledger, random reconstruction.

This is exactly `execution_matrix.py`'s 9-mutation fault matrix, whose
result is stored as `fault_control_result` / `runs/execution_matrix/*.json`.
For the adversarial family, `all_predictions_matched: false` with 2 of 30
executions (`adversarial-seed14001-causal_reorder`,
`adversarial-seed14003-causal_reorder`) not matching their frozen
prediction — so per §13's "every required fault must produce its frozen
predicted rejection," fault-control validity is **not** established for the
adversarial family. `runs/execution_matrix/adversarial.json`'s own
`status` field correctly says `"unsupported"`.

`integrated.py` has a gate named `negative_and_fault_injection_controls_pass`
that sounds like it should cover this. It does not:

```python
controls_ok = all(
    r.get("support_checks", {}).get("negative_controls_correctly_fail")
    for r in residual_result.get("per_world_family", {}).values()
) and len(residual_result.get("per_world_family", {})) > 0
```

This reads `residual_result` (05B's negative controls — corrupted/mangled
residuals correctly failing semantic probes), not `execution_matrix_result`
(the seed-based frozen fault-prediction matrix required by §13).
`execution_matrix_result` is never passed into `evaluate()` at all — same
defect shape as §1, on a different required gate.

**Conclusion:** identical root cause to finding #1: a whole required
component (`execution_matrix_result`, i.e. §13's fault-control matrix) is
computed and honestly reported at the component level, but structurally
excluded from the integrated gate table. The `negative_and_fault_injection_controls_pass`
gate name is a false friend — it passes based on unrelated 05B evidence
while the real §13 fault-control matrix result (which fails for
adversarial) is silently absent from the top-level accounting.

## 3. The "contract schema gap" — precise scope and which requirements it violates

**What is missing, precisely:** §8 ("BEGINNING CONTRACT") specifies a
"Minimum contract contents" list of 17 fields the beginning contract must
carry (protocol version, world-family ID, physics-configuration hash,
identity-table commitment, relationship schema, obligation schema,
causal-order rules, locked beginning payload schema, dump operator,
residual schema, ledger schema, observer-specification hash,
resource-objective ID, declared causal path, intentionally discarded
fields, irrelevant fields, frozen semantic-probe IDs, delayed-probe
generator hash) and requires the boundary transition to consume the actual
contract object (§8 point 6: "Pass the actual contract object into the
boundary transition").

The runtime `FrozenContract` object that `execute_J()` actually receives,
builds, hashes, and consumes (`boundary.py::locked_beginning_contract()`)
contains exactly two fields:

```python
return FrozenContract({
    "total_conserved_invariant": config.total_resource,
    "min_resolutions": 1,
})
```

`protocol/beginning_contract_schema.json` (a frozen companion file,
correctly produced and hashed before tick zero per §7) documents this
explicitly and honestly as `operationally_implemented_fields` (2 fields)
versus `documented_full_schema_fields` (the full 17), with a note calling
it "a declared scope limitation, not a silent gap."

**Does it violate the frozen beginning-contract requirements (§8)? Yes.**
§8 calls its field list "Minimum contract contents" — "minimum" is a floor,
not optional guidance — and the object that is actually built, hashed,
frozen, and consumed by J carries 2 of the 17 required minimum fields. The
*mechanism* around those 2 fields (immutable before tick zero, SHA-256
digest, `committed_at_tick = -1` semantics, single-use `consume()`,
rejection of post-hoc creation/modification) is correctly implemented and
independently confirmed below — but the *content* required by §8 is
incomplete. This is a real, not cosmetic, protocol non-conformance.

**Does it violate canonical evidence requirements (§19)? No, in the narrow
sense.** §19's "Result Format" list does not mandate a specific field count
inside the beginning contract; it requires the canonical result to include
things like world-family results, hashes, etc. `boundary.py`'s
`to_evidence()` records exactly and honestly what the operational contract
contains (`{"data": {...2 fields...}, "content_hash": ..., "consumed": ...}`)
— nothing is misrepresented as more complete than it is, and §7's "beginning
contract for each family" and "beginning-contract schema" freeze
requirements were both satisfied (both files exist, hashed, before tick
zero).

**Does it violate validator requirements (§18)? No, but it exposes a blind
spot.** §18's explicit rejection-class list does not name "beginning
contract missing minimum §8 fields" as something the validator must reject.
Checked directly: `validator.py`'s only contract-related checks are hash-
consistency (`beginning_commitment.content_hash` matches `hash_obj(data)` —
i.e. it was not modified) and correct rejection of the shortcut arm that
never calls `consume()`. It does not check field-count completeness against
§8's list, so it neither falsely certifies completeness nor is obligated by
its own declared checklist to catch this. It simply cannot see this
particular gap, because §18 never asked it to look.

**Is it only an optional implementation goal? No.** §8's field list is
worded as a mandatory minimum, inside the core protocol body (not an
appendix or "nice to have" section), and it materially matters: several of
the missing fields (declared causal path, frozen semantic-probe IDs,
observer-specification hash) are exactly the kind of content that, if
threaded into J, would let §8's own required rejections ("a transition
that does not read contract fields," "reconstruction using discarded
source state") be checked against a much richer contract than the current
2-field one allows. Calling it "optional" would understate a genuine,
if honestly disclosed and scoped, protocol non-conformance.

## 4. Protocol-to-evidence gate matrix (§17, all 16 required items)

All raw values below were read directly from the sealed evidence; nothing
was recomputed or re-scored.

| # | Gate (per §17) | Governing clause | Evidence path | Raw measured value | Component status | Expected integrated effect | Correctly reflected in `integrated_determination.json`? |
|---|---|---|---|---|---|---|---|
| 1 | Required expansion and contraction | §16 | `runs/expansion/{friendly,adversarial}.json` | friendly: R(genesis)=3, need R(t1)≥6, provable ceiling=5; adversarial: R(genesis)=4, need R(t1)≥8, provable ceiling=6 | **unsupported**, both families (mathematically impossible at these world sizes) | should fail a dedicated gate | **NO** — no gate reads `expansion_result`; the same-named `expanding_and_contracting_represented_world` gate (`ok: true`) instead checks only that 05A ran |
| 2 | Beginning contract committed before tick zero | §8 pts 1–4, §10 req #6 | `runs/boundary/{fid}.json.beginning_commitment` | `committed_at_tick=-1`, content_hash present and stable, contract built from `WorldConfig` only | supported, both families | pass | Yes — `independently_locked_beginning_contract`, `ok: true` |
| 3 | Ending-derived return value | §10 required transition | `runs/boundary/{fid}.json` arms | `return_value_of(ending_state)` computed and fed to `execute_J` in every arm | supported, both families | pass | Yes — `ending_derived_return_value_present`, `ok: true` |
| 4 | Executed J transition | §8 required transition, §10 req #7 | `runs/boundary/{fid}.json` arms | `execute_J()` called; `contract.consumed=true` recorded per arm | supported, both families | pass | Yes — `executed_transition_ending_to_beginning`, `ok: true` |
| 5 | At least one closing history | §10 req #1 | `runs/boundary/{fid}.json.support_checks` | `at_least_one_natural_closing_history: true` (both families; 256 histories enumerated per family) | supported | pass | Yes, merged with #6 into `both_closing_and_non_closing_histories`, `ok: true` |
| 6 | At least one non-closing history | §10 req #2 | same | `at_least_one_natural_non_closing_history: true` (both families) | supported | pass | Yes, merged with #5 (same gate) |
| 7 | Causal endpoint sensitivity | §10 reqs #4–5 | `runs/boundary/{fid}.json.support_checks` | `relevant_intermediate_breaks_closure`, `irrelevant_intermediate_preserves_closure`, `relevant_intermediate_modifies_causal_path`, `irrelevant_intermediate_does_not_modify_causal_path` all `true` (both families) | supported | pass | Yes — `causal_sensitivity_and_specificity`, `ok: true` |
| 8 | Genuine information loss | §11 | `runs/residual/{fid}.json.support_checks.non_injective_loss_demonstrated` | `true`, both families (each residual has ≥1 collision group) | supported | pass | Yes — `genuine_information_loss`, `ok: true` |
| 9 | Semantic continuity, all core probes | §11 | `runs/residual/{fid}.json.main_probe_grade.scoring.required_core` | `9/9` pass, both families | supported | pass | Partially — measured distinctly (9/9) at the component level, but folded (AND) into `preserved_semantic_behavior_through_loss` alongside #10 and #11 rather than reported as its own gate; `ok: true` in this run |
| 10 | Semantic continuity, all delayed probes | §11 | `runs/residual/{fid}.json.main_probe_grade.scoring.delayed` | `8/8` pass, both families | supported | pass | Partially — same merged gate as #9 |
| 11 | Clean leakage audit | §12 | `runs/residual/{fid}.json.leakage_audit` (probe-answer leakage) | clean, both families | supported | pass | Partially — folded into the same merged gate as #9/#10, `ok: true`. (Note: a *separate* simulator-core no-label-leakage audit, `runs/label_audit.json`, `clean: true`, is reported top-level but is also not itself a §17 gate — it is a §9/§18 simulator-isolation concern, not the §12 leakage audit) |
| 12 | Ledger causality | §13 (part 1) | `runs/boundary/{fid}.json` arm 8, `runs/residual/{fid}.json.controls` | 05A arm 8 (correct return, corrupted ledger) fails to close; 05B ledger-removal/staling/contradiction controls correctly fail probes, both families | supported | pass | Yes — `narrative_ledger_causally_load_bearing`, `ok: true` |
| 13 | Valid fault controls | §13 (part 2) | `runs/execution_matrix/{fid}.json` | friendly: 3/3 executions match prediction; adversarial: **28/30** match, 2 `causal_reorder` executions do not | friendly **supported**, adversarial **unsupported** | should fail a dedicated gate (adversarial) | **NO** — no gate reads `execution_matrix_result`; `negative_and_fault_injection_controls_pass` (`ok: true`) instead checks unrelated 05B negative-control data |
| 14 | Primary observer indistinguishability | §14, "Primary support threshold" | `runs/observer/{fid}.json.primary_result` | friendly: TV=0.276306, acc=0.638153; adversarial: TV=0.240234, acc=0.620117 (threshold: supported only if TV≤0.05 **and** acc≤0.55) | **unsupported**, both families | should fail | Yes — `no_qualifying_distinction_for_primary_bounded_observer`, `ok: false`, listed in `failed_gates` |
| 15 | Full-state observer boundary detection | §14, "Positive control" | `runs/observer/{fid}.json.positive_control_result` | TV=1.0, acc=1.0, both families (threshold: TV≥0.25 or acc≥0.75) | supported (valid), both families | pass | Yes — `positive_control_observer_detects_boundary`, `ok: true` |
| 16 | Fidelity-matched resource advantage | §15 pt 4 | `runs/resource/{fid}.json.pareto` | regression on 3 baselines in both families: `general_purpose_lossless_compression`, `general_purpose_lossy_compression_matched_fidelity`, `scripted_cyclic_replay` (peak canonical bytes not strictly lowest) | **unsupported**, both families | should fail | Yes — `fidelity_matched_resource_advantage`, `ok: false`, listed in `failed_gates` |

**Row count check:** 16 required items map onto exactly **13** gates that
actually exist in `integrated.evaluate()`'s output. Items 5+6 are correctly
merged (a logical AND of both is equivalent to requiring both). Items
9+10+11 are correctly merged in the same sense, and the individual 9/9 and
8/8 counts are separately and correctly available in the component
evidence even though the integrated gate collapses them. Items **1 and 13
have no real gate at all** — the two "extra" gates that fill their slots
by name resemblance measure different things, both trivially/incidentally
`ok: true` for reasons unrelated to §17's actual items 1 and 13.

## 5. Were all 16 gates evaluated, or only observer and resource?

**Neither extreme is exactly right; the precise answer is: 13 gates were
evaluated, not 16, and of those 13, 11 correctly and fully cover 14 of the
16 required items (with two legitimate, disclosed merges: 5+6, and
9+10+11). Items 1 and 13 were never evaluated as such** — the code
computes their real underlying data (`expansion_result`,
`execution_matrix_result`) and reports it faithfully in the standalone
component dashboards, but `integrated.evaluate()`'s function signature
(`boundary_result, residual_result, observer_result, resource_result`)
structurally cannot receive either one, so neither can ever gate the
integrated status, in this run or any future run of this same code.

This is not "only observer and resource were evaluated" — reciprocal
closure, loss, semantic continuity, ledger causality, and both observer
sub-claims were all genuinely evaluated and correctly gated. It is
specifically the two newest components (expansion/contraction and the
seed-based fault-execution matrix — both added later in this protocol
version's development, per the task history) that were wired into the
per-family dashboard and canonical result but never wired into the
integrated gate function.

## 6. Why the validator returned `valid: true`

Four distinct claims must not be conflated, and the sealed evidence
supports exactly one of them:

- **Structurally valid evidence — YES, and this is what `valid: true`
  actually certifies.** The validator's 57 checks confirm: every
  referenced evidence file exists and hashes correctly; every recomputable
  quantity (history/microstate/collision counts, semantic scores, observer
  distributions, resource peak-byte totals) matches an independent
  recomputation from raw config and seeds; no probe-answer leakage; no
  label-driven simulator behavior; the shortcut/copy/ignore detectors fire
  correctly; and — critically for this audit — `stored_integrated_gates_match_recompute`
  passed because the validator recomputes the integrated gates using the
  *exact same* `integrated.evaluate(boundary_result, residual_result,
  observer_result, resource_result)` call the generator used. Both share
  the identical blind spot identified in §1/§2/§5, so this particular check
  is self-consistent but cannot detect that blind spot — it was never
  designed to (§18's rejection-class list, reproduced in §7 below, does not
  include "integrated gate table omits a required component").

- **Scientifically supported component — NO, correctly reported as such at
  the component level.** `expansion_contraction_result.status` is
  `"unsupported"` in the sealed evidence, with the exact ceiling arithmetic
  recorded. `execution_matrix_result`'s adversarial entry is
  `"unsupported"` with `all_predictions_matched: false` and the two
  offending `execution_id`s named. Neither of these true, honest,
  component-level `"unsupported"` findings was hidden, altered, or
  contradicted anywhere in the sealed evidence — they simply were never
  propagated into the 16-gate accounting.

- **Failed control — YES, for the 2 causal_reorder executions, and this
  too is honestly recorded.** `execution_matrix.py`'s own
  `unexpected_predictions` field names them explicitly, and the
  `FAULT_PREDICTIONS` mismatch is a genuine, preserved negative finding
  (per the project's standing "do not engineer away a failed result"
  constraint) — not evidence of corruption or invalidity in the run itself.

- **Invalid experiment — NO.** Nothing found in this audit indicates
  post-hoc contract modification, label leakage into the simulator, reuse
  of a reserved seed, retroactive threshold changes, or tampering with any
  raw evidence file. `valid: true` is an accurate claim about the
  integrity of what was measured. It is not, and was never claimed by
  `validator.py` to be, a claim that the *integrated aggregation logic*
  itself is complete or defect-free.

In short: `valid: true` + `not_supported` + "two components independently
show real failures that never appear in `failed_gates`" are not
contradictory. They describe, respectively: the data is trustworthy; the
top-level conclusion happens to be right anyway; and the code that produces
the top-level conclusion has a gap that this run's particular results
happened not to expose as a wrong *answer* (only as an incomplete
*explanation*).

## 7. Canonical digest coverage

Traced directly from `src/animus_test05/run.py::execute()`:

| Category | Covered by `canonical_digest`? | How |
|---|---|---|
| All raw per-family runs (boundary, residual, observer, resource, expansion, execution_matrix) | **Yes** | Each is embedded directly inside `result` (e.g. `world_family_results`, `fault_control_result`, `expansion_contraction_result`, `positive_control_result`, `observer_sensitivity_results`, etc.) *and* every `runs/*.json` file's SHA-256 is separately recorded in `evidence_manifest`, which is itself embedded in `result` before `hash_obj(result)` runs |
| Protocol files | **Yes** | `protocol_hash` is embedded directly; every `protocol/*.json` companion file's hash is embedded via `companion_file_hashes` (copied from the freeze-time manifest) |
| Configuration files | **Yes** | `config/*.json` file hashes are part of the same `companion_file_hashes` list; `config_hash` is derived from `companion_manifest_digest` (a hash over all companion-file hashes, protocol doc included) and is itself embedded in `result` |
| World definitions | **Yes** | `worlds/{friendly,adversarial}.json` are written and hashed during `freeze()` into the same `manifest_entries` that produce `companion_manifest_digest` → `config_hash` → embedded in `result`; their hashes also appear directly in `companion_file_hashes` |
| Component results | **Yes** | Embedded directly (see row 1) |
| **`results/integrated_determination.json`** | **No** | This file is produced by `validator.py`, invoked *after* `execute()` has already computed and written `canonical_digest`. It is a deliberately separate, later, independently-derived artifact — not part of the frozen generator output, and by design not hashed into `canonical_digest` |
| **`validator/validation_report.json`** | **No** | Same reasoning — produced by a still-later validator invocation, entirely outside the digest's scope |

This asymmetry is intentional protocol design (§18's requirement that the
validator "recompute conclusions from raw evidence" rather than trust a
cached status), not an oversight: `canonical_digest` seals exactly what
`execute()` produced at tick zero, and the validator's output is meant to
be independently re-derivable — and was, in fact, re-derived twice in this
session, byte-identically, from the same sealed raw evidence. But it does
mean that neither `results/integrated_determination.json` nor
`validator/validation_report.json` is tamper-evident via `canonical_digest`
on their own; their trustworthiness rests entirely on being reproducible
from the (digest-covered) raw evidence, which this audit did not
re-execute but which the prior session's two independent validator runs
already demonstrated (byte-identical `valid: true`, 57/57 checks, both
times).

## 8. Concluding classification

**D. A precise hybrid classification, more accurate than B or C alone:**

The sealed run's raw component evidence is genuine, was correctly measured
under the frozen protocol and seeds, and is validator-confirmed
self-consistent (§6). The `not_supported` bottom-line status in
`results/integrated_determination.json` is **not falsified by this audit**:
both of the two required properties that were silently excluded from the
gate table (§16's R(t) expansion/contraction, §13's fault-control matrix)
were themselves genuinely failing/unsupported in this run's data, not
passing — so including them correctly could only have kept the status at
`not_supported`, never flipped it toward `supported`. There is therefore no
basis to distrust this run's `not_supported` conclusion, and no basis to
mark this specific sealed run's raw evidence "invalid."

However, this is more than an "incomplete failed-gate list" in the benign
sense of option B. `integrated.py::evaluate()` — the single function both
the generator and the validator call to produce the integrated
determination — has a **material, structural code defect**: its parameter
list (`boundary_result, residual_result, observer_result,
resource_result`) architecturally cannot receive 2 of the 6 computed
components (`expansion_result`, `execution_matrix_result`), so those 2 of
the protocol's 16 required §17 gates can never be evaluated by this
function, in this run or any other. Two gate names in the current output
(`expanding_and_contracting_represented_world`,
`negative_and_fault_injection_controls_pass`) are misleading in that they
occupy the visual slot of, but do not measure, the corresponding required
§17 item. Because the validator's own recomputation reuses this same
function, it cannot catch its own blind spot — `valid: true` certifies
self-consistency, not §17-completeness.

The practical risk this poses is prospective, not retrospective: **a future
run of this same code, on a world configuration where the observer and
resource gates both happen to pass, would report the integrated conjecture
as `"supported"` while silently ignoring a real R(t) or fault-control
failure**, if either were present. That would be a false positive the
validator's current design cannot detect, because both the "generator" and
the "independent" recomputation share the identical omission.

**Recommendation, consistent with "do not modify the sealed run":** do not
alter, rescore, or re-derive anything under `evidence/test05/revised_development_v1.2.0-dev3/`.
This run's `not_supported` conclusion stands as correctly reached, for the
reasons it gives plus the two it omits. But `integrated.py::evaluate()`
should not be treated as a trustworthy 16-gate implementation of §17 until
a new protocol version threads `expansion_result` and
`execution_matrix_result` through it as first-class gates (with their own
`failed_gates`/`ineligible_gates` entries, not folded into misleadingly-named
existing gates) — per the protocol's own rule that a defect discovered
after tick zero must be fixed under a new version rather than patched into
this sealed run.

---

*This document is descriptive and non-authoritative. It creates no new
evidence, changes no hash, and does not alter `results/integrated_determination.json`,
`results/test05_development_result.json`, or any file under
`revised_development_v1.2.0-dev3/` or `superseded_development_pilot/`.*
