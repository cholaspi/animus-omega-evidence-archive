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
    # Protocol v1.3.0-dev4, correction 9: dimensions chosen so the section-16
    # expansion/contraction inequality (R(t1) >= 2*R(t0) and R(t2) <=
    # R(t0)+1) is actually mathematically achievable and actually witnessed
    # by at least one exhaustively-enumerated history -- not merely
    # "checked and found impossible" as in v1.2.0-dev3. These exact
    # dimensions were verified empirically (not just by hand-arithmetic on
    # the ceiling) by running expansion.evaluate_world_family() against
    # every candidate in a small search before freezing this file; every
    # combination below is confirmed "supported" -- see
    # expansion.preflight_feasibility_check, which run.freeze() now calls
    # and refuses to freeze on failure, as the mechanical, non-bypassable
    # version of that same verification. history_length is kept far under
    # the protocol's 1,000,000-history exhaustive-enumeration bound
    # (alphabet size 4): standard_config uses the smallest length found
    # feasible (1,024 / 4,096 admissible histories); observer_config keeps
    # the prior "2*num_agents + 1" margin for a phase-matched interior
    # window at a still-tiny 16,384 / 262,144 histories.
    return [
        WorldFamily(
            family_id="friendly",
            description=(
                "Friendly obligation world: 3 agents, a simple 1-obligation causal chain, faithful "
                "reconstruction, no adversarial conditions. Dimensions chosen (protocol v1.3.0-dev4) so "
                "the section-16 expansion/contraction inequality is mathematically achievable and "
                "actually witnessed by an enumerated history (empirically verified, not asserted)."
            ),
            standard_config=WorldConfig(
                world_id="friendly",
                num_agents=3,
                num_obligations=1,
                history_length=5,
                total_resource=3,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            observer_config=WorldConfig(
                world_id="friendly-observer-horizon",
                num_agents=3,
                num_obligations=1,
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
                "Adversarial world: 4 agents, a 2-obligation causal chain, and adversarial probes for "
                "identity substitution and causal reordering layered on top of the same residual-collision, "
                "obligation-deletion, contradiction, stale-event, and duplicate-event controls applied to "
                "every world family (see residual.run_controls). Dimensions chosen (protocol v1.3.0-dev4) "
                "so the section-16 expansion/contraction inequality is mathematically achievable and "
                "actually witnessed by an enumerated history, while keeping exactly 2 obligations so the "
                "causal_reorder fault mutation has a real, immediately-dependent resolve pair to act on "
                "(see execution_matrix._causally_significant_reorder)."
            ),
            standard_config=WorldConfig(
                world_id="adversarial",
                num_agents=4,
                num_obligations=2,
                history_length=6,
                total_resource=4,
                reconstruction_algorithm="faithful_replay",
                ledger_capacity=64,
            ),
            observer_config=WorldConfig(
                world_id="adversarial-observer-horizon",
                num_agents=4,
                num_obligations=2,
                history_length=9,  # 2*num_agents + 1
                total_resource=4,
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
