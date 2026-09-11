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
revised (v2) protocol. It remains available for comparison. The revised
protocol and its own, separately generated evidence live alongside this
directory under a new dated evidence directory and a new protocol version.
