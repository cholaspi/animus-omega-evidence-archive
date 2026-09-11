"""Development world families for Test 05.

Per the run procedure, conclusions must not rest on repeated seeds of a
single template. Each entry below is a *structurally different* world: a
different number of agents, a different obligation-chain length, a different
reconstruction algorithm, a different ledger capacity, or a different
adversarial condition (residual collision pressure, identity substitution,
causal reordering). World families are independent of arm labels: nothing
here encodes an expected outcome.
"""

from __future__ import annotations

from dataclasses import dataclass

from .world import WorldConfig


@dataclass(frozen=True)
class WorldFamily:
    family_id: str
    description: str
    config: WorldConfig
    # Extra, family-specific knobs consumed by 05B/05C/05D, not by the core
    # world mechanics in world.py.
    loss_profile: str  # which microstate fields residual.py discards
    adversarial: tuple[str, ...] = ()  # e.g. ("identity_substitution",)


def all_world_families() -> list[WorldFamily]:
    return [
        WorldFamily(
            family_id="triad-standard",
            description="3 agents, 2-obligation chain, faithful reconstruction.",
            config=WorldConfig(
                world_id="triad-standard",
                num_agents=3,
                num_obligations=2,
                history_length=4,
                total_resource=3,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            loss_profile="standard",
        ),
        WorldFamily(
            family_id="quad-chain",
            description="4 agents, 3-obligation chain, faithful reconstruction.",
            config=WorldConfig(
                world_id="quad-chain",
                num_agents=4,
                num_obligations=3,
                history_length=4,
                total_resource=4,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            loss_profile="standard",
        ),
        WorldFamily(
            family_id="triad-lossy-reconstruction",
            description=(
                "3 agents, 2-obligation chain, but reconstruction replays "
                "with a lossy algorithm that drops blocked-event detail; "
                "adversarial for reciprocal closure since some natural "
                "histories will fail to reconstruct exactly."
            ),
            config=WorldConfig(
                world_id="triad-lossy-reconstruction",
                num_agents=3,
                num_obligations=2,
                history_length=4,
                total_resource=3,
                reconstruction_algorithm="lossy_replay",
                ledger_capacity=64,
            ),
            loss_profile="aggressive",
        ),
        WorldFamily(
            family_id="triad-short-ledger",
            description=(
                "3 agents, 2-obligation chain, 5-tick history, and a "
                "ledger capacity (3) smaller than the relevant-event count "
                "some histories produce, forcing ledger overflow handling."
            ),
            config=WorldConfig(
                world_id="triad-short-ledger",
                num_agents=3,
                num_obligations=2,
                history_length=5,
                total_resource=3,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=3,
            ),
            loss_profile="standard",
        ),
        WorldFamily(
            family_id="pentad-long-chain",
            description="5 agents, 4-obligation chain, faithful reconstruction.",
            config=WorldConfig(
                world_id="pentad-long-chain",
                num_agents=5,
                num_obligations=4,
                history_length=4,
                total_resource=5,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            loss_profile="standard",
        ),
        WorldFamily(
            family_id="triad-adversarial-identity",
            description=(
                "3 agents, 2-obligation chain; adversarial identity "
                "substitution probes are added on top of the standard "
                "semantic contract to test whether reconstruction can be "
                "fooled by a relabeled agent with matching balances."
            ),
            config=WorldConfig(
                world_id="triad-adversarial-identity",
                num_agents=3,
                num_obligations=2,
                history_length=4,
                total_resource=3,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            loss_profile="standard",
            adversarial=("identity_substitution",),
        ),
        WorldFamily(
            family_id="quad-adversarial-reorder",
            description=(
                "4 agents, 3-obligation chain; adversarial causal-reorder "
                "probes are added to test whether a reordered ledger (same "
                "entries, different order) is wrongly accepted as "
                "equivalent."
            ),
            config=WorldConfig(
                world_id="quad-adversarial-reorder",
                num_agents=4,
                num_obligations=3,
                history_length=4,
                total_resource=4,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            loss_profile="standard",
            adversarial=("causal_reorder",),
        ),
    ]


def observer_world_families() -> list[WorldFamily]:
    """Dedicated (smaller) world families for Test 05C. Observer boundary
    detection needs a history long enough to contain a phase-matched
    interior window well before the boundary window, which requires a
    longer history than 05A/05B use; to keep exact enumeration tractable
    (alphabet_size ** history_length grows fast) these use fewer agents
    than the largest 05A/05B families."""
    return [
        WorldFamily(
            family_id="observer-duo",
            description="2 agents, 1 obligation, 5-tick history (exact enumeration, small).",
            config=WorldConfig(
                world_id="observer-duo",
                num_agents=2,
                num_obligations=1,
                history_length=5,
                total_resource=2,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            loss_profile="standard",
        ),
        WorldFamily(
            family_id="observer-triad",
            description="3 agents, 2 obligations, 7-tick history (exact enumeration).",
            config=WorldConfig(
                world_id="observer-triad",
                num_agents=3,
                num_obligations=2,
                history_length=7,
                total_resource=3,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            loss_profile="standard",
        ),
    ]


def get_world_family(family_id: str) -> WorldFamily:
    for wf in all_world_families():
        if wf.family_id == family_id:
            return wf
    raise KeyError(family_id)
