# Classification Record — Test 05 v1.2.0-dev3

**Status: NONCANONICAL CLASSIFICATION RECORD.** This file is not part of the
sealed evidence tree, is not covered by `canonical_digest`, and does not
modify `evidence/test05/revised_development_v1.2.0-dev3/` or
`evidence/test05/reviews/POST_RUN_AUDIT_v1.2.0-dev3.md`, both of which
remain byte-for-byte as sealed.

## Classification

**informative development run, invalid for protocol acceptance**

## Reason

The overall `not_supported` direction reached by v1.2.0-dev3 remains
informative — the post-run audit (`POST_RUN_AUDIT_v1.2.0-dev3.md`)
confirmed that both required properties the integrated evaluator failed to
gate (the section-16 expansion/contraction requirement and the section-13
fault-control matrix) were themselves genuinely failing in that run's
data, so a correctly-wired gate table could only have kept the status at
`not_supported`, never flipped it toward `supported`.

However, the run did not fully comply with its own frozen protocol:

- The runtime `FrozenContract` omitted 16 of the 18 fields section 8
  declares mandatory (`boundary.locked_beginning_contract` carried only
  `total_conserved_invariant` and `min_resolutions`).
- The integrated evaluator (`integrated.py::evaluate()`) omitted 2 of the
  16 required section-17 gates (`expansion_and_contraction` and
  `fault_control_validity`), with two differently-scoped gates occupying
  their slots by name resemblance alone.

Both are genuine protocol non-conformances in the implementation, not
merely reporting gaps — see the post-run audit for the full mechanical
trace. This is why the run is classified **invalid for protocol
acceptance** despite its direction being informative and its raw
component evidence being validator-confirmed self-consistent.

## Scope of this classification

This classification governs how v1.2.0-dev3 is described in all future
reporting (development reports, handoff summaries, protocol documents). It
does not:

- rescore, regenerate, or alter any file under
  `evidence/test05/revised_development_v1.2.0-dev3/`
- rescore, regenerate, or alter
  `evidence/test05/reviews/POST_RUN_AUDIT_v1.2.0-dev3.md`
- retroactively apply v1.3.0-dev4's corrected acceptance criteria to
  v1.2.0-dev3's evidence
- imply that v1.2.0-dev3's raw component measurements are themselves
  unreliable (the validator's 57/57 clean checks concern structural
  self-consistency, which this classification does not dispute)

## Corrective action

The identified defects are corrected in protocol version v1.3.0-dev4
(`docs/TEST_05_PROTOCOL_v1.3.0-dev4.md`, section 0: "Amendments from
v1.2.0-dev3"), run under a new evidence directory
(`evidence/test05/revised_development_v1.3.0-dev4/`) with new development
seeds, per the standing rule that a defect discovered after tick zero is
corrected under a new protocol version rather than patched into the
sealed run.
