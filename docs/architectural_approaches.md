# Kaggriculture Simulation: Architectural Approaches

This document outlines the three candidate architectural approaches for the Kaggle Kaggriculture simulation competition. Since Kaggriculture is a 720-turn (30 days, 24 steps/day) multi-agent dynamic market farming simulation with deterministic state transitions, the simulator design directly dictates our search/planning throughput and engineering velocity.

---

## Comparative Matrix

| Criterion | 1. Vectorized JAX/NumPy | 2. Object-Oriented (OOP) | 3. Hybrid Dataclass (Recommended) |
| :--- | :--- | :--- | :--- |
| **Rollout Throughput** | Extremely High (10M+ steps/sec) | Low (< 50,000 steps/sec) | High (500,000+ steps/sec) |
| **Search/MCTS Friendliness** | Excellent (Parallel batch rollouts) | Poor (Requires expensive deepcopy) | Excellent (Cheap dataclass copying) |
| **Implementation Complexity**| Extreme (Requires flat arrays) | Low (Natural mapping) | Moderate (Clean pure transitions) |
| **Type Safety & IDE Support** | Poor (Opaque multi-dim arrays) | Excellent (Class attributes) | Excellent (Type-hinted fields) |
| **Kaggle JSON Map Ease** | Hard (Must array-encode state) | Easy (Direct JSON parser) | Easy (Dataclass parse/serialize) |

---

## 1. Vectorized JAX/NumPy Pure-Functional State-Space

### Concept
The complete game state is flattened into single- or multi-dimensional numerical arrays. Transitions are implemented using vectorized operations (using `numpy` or `jax.numpy`). The environment step is a pure function:

$$\text{step}(S_t, A_t) \to S_{t+1}$$

### Code Sketch
```python
import jax.numpy as jnp
from typing import NamedTuple

class JaxEnvState(NamedTuple):
    # Crops: shape (num_agents, grid_size, 3) -> [crop_type, growth_stage, water_level]
    crop_grid: jnp.ndarray
    # Livestock: shape (num_agents, 2) -> [feed_level, age]
    livestock: jnp.ndarray
    # Market Index: shape (num_crops,) -> prices
    market_index: jnp.ndarray
    step_count: jnp.ndarray

def step(state: JaxEnvState, action: jnp.ndarray) -> JaxEnvState:
    # Deterministic vector calculations for growth, watering, feeding, and market index
    next_crop_grid = jnp.where(action == WATER_ACTION, state.crop_grid + 1.0, state.crop_grid)
    ...
    return JaxEnvState(crop_grid=next_crop_grid, ...)
```

---

## 2. Standard Object-Oriented (OOP) Gym-Like Environment

### Concept
The classic reinforcement learning environment pattern. All entities are represented as stateful class instances that reference and mutate each other.

### Code Sketch
```python
class Crop:
    def __init__(self, crop_type: str):
        self.crop_type = crop_type
        self.water_level = 10
        self.growth_stage = 0

    def grow(self, water_applied: int):
        self.water_level = max(0, self.water_level - 1 + water_applied)
        if self.water_level > 5:
            self.growth_stage += 1

class KaggricultureEnv:
    def __init__(self):
        self.crops = [Crop("WHEAT") for _ in range(9)]
        self.market_prices = {"WHEAT": 10.0}

    def step(self, actions: list) -> tuple:
        for action in actions:
            # Mutate state directly
            ...
        return self.get_obs(), self.get_reward()
```

---

## 3. Hybrid Dataclass & Pure-Transition Simulator (Recommended)

### Concept
We store state in frozen, lightweight, typed Python `dataclasses`. We implement state transitions as pure, decoupled functions that return new state instances. 

