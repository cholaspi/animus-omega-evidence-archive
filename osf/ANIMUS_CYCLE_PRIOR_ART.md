# Relationship to neighboring techniques

**Document status:** systematic-search protocol, preserved screening record,
and companion orientation to the proposed design specification, version 1.2,
2026-09-12
**Authors:** Cholee Hackett; Kelly Hackett
**Document license:** Creative Commons Attribution 4.0 International

## Purpose, method, and limit

The Animus cycle combines mechanisms related to checkpointing, event sourcing,
deterministic replay, fixed-point constraints, boundary conditions, cyclic
reasoning, and state reconstruction. The specification claims no priority over
those mechanisms.

**Animus Omega Cycle** is the proposed public name for the optional stronger
branch-reconvergence version of that contract. Its technical subtype name is
**Animus Omega branch-reconvergence cycle**. This naming does not establish
scientific or technical novelty, legal exclusivity, completed Test 05 evidence,
or absence from prior systems.

This document records a cross-disciplinary systematic search performed on
2026-09-12. The exact fixed rerun matrix and every returned title/snippet
decision are preserved in `ANIMUS_CYCLE_PRIOR_ART_SEARCH_LOG.md`. A rerun can
reproduce the submitted queries, not the ranking or coverage of changing public
indexes. This record is not proof that no equivalent system exists.

The comparison uses the following rule throughout:

> A cited technique does not entail the complete Animus-cycle contract merely
> because it can be used to implement one of its requirements. Conversely, a
> requirement is not absent from a field merely because it is not entailed by a
> standard definition.

The proposed contribution is therefore described only as a named design
contract with separated validation outcomes. No scientific or technical
novelty is asserted.

## Search protocol frozen before searching

The fixed rerun matrix was defined before its nine searches were submitted.
This section and the execution log transcribe that matrix exactly.

## Source-supported comparison

| Technique | What the checked source supports | Relationship to the Animus-cycle contract | What is not established |
|---|---|---|---|
| Fixed-point theory | Banach proves a unique fixed point for contractions on complete metric spaces. Tarski proves fixed-point results for monotone maps on complete lattices. | A finite Animus fixture may be formulated as a fixed-point or constraint problem; `NONE`, `UNIQUE`, and `MULTIPLE` count valid solutions under that fixture. | Neither theorem applies to every Animus fixture without its stated assumptions. Fixed-point theory does not forbid endpoint-derived returns, validation predicates, or separated reports. |
| Boundary-value and shooting methods | Standard shooting converts a boundary-value problem into initial-value trials and adjusts guessed initial data using endpoint residuals. | This resembles candidate execution followed by endpoint testing. | A standard boundary-value problem does not by itself make the endpoint supply a condition required at the beginning. Such a return map can nevertheless be added to a formulation. |
| Cyclic proofs | Cyclic proof systems use finite proof graphs with back-links and a global trace or progress condition for soundness. | They are a useful comparison for disciplined circular structure and global validation conditions. | A proof back-link is not a temporal ending-derived state return. The cited formalism does not make provenance, replay, information loss, or continuity its standard outcome dimensions, but this check does not prove those ideas absent from all cyclic-proof work. |
| Event sourcing | Fowler defines application state as derivable by processing a sequence of events and describes replay and alternative projections. | Event logs and replay can supply reconstruction and provenance mechanisms for an Animus implementation. | Event sourcing alone does not entail reciprocal boundary closure or a frozen beginning contract. Event-sourced applications may add such rules, so no universal absence claim follows. |
| Distributed snapshot and rollback recovery | Chandy and Lamport define a consistent distributed snapshot. Elnozahy et al. survey checkpoint-based rollback-recovery protocols in message-passing systems. | Checkpoints, snapshots, and recovery protocols can preserve or reconstruct state and can serve as controls or implementation components. | “Checkpoint/restore returns a saved copy and trusts it” is not supported; recovery systems may include consistency checks, logging, replay, and validation. Basic restoration alone does not establish reciprocal closure. |
| Deterministic replay | ReVirt records sufficient execution information, together with a checkpoint, to replay a virtual machine for intrusion analysis. | Deterministic replay supports reproducibility and corresponds to the contract's `REPLAY_DETERMINISTIC` predicate. | Replay alone does not establish the complete closure contract, but it can be composed with boundary search and independent validation. |

