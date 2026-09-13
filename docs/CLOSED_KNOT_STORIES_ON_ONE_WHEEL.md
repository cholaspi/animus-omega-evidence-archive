# Closed-Knot Stories on One Wheel: A Narrative Use Case for the Animus Cycle

**By Cholee Hackett**

**Published:** September 13, 2026

**Status:** Use-case note for story and simulation builders. This is a way to use an Animus cycle. It does not extend the research claims, replace Tests 01–04, constitute Test 05 evidence, or define a second theory.

## The job

Some narratives need time to feel nonlinear while the world remains one authoritative history.

A letter is already on the table.

A figure in the doorway is the same person, later.

A vision of a child is not a second timeline; it is the ending of this life, readable too early.

Players still walk through Monday and then Tuesday. The engine is not a time-travel sandbox. It enforces a contract: a small set of declared facts must satisfy frozen conditions at both ends of the run. The ending places permitted facts into a return package. That package reconstructs a candidate beginning, which must execute forward and satisfy the ending contract.

Inside the story, characters may experience this as a future that made their lives possible. Outside the story, the engine treats it as a consistency and validation problem.

That contract is an **Animus cycle**. For story teams, it can be pictured as a wheel.

## The picture, not a new object

- **Rim** — the one official history, experienced and executed forward.
- **Hub** — the short protected list: identities, debts, the letter, the scar, and the doorway that the ending is permitted to plant.
- **Spoke** — a typed ending-derived return whose content becomes effective in a reconstructed beginning (`authored_at` ≠ `effective_tick`). It is rare, declared, validated, and allowed to fail.

The wheel is a diagram of an Animus cycle. It is not a separate research program or an “Animus wheel” theory.

Under the hood, the simulation always **folds forward** from a seed plus an event log. Nonlinear cameras follow spokes. They do not rewind physics.

```text
RETURN_WRITE {
  authored_at: 40
  effective_tick: 3
  payload: "figure in the doorway"
}
```

This record does not mutate an already-executed tick. It becomes part of an ending-derived return package. The engine reconstructs a candidate beginning containing the permitted fact, runs the history forward again, and checks whether tick 40 validly produces the same return.

## The closed knot

In an ordinary linear story, the beginning supplies causes and the ending contains their effects.

In a closed-knot story:

1. The beginning produces the ending.
2. The ending supplies one or more conditions required by the beginning.
3. The reconstructed beginning executes forward.
4. That execution must reproduce an ending that satisfies the frozen contract.
5. If it cannot, the candidate history does not close.

The characters still live forward through one history. Some conditions of their lives exist only because later parts of that same history supply them.

This is the structure behind stories in which:

- a future character delivers the object that began an earlier quest;
- a descendant preserves the relationship required for their own birth;
- an older identity becomes the stranger remembered by its younger self;
- a warning causes the very decision it describes;
- a final scene supplies the image shown in the opening scene.

The engine does not need unrestricted time travel. It needs a bounded set of ending-derived facts and a validator that rejects inconsistent histories.

## One history, not unlimited timelines

Candidate histories may be evaluated during validation, but only one represented history is authoritative. The wheel does not require parallel timelines.

An implementation can enumerate possible return packages, execute each candidate beginning, and classify the result:

- **NONE** — no candidate history satisfies the contracts;
- **UNIQUE** — exactly one candidate history closes;
- **MULTIPLE** — more than one candidate history closes.

These are validation outcomes. They are not automatically represented as worlds inhabited by characters.

If a game intentionally represents several branches and later reconciles them, that is the optional **Animus Omega Cycle** profile. Branch reconvergence is not required for the closed-knot narrative described here.

## What the hub protects

The hub should remain small. It is not a complete save file.

Good protected facts include:

- stable character identities;
- ancestry or relationship requirements;
- ownership of a unique object;
- a debt, promise, or unresolved obligation;
- a message whose authorship matters;
- the eligibility rule for an ending-derived write.

Ordinary microstate can remain outside the hub:

- exact foot placement;
- incidental weather;
- background animation;
- filler dialogue;
- irrelevant inventory ordering.

The contract should protect what the story promises to remember, not every byte the engine has processed.

## What inhabitants can perceive

The declared observer interface does not expose the reconstructed boundary unless the design intentionally represents it.

A character may see:

- the letter;
- the scar;
- the doorway;
- a memory that has always been present;
- an older person who knows too much.

The character does not automatically see:

- candidate enumeration;
- rejected histories;
- the global validation pass;
- hidden provenance fields;
- the reconstruction boundary.

A story may give characters a language for these hidden mechanics, but that is a narrative choice rather than a requirement of the cycle.

## Failure is part of the story system

A closed knot should be able to fail.

Reject the history when:

- the future author never becomes eligible to write the return;
- the returned letter contains information the executed ending never produced;
- the protected identity changes;
- two required facts contradict each other;
- reconstruction produces an ending that cannot return the same permitted facts;
- the projection is edited after outcomes are known merely to force a PASS.

Failure may trigger a game-over state, a visible paradox, another candidate evaluation, or a designer review. The important part is that the engine reports the broken contract instead of silently choosing its favorite history.

## A practical build

A small prototype is enough:

- 1 location shown at an early and late era;
- 3 characters represented at different ages;
- 1 protected letter;
- 1 protected relationship;
- 1 ending-derived doorway event;
- 2 invalid candidate histories;
- 1 valid closed history;
- 1 observer view that never exposes validation metadata.

The test is not whether the story contains mysterious imagery. The test is whether the engine can answer:

- Who authored this fact?
- When did it become effective?
- Was the author eligible?
- Which beginning contract required it?
- Did forward execution reproduce a valid ending?
- Why were the other candidate histories rejected?

## What this does not claim

This note describes how a game or simulation can implement a closed-knot narrative in which later events supply conditions required by earlier events.

It does not claim:

- that physical time behaves this way;
- that a simulation has rewound reality;
- that the future can alter an already-executed event log;
- that one self-consistent history proves predestination;
- that narrative closure is evidence for the Animus Omega conjecture;
- that this teaching use case is a completed Test 05 result.

Narratively, the future can be responsible for conditions in the past. Computationally, the engine constructs a candidate beginning from an ending-derived return package and executes the history forward to test whether it closes.

## Names to keep straight

- **Animus cycle** — the minimum reciprocal-boundary closure contract.
- **Wheel** — a narrative diagram of that contract, not a new theory.
- **Animus Omega Cycle** — the optional branch-reconvergence profile.
- **Teaching use case** — an implementation pattern, not experimental evidence.

Cite the [Animus cycle specification](../osf/ANIMUS_CYCLE.md) for the contract. Use this note as a narrative-design example.

## Citation

Hackett, Cholee. “Closed-Knot Stories on One Wheel: A Narrative Use Case for the Animus Cycle.” Use-case note, September 13, 2026.

A permanent OSF citation will be added only after a real record is deposited and its identifier is confirmed. No DOI or OSF identifier is claimed here.