### Code Sketch
```python
from dataclasses import dataclass, replace
from typing import Tuple

@dataclass(frozen=True, slots=True)
class CropState:
    crop_type: str
    water_level: int
    growth_stage: int

@dataclass(frozen=True, slots=True)
class FarmState:
    crops: Tuple[CropState, ...]
    livestock_feed: int
    market_prices: Tuple[float, ...]
    step_count: int

def transition_crop(crop: CropState, action: str) -> CropState:
    new_water = max(0, crop.water_level - 1 + (1 if action == "WATER" else 0))
    new_stage = crop.growth_stage + 1 if new_water > 5 else crop.growth_stage
    return replace(crop, water_level=new_water, growth_stage=new_stage)

def transition_state(state: FarmState, joint_actions: dict) -> FarmState:
    new_crops = tuple(transition_crop(c, joint_actions.get(f"crop_{i}")) for i, c in enumerate(state.crops))
    ...
    return replace(state, crops=new_crops, step_count=state.step_count + 1)
```

---

## 🔍 Path Deep Dives & Implementation Blueprints

Here is the exhaustive engineering blueprint for how to approach, design, and implement each of the three paths.

---

### Deep Dive: Path 1 — Vectorized JAX/NumPy Pure-Functional State-Space

#### 1. State Mapping and Memory Layout
To execute JAX’s JIT compiler (`@jax.jit`), all data structures must be of static size and flat types. Dynamic list operations or dictionary lookups are forbidden inside the step function.
- **State Tensors:** We maintain a single continuous block of memory (or a `NamedTuple` of static arrays) representing the state.
  - `crop_tensor`: Shape `(num_agents, num_grid_plots, 4)` containing floats: `[crop_type_id, growth_stage, water_level, age]`.
  - `livestock_tensor`: Shape `(num_agents, num_animals, 3)` containing floats: `[animal_type_id, hunger, yield_counter]`.
  - `market_orders`: Shape `(num_agents, max_orders_per_agent, 4)` containing: `[is_active, item_id, price, quantity]`.
  - `meta_tensor`: Shape `(3,)` for `[step_count, wind_direction, weather_multiplier]`.

#### 2. Combinatorial Action Vectorization
Because agents can perform multiple actions per turn (e.g., watering plot 2, planting plot 4, feeding cow 0, and placing 2 buy orders), we must represent actions as a composite array of integers.
- **Action Interface:** Represented as an integer vector of fixed shape, e.g., shape `(num_grid_plots + num_animals + max_market_actions, )`.
- **Masking:** To handle invalid actions (e.g., watering an empty plot, feeding a dead animal), we must pass an accompanying `action_mask` tensor. Inside the transition function, we multiply actions by the valid action mask:
  $$\text{effective\_action} = \text{action} \odot \text{action\_mask}$$

#### 3. Execution & Optimization Engine
We compile the step transition function and reward evaluation with JAX:
```python
import jax

@jax.jit
def batched_step(states: JaxEnvState, actions: jnp.ndarray, masks: jnp.ndarray) -> JaxEnvState:
    # Vectorized execution across a batch of states for MCTS lookahead
    return jax.vmap(step)(states, actions, masks)
```
- **How to build MCTS with this:** You would implement a fully vectorized Monte Carlo Tree Search. Instead of a pointer-based tree, the search tree is stored as pre-allocated arrays of parents, children, visit counts, and action values.
- **Testing Parity:** Verify by matching JAX array updates against a single-step reference calculation.

---

### Deep Dive: Path 2 — Standard Object-Oriented (OOP) Gym-Like Environment

#### 1. Memory and Object Structure
State is scattered across highly readable objects that contain domain logic:
```python
class FarmWorld:
    def __init__(self):
        self.agents = {}
        self.order_book = OrderBook()
        self.turn = 0
```
- **Instantiation:** Creating instances of these classes is trivial. Mapping the Kaggle raw environment JSON to this structure requires writing a parser that instantiates `Crop`, `Livestock`, and `Order` objects and sets their attributes directly.

