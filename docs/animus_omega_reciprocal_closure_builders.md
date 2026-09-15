# Animus Omega: Reciprocal Closure for Persistent LLM-Informed Worlds
### A Closure Contract for Worlds with Committed End-to-Beginning Constraints

**Cholee Hackett, Kelly Hackett**
15 September 2026
*Proposed author list; authorship, order, and affiliations require confirmation.*
*Author-review draft, revision 4 (builder-facing reshaping of revision 3). Not submitted, accepted, or peer reviewed.*

---

> **Revision note (rev 3 to rev 4).** This revision re-scopes the document for its intended readers: builders of persistent simulations and LLM-informed worlds. Five changes. (1) The contribution is narrowed from "a general framework for persistent worlds" to a closure contract for the specific class of worlds that carry committed end-to-beginning constraints (authored destiny, prophecy payoff, bootstrap loops, multi-branch reconciliation). (2) A new early section answers the question a builder asks first: what does this give me that event sourcing and validation do not, and when is it not worth adopting. (3) The world-design material is retained but reframed as buildable design patterns rather than as vision, since this audience builds exactly these mechanics. (4) The four component studies are pulled into a clearly separated foundational-research track, reported for completeness, because a builder prices adoption on the runnable artifact, not on the science arm. (5) The runnable spec, fixtures, and reference engine are moved forward. One wall is kept throughout and it is the only one this audience needs: the pattern is a building tool, never a claim about physical reality, consciousness, or time.

---

## Abstract

Persistent LLM-informed worlds have two jobs that pull against each other. They must generate new events, and they must not let a generated proposal silently overwrite accepted identity, ownership, and causal history. Ordinary state management already handles the first job well: event sourcing plus a validation gate keeps a model's description of a transfer from establishing that the transfer occurred. This paper is about a second, narrower job that ordinary state management does not do. Some worlds carry constraints that span an entire run and bind its ending to its beginning: a prophecy that must pay off, a founding artifact that a later event must actually produce, a destiny that must be earned rather than asserted. Forward, step-by-step validation cannot enforce these, because it checks each transition in isolation and has no notion of a committed end-to-beginning constraint.

We present Animus Omega's reciprocal-boundary closure contract as a machine-checkable guarantee for exactly that class of world. An executed ending supplies a typed return; a candidate beginning is reconstructed under a declared rule; forward execution must reach an ending that satisfies independently declared conditions; and, in the optional extension, represented branches must reconcile into one authoritative history without hiding unresolved protected differences. We give the contract in compact notation, state plainly when it is worth adopting and when it is not, supply elementary distinctions and counterexamples that mark its adoption costs, and summarize four existing component studies as a foundational track with their original limits. No new experiment, independent replication, or completed end-to-end evaluation is reported. The open engineering question is whether reciprocal closure earns its complexity over strong conventional validation for worlds that carry committed end-to-beginning constraints. We argue it does for that class and does not outside it.

**Keywords:** persistent simulations; large language models; narrative systems; reciprocal closure; state reconstruction; multiagent systems; provenance; bootstrap constraints.

---

## 1. Introduction: two jobs, and the one nobody has a spec for

A persistent artificial world must support new events and preserve the consequences of events already accepted. A character can change its mind, an object can change ownership, a community can revise its understanding. None of these requires the world to silently replace the history that explains them. In an LLM-informed world, this suggests separating generated proposals from authoritative transitions: a model may describe a transfer, but that description should not by itself establish that the transfer occurred.

The tooling for that first job exists and is good. Generative Agents combines experience records, retrieval, reflection, and planning in a town of 25 agents [1]. MemGPT organizes information across memory tiers rather than placing every record in the immediate model context [2]. LongMemEval shows that retrieval and memory organization remain consequential to long-term conversational performance [3]. Event sourcing reconstructs state from a recorded log [13]. If your only requirement is "do not corrupt accepted history," you can build that today from these parts, and you do not need anything in this paper.

There is a second job these parts do not do. Consider a world with a constraint that binds its ending to its beginning:

- A **founding artifact** exists at the start of a civilization, and the story requires that a later expedition within the same run actually produced and deposited it. The loop must close.
- A **prophecy** is planted early and the world must honor it by the end, checked as a fact rather than felt as a theme.
- An **authored destiny**: this run must end with a specific condition true, and generative agents must be free to act while that committed ending still holds.
- Several **branches** of a history must reconcile into one authoritative record without quietly discarding an obligation one branch still owes.

Forward validation, applied step by step, cannot enforce any of these. It confirms that each transition was legal when it happened. It has no mechanism to require that the end of a run derive a return that satisfies the run's own beginning, or that a founding artifact accepted at tick zero is genuinely produced before the run ends. A builder who wants that guarantee is currently on their own: they enforce it by author vigilance and hope no agent drifts the late game into incoherence.

Animus Omega asks a narrow structural question for exactly this class of world. Can the ending of a bounded simulated history supply a return that genuinely satisfies the history's beginning under a declared reconstruction rule? Its optional branch-reconvergence extension asks whether declared alternatives can reconcile into one authoritative history without hiding unresolved protected differences [4]. This paper organizes that contract for builders, states when it earns its keep and when it does not, and connects it to a bounded evaluation agenda. The analyses here are design analysis, not retroactive findings of the component studies, and the proposed evaluation is not a completed end-to-end test.

