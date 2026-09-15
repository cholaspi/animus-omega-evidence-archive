# Animus Omega for Builders: Start Here

**The problem.** You are building a persistent, generative world. You already have a state store, an event log, and a validation gate, so accepted history does not get silently overwritten. That covers most of what a persistent world needs. It does not cover one thing: constraints that bind a run's ending to its beginning. A prophecy that must pay off. A founding artifact that a later event must actually produce. A stable time loop that has to close. Forward, step-by-step validation cannot enforce these, because it checks each transition in isolation and has no notion of a committed end-to-beginning constraint.

**What this gives you.** Animus Omega's reciprocal-closure contract is a machine-checkable guarantee for exactly that class of world. An executed ending supplies a typed return; a candidate beginning is reconstructed; forward execution must reach an ending that satisfies independently declared conditions. If your bootstrap loop never closes, the history fails closure and you know. If it closes, you have a guarantee, not author vigilance.

**Try it.** The handshake demo runs the contract in your browser: watch a valid history pass the full check, and watch a mutated ending fail. It is a teaching model, not evidence.
https://animusomega.com/handshake

## When to use this

- Authored destiny or prophecy that must stay consistent while generative agents act freely.
- Bootstrap or stable-time-loop narratives that must actually close, not just gesture at a loop.
- Worlds where a committed future constraint must constrain the past, and you need a guarantee.
- Multi-branch worlds that must reconcile into one history without hiding an obligation a branch still owes.

## When not to use this

- Your only requirement is "do not corrupt accepted history." Event sourcing plus a validation gate is enough, and simpler.
- Your world has no committed end-to-beginning constraint. The reciprocal machinery is then pure overhead.
- Your loop is thematic flavor, not a mechanic you need enforced. A symbol does not need a validator.

## Go deeper

- **Full paper:** [Animus Omega: Reciprocal Closure for Persistent LLM-Informed Worlds](./animus_omega_reciprocal_closure_builders.md) — the contract in full, the "why not just event sourcing" argument, the adoption costs, and the evaluation agenda.
- **Specification:** [The Animus cycle](../osf/ANIMUS_CYCLE.md)
- **Claims boundary:** [Claims not made by the Animus-cycle specification](../osf/NOT_CLAIMED.md).
- **Evidence archive:** [dated, checksummed Tests 01-04](../exact-evidence-tests-01-04-2026-09-10.zip). Note: these are component studies and do not establish the combined cycle, and archive integrity is not the same as independent replication.

## One honest boundary

This is a building tool. It enforces a story constraint and says nothing about physical reality, consciousness, or actual time. Everything cosmological or speculative lives in the separate creative work and never in the contract.