#### 2. Search Optimization (Undo/Redo Logs over Deepcopy)
Since `copy.deepcopy()` is too slow, to run MCTS or lookahead search with this path, we must implement an **Undo-Log pattern** (similar to chess or database transaction logs).
- **Action Commits:** Every state change registers a reverse transaction. For example, when calling `crop.grow()`, we append an record to a step-local list:
  `self.undo_log.append(lambda: setattr(crop, "growth_stage", crop.growth_stage - 1))`
- **Backtracking:** To go up a search branch, we pop transactions and apply them in reverse:
  ```python
  def backtrack(self):
      while self.undo_log:
          undo_fn = self.undo_log.pop()
          undo_fn()
  ```
- **Complexity:** This pattern is highly error-prone. If even one method fails to log an undo operation, the entire search space becomes corrupted, making search results garbage.

#### 3. Verification & Validation
- **Testing:** Standard pytest suites that call environment steps and asserts state assertions (e.g., `assert crop.water_level >= 0`).

---

### Deep Dive: Path 3 — Hybrid Dataclass & Pure-Transition Simulator (Recommended)

#### 1. Dataclass Structure and State Compilation
We represent the environment state using frozen Python dataclasses. This ensures the states are immutable and hashing/lookup operations are fast.

```python
from dataclasses import dataclass, replace
from typing import Tuple, Dict, NamedTuple

@dataclass(frozen=True, slots=True)
class CropState:
    id: int
    crop_type: int        # Integer mapped (e.g., 1=WHEAT, 2=CORN)
    growth_stage: int     # 0 to 4
    water_level: int      # 0 to 100
    age: int

@dataclass(frozen=True, slots=True)
class AgentState:
    agent_id: str
    balance: float
    inventory: NamedTuple # Flat type-hinted quantities
    crops: Tuple[CropState, ...]
```
- **Memory Optimization:** Utilizing `slots=True` significantly optimizes attribute access and memory allocation by completely avoiding the overhead of `__dict__`. This allows thousands of states to reside in memory simultaneously.

#### 2. Functional State Transition Logic
All transitions are pure functions. To step the state, we pass the immutable state container and return an updated state using `dataclasses.replace()`.

```python
def step_world(state: WorldState, joint_actions: Dict[str, Action]) -> WorldState:
    # 1. Update Crop States
    updated_agents = {}
    for agent_id, agent in state.agents.items():
        agent_action = joint_actions.get(agent_id)
        next_crops = tuple(
            step_crop(crop, agent_action.watering[i]) 
            for i, crop in enumerate(agent.crops)
        )
        updated_agents[agent_id] = replace(agent, crops=next_crops)
        
    # 2. Execute Deterministic Market Matcher
    next_market = match_market_orders(state.market, joint_actions)
    
    # 3. Compile next World State
    return replace(state, agents=updated_agents, market=next_market, step=state.step + 1)
```

#### 3. Monte Carlo Tree Search Optimization
With pure-functional updates, cloning a state is instant and safe.
- **Tree Node Formulation:**
  ```python
  class MCTSNode:
      def __init__(self, state: WorldState, parent=None):
          self.state = state
          self.parent = parent
          self.children = {}
          self.visit_count = 0
          self.total_value = 0.0
  ```
- **Expansion Phase:** To expand a node, we simply call `step_world(self.state, action)`. Since `WorldState` is frozen, we don't need to perform any deep copying. Different child branches will never leak mutations to each other.
- **Parallelization:** We can run rollouts across multiple worker threads using Python’s `multiprocessing` or `concurrent.futures`, as there are no thread-safety issues with immutable state containers.

#### 4. Automated Testing and Integrity Verification
- **State Invariance Tests:** Write unit tests that confirm that calling `step_world` on a state does *not* mutate the original state reference.
- **Equivalence Tests:** Confirm that serializing a state to JSON (for communication with Kaggle) and parsing it back yields exactly the same `WorldState` attributes.