## 2. Scope, terminology, and the one wall this audience needs

**Four meanings kept separate.** *World state* denotes accepted records and permitted transitions. *Agent belief* denotes what a participant currently represents as true. *Narrative interpretation* denotes an explanation given by an inhabitant, player, or author. *Validation* denotes an explicit check against a declared contract. A belief may be false without corrupting world state, and an evocative interpretation may be meaningful without validating a transition. Builders already live this distinction; it is why a non-player character can be wrong without the save file becoming wrong.

**Observer** is an operational term for an interface with restricted observations. It is not a claim of consciousness. A shared model can generate outputs for several bounded contexts without implying that a conscious entity has literally divided. **Fidelity** means preservation of specified states, consequences, or observations, not subjective indistinguishability.

**The single wall.** The design patterns in this paper, including bootstrap loops, temporal gateways, reincarnation-as-role-reinstantiation, and legends-derived-from-real-events, are mechanics you build. They are not claims about physical reality, consciousness, or actual time. The contract enforces a story constraint; it says nothing about the universe. This is the only boundary this audience needs, and everything below holds it. Evocative names (ouroboros, Lighthouse, remembrance, compassion) are labels for operations; an evocative reading of an operation is not evidence for that reading.

**Terms.** An *Animus cycle* is the published reciprocal-boundary contract. An *Animus Omega cycle* is its optional, stronger branch-reconvergence profile. Candidate histories examined by a validator are not automatically inhabited parallel worlds, and a periodic spatial topology is distinct from cyclic history [4, 7].

## 3. Related work and the proposed distinction

**Memory and multiagent environments.** Memory-bearing agents are not new. The relevant question is how a system connects remembered claims to permitted actions and accepted consequences. Generative Agents supplies an architecture for remembering and reflecting in a shared environment [1]; MemGPT addresses movement between memory tiers [2]; LongMemEval offers tasks involving temporal reasoning, updates, and abstention [3]. These are components and comparators, not strawman systems that forget at every turn. A simulation can also support agent evaluation without reproducing human society; for example, tau-squared-Bench evaluates conversational agents in an environment where both assistant and simulated user act [10]. Animus-style tasks add a reciprocal dependency rather than relabel ordinary tool-result verification as closure. A completed action, a preserved obligation, and a valid ending-to-beginning return are different outcomes.

**Computational narrative and model description.** Riedl and Young distinguish causally coherent plot progression from the intelligibility of character intentions [11]. A character's reason to cooperate and the machine-checkable result of that cooperation should not be fused; a narrative supplies reasons to act, but the validator checks the resulting events. The ODD protocol is a useful precedent for describing simulation purpose, entities, scheduling, and design concepts [12]. An Animus implementation should similarly separate events imposed by design from events that arise from agent decisions. A prearranged successful ending is an acceptable authored experience, but it is not evidence that autonomous agents reliably find such an ending.

**State reconstruction and formal checking.** Event sourcing is the direct precedent for reconstructing state from recorded events [13]. Alloy illustrates finite-scope exploration and counterexample search [14]. The Animus specification itself names fixed-point constraints, checkpointing, event sourcing, and replay as close neighbors [4]. The name does not establish novelty over these techniques, and an existing implementation could satisfy the same contract. The proposed distinction is procedural: a particular ending must supply permitted return content; the beginning requirements must be fixed independently; forward reconstruction must be checked; and failures, losses, and branches must be reported separately. Whether this composition earns its keep over strong existing methods is an empirical question, and a related caution is that cycle-consistent image translation can hide information rather than perform the intended transformation [15]. That is an analogy about evaluation failure, not evidence that Animus Omega exhibits it.

## 4. Why not just event sourcing? When reciprocal closure is worth it

This is the section to read first if you already run a state store, an event log, and a validation gate. The honest answer to "what does this give me that I do not already have" is: nothing, unless your world carries a constraint that binds its ending to its beginning. If it does, reciprocal closure gives you a machine-checkable guarantee that no forward validator can produce. This section draws that line precisely, in both directions, so you can decide in five minutes whether the pattern is for you.

### 4.1 What forward validation already gives you (and why it is usually enough)

Event sourcing plus a validation gate checks **per-transition legality**. Each proposed event is evaluated against the rules as it is appended: is this writer eligible, does this transfer have a supporting record, does this state change respect ownership and permissions. This catches unsupported transfers, altered identities, illegal writes, and forbidden observations, locally, step by step, as they happen. Accepted history is reconstructable from the log, and a generated proposal never becomes authoritative just because a model emitted it.

For most persistent worlds this is the whole requirement. If your world only needs to grow without corrupting what it has already accepted, stop here. You do not need reciprocal closure, and adopting it would be complexity you do not use. We want to be the spec you reach for when it helps, not the one you cargo-cult when it does not.

### 4.2 The guarantee forward validation cannot give

Forward validation is local and step-wise. It has no representation of a constraint that spans an entire run and ties its end to its beginning. Three capabilities fall in this gap, and each is a mechanic builders actually ship:

**Committed endings (authored destiny).** You want to guarantee that a run ends with a specific condition true, while leaving agents free to act along the way. Forward validation lets the world wander anywhere; nothing forces the ending to satisfy a pre-committed condition. You are left enforcing destiny by watching the run and intervening, which does not scale and breaks under autonomous agents.

