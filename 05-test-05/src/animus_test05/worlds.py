"""Frozen development world families for Test 05, protocol v2.

Revision note (protocol v2): the v1 draft used seven world families for
05A/05B/05D plus two dedicated families for 05C. Per the revised protocol
this was replaced with exactly **two** world families -- a friendly
obligation world and an adversarial world -- so that "many arms/controls
from one template" is never mistaken for "many independent world
families." Each family carries two *configurations*: a ``standard_config``
(used by 05A/05B/05D, short history for tractable exhaustive enumeration of
every admissible history) and an ``observer_config`` (the same family's
agent count and obligation structure, but a longer history so a
phase-matched interior window exists for 05C -- still the same family, not
a new one). Nothing here encodes an expected outcome, arm label, or closure
status.
"""

from __future__ import annotations

from dataclasses import dataclass

from .world import WorldConfig


@dataclass(frozen=True)
class WorldFamily:
    family_id: str
    description: str
    standard_config: WorldConfig
    observer_config: WorldConfig
    loss_profile: str
    adversarial: tuple[str, ...] = ()

    # Backward-compatible alias: most 05A/05B/05D code just wants "the"
    # config for this family (the short, fully-enumerable one).
    @property
    def config(self) -> WorldConfig:
        return self.standard_config


def all_world_families() -> list[WorldFamily]:
    return [
        WorldFamily(
            family_id="friendly",
            description=(
                "Friendly obligation world: 3 agents, a simple 2-obligation causal chain, faithful "
                "reconstruction, no adversarial conditions."
            ),
            standard_config=WorldConfig(
                world_id="friendly",
                num_agents=3,
                num_obligations=2,
                history_length=4,
                total_resource=3,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            observer_config=WorldConfig(
                world_id="friendly-observer-horizon",
                num_agents=3,
                num_obligations=2,
                history_length=7,  # 2*num_agents + 1: guarantees a phase-matched interior window
                total_resource=3,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            loss_profile="standard",
        ),
        WorldFamily(
            family_id="adversarial",
            description=(
                "Adversarial world: 3 agents, a 3-obligation causal chain, and adversarial probes for "
                "identity substitution and causal reordering layered on top of the same residual-collision, "
                "obligation-deletion, contradiction, stale-event, and duplicate-event controls applied to "
                "every world family (see residual.run_controls)."
            ),
            standard_config=WorldConfig(
                world_id="adversarial",
                num_agents=3,
                num_obligations=3,
                history_length=4,
                total_resource=3,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            observer_config=WorldConfig(
                world_id="adversarial-observer-horizon",
                num_agents=3,
                num_obligations=3,
                history_length=7,
                total_resource=3,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            loss_profile="standard",
            adversarial=("identity_substitution", "causal_reorder"),
        ),
    ]


def observer_world_families() -> list[WorldFamily]:
    """The same two families, exposed for 05C callers that historically
    asked for a dedicated observer-family list. 05C uses each family's
    ``observer_config`` rather than ``standard_config``."""
    return all_world_families()


def get_world_family(family_id: str) -> WorldFamily:
    for wf in all_world_families():
        if wf.family_id == family_id:
            return wf
    raise KeyError(family_id)