## Detailed qualifications

### Fixed points and self-consistency

An Animus cycle can be represented by a mapping or relation whose accepted
histories satisfy a consistency condition. Calling this a fixed-point problem
does not select a theorem automatically. Banach's result requires a contraction
on a complete metric space [1]; Tarski's result concerns monotone mappings on
complete lattices [2]. The finite fixture's valid-history count is a solution
count, not a new fixed-point classification.

The Animus contract additionally *requires* an executed ending, an
ending-derived return, named validation predicates, and separate reports for
closure, uniqueness, information loss, and continuity. These are requirements
of this specification. Fixed-point formulations can encode comparable
procedures, so the comparison supports no claim that they are absent from
fixed-point work.

The closed-timelike-curve paper by Friedman et al. studies consistency of the
Cauchy problem in spacetimes containing closed timelike curves [3]. It is
relevant as neighboring self-consistency work, not as evidence for the Animus
contract or for a novelty gap.

### Boundary-value and shooting methods

Shooting methods select or adjust initial values, integrate forward, and compare
the result with terminal boundary conditions [4]. That procedural resemblance
is close to candidate enumeration and endpoint checking. Standard boundary
conditions are prescribed constraints; they do not intrinsically say that an
executed endpoint authors or supplies an initial condition. A model can add an
endpoint-to-initial map, provenance rules, and separate reports. The distinction
is therefore “not entailed by the standard method,” not “absent.”

### Cyclic proofs

Brotherston and Simpson describe cyclic proof systems based on finite,
possibly cyclic derivation graphs subject to a global trace condition [5].
Their disciplined circularity is structurally adjacent to this project.
However, a proof-theoretic back-link and soundness condition are not the same
objects as a temporal state return and a sealed-history validator. This is a
domain distinction, not evidence that the complete conjunction is novel.

### Event sourcing

Fowler's canonical practitioner description says that application state can be
determined by a sequence of events and rebuilt by replay [6]. This supports the
claims about event-log reconstruction and replay. It does not support the
categorical claim that event sourcing is always “linear” in a way that excludes
cycles, workflows, snapshots, validation, or reciprocal constraints. Event
sourcing alone does not entail the Animus contract; a particular event-sourced
system could implement it.

CQRS is not required for this comparison and is not treated as part of the
definition of event sourcing. The unverified “CQRS Documents” item from the
draft is omitted because a stable author-controlled source-of-record was not
confirmed.

### Checkpoint, snapshot, and rollback recovery

Chandy and Lamport establish a method for recording a consistent global state
of a distributed system [7]. Elnozahy et al. classify and survey rollback
recovery based on checkpoints and message logging [8]. These sources support
checkpointing and recovery as substantial consistency and reconstruction
techniques, not as a “known cheat” that merely trusts a saved copy.

An exact saved-state return can be used as a control in an Animus fixture.
Restoration alone does not establish ending-derived reciprocal closure; the
fixture must still satisfy its derivation, endpoint, provenance, and validation
requirements.

### Deterministic replay

ReVirt combines a checkpoint with logged nondeterministic events so an earlier
execution can be replayed [9]. This supports deterministic replay as a
reproducibility and analysis mechanism. The Animus contract treats replay as
one named predicate, not as a competing closure theory. Replay can also be part
of a system that adds reciprocal boundary constraints, so no absence claim is
made.

## Information loss remains optional