**Bootstrap loops that must close.** A later event must supply an earlier condition, and the loop has to actually close within the run. Forward validation, run start to finish, cannot verify that a thing consumed at the beginning is genuinely produced by the end, because the thing was already legal when it was accepted at the start. The check it would need points backward, and forward validation has no such check.

**Prophecy and foreshadowing that must pay off.** A condition is planted at the beginning that the ending must honor, verified as a fact rather than felt as a theme. Forward validation has no notion of an obligation opened early that must be discharged late.

### 4.3 The scenario that makes the difference concrete

A civilization is seeded at tick zero with a founding-method capsule. The story requires that the capsule was produced and deposited by a later expedition within the same run. This is a stable bootstrap loop: seed, then discovery, then development, then the expedition, then the deposit that becomes the seed.

**With forward validation only.** At tick zero the capsule is present in the initial state and validates as a legal object. The run proceeds. At the end, an expedition may or may not produce the capsule. Forward validation never checks that it did, because the capsule was already legal at the start. You can therefore ship a world in which the founding method exists but was produced by nothing in the run. The loop is open and nothing detects it. Worse, generative agents can drift the late game so the expedition never happens, and your world is now internally incoherent in exactly the way that breaks immersion the moment a player traces the lore. The prophecy silently fails and no gate fires.

**With reciprocal closure.** The capsule deposited at the beginning opens an unresolved return obligation. The candidate history is accepted only if forward execution reaches an ending that derives the required return (the produced capsule) and that return satisfies the beginning contract (it matches the seed). If the later expedition never produces it, the history fails closure. You get a machine-checkable guarantee that the loop closed: that the destiny was earned rather than asserted, that the prophecy paid off, that the founding artifact genuinely came from within the run.

There is a second guarantee stacked on this, and builders who care about lore integrity will want it. The contract includes a dependence check: removing the returned beginning fact must break the derivation of the validated return. That is the difference between "the artifact happens to be present" and "the artifact is load-bearingly produced by the later event." Delivery provenance is not correctness, though; a circularly sourced blueprint can circulate consistently while describing a device that fails under the world's mechanics, so the contract checks the return's validity separately from its provenance.

### 4.4 When it is worth adopting, and when it is not

Adopt reciprocal closure when your world has at least one committed end-to-beginning constraint that must hold under autonomous agents:

- Authored destiny or prophecy that must remain consistent while generative agents act freely.
- Bootstrap or stable-time-loop narratives that must actually close rather than merely gesture at a loop.
- Persistent worlds where a committed future constraint must constrain the past and you need a guarantee rather than author vigilance.
- Multi-branch worlds that must reconcile into one authoritative history without hiding an obligation a branch still owes (the Omega extension, Section 6.3).

Do not adopt it when:

- Your only requirement is "do not corrupt accepted history." Event sourcing plus validation is sufficient and simpler.
- Your world has no committed end-to-beginning constraint. The reciprocal machinery is then pure overhead.
- Your loop is thematic flavor, an ouroboros in the logo, not a mechanical constraint you need enforced. A symbol does not need a validator.

### 4.5 The comparison, at a glance

| Question | Forward validation (event sourcing plus gate) | Reciprocal closure (Animus cycle) |
|---|---|---|
| Was each transition legal? | Yes | Yes (inherits it) |
| Is accepted history reconstructable from the log? | Yes | Yes |
| Did the ending satisfy a committed beginning constraint? | No representation of this | Yes, as a pass or fail on the whole run |
| Did a bootstrap loop actually close within the run? | Cannot check | Yes, via the ending-derived return |
| Is the closing artifact load-bearingly produced, not just present? | Cannot check | Yes, via the ablation dependence check |
| Do branches reconcile without hiding an owed obligation? | Out of scope | Yes, in the Omega extension |
| Cost when you have no end-to-beginning constraint | None | Overhead with no payoff |

### 4.6 The costs you are signing up for

Reciprocal closure is a stronger requirement than forward validation, and Section 6 states its costs precisely rather than hiding them. In brief: a valid route home does not guarantee agents take it, so a liveness guarantee needs an added assumption such as a deadline or a progress measure (6.2); present agreement between two states does not by itself preserve their future consequences, so your protected projection must include the futures you care about (6.3); and a finite archive cannot retain arbitrary distinctions indefinitely, so you must declare what is retained and what is allowed to be lost (6.4). These are the adoption costs. Pay them only when the guarantee in 4.2 is one you actually need.

## 5. The world as buildable design patterns

For this audience the world-design material is not vision, it is a pattern library. Each motif below is a mechanic you can implement, paired with the operation it maps to and the boundary that keeps it honest. None is an empirical result, and none asserts anything about reality; the single wall from Section 2 holds throughout.

### 5.1 Differentiation: one foundation, many lives

The world begins with a shared generative foundation and differentiates participation into characters. Each character gets a bounded observation interface, a local memory, permissions, capabilities, and a lineage identifier. Birth, death, or reincarnation in the fiction maps to explicit creation, suspension, retirement, or re-instantiation of a role, and such operations need not erase historical consequences. A builder reads this as: scoped contexts over a shared model, with lineage records that survive role changes.

