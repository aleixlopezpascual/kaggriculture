"""Kaggriculture Monte Carlo Tree Search (MCTS) agent."""

import math
from dataclasses import dataclass

from src.agents.base import BaseAgent
from src.agents.escalation import EscalationAgent
from src.env.state import StrategicTarget, WorldState
from src.env.transitions import step_world


@dataclass
class MCTSNode:
    """A node in the MCTS tree, branching on macro StrategicTargets."""

    state: WorldState
    parent: "MCTSNode | None" = None
    target: StrategicTarget | None = None
    visits: int = 0
    value: float = 0.0
    children: list["MCTSNode"] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


class MCTSAgent(BaseAgent):
    """Monte Carlo Tree Search decision agent using stateless macro targets."""

    def __init__(self, num_simulations: int = 20, exploration_weight: float = 1.414):
        self.num_simulations = num_simulations
        self.exploration_weight = exploration_weight
        self.heuristic_fallback = EscalationAgent()
        self.active_target: StrategicTarget | None = None

    def act(self, state: WorldState) -> dict:
        """Runs MCTS to select the best target, then acts heuristically."""
        if not state.farm.workers:
            return {"worker_actions": {}, "farm_actions": []}

        # 1. Check if we need to re-plan strategic targets
        # Re-plan at Turn 0, start of each day, or if we have no target yet
        should_replan = (
            self.active_target is None
            or state.turn == 0
            or state.turn % 24 == 0
            or self._is_target_achieved(state, self.active_target)
        )

        if should_replan:
            self.active_target = self._search_best_target(state)

        # 2. Execute the current strategic target hourly via the Heuristic Core
        return self.heuristic_fallback.act(state, target=self.active_target)

    def _is_target_achieved(self, state: WorldState, target: StrategicTarget) -> bool:
        """Determines if the active strategic target's counts are satisfied."""
        workers_satisfied = len(state.farm.workers) >= target.target_workers
        cows = sum(1 for a in state.animals if a.animal_type == "Cow")
        sheep = sum(1 for a in state.animals if a.animal_type == "Sheep")
        geese = sum(1 for a in state.animals if a.animal_type == "Goose")

        animals_satisfied = (
            cows >= target.target_cows
            and sheep >= target.target_sheep
            and geese >= target.target_geese
        )

        # Check crops
        crop_counts = {}
        for c in state.crops:
            crop_counts[c.crop_type] = crop_counts.get(c.crop_type, 0) + 1

        crops_satisfied = True
        for crop, count in target.crop_priorities.items():
            if crop_counts.get(crop, 0) < count:
                crops_satisfied = False
                break

        return workers_satisfied and animals_satisfied and crops_satisfied

    def _search_best_target(self, state: WorldState) -> StrategicTarget:
        """MCTS search over the set of candidate targets."""
        # Setup Candidates
        candidates = []

        if state.turn >= 680:
            # Late-game liquidation target
            candidates.append(
                StrategicTarget(
                    target_workers=len(state.farm.workers),
                    target_cows=0,
                    target_sheep=0,
                    target_geese=0,
                    crop_priorities={},
                    budget_reserved_for_seeds=0.0,
                    is_liquidating=True,
                )
            )
        else:
            # Focus 1: Baseline strawberry rush (high-yield, early game)
            candidates.append(
                StrategicTarget(
                    target_workers=3,
                    target_cows=0,
                    target_sheep=0,
                    target_geese=0,
                    crop_priorities={"Strawberry": 15},
                    budget_reserved_for_seeds=150.0,
                    is_liquidating=False,
                )
            )
            # Focus 2: Mid-game Livestock Expansion (4C/2S)
            candidates.append(
                StrategicTarget(
                    target_workers=4,
                    target_cows=4,
                    target_sheep=2,
                    target_geese=0,
                    crop_priorities={"Wheat": 6, "Strawberry": 8},
                    budget_reserved_for_seeds=200.0,
                    is_liquidating=False,
                )
            )
            # Focus 3: The 8C/4S Absolute Gold-Medal Meta Ceiling
            candidates.append(
                StrategicTarget(
                    target_workers=5,
                    target_cows=8,
                    target_sheep=4,
                    target_geese=0,
                    crop_priorities={"Wheat": 12, "Melon": 4},
                    budget_reserved_for_seeds=400.0,
                    is_liquidating=False,
                )
            )

        root = MCTSNode(state=state)

        # Expand root immediately with candidates
        for target in candidates:
            root.children.append(MCTSNode(state=state, parent=root, target=target))

        for _ in range(self.num_simulations):
            # Selection (always select from root's direct children for macro choice)
            node = self._select_ucb(root)

            # Simulation (Rollout) guided by candidate target
            reward = self._rollout(node.state, node.target)

            # Backpropagation
            node.visits += 1
            node.value += reward
            root.visits += 1
            root.value += reward

        # Retrieve the target from the child with the highest average value
        best_child = max(
            root.children, key=lambda c: (c.value / c.visits) if c.visits > 0 else -1.0
        )
        return best_child.target if best_child.target else candidates[0]

    def _select_ucb(self, node: MCTSNode) -> MCTSNode:
        """Selects a child node using standard Upper Confidence Bound (UCB1)."""
        best_score = -float("inf")
        best_child = node.children[0]

        for child in node.children:
            if child.visits == 0:
                return child
            exploitation = child.value / child.visits
            exploration = self.exploration_weight * math.sqrt(
                math.log(node.visits) / child.visits
            )
            score = exploitation + exploration
            if score > best_score:
                best_score = score
                best_child = child

        return best_child

    def _rollout(self, state: WorldState, target: StrategicTarget) -> float:
        """Brief daily rollout of the fast simulator guided by the target."""
        curr_state = state
        depth = 48  # Simulate 2 full days forward
        start_gold = state.farm.gold

        for _ in range(depth):
            # Get tactical hourly worker actions for target
            joint_actions = self.heuristic_fallback.act(curr_state, target=target)
            try:
                curr_state = step_world(curr_state, joint_actions)
            except Exception:
                break

        # Value scoring: gold accumulated + asset values
        gold_gained = curr_state.farm.gold - start_gold
        cows = sum(1 for a in curr_state.animals if a.animal_type == "Cow")
        sheep = sum(1 for a in curr_state.animals if a.animal_type == "Sheep")
        geese = sum(1 for a in curr_state.animals if a.animal_type == "Goose")

        asset_valuation = cows * 400 + sheep * 240 + geese * 120
        # Add basic weight for inventory items
        asset_valuation += sum(curr_state.farm.inventory.values()) * 15

        return float(gold_gained + asset_valuation)