Information loss is not required for an Animus cycle. Exact recurrence,
complete checkpoint return, lossless reconstruction, and lossy reconstruction
are distinct candidate architectures. Continuity through information loss is a
separate, stronger hypothesis and must not be inferred from closure.


## Earlier review outcome

On 2026-09-12, this comparison received two independent technical reviews: one
from a formal-methods perspective and one from a distributed-systems
perspective. Both reviews rejected the draft's categorical matrix and its claim
that no prior technique holds the five-property conjunction. The principal
reasons were:

- the search was not exhaustive;
- several table marks confused “not required by a standard definition” with
  “absent from every implementation”;
- cyclic proofs and boundary-value methods were assigned reciprocal-boundary
  properties they do not intrinsically have;
- event sourcing and checkpoint recovery were described too narrowly; and
- fixed-point formulations can encode additional return and validation rules.

This revision incorporates those corrections and adds the systematic search
record above. The earlier reviews were technical screening, not external peer
review. The systematic search found no complete match but still cannot prove
absence. Qualified external review remains required before considering any
novelty language. The approved statement is:

> We propose the name and specification for this particular conjunction. A
> documented search found close partial precedents and no complete match, but
> we have not established that the conjunction is absent from prior systems.

## Verified references

1. Banach, S. (1922). “Sur les opérations dans les ensembles abstraits et leur
   application aux équations intégrales.” *Fundamenta Mathematicae*, 3(1),
   133–181. https://doi.org/10.4064/fm-3-1-133-181
2. Tarski, A. (1955). “A lattice-theoretical fixpoint theorem and its
   applications.” *Pacific Journal of Mathematics*, 5(2), 285–309.
   https://doi.org/10.2140/pjm.1955.5.285
3. Friedman, J. L., Morris, M. S., Novikov, I. D., Echeverria, F., Klinkhammer,
   G., Thorne, K. S., & Yurtsever, U. (1990). “Cauchy problem in spacetimes with
   closed timelike curves.” *Physical Review D*, 42(6), 1915–1930.
   https://doi.org/10.1103/PhysRevD.42.1915
4. Stoer, J., & Bulirsch, R. (2002). *Introduction to Numerical Analysis* (3rd
   ed.). Springer. https://doi.org/10.1007/978-0-387-21738-3
5. Brotherston, J., & Simpson, A. (2011). “Sequent calculi for induction and
   infinite descent.” *Journal of Logic and Computation*, 21(6), 1177–1216.
   https://doi.org/10.1093/logcom/exq052
6. Fowler, M. (2005, December 12). “Event Sourcing.” MartinFowler.com.
   https://martinfowler.com/eaaDev/EventSourcing.html
7. Chandy, K. M., & Lamport, L. (1985). “Distributed snapshots: Determining
   global states of distributed systems.” *ACM Transactions on Computer
   Systems*, 3(1), 63–75. https://doi.org/10.1145/214451.214456
8. Elnozahy, E. N., Alvisi, L., Wang, Y.-M., & Johnson, D. B. (2002). “A survey
   of rollback-recovery protocols in message-passing systems.” *ACM Computing
   Surveys*, 34(3), 375–408. https://doi.org/10.1145/568522.568525
9. Dunlap, G. W., King, S. T., Cinar, S., Basrai, M. A., & Chen, P. M. (2002).
   “ReVirt: Enabling intrusion analysis through virtual-machine logging and
   replay.” In *Proceedings of the 5th Symposium on Operating Systems Design and
   Implementation (OSDI ’02)*, 211–224. USENIX Association.
   https://www.usenix.org/conference/osdi-02/revirt-enabling-intrusion-analysis-through-virtual-machine-logging-and-replay

## Excluded draft references

The following draft items are not used as evidence here:

- Keller (1968), because the exact edition, publisher record, and intended
  passage were not confirmed during this check;
- Young (2010), because a stable original or author-controlled record was not
  confirmed;