Three records stay distinct: accepted world history, declared continuity inheritance, and currently accessible character memory. Intentional forgetting restricts the third without corrupting the first. This is what makes myths, honest mistakes, and rediscovery possible without treating accidental implementation drift as meaningful plot. A builder wants exactly this separation so a character can be wrong, or can forget, without the ledger becoming wrong.

### 5.2 Folklore as discoverable effects of declared mechanics

The creative purpose is a world that generates legends about its own hidden structure. An ouroboros can encode a validated return route. An Atlantis-like settlement can be reachable only through the temporal hub. A traveler can carry knowledge whose source is a later episode. Mandela-style discrepancies in recollection can arise from ordinary error, misleading testimony, or a specifically permitted record inherited from an alternative history. These are alternative in-world causes, not claims about real folklore. The engineering discipline is that provenance must distinguish these cases, and the system should not invent a hidden cause only after a player asks for an explanation.

**Table 1. Creative motifs and their proposed operational counterparts. None is an empirical result.**

| Motif | Proposed operation | Required boundary |
|---|---|---|
| One observer, many roles | Shared model with separately scoped contexts and permissions | Shared infrastructure does not establish a shared consciousness |
| Reincarnation | New role bound to a declared lineage and inheritance record | Earlier obligations cannot disappear without an authorized transition |
| Remembering | Permitted retrieval or a limited perspective change | No access to hidden validation outcomes or unrestricted global state |
| Ouroboros / breadcrumbs | Artifacts with traceable origins that refer to reciprocal dependencies | Symbolic similarity alone is not provenance |
| Lighthouse and temporal hub | Typed routing into a reconstructed candidate chronology | No editing of accepted history or undeclared restoration of discarded branches |
| Compassion and unity | Actions that enable coordination or resolve protected conflicts | Cooperation, reconvergence, and closure remain separate results |
| Closing-world contraction | A scenario changes population or resource availability | Decline is neither a success metric nor a universal requirement |

### 5.3 The Lighthouse and a local seeding cycle (a worked bootstrap pattern)

The Lighthouse is a landmark where inhabitants gather, preserve route knowledge, and coordinate the contributions needed for passage. Operationally it is an in-world gateway to a permitted temporal hub; its appearance is optional, and another interface could expose the same contract. The hub is not an administrator console and does not suspend the world's laws. A route identifies an origin, destination, payload, eligibility rule, and required evidence. A destination before the first native inhabitants is not before the simulator itself exists, and any arriving traveler remains a represented participant.

This is the pattern from Section 4.3 stated as a reusable mechanic. A candidate containing the early capsule must execute into a future that actually supplies its permitted return; failure to develop the required capacity invalidates that candidate. The fiction does not require a first unassisted civilization outside the loop, because the complete candidate is evaluated as one constrained history. An early deposit opens an unresolved return requirement until its later source is established, and the contents also require a separate validity check, since delivery provenance is not technological correctness. A transfer from an advanced branch to another branch, by contrast, is not a cycle unless a reciprocal dependency is also specified, and several locally closing routes must be checked jointly when they share resources.

### 5.4 Coordination, and the inward phase

The larger world gives characters reasons to coordinate: preserve a loved one's work, protect a community, fulfill an inherited promise, establish a future no participant can reach alone. Cooperation may resolve a debt or authorize a transfer, making previously incompatible continuations eligible for reconciliation. A closing-world scenario could include population contraction, but such conditions change the stakes rather than prove readiness for return, and conflict might destroy required knowledge rather than produce unity. Refusal must remain representable, and an affective description cannot substitute for a qualifying event: the action model distinguishes freely chosen cooperation from an imposed outcome. This is a design constraint, not a claim that software measures genuine love. Meditation or remembrance maps to limited retrieval of permitted continuity records; a change of perspective does not reveal evaluator labels, expected outputs, or the private ledger, and no population threshold unlocks the hub by itself.

### 5.5 Return, custodianship, and renewed expansion

Inhabitants who reach the hub need not become a single mind. They may keep distinct memories and roles while sharing a route network. A unified authoritative record is an operation on the representation, not proof that personalities merged. The integrated system may preserve a selected inheritance and begin another declared episode, stating which distinctions survive, which become inaccessible to characters, and which are discarded. An archive of incompatible alternatives is not one lived history; alternatives stay labeled as such, hidden executable copies of discarded branches are not permitted, and renewed branching requires a declared new origin rather than quiet restoration [4]. A continuous identity can accumulate experience without returning to an identical information state, and exact repetition of the complete state cannot simultaneously retain arbitrary additional information, so the archive must name its retention policy rather than use the cycle metaphor as a substitute for storage accounting.

## 6. The bounded computational contract

The following restates the published design at an abstract level. It is not a replacement specification, and finiteness applies to the reported evaluation domain, not to a claim that all conceivable stories can be exhaustively examined.

### 6.1 State, execution, and observer interfaces

Let D contain a frozen finite candidate domain, transition rules, horizon T, beginning and ending predicates, permitted return schema, retention rules, observer interfaces, and failure conditions. Let S_t be world state, L_t its accepted event record, and m_{i,t} the local memory of character i. Its observation and action proposal are:

o_{i,t} = O_i(S_t, L_t)   (1)

a_{i,t} ~ pi_theta_t( . | m_{i,t}, o_{i,t} )   (2)

