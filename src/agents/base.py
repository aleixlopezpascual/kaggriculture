"""Kaggriculture abstract base agent interface."""

from abc import ABC, abstractmethod

from src.env.state import WorldState


class BaseAgent(ABC):
    """Abstract base agent for Kaggriculture decisions."""

    @abstractmethod
    def act(self, state: WorldState) -> dict:
        """Determines actions for all workers and the farm.

        Args:
            state: The current WorldState snapshot.

        Returns:
            dict: Joint actions structure, containing:
                  {
                      "worker_actions": {worker_id: ActionTuple},
                      "farm_actions": [FarmActionsList]
                  }
        """