- Brotherston's 2006 thesis, because the journal article above is sufficient
  for the limited cyclic-proof statement;
- adjacent consensus and cryptographic references, because no claim about those
  fields is needed for this comparison.

### Screening and preservation

Screening has three stages: title/snippet, abstract, then accessible full text.
For each record retained after title/snippet screening, the log preserves its
stable identifier, field, decision, E1–E6 assessment where applicable, and a
reason. Searches are reported exactly enough to rerun, with access date and
database limitations. One researcher performed the search and screening; no
independent duplicate screening or inter-rater agreement is claimed.


### Search strings

The fixed rerun submits each family once, with the exact domain restriction and
two exact discovery variants preserved in
`ANIMUS_CYCLE_PRIOR_ART_SEARCH_LOG.md`. The submitted families are:

1. `("endpoint-derived" OR "terminal-state-derived" OR "final-state-derived")
   AND (initial OR beginning OR boundary) AND (return OR reconstruction)`
2. `("reciprocal boundary" OR "cyclic boundary condition" OR
   "periodic boundary condition") AND (execution OR replay OR provenance)`
3. `(fixed point OR self-consistency) AND (checkpoint OR event log OR replay)
   AND (validation OR provenance)`
4. `("deterministic replay" OR "record and replay") AND (cyclic OR fixed point
   OR boundary) AND (checkpoint OR reconstruction)`
5. `("event sourcing" OR "event log") AND (cycle OR cyclic OR fixed point)
   AND (replay OR reconstruction OR validation)`
6. `(workflow OR provenance) AND (cyclic OR loop OR iteration) AND
   (replay OR reconstruction) AND (validation OR verification)`
7. `(rollback recovery OR distributed snapshot OR checkpoint) AND
   (fixed point OR self-consistency OR cyclic) AND (endpoint OR boundary)`
8. `(shooting method OR boundary value problem OR periodic solution) AND
   (replay OR provenance OR event log OR checkpoint)`
9. `(cyclic proof OR circular proof) AND (execution trace OR replay OR
   provenance OR reconstruction)`

The fixed rerun does not claim exhaustive native-database coverage or complete
backward/forward citation chasing. Earlier field-oriented searches and citation
chasing informed the comparison table, but they are supplementary discovery,
not part of the fixed rerun's result counts. This narrower scope is intentional:
only searches with complete query and result-level logs contribute to the
systematic-search conclusion.

## Included records and equivalence assessment

`Y` means the accessible primary source establishes the criterion. `N` is used
only when the described method positively uses a different operation, most
often no reciprocal endpoint-to-beginning return. `?` means the criterion was
not established and is not an inference of absence.