A host transition function evaluates proposals and updates state only through permitted events. An observation function returns a declared local view, not the global clock, expected endpoint, candidate-search trace, or private validator record. An agent-generated receipt is not authoritative merely because it labels itself successful. For reproducible analysis, let xi denote declared external inputs and recorded nondeterministic choices, including applicable model outputs. A deterministic executor yields H = F_D(x; xi) from candidate beginning x. Replaying recorded model outputs checks host reconstruction of that episode; asking a live model to reproduce the outputs is a different experiment, and both require separate outcome labels.

### 6.2 Reciprocal return and validation

Let G_D(H) derive a typed return r from executed history H. Let K_D(r) reconstruct a candidate beginning, using only the fixed scaffold and retained information explicitly allowed by D. A useful abstract sequence is:

H = F_D(x; xi),   r = G_D(H),   x' = K_D(r),   H' = F_D(x'; xi)   (3)

Any operator can fail with a bottom value. Let B_D and E_D be beginning and ending predicates, J_D the declared endpoint-agreement relation, and V_D the remaining sealed-history checks. A compact closure condition is:

Close_D(x)  iff  B_D(x) and E_D(H) and B_D(x') and E_D(H') and J_D( r, G_D(H') ) and V_D(H, H', r)   (4)

with all terms defined. Here V_D includes writer eligibility, return derivation, append-identity and duplicate-write checks, replay, retention compliance, and the specified ablation test. Removing the returned beginning fact must defeat the required dependence under the fixture's declared intervention; such an ablation is a conditional diagnostic, not a universal causal theory. The contract is frozen before outcomes are inspected. Merely setting x' to a preferred save, attaching an expected return, or editing B_D to accommodate a result does not satisfy it. Full-state equality x' = x is optional; the declared predicates determine what must agree, and lossy and lossless reconstruction are distinct modes. A separate validation pass is not automatically an independently implemented validator or an external replication.

The eight named validation predicates are: BEGINNING_HELD, FORWARD_REACHES_END, RETURN_DERIVED_FROM_END, WRITER_ELIGIBLE, ENDPOINT_AGREES, NO_DUPLICATE_WRITES, REPLAY_DETERMINISTIC, RETENTION_RULE_HELD. Overall closure passes only when a candidate survives the full sealed-history validation.

### 6.3 Branches and protected equivalence

For represented branch states z_1 through z_k, let P_D be a declared projection over protected identities, obligations, causal dependencies, ownership, permissions, and observations. Eligibility may require:

z_i equiv_D z_j  iff  P_D(z_i) = P_D(z_j)   (5)

A reconciliation operator must report inputs, ancestry, conflicts, retained fields, discarded distinctions, and its canonical output. The one-history condition must hold before the final reciprocal return is accepted. All input branches require an ancestry path or a rejection justified by the predeclared rule; timeout, arbitrary deletion, or retaining an undeclared executable trunk does not count [4]. Narrative similarity is insufficient: two characters holding apparently identical tools differ consequentially when one owns the tool and the other has an unresolved duty to return it. Actions may resolve that present duty, but they do not erase every historical distinction, and whether consolidation is allowed depends on the future questions the contract promises to preserve.

## 7. Analytical boundaries (the adoption costs, stated as deductions)

The observations below are elementary deductions for the stated model, not claims of mathematical novelty. For a builder they are the fine print: the conditions under which the guarantee in Section 4 needs extra assumptions to hold.

**7.1 Finite closure is decidable under terminating checks.** If the declared candidate set is finite and each execution and predicate evaluation terminates, existence and uniqueness of a closing candidate can be decided by exhaustive enumeration: evaluate Equation (4) for each candidate and count passes, giving NONE, UNIQUE, or MULTIPLE. This gives no useful general complexity bound, and it does not establish that inhabitants discover a closing history autonomously. If external model calls can hang or execution is unbounded, you must add explicit timeout and failure rules. A small constructed example: if a return value is p in {0, 1, 2} and declared execution derives f(p) = (2 - p) mod 3, then exact return agreement f(p) = p holds only for p = 1. This is an algebraic illustration, not an executed Animus implementation, and finding the value says nothing about how an autonomous population would reach it.

**7.2 A route home does not guarantee return (safety is not liveness).** In a finite graph with states u and v, where from u an agent may wait at u or enter terminal state v, a route to v always exists, but an agent that always waits never reaches it. Existence of a valid return path is therefore not a liveness guarantee. If your world needs agents to actually close the loop, you must add an assumption: a finite deadline, a well-founded progress measure, fairness, or restrictions on permitted choices. A validator that refuses every invalid merge preserves safety indefinitely while the world never reconverges, so reporting successful rejection alone would hide the failure to complete the intended cycle. State which assumption you use instead of treating breadcrumbs as a guarantee.

**7.3 Present agreement need not preserve future consequences.** If two branch states share a projected open-promise field but have different deadlines omitted from the projection, the same later action may fulfill one promise and violate the other, so present equality under Equation (5) is inadequate for the promised future behavior. A sufficient condition is stronger than a current-state comparison: writing A(z) for available actions, F(z, a) for a deterministic transition, and O(z) for the protected observation, assume that whenever P(z_1) = P(z_2), we have A(z_1) = A(z_2), O(z_1) = O(z_2), and P(F(z_1, a)) = P(F(z_2, a)) for every a in A(z_1). Under this assumption, equal projected states produce equal protected observations and projected states under every common finite permitted action sequence (by induction on the sequence). This concerns matched action sequences, not independently sampled model decisions; a stochastic-policy version needs additional conditions, and a merge operator must preserve the equivalence class rather than change the protected state. The practical lesson: your protected projection must include the futures you actually care about.

**7.4 A finite archive cannot retain arbitrary distinctions.** A fixed-width B-bit representation has at most 2^B distinct values, so distinguishing N answer-distinct histories requires B at least the ceiling of log base 2 of N; otherwise two answer-distinct histories share a representation. Cycles can organize reuse but cannot provide unbounded exact memory at fixed capacity. Your choices are to restrict the task, identify genuinely equivalent histories, allow growth, use external storage, or explicitly permit loss, and all retained copies and retrieval infrastructure belong in the resource accounting.

## 8. Foundational research track (reported for completeness)

This section belongs to the project's foundational science arm, not to the builder-facing contribution. It is summarized from the project's published record, without reanalysis or independent replication. The four studies address different questions and cannot be combined into a single measure of architectural success. A builder pricing adoption should weight the runnable artifact in Section 10 far more heavily than these results; they are included so the record is complete and so no reader mistakes them for support the contract does not yet have.

**Table 2. Reported component-study outcomes. No new result is reported here. Source: the public evidence summary [9].**

| Study | Published outcome | Interpretation boundary |
|---|---|---|
| Test 01 | Reset-persistence method validation and threshold calibration; future threshold 0.200407323 nats | No independent confirmatory coupling effect |
| Test 02 | Exhaustive enumeration of 66,064 binary relations on 2-4 states at periods 1-8 | Exact only in the stated finite domain; not evidence of scalable narrative closure |
| Test 03 | Carried-state comparison unsupported: Q < 0 in 0/20 reserved bundles; mean Q = 0.6826707925423762 | No predictive advantage demonstrated for the tested recurrent model under that design |
| Test 04 | Revision 1 aborted. Revision 2: 60/60 replay arms passed through tick 4096 | Complete-checkpoint replay in one deterministic implementation, not lossy continuity or resource savings |

**Reported measures and limits.** Test 01's stated contrast is P_rel = I(S_end; S_seed) - sum over i of I(s_{i,end}; s_{i,seed}), where I is mutual information, S the joint state, and s_i an agentwise component; the source reads this as a joint-minus-agentwise contrast, not a unique decomposition of purely relational information. Threshold calibration uses the complete 1,024-assignment paired sign-flip distribution over ten matched training pairs, with initialization, training exposure, architecture, and compute budget matched but trained weights not identical; the calibrated threshold is for a future independent comparison, and statistical-complexity matching remains pending. Test 02 counts rooted closed walks with period dividing T as W_T = trace(M^T), uses Mobius inversion for the count P_T of minimal period exactly T, and sets C_T = P_T / T to remove rotations; C_T = 1 classifies one primitive period-T cycle. This is a combinatorial property of the relation and does not establish writer eligibility, an ending-derived return, or that an agent reaches the cycle. Test 03 compares a carried-state RNN against an approximately parameter-matched fixed-window MLP, with endpoint Q the mean RNN-minus-window cross-entropy difference over horizons 13-16 in level-L1 persistent-memory worlds; positive Q favors the window comparison. The public record reports one reserved execution over seeds 12000-12019 with Q < 0 in 0/20 bundles and mean Q = 0.6826707925423762, so primary support failed; matching parameter counts does not match stored context or computation. Test 04 Revision 2 uses 20 reserved seeds, 43000-43019, at checkpoints 37, 113, and 251, giving 60 seed-by-checkpoint arms, with immediate complete-checkpoint equality, canonical idempotence, and future semantic-state and observer-output agreement through tick 4096, and zero reported mismatches; Revision 1 remains aborted and contributes no result, and Revision 2 was prespecified under a frozen protocol, not externally preregistered before execution [16].

**What these do and do not support.** Method validation can make a later measurement interpretable without establishing the target effect. Bounded enumeration can characterize a finite relation without demonstrating inhabited-world coherence. An unsupported recurrent-model result argues against assuming recurrence alone guarantees a benefit, without testing every reciprocal architecture. Exact replay provides an implementation capability without demonstrating that discarding information is safe. Built-in passing examples satisfy rules chosen for them and are not independent validation of the broader hypothesis; the public record reports no valid end-to-end (Test 05) result [5].

## 9. Evaluation agenda for the proposed application

**Start from the existing bounded benchmark.** The public Persistent Multi-Agent Closure Benchmark proposes six agents, a shared authoritative ledger, distinct observations, a midpoint model replacement, and explicit protected state [8]. It is a development protocol, not a frozen confirmatory experiment and not an end-to-end test, and its local deterministic adapter is not evidence of a live external-provider replacement. Arm A uses ordinary forward execution, checkpoints, and ledger validation. Arm B is an enhanced, compute-matched forward baseline. Arm C adds the permitted return, candidate reconstruction, forward replay, and closing comparisons. Relevant information, seeds, inputs, schedules, and budgets must match. The key comparison is incremental value: ordinary validation must receive the identities, receipts, commitments, and provenance it needs, or a benefit from adding basic evidence checking could be misattributed to reciprocal closure. This is exactly the Section 4 question posed as an experiment: does the reciprocal machinery beat a strong forward baseline on worlds with committed end-to-beginning constraints.

**Outcomes and independent labels.** Closure is a mechanism diagnostic for Arm C, not itself a failure-detection score or a task-success criterion. Invalid histories require labels constructed independently of the tested validators, and valid histories must be included to measure false rejection. Useful fault families include an unsupported transfer, altered identity, lost obligation, missing return, ineligible writer, forbidden observation, and a reconstruction that changes a protected future consequence; a benign change outside the protected projection should remain admissible. Development and reserved faults must be separated before outcomes are examined. An offline study gives every validator the same recorded candidate episode to isolate detection; an online study can let validation block or repair actions, but intervention then changes trajectories and must separately evaluate completion, adverse side effects, and cost.

**A separate reconvergence study.** The Omega extension requires an additional study in which represented branches are actually created and then reconciled; an always-single history cannot receive credit for branch reduction. Negative controls should include hidden full-state copies, transitions that inspect preferred outcomes, arbitrary deletion, and protected conflicts with no permitted resolution [4]. Measure how many distinctions survive, which obligations were resolved, and whether the same protected future behavior is preserved; increased agreement in dialogue is not a substitute.

**Cost and replication.** Storage accounting must include active state, event records, checkpoints, indexes, caches, branch provenance, return packages, and any retained model inputs and outputs. Compute accounting must include candidate search, failed attempts, branch execution, reconstruction, and validation. Reducing the number of visible characters or live branches is not evidence of lower total cost. The public protocol leaves the minimum meaningful effect, significance threshold, sample size, power, and cost ceiling unresolved [8]; this draft supplies no invented values for those fields. Fresh-process replay, a separately implemented checker, and external replication address different failure modes and should all be distinguished.

## 10. The runnable artifact and how to adopt

For this audience the trustworthy evidence is not the science track, it is code that does what the spec says. The published package provides a machine-checkable contract you can run and inspect, and adoption should begin there rather than with the propositions.

**What exists to run.** The package includes the Animus Cycle specification (version 1.0), a claims-boundary document, registration metadata, a simulator specification, a reference engine with types, a candidate generator, and tests, together with frozen reference fixtures: a clean PASS, a mutate-endpoint FAILURE, and a separately versioned ORIGIN_CUT branching example. Checksums are published for the evidence package. These fixtures are the fastest way to see the contract reject something: run the mutate-endpoint fixture and watch closure fail because the ending-derived return no longer satisfies the beginning contract, then run the clean fixture and watch it pass through the full sealed-history validation.

**How it sits on your stack.** The contract is designed to sit above a state-and-event layer, not to replace it. If you already run event sourcing, the accepted event record L_t is your log, the transition function is your validation gate, and reciprocal closure adds three things on top: the return derivation G_D, the beginning reconstruction K_D, and the closing comparison of Equation (4). If you run a memory-tiered agent loop in the style of MemGPT [2] or a generative-agent architecture [1], the per-character local memory m_{i,t} and observation interface O_i map onto your existing context and retrieval scoping, and the contract governs only which whole runs are accepted, not how any single step is generated. The reciprocal check runs at run boundaries, so its cost is paid per candidate history rather than per token.

**What to measure before you trust it in production.** Latency per validated transition and per closing check, storage per run including return packages and branch provenance, and the false-rejection rate on valid histories. The evaluation agenda in Section 9 is the disciplined version of this; the minimum viable version is running Arm A against Arm C on your own world and asking whether closure catches a broken bootstrap loop that your forward gate lets through. If it does not catch anything your gate misses, your world does not have the constraints this pattern is for, and Section 4.4 told you not to adopt it.

## 11. Limitations and ethical boundaries

**Internal consistency is not empirical truth.** A self-consistent cycle can preserve false assumptions. The system must distinguish measured inputs, simulation rules, generated possibilities, and agent beliefs. For a fictional world, rules can be stipulated; for any representation of reality, observations must be allowed to falsify assumptions, and a real-world mismatch cannot be rewritten to protect a desired ending. Nothing here establishes consciousness, subjective continuity, physical retrocausality, a real Atlantis, or a measurable emotional substrate. Folklore and speculative motifs are design inspiration, not evidence for the contract, and the Lighthouse is an illustrative interface rather than a studied installation.

**Freedom, immersion, and failure.** A guaranteed return may require restricting choices, and those restrictions should be disclosed in the model even if hidden from fictional inhabitants. A system that guarantees closure by rejecting almost all meaningful variation may fail its interactive purpose, while a rich world that sometimes does not close can still be coherent, but it has not demonstrated guaranteed convergence. Representing population decline, death, or conflict is not a recommendation for real-world policy or a reason to optimize for suffering; those scenarios are optional and unnecessary for the minimum contract. Simulated refusal and disagreement should remain identifiable rather than rewritten as consent.

**People, privacy, and interpretive risk.** If later work uses human participants, it needs appropriate review, consent, and disclosure. A world built around secret messages and hidden causal structure should not encourage players to treat real coincidences or personal distress as evidence that they occupy a simulated mission, and interfaces should make the fictional boundary clear. Memory archives can contain personal or licensed information, so source permissions, retention limits, access control, and deletion requirements must precede deployment; a claim of immutable history does not authorize indefinite retention of sensitive data.

## 12. Conclusion

Animus Omega connects a world-design question with a precise computational one. The world-design question asks whether distinct lives, limited memories, legends, and temporal gateways can arise from coherent rules that inhabitants can investigate. The computational question asks whether an executed ending supplies a valid return under independently declared requirements, and whether represented branches can reconcile without losing the protected consequences of their histories.

For builders, the contribution is scoped and honest: reciprocal closure is not a general upgrade to persistent-world infrastructure, and for the common case of "do not corrupt accepted history" you should keep using event sourcing and validation. Its value is a machine-checkable guarantee for the specific class of world that carries committed end-to-beginning constraints, the destinies, prophecies, and bootstrap loops that forward validation cannot enforce. The elementary obstacles are real and priced in: a route need not be followed, a present match need not preserve the future, and finite storage cannot retain arbitrary distinctions. The next evidentiary step is a bounded comparison against competent conventional validation, followed separately by reconvergence studies where meaningful alternatives are genuinely executed. The intended outcome is neither a proof that reality is simulated nor a system that merely repeats. It is a testable account of how a generated world can keep developing while remaining answerable to what it has committed to become.

## Provenance, assistance, and author review

This is an AI-assisted author-review draft. Generative AI tools were used substantially for source-assisted synthesis, organization, prose drafting, proposed mathematical exposition, and this builder-facing reshaping. This disclosure describes drafting assistance, not an AI-authored independent replication, and no generative AI tool is listed as an author. The proposed human authors must verify all content, references, contributions, and submission declarations before approval. The author names are drawn provisionally from the joint project specification; their inclusion is not confirmation of authorship or consent. That specification also lists Kelly Hackett as providing financial and non-financial support, and the scope of that disclosure to this paper requires confirmation. Results were summarized from the public record; the original experiments and archive verification were not rerun, and this document neither amends a frozen protocol nor authorizes a reserved experiment.

## Appendix A. Source snapshot and evidence boundaries

Repository documents are cited at the following fixed commit rather than a moving branch: 399025929d072cf73259795d3d662c89a8828c8c. The repository's dated evidence package is named exact-evidence-tests-01-04-2026-09-10.zip, and its README reports SHA-256 28caf6b0bdd02f4c9441b01bd528ae7dcb70408e8751fff4ca09fcc52044dfd1. This checksum is a reported identifier, not a claim of fresh local verification. Before submission, the authors should verify the detailed results against the canonical reports and preserve the exact source bytes used. A fixed identifier supports traceability but does not validate a result. The illustrative setting in this paper is a design proposal, not an additional dataset or empirical corroboration.

## References

*All specific citations require verification against the real sources before any credentialed reader sees them. The two most load-bearing recent ones for this audience are [1] and [2]; the recent benchmark and memory citations [3, 10] should be confirmed for exact titles, venues, and identifiers.*

[1] Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., and Bernstein, M. S. Generative Agents: Interactive Simulacra of Human Behavior. arXiv:2304.03442v2, 2023.

[2] Packer, C., Wooders, S., Lin, K., Fang, V., Patil, S. G., Stoica, I., and Gonzalez, J. E. MemGPT: Towards LLMs as Operating Systems. arXiv:2310.08560, 2023-2024.

[3] Wu, D., Wang, H., Yu, W., Zhang, Y., Chang, K.-W., and Yu, D. LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory. arXiv:2410.10813v2, 2025.

[4] Hackett, C. and Hackett, K. The Animus Cycle. Proposed design specification, version 1.0, 11 September 2026. Repository snapshot at commit 3990259.

[5] Animus Omega project. Animus Omega: Vision and Proposed Applications. Vision statement, 14 September 2026.

[6] Hackett, C. Closed-Knot Stories on One Wheel: A Narrative Use Case for the Animus Cycle. Use-case note, 13 September 2026.

[7] Animus Omega project. Claims Not Made by the Animus-Cycle Specification. Companion claims boundary, version 1.0, 11 September 2026.

[8] Hackett, C. and Hackett, K. Persistent Multi-Agent Closure Benchmark. Development protocol, 13 September 2026.

[9] Animus Omega project. Persistence and Primitive Closure in Finite Computational Systems. Public structured evidence summary for Tests 01-04, 2026.

[10] Barres, V., Dong, H., Ray, S., Si, X., and Narasimhan, K. tau-squared-Bench: Evaluating Conversational Agents in a Dual-Control Environment. arXiv:2506.07982, 2025.

[11] Riedl, M. O. and Young, R. M. Narrative Planning: Balancing Plot and Character. Journal of Artificial Intelligence Research, 39:217-268, 2010.

[12] Grimm, V. et al. The ODD Protocol for Describing Agent-Based and Other Simulation Models: A Second Update. Journal of Artificial Societies and Social Simulation, 23(2):7, 2020.

[13] Fowler, M. Event Sourcing. Technical article, 2005.

[14] Alloy project. About Alloy. Project documentation.

[15] Chu, C., Zhmoginov, A., and Sandler, M. CycleGAN, a Master of Steganography. arXiv:1712.02950, 2017.

[16] Animus Omega project. Test 04 terminology correction. Correction dated 10 September 2026.
