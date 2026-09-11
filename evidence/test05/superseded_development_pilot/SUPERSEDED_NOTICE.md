# Superseded development pilot

**Label:** `superseded_development_pilot`

**Status of this run when superseded:** completed (not active, not aborted).
It ran to completion in scratch space (`/tmp/test05_smoke2`, never inside
this repository) under the protocol-v1 draft implementation, then was
copied here byte-for-byte before any protocol changes were applied.

**Why it was superseded:** protocol improvements (observer freezing,
resource-objective freezing, a two-world-family design, a strengthened
beginning commitment, arm-label removal from simulator inputs, core/delayed
semantic probe separation, sensitivity+specificity closure interventions,
and an expanded independent validator) were specified by the requester
before its conclusions were accepted or acted on. Per run-integrity rule 6,
none of those new acceptance criteria are applied to this pilot
retroactively: it is preserved exactly as it ran, under the acceptance
criteria that existed when it ran.

**What is preserved here, unmodified:**

- `results/test05_development_result.json` -- the canonical result this
  pilot produced.
- `evidence/` -- every per-world-family evidence file it wrote.
- `MANIFEST.json` -- its evidence manifest.

**Pilot's headline result (protocol v1, seven world families for
05A/05B/05D, two dedicated smaller families for 05C):**

- `reciprocal_closure`: supported (6/7 world families)
- `semantic_continuity`: supported (7/7 world families)
- `observer_boundary`: unsupported (both observer world families showed a
  qualifying distinction for every bounded observer class in the ladder)
- `resource_advantage`: supported (6/7 world families)
- `integrated_result`: **not_supported** (gated by the observer result)
- `canonical_digest`: `c0cdd03258c587ce2196f086eeb291903a93bdc6863e863837a5b2a05ac46158`

This pilot is not deleted, not overwritten, and not reinterpreted under the
revised protocol. It remains available for comparison. The revised protocol
(v1.2.0-dev3) and its own, separately generated evidence live under
`evidence/test05/revised_development_v1.2.0-dev3/`.

## Provenance record (added when this notice was reviewed for sealing)

**Exact source recoverable at:** git commit `fbcd06067695c98a817e0fadff4b1c56eeb632fb`
("Add Test 05 development source (protocol v1 draft, pre-revision)"). This
commit is the source-only checkpoint created immediately after the pilot ran
in scratch space and before any protocol-revision edit touched the source
tree; no source file changed between the pilot's execution and that commit.

**Verification performed:** the pilot's own `source_hash` field (below) was
independently recomputed from the `.py` files as they exist in commit
`fbcd060`, relative to that commit's `05-test-05/` root (matching
`run.compute_source_hash()`'s convention), and the recomputed hash matches
exactly.

| Field | Value |
|---|---|
| Source commit | `fbcd06067695c98a817e0fadff4b1c56eeb632fb` |
| `source_hash` (recorded and independently reverified) | `0d95e08024fab159f28ae06277f2ca93c736eed728351eadf0a906c86b0cea42` |
| `canonical_digest` (this pilot's evidence digest) | `c0cdd03258c587ce2196f086eeb291903a93bdc6863e863837a5b2a05ac46158` |
| `protocol_hash` | `d7373f2847a50846814bca5edf327b33dfa7362b866e5eab11e103c8323a9408` |
| `config_hash` | `d7bf74f86444b10f377cd09ceb4da9f3ad53585b1c7ec100ada3e79bf3740d13` |
| Sealed evidence path (this move preserved via `git mv`, history intact) | `evidence/test05/superseded_development_pilot/` (previously `05-test-05/superseded-development-pilot-2026-09-11/`) |

No source, protocol, config, threshold, or evidence value was altered by
this relocation or by this provenance review -- only this notice's own text
and the directory path changed.