| Record | Field | E1 | E2 | E3 | E4 | E5 | E6 | Assessment |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| Crofts, *Efficient Method for Detection of Periodic Orbits in Chaotic Maps and Flows* (2007), [arXiv:0706.1940](https://arxiv.org/abs/0706.1940) | Numerical methods | Y | Y | Y | Y | ? | Y | Strongest reciprocal-closure match. A finite return-map problem is independently checked by interval methods for no or unique solutions, but no provenance-linked replay or reconstruction audit is established. |
| Gasull & Mañosa, “Periodic orbits of discrete and continuous dynamical systems via Poincaré-Miranda theorem” (2018), [arXiv:1809.06208](https://arxiv.org/abs/1809.06208) | Numerical methods | Y | Y | Y | Y | ? | Y | Bounded return-map boxes and independent sign conditions establish existence and number of periodic orbits; provenance and replay are not established. |
| Kumar, “A new fast multiple-shooting method for computing periodic orbits...” (2026), [arXiv:2601.00149](https://arxiv.org/abs/2601.00149) | Numerical methods | Y | Y | Y | ? | ? | ? | A finite modulo-\(q\) multiple-shooting system makes the last map return to the first point, but no distinct history validator or provenance/replay audit is established. |
| Gander & Wu, “Convergence analysis of a periodic-like waveform relaxation method...” (2019), [doi:10.1007/s00211-019-01060-8](https://doi.org/10.1007/s00211-019-01060-8) | Numerical methods | Y | Y | Y | ? | ? | ? | Endpoint feedback enters the next iterate's initial condition; convergence analysis does not establish the complete validation and audit contract. |
| Liu, “When May an Agent Stop? Evidence-Carrying Termination for Tool-Using LLMs” (2026), [arXiv:2608.23623](https://arxiv.org/abs/2608.23623) | Formal verification | Y | N | Y | Y | Y | ? | Strongest auditability match: a trusted contract, immutable evidence, fail-closed validation, and deterministic reconstruction are explicit, but no ending supplies a beginning condition. |
| Chang, Geng & Chang, “Mnemosyne: Agentic Transaction Processing for Validating and Repairing AI-generated Workflows” (2026), [arXiv:2607.00269](https://arxiv.org/abs/2607.00269) | Workflow/runtime verification | Y | N | Y | Y | Y | ? | Finite-state constraints, transition logs, deterministic admission, and replay checks are explicit; reciprocal boundary closure is not. |
| Nakajima, “The Log is the Agent: Event-Sourced Reactive Graphs for Auditable, Forkable Agentic Systems” (2026), [arXiv:2605.21997](https://arxiv.org/abs/2605.21997) | Event sourcing | ? | N | ? | Y | Y | ? | Append-only lineage, deterministic projection, replay, and strict reproducibility validation are explicit; no endpoint-derived beginning is described. |
| Rhodes & Kang, “Proof of Execution: Runtime Verification for Governed AI Agent Actions” (2026), [arXiv:2607.05397](https://arxiv.org/abs/2607.05397) | Runtime verification | ? | N | Y | Y | Y | ? | A fixed execution contract, causal event stream, replay context, and validator are explicit, but the terminal output is not returned as a required beginning condition. |
| Geels et al., “Friday: Global Comprehension for Distributed Replay” (2007), [ACM record](https://dl.acm.org/doi/10.5555/1973430.1973451) | Distributed replay | ? | ? | ? | ? | ? | ? | Captures distributed execution, replays it, and checks global predicates. The stricter return-specific provenance and boundary criteria are not established. |
| Charapko et al., “Retroscope: Retrospective Monitoring of Distributed Systems” (2019), [doi:10.1109/TPDS.2019.2911944](https://doi.org/10.1109/TPDS.2019.2911944) | Distributed systems | ? | ? | ? | ? | ? | ? | HLC-stamped logs reconstruct consistent global states and test predicates, but no reciprocal boundary contract or separated closure report is established. |
| Carbone et al., “Lightweight Asynchronous Snapshots for Distributed Dataflows” (2015), [arXiv:1506.08603](https://arxiv.org/abs/1506.08603) | Distributed systems | ? | ? | ? | ? | ? | ? | Checkpoint and recovery support cyclic dataflows with a minimal log; they do not establish endpoint-derived return and full-history validation. |
| O'Callahan et al., “Engineering Record And Replay For Deployability” (2017), [USENIX](https://www.usenix.org/conference/atc17/technical-sessions/presentation/ocallahan) | Deterministic replay | ? | N | ? | ? | ? | ? | Records process inputs and nondeterminism for exact replay; its interface boundary is not a reciprocal temporal boundary. |
| Pham, Malik & Foster, “Using Provenance for Repeatability” (2013), [USENIX](https://www.usenix.org/conference/tapp13/technical-sessions/presentation/pham) | Workflow provenance | ? | ? | ? | ? | Y | ? | A provenance trace drives partial deterministic replay in the same event order; no endpoint-to-beginning condition is described. |
| Zhuang et al., “ExoFlow: A Universal Workflow System for Exactly-Once DAGs” (2023), [USENIX](https://www.usenix.org/conference/osdi23/presentation/zhuang) | Workflow recovery | ? | N | ? | ? | ? | ? | Durable workflow state coordinates rollback and task replay, but the workflow is a DAG and does not implement reciprocal closure. |
| Woodman et al., “Achieving Reproducibility by Combining Provenance with Service and Workflow Versioning” (2011), [doi:10.1145/2110497.2110512](https://doi.org/10.1145/2110497.2110512) | Workflow provenance | ? | N | ? | ? | Y | ? | Complete provenance traces can be transformed into workflows and re-enacted; no ending-derived beginning condition is described. |

**Screening result:** no record in the assessed set establishes all E1–E6, so
no record reached the E7–E9 complete-contract assessment gate.
The numerical literature supplies the closest source-supported E1–E4 and E6
combination. Replay, event-sourcing, workflow, and runtime-verification
literature supplies the closest E3–E5 combination. The searches did not locate
one primary record that joins reciprocal return-map closure to provenance-linked
replay/reconstruction and separated outcomes.

## Excluded records retained with reasons

| Record or lead | Exclusion reason |
|---|---|
| Elnozahy et al., “A Survey of Rollback-Recovery Protocols in Message-Passing Systems” (2002), [doi:10.1145/568522.568525](https://doi.org/10.1145/568522.568525) | Secondary survey used for citation chasing, not one candidate method. |
| Garg et al., “Deterministic Replay: A Survey” (2015), [doi:10.1145/2790077](https://doi.org/10.1145/2790077) | Secondary survey; no single implementation is assessable for the conjunction. |
| “Improving Workflow Fault Tolerance through Provenance-Based Recovery” (2011), [doi:10.1007/978-3-642-22351-8_12](https://doi.org/10.1007/978-3-642-22351-8_12) | Highly relevant abstract mentions workflow loops, provenance, checkpoints, and replay, but full primary text was subscription-restricted; retained as an unresolved lead, not negative evidence. |
| “Multiple Shooting Techniques Revisited,” [doi:10.1007/978-1-4684-7324-7_6](https://doi.org/10.1007/978-1-4684-7324-7_6) | Publisher preview confirms boundary-value multiple shooting, but full text was restricted and insufficient for E1–E6. |
| Erb et al., “Consistent Retrospective Snapshots in Distributed Event-sourced Systems” (2017) | Relevant lead, but no stable publisher, DOI, repository, or author-controlled full source was verified in this run. |
| Tian et al., “Periodic boundary condition and its numerical implementation algorithm...” (2019), [doi:10.1016/j.compositesb.2018.10.053](https://doi.org/10.1016/j.compositesb.2018.10.053) | Ordinary periodic finite-element boundary conditions; no replay/provenance history or endpoint-authored return. |
| Jones, “Use of a shooting method to compute eigenvalues of fourth-order ordinary differential equations” (1993), [ScienceDirect](https://www.sciencedirect.com/science/article/pii/037704279390065J) | Standard two-point boundary-value/eigenvalue shooting; no replay, provenance, or history validation. |
| Atserias & Lauria, “Circular (Yet Sound) Proofs” (2023), [doi:10.1145/3579997](https://doi.org/10.1145/3579997) | Cyclic proof graph with a soundness condition, not a temporal endpoint-derived return or replayable history. |
| Narayanan & Ren, “Circular Trace Reconstruction” (2021), [doi:10.4230/LIPIcs.ITCS.2021.18](https://doi.org/10.4230/LIPIcs.ITCS.2021.18) | “Circular” describes the unknown string; deletion-trace reconstruction does not implement reciprocal executed closure. |
| Vidal, “From Reversible Computation to Checkpoint-Based Rollback Recovery...” (2023), [arXiv:2309.04873](https://arxiv.org/abs/2309.04873) | Rollback to an earlier consistent state, without an endpoint-derived beginning return or return-specific validation. |
| “RecPlay: A Fully Integrated Practical Record/Replay System,” [doi:10.1145/312203.312214](https://doi.org/10.1145/312203.312214) | “Cyclic debugging” is iterative debugging, not reciprocal temporal closure. |
| *Terminal-Universe*, arXiv:2609.04148 | Submitted after the 2026-09-10 cutoff. |


## Systematic-search execution log

**Execution date:** 2026-09-12
**Publication cutoff:** 2026-09-10 inclusive
**Searchers/screeners:** one primary researcher using five independent
field-focused search passes; final decisions consolidated under the frozen
criteria above.

All nine frozen query families were rerun once in a fixed domain matrix. The
matrix returned 72 rows representing 64 canonical unique records. Every row,
exact query, domain restriction, result count, duplicate, and title/snippet
decision is preserved in `ANIMUS_CYCLE_PRIOR_ART_SEARCH_LOG.md`.

| Pass | Query families and principal variants | Indexes or stable-source surfaces reached |
|---|---|---|
| Formal methods | F1, F3, F4, F6, F7, F9; fixed-point certificates, model checking, cyclic proofs, runtime verification, provenance | ACM DL, IEEE Xplore, arXiv, USENIX, DROPS, author-controlled proceedings copies |
| Distributed systems and replay | F3–F7 plus distributed replay, consistent cuts, replicated logs, global predicates, event-sourced snapshots | ACM DL, IEEE Xplore, dblp, USENIX, arXiv, SpringerLink, ScienceDirect |
| Numerical boundary methods | F1–F4 and F8; periodic orbits, return maps, multiple shooting, interval validation, waveform relaxation | arXiv, SpringerLink, SIAM, ScienceDirect, IEEE Xplore, Crossref |
| Workflow and provenance | F1–F9; cyclic workflows, process mining, provenance replay, fault recovery, event logs | ACM DL, IEEE Xplore, USENIX, dblp, SpringerLink, ScienceDirect, Crossref, OpenAlex, Semantic Scholar, PMC |
| Cross-domain conjunction | F1–F9 plus six targeted combinations joining return maps, endpoint feedback, deterministic replay, provenance, validation, and multiplicity | ACM DL, IEEE Xplore, arXiv, USENIX, SpringerLink, ScienceDirect, OpenAlex, Semantic Scholar, Oxford Academic |

Earlier field-oriented discovery and citation chasing used these additional
strings:

- `"self-consistent" initial conditions replay provenance validation finite`;
- `"closed-loop" workflow provenance replay validation endpoint`;
- `"periodic orbit" shooting method continuation replay reconstruction uniqueness`;
- `"fixed point" "event log" deterministic replay provenance`;
- `"return map" endpoint initial condition provenance replay`; and
- `"replay" "multiple solutions" boundary value provenance`.

The fixed rerun was deduplicated by DOI, arXiv identifier, or canonical URL.
Positive E assessments require accessible primary text. Abstract-only,
paywalled, and insufficient records are retained as exclusions or unresolved
leads rather than treated as negative evidence.

### Sources and coverage

The search covers records dated from database inception through 2026-09-10.
The fixed rerun targets these public index and publisher surfaces:

- ACM Digital Library and IEEE Xplore for distributed systems, replay,
  checkpointing, workflow, and formal methods;
- USENIX proceedings for systems and replay;
- arXiv for openly indexed computer science and numerical work;
- SpringerLink and ScienceDirect for numerical methods, boundary-value
  problems, workflow, and provenance literature; and
- Oxford Academic for formal-method discovery.

Earlier supplementary discovery reached dblp, Crossref, Semantic Scholar, and
OpenAlex, but those searches are not included in the fixed rerun's counts or
systematic-search conclusion because their result-level logs were not retained.

Search-engine results may locate a record, but inclusion requires a stable
publisher, proceedings, repository, DOI, or author-controlled source.

### Eligibility criteria

A record is included for full-text equivalence assessment when it:

1. was publicly available by 2026-09-10;
2. describes a technical method, formal model, or implemented system;
3. concerns at least two elements of the conjunction: reciprocal boundary
   closure, executed endpoint derivation, replay/reconstruction, independently
   declared validation, or explicit provenance; and
4. has enough accessible primary text to assess what the method requires.

Records are excluded from equivalence assessment when they are duplicate
versions, secondary summaries without additional technical content, use
“cycle” only as a scheduling or iteration label, concern only ordinary periodic
boundary conditions, or lack accessible text sufficient to test the criteria.
Every returned row, including irrelevant keyword hits, is retained in the
execution log with a reason.

### Preliminary equivalence screen and complete-contract rule

E1–E6 are necessary preliminary criteria for identifying the nearest
cross-disciplinary matches:

- **E1 finite declared evaluation domain:** a finite state, trace, candidate,
  or bounded execution domain is declared for the result;
- **E2 reciprocal executed boundary:** forward execution from a candidate
  beginning reaches an ending, and content derived from that executed ending
  supplies a condition required at the beginning;
- **E3 result-independent beginning contract:** the beginning or boundary
  acceptance conditions are declared independently of the observed candidate
  result;
- **E4 independent validation:** a distinct check evaluates the sealed or
  completed history against beginning, endpoint, and return requirements;
- **E5 provenance and replay/reconstruction:** the method records the origin of
  the return and supports deterministic replay or a declared reconstruction
  rule sufficient to audit it;
- **E6 separated outcomes:** closure/existence is reported separately from at
  least uniqueness or multiplicity, replay, information retention/loss, or
  state equality.

A **complete contract match** must satisfy E1–E6 and also:

- **E7 causal ablation:** removing the returned beginning fact prevents the
  validated returned content from being derived;
- **E8 bounded observers:** observer output is explicitly local and excludes
  the hidden global state, boundary, contract, return, enumeration, and
  validation metadata; and
- **E9 one authoritative history:** candidate search is a validation procedure,
  not represented branching, except under an explicitly declared branch
  intervention.

These nine criteria map the required invariants in `ANIMUS_CYCLE.md`: E1 maps
the finite domain; E2 maps forward execution and ending-derived return; E3 maps
the beginning contract; E4 maps independent sealed-history validation; E5 maps
return provenance, replay, and reconstruction; E6 maps separated outcomes; and
E7–E9 map causal ablation, bounded observers, and one authoritative history.

Functional equivalence counts even when terminology differs. A record that
fails or leaves any E criterion unclear is a partial match, not a complete
match. Because no assessed record passed E1–E6, none reached the E7–E9
full-contract assessment gate.

## Systematic-search conclusion

This search **did not identify a complete E1–E9 match**. No record passed the
E1–E6 preliminary gate, so none could qualify for the complete-contract
E7–E9 assessment. The search therefore improves
the comparison from an unsystematic source check to a documented negative
search result. It does **not** establish a true prior-art gap. Non-retrieval
cannot prove absence, several promising records were inaccessible, database
searches were mediated by public web indexes rather than authenticated native
database APIs, terminology may differ, citation chasing was bounded, and
screening was performed by one researcher.

The supported conclusion is:

> Across the documented searches and accessible primary records through
> 2026-09-10, we identified close partial precedents but no source-supported
> record satisfying the frozen complete-contract criteria. This is a
> documented negative search result, not proof that the conjunction is absent
> from prior systems and not a scientific or technical novelty claim.

Before any novelty language is considered, the unresolved provenance-based
workflow-recovery chapter and other inaccessible leads should be obtained, and
qualified external reviewers should independently rerun or challenge the search
and equivalence decisions.

### Research question

Does a record published before 2026-09-11 describe a single finite-system
method or implementation that satisfies the complete Animus-cycle conjunction,
rather than merely one or more neighboring mechanisms?
