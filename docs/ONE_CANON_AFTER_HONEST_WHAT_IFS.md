# One Canon After Honest What-Ifs: A Developer Use Case for the Animus Cycle

**By Cholee Hackett**

**Published:** September 12, 2026

**Status:** Design note for game and simulation developers. Not a benchmark, not Test 05, and not a claim about physical time.

Persistent worlds usually die in one of two ways.

They keep every fork and drown in timelines.

Or they pick a favorite save and pretend the other outcomes never ran.

This note describes a third engineering pattern: **run a few declared alternatives, reconcile only what a frozen rule declares equivalent, return to one authoritative history, then let that ending validly seed the next beginning.**

The minimum contract is an **Animus cycle**.

Declared branch reconvergence is an **optional profile** called the **Animus Omega Cycle**. You do not need branching to use the contract. You need branching only when exploring alternatives is part of the product.

## The problem developers already have

A live simulation or agent world accumulates:

- identities and inventories
- relationships and quests
- AI memory and tool traces
- environment and animation state
- player or policy decisions

When a designer, an agent, or a player asks, “What if we break the treaty?”, most stacks either clone the universe or ignore the question.

Clones do not scale. Silent deletion is not auditable. Both make the next season’s “inherited world” a handwritten recap.

You want something narrower:

1. Explore a small number of outcomes under the same rules.
2. Return to one authoritative canon.
3. Know which facts were protected, which were discarded, and why a merge was refused.
4. Start the next era from a package the last era actually produced.

## Two layers (do not fuse the names)

**Animus cycle (minimum).**

A finite run is valid only if its ending produces and validates a return that satisfies a beginning contract declared in advance. Forward execution from the reconstructed beginning must produce an ending that satisfies the declared ending contract. The declared observer interface must not expose a discontinuity at the reconstructed boundary. Information loss is optional and reported separately from closure.

This layer is useful even with **one** timeline: New Game+, a season reset, crash restore, or “the town still owes you” after a wipe.

**Optional branch-reconvergence profile.**

At a fork declared in advance, spawn 2–4 represented histories. Compare them with a **frozen narrative-equivalence projection**. Merge only if protected facts agree. Reject if they do not. When one trunk remains, apply the Animus-cycle return. Reconvergence alone is not closure.

This layer is useful when what-ifs are part of design, training, or play—and the shipped world must still be singular.

## Why this is a use case, not a vibe

### 1. Bounded live state

You stop treating the whole era as hot RAM.

Keep a **ledger**: identities, ownership, obligations, completed decisions, and facts required for the next beginning.

Dump **microstate**: pathing, weather, animation, and most chatter.

That is ordinary streaming with a written rule. The benefit is a capped working set for long runs, not free fidelity.

### 2. Alternatives without staffing a multiverse

Full branches are expensive. Treat them as a budget:

- 1 declared origin
- 2–4 playable branches
- short horizon
- 1 trunk after contraction

More “dimensions” belong in an editor as cheap event-only shadows, not as four parallel cities of LLM agents.

The resource advantage over “keep every timeline” is **one live canon** after contraction. As a first-order estimate, the additional execution cost is proportional to `branch_count × horizon × tick_cost`. This estimate excludes fixed costs, storage, reconciliation, and work shared across branches. If you cannot shorten the horizon, do not add a fifth branch.

### 3. Merge that can fail

A merge is not “we liked ending B.”

Before anyone sees outcomes, freeze which facts are protected—who died, who holds the treaty, whether a debt exists—and which distinctions may be discarded—coat color, weather, or filler dialogue.

Every merge report should list:

- input branches
- output trunk
- protected facts retained
- distinctions discarded
- conflicts and the rule used
- full ancestry

If a protected conflict has no permitted rule, **reject**. Then the designer, the player, or the era-end interface chooses—or the cycle does not close. That failure is a feature. Hidden favorite-branch selection is how trust dies.

### 4. A next beginning that is not a new random seed

Season wipes and generational games usually fake continuity with a trailer.

Here the ending emits a **return package**: continuing identities, inherited obligations, world-generation constraints, and a seed derived from the executed history. The next beginning must satisfy the declared contract. Forward execution must still be able to produce a valid ending. You may not edit the projection after the fact to force a PASS.

Developers get a checked object instead of a lore document.

### 5. Hardening and quality assurance

The same predicates become tests:

- mutate the endpoint → handshake FAIL
- delete an obligation → semantics FAIL
- change only weather → still PASS
- replay the event log in a fresh process → same ledger and observer-visible lines

That tests the declared continuity of the **canon**, not only byte restoration. Checkpoints already protect restorable state. This tests “what we promised the world would remember.”

## A small implementation that would demonstrate the distinction

Do not start with a universe.

- 1 map, 4 locations, 6 agents
- 1 fork (accept or refuse an alliance)
- 3 branches with a short horizon
- about 10 protected predicates
- 1 rejected merge on purpose (same slogan, opposite relationship)
- staged deterministic reconciliation to one trunk
- 1 ending-derived seed for era 2

Such a build would be a development prototype and teaching artifact. It would not become Test 05 evidence unless it were executed under a prospectively frozen protocol with independent validation and the required controls.

If that build does not feel different from three save slots and a recap slide, stop. The architecture is justified only when players or tools can ask *why this fact survived* and receive an audit rather than a cutscene.

## What this does not give you

- Lower GPU cost than one world plus checkpoints if branches stay hot
- Bit-exact fidelity after a dump
- Automatic story quality
- Physical time loops, consciousness, or “the engine is predestined”
- A drop-in replacement for Git, CRDTs, or narrative planners

Ordinary version control merges files. It does not require a beginning contract, an ending-derived return, or sealed-history validation. Use those tools for source. Use this contract when the **world state itself** must close.

## Suggested build order

1. Deterministic tick, event log, and exact checkpoint restore.
2. Ledger versus dumpable microstate. Continue an era from a return package.
3. Contract tests (PASS/FAIL) on restore.
4. Development-only declared forks with a frozen projection and rejection on conflict.
5. Player-visible audit only if reconvergence is part of the fantasy.

Most shipped games should stop at step 3. Steps 4–5 are for generational simulations, agent towns, scenario tools, and time-loop games that need one official record after honest what-ifs.

## Names to keep straight

- **Animus cycle** — minimum reciprocal-boundary contract. Default: one history.
- **Animus Omega Cycle** — optional branch-reconvergence profile on top of that contract.
- **Teaching simulator and fixtures** — executable examples, not production evidence.

Cite the [Animus cycle specification](../osf/ANIMUS_CYCLE.md) for the contract. The [conceptual simulator](https://animusomega.com/simulator) is a teaching model, not Test 05 or experimental evidence. Use this note only as a developer use case.

## Citation

An Animus cycle (Hackett & Hackett, 2026) is a finite-system run whose ending produces and validates a return that satisfies the run’s beginning contract under a declared reconstruction rule. Branch reconvergence is optional and must still pass that contract after one authoritative history remains.

**Current source:** Hackett, Cholee, and Hackett, Kelly. “The Animus Cycle.” Proposed design specification, version 1.0, September 11, 2026. [Repository copy](../osf/ANIMUS_CYCLE.md).

A permanent OSF citation will be added after the record is deposited and its identifier is confirmed. No DOI or OSF identifier is claimed here.