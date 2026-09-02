"""Kaggriculture Monte Carlo Tree Search (MCTS) agent."""

import math
import random
from dataclasses import dataclass
from src.agents.base import BaseAgent
from src.env.state import WorldState
from src.env.transitions import step_world
from src.agents.heuristic import HeuristicAgent


@dataclass
class MCTSNode:
    """A node in the Monte Carlo Tree Search tree."""

    state: WorldState
    parent: "MCTSNode | None" = None
    action: dict | None = None
    visits: int = 0
    value: float = 0.0
    children: list["MCTSNode"] = None

    def __post_init__(self):
        if self.children is None:
            self.children = []


class MCTSAgent(BaseAgent):
    """Monte Carlo Tree Search decision agent utilizing stateless transitions."""

    def __init__(self, num_simulations: int = 20, exploration_weight: float = 1.414):
        self.num_simulations = num_simulations
        self.exploration_weight = exploration_weight
        self.heuristic_fallback = HeuristicAgent()

    def act(self, state: WorldState) -> dict:
        """Runs MCTS to select the best joint action from the current state."""
        if not state.farm.workers:
            return {"worker_actions": {}, "farm_actions": []}

        root = MCTSNode(state=state)

        for _ in range(self.num_simulations):
            # 1. Selection
            node = root
            while node.children:
                node = self._select_ucb(node)

            # 2. Expansion
            if node.visits > 0 or node == root:
                self._expand(node)
                if node.children:
                    node = random.choice(node.children)

            # 3. Simulation (Rollout)
            reward = self._rollout(node.state)

            # 4. Backpropagation
            curr = node
            while curr is not None:
                curr.visits += 1
                curr.value += reward
                curr = curr.parent

        # Choose child with maximum visits or highest value
        if not root.children:
            return self.heuristic_fallback.act(state)

        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.action if best_child.action else {"worker_actions": {}, "farm_actions": []}

    def _select_ucb(self, node: MCTSNode) -> MCTSNode:
        """Selects a child node using Upper Confidence Bound (UCB1)."""
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

    def _expand(self, node: MCTSNode):
        """Expands a leaf node by adding children for possible actions."""
        # Generate 3 candidate actions (using combinations of move/work choices)
        candidates = []

        # Candidate 1: The heuristic's best choice
        candidates.append(self.heuristic_fallback.act(node.state))

        # Candidate 2: Move randomly
        random_worker_actions = {}
        for worker in node.state.farm.workers:
            rand_dir = random.choice(["UP", "DOWN", "LEFT", "RIGHT"])
            random_worker_actions[worker.worker_id] = ("MOVE", rand_dir)
        candidates.append({"worker_actions": random_worker_actions, "farm_actions": []})

        # Candidate 3: Idle action
        candidates.append({"worker_actions": {}, "farm_actions": []})

        for act in candidates:
            try:
                next_state = step_world(node.state, act)
                node.children.append(
                    MCTSNode(state=next_state, parent=node, action=act)
                )
            except Exception:
                continue

    def _rollout(self, state: WorldState) -> float:
        """Performs a brief simulation rollout using greedy actions."""
        curr_state = state
        depth = 3  # short lookahead for efficiency (<100ms target)
        total_gold_gained = 0

        start_gold = state.farm.gold

        for _ in range(depth):
            act = self.heuristic_fallback.act(curr_state)
            curr_state = step_world(curr_state, act)

        total_gold_gained = curr_state.farm.gold - start_gold
        # Add basic heuristic value for inventory counts as well
        inv_value = sum(curr_state.farm.inventory.values()) * 50

        return float(total_gold_gained + inv_value)
