"""Kaggriculture Head-to-Head Agent Tournament Runner."""

import sys
import time
from pathlib import Path

from kaggle_environments import make

# Add project root and C++ source directory to Python path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(PROJECT_ROOT))
sys.path.append(str(PROJECT_ROOT / "competitors" / "six_day_agent_source"))

from agent_main import agent as six_day_agent_fn
from agent_main_v2 import agent as six_day_agent_fn_v2

from src.agents.base import BaseAgent
from src.agents.escalation import EscalationAgent
from src.agents.heuristic import HeuristicAgent
from src.agents.mcts import MCTSAgent
from src.env.parser import parse_world_state

ITEM_NAME_MAP = {
    "Wheat": "WHEAT",
    "Carrot": "CARROT",
    "Tomato": "TOMATO",
    "Strawberry": "STRAWBERRY",
    "Strawberries": "STRAWBERRY",
    "Melon": "MELON",
    "Melons": "MELON",
    "Egg": "EGG",
    "Eggs": "EGG",
    "Milk": "MILK",
    "Wool": "WOOL",
    "Fertilizer": "FERTILIZER",
    "Goose": "GOOSE",
    "Geese": "GOOSE",
    "Cow": "COW",
    "Cows": "COW",
    "Sheep": "SHEEP",
}


def translate_worker_action(act, worker_x, worker_y):
    if not act:
        return ["PASS"]

    act_type = act[0]

    # 1. Translate movements directly
    if act_type == "MOVE":
        direction = act[1]
        if direction in {"UP", "NORTH"}:
            return ["NORTH"]
        elif direction in {"DOWN", "SOUTH"}:
            return ["SOUTH"]
        elif direction in {"LEFT", "WEST"}:
            return ["WEST"]
        elif direction in {"RIGHT", "EAST"}:
            return ["EAST"]
        return ["PASS"]

    # 2. Coordinate-based actions: TILE, PLANT, WATER, HARVEST, FEED, etc.
    if act_type in {"TILE", "PLANT", "WATER", "HARVEST", "FEED"}:
        tx, ty = act[1], act[2]

        # Check if the worker is standing on (tx, ty)
        if worker_x == tx and worker_y == ty:
            # Stand on it -> execute the interaction action!
            if act_type == "TILE":
                return ["DIG"]
            elif act_type == "WATER":
                return ["WATER"]
            elif act_type == "HARVEST":
                return ["HARVEST"]
            elif act_type == "FEED":
                return ["FEED"]
            elif act_type == "PLANT":
                crop = act[3]
                crop_upper = ITEM_NAME_MAP.get(crop, str(crop).upper())
                return ["PLANT", crop_upper]
        else:
            # Adjacent or distant -> must move towards (tx, ty)!
            if tx > worker_x:
                return ["EAST"]
            elif tx < worker_x:
                return ["WEST"]
            elif ty > worker_y:
                return ["SOUTH"]
            elif ty < worker_y:
                return ["NORTH"]
            return ["PASS"]

    # 3. Drop/Pickup commands
    if act_type == "DROP":
        return ["DROP"]
    elif act_type == "PICKUP":
        item = act[1]
        qty = act[2] if len(act) > 2 else 1
        item_upper = ITEM_NAME_MAP.get(item, str(item).upper())
        return ["PICKUP", item_upper, int(qty)]

    return ["PASS"]


def translate_farm_actions(farm_actions):
    translated = []
    for act in farm_actions:
        if isinstance(act, str):
            act_type = act
            args = []
        else:
            act_type = act[0]
            args = act[1:]

        if act_type == "HIRE_WORKER":
            translated.append(["HIRE"])
        elif act_type == "BUY_LAND":
            translated.append(["BUY_LAND"])
        elif act_type == "BUY_ANIMAL":
            animal = args[0]
            animal_upper = ITEM_NAME_MAP.get(animal, str(animal).upper())
            translated.append(["BUY_ANIMAL", animal_upper, 1])
        elif act_type == "BUY_SEED":
            crop = args[0]
            qty = args[1] if len(args) > 1 else 1
            crop_upper = ITEM_NAME_MAP.get(crop, str(crop).upper())
            translated.append(["BUY_SEED", crop_upper, int(qty)])
        elif act_type == "BUY_PRODUCT":
            product = args[0]
            qty = args[1] if len(args) > 1 else 1
            product_upper = ITEM_NAME_MAP.get(product, str(product).upper())
            translated.append(["BUY_PRODUCT", product_upper, int(qty)])
        elif act_type == "SELL":
            item = args[0]
            qty = args[1] if len(args) > 1 else 1
            item_upper = ITEM_NAME_MAP.get(item, str(item).upper())
            translated.append(["SELL", item_upper, int(qty)])
    return translated


def wrap_agent(agent_instance: BaseAgent):
    """Wraps our custom BaseAgent into a Kaggle-compatible callable agent."""

    def kaggle_agent_fn(obs, config):
        try:
            state = parse_world_state(obs)
            joint_actions = agent_instance.act(state)

            # Retrieve players and map positions
            # Worker 1 (Farmer)
            farmer_action_local = joint_actions.get("worker_actions", {}).get(1)
            farmer_worker_state = None
            for w in state.farm.workers:
                if w.worker_id == 1:
                    farmer_worker_state = w
                    break

            farmer_x = farmer_worker_state.x if farmer_worker_state else 4
            farmer_y = farmer_worker_state.y if farmer_worker_state else 4
            farmer_action = translate_worker_action(
                farmer_action_local, farmer_x, farmer_y
            )

            # Worker 2+ (Hired Hands)
            hands_actions = []
            for worker_id, act_local in sorted(
                joint_actions.get("worker_actions", {}).items()
            ):
                if worker_id > 1:
                    hand_worker_state = None
                    for w in state.farm.workers:
                        if w.worker_id == worker_id:
                            hand_worker_state = w
                            break
                    hand_x = hand_worker_state.x if hand_worker_state else 4
                    hand_y = hand_worker_state.y if hand_worker_state else 4
                    hands_actions.append(
                        translate_worker_action(act_local, hand_x, hand_y)
                    )

            market_actions_local = joint_actions.get("farm_actions", [])
            market_actions = translate_farm_actions(market_actions_local)

            return {
                "farmer": list(farmer_action),
                "hands": [list(h) for h in hands_actions],
                "market": market_actions,
            }
        except Exception as e:
            import traceback

            print(f"\n[AGENT EXCEPTION in {agent_instance.__class__.__name__}]: {e}")
            traceback.print_exc()
            return {"farmer": ["PASS"], "hands": [], "market": []}

    return kaggle_agent_fn


import importlib.util


def load_competitor_agent(name: str, filename: str):
    """Loads a compiled or extracted competitor agent from our notebooks directory."""
    path = PROJECT_ROOT / "competitors" / "notebooks" / filename

    # Temporarily append the module's parent directory to sys.path to resolve
    # local imports (e.g. multi-file agents)
    module_dir = str(path.parent)
    if module_dir not in sys.path:
        sys.path.insert(0, module_dir)

    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.agent


def get_agent_callable(agent_name: str):
    """Returns a fresh callable for the requested agent."""
    if agent_name == "Heuristic":
        return wrap_agent(HeuristicAgent())
    elif agent_name == "Heuristic v2 (Escalation)":
        return wrap_agent(EscalationAgent())
    elif agent_name == "MCTS":
        # Create a fresh MCTS instance to avoid state leakage across matches
        return wrap_agent(MCTSAgent(num_simulations=20))
    elif agent_name == "Six-Day Fieldbook":
        # The C++ agent is stateless on the Python side
        return six_day_agent_fn
    elif agent_name == "Six-Day Fieldbook v2":
        return six_day_agent_fn_v2
    elif agent_name == "Three-Day Shop Router (Original)":
        return load_competitor_agent("three_day_agent", "three_day_main.py")
    elif agent_name == "Three-Day Shop Router v2":
        return load_competitor_agent(
            "three_day_optimized_agent", "three_day_optimized.py"
        )
    elif agent_name == "Thomas 93.8% Router":
        return load_competitor_agent("thomas_agent", "thomas_router.py")
    elif agent_name == "Lynn Mathematical Router":
        return load_competitor_agent("lynn_agent", "lynn_router.py")
    elif agent_name == "EXP-173 Super-Fusion Router":
        return load_competitor_agent("fusion_agent", "fusion_router.py")
    elif agent_name == "EXP-173 v36 Fusion Router":
        return load_competitor_agent("v36_fusion_agent", "v36_fusion_router.py")
    elif agent_name == "EXP-173 v45 Fusion Router":
        return load_competitor_agent("v45_fusion_agent", "v45_fusion_router.py")
    elif agent_name == "Guru Master Engine V3":
        return load_competitor_agent("guru_v3_agent", "guru_v3_router.py")
    elif agent_name == "Reyhan Dynamic Route Agent":
        return load_competitor_agent("reyhan_agent", "reyhan_dynamic_router.py")
    elif agent_name == "Jaxa 2802 Elo Router":
        return load_competitor_agent("jaxa_agent", "jaxa_2802_router/main.py")
    elif agent_name == "Jaxa V48 Clear-Queue":
        return load_competitor_agent("jaxa_v48_agent", "v48_main.py")
    elif agent_name == "Tetsu Market-Smart Router":
        return load_competitor_agent("tetsu_agent", "tetsu_smart_router/main.py")
    elif agent_name == "Kaito v21.1 Router":
        return load_competitor_agent("kaito_v21_agent", "kaito_v21_router.py")
    elif agent_name == "Kaito v27":
        return load_competitor_agent("v27_agent", "v27_main.py")
    elif agent_name == "Boatlee v14":
        return load_competitor_agent("v14_agent", "v14_main.py")
    elif agent_name == "Bruceqdu High-Score":
        return load_competitor_agent("bruceqdu_agent", "bruceqdu_main.py")
    elif agent_name == "random":
        return "random"
    else:
        raise ValueError(f"Unknown agent name: {agent_name}")


def run_single_match(seed: int, agent_0_name: str, agent_1_name: str, turns: int = 720):
    """Runs a single head-to-head match between two fresh agent callables on a seed."""
    start_time = time.time()
    try:
        agent_0_fn = get_agent_callable(agent_0_name)
        agent_1_fn = get_agent_callable(agent_1_name)

        env = make("kaggriculture", configuration={"episodeSteps": turns, "seed": seed})
        env.run([agent_0_fn, agent_1_fn])

        gold_0 = float(env.state[0].reward if env.state[0].reward is not None else 0.0)
        gold_1 = float(env.state[1].reward if env.state[1].reward is not None else 0.0)

        duration = time.time() - start_time

        return {
            "seed": seed,
            "agent_0": agent_0_name,
            "agent_1": agent_1_name,
            "gold_0": gold_0,
            "gold_1": gold_1,
            "winner": (
                agent_0_name
                if gold_0 > gold_1
                else (agent_1_name if gold_1 > gold_0 else "Tie")
            ),
            "duration": duration,
            "success": True,
            "error": None,
        }
    except Exception as e:
        import traceback

        return {
            "seed": seed,
            "agent_0": agent_0_name,
            "agent_1": agent_1_name,
            "gold_0": 0.0,
            "gold_1": 0.0,
            "winner": "Error",
            "duration": time.time() - start_time,
            "success": False,
            "error": f"{str(e)}\n{traceback.format_exc()}",
        }


def main():
    print("=" * 70)
    print("      KAGGRICULTURE SYSTEMATIC HEAD-TO-HEAD AGENT TOURNAMENT")
    print("=" * 70)

    # 1. Define participants and seeds
    agents = [
        "Six-Day Fieldbook v2",
        "Thomas 93.8% Router",
        "Lynn Mathematical Router",
        "EXP-173 Super-Fusion Router",
        "EXP-173 v36 Fusion Router",
        "EXP-173 v45 Fusion Router",
        "Guru Master Engine V3",
        "Reyhan Dynamic Route Agent",
        "Jaxa 2802 Elo Router",
        "Tetsu Market-Smart Router",
        "Heuristic v2 (Escalation)",
    ]
    seeds = [42]

    print(f"Participants: {', '.join(agents)}")
    print(f"Seeds:        {seeds}")
    print(
        f"Total Matches: {len(agents) * (len(agents) - 1) * len(seeds)} "
        "(each pair, both seat configurations)"
    )
    print("-" * 70)

    # Generate all match tasks (each pair of agents, both seats, each seed)
    match_tasks = []
    for seed in seeds:
        for i, a0 in enumerate(agents):
            for j, a1 in enumerate(agents):
                if i != j:
                    match_tasks.append((seed, a0, a1))

    # 2. Run matches sequentially to avoid sys.stdout/sys.stderr redirection
    # collisions in kaggle_environments
    results = []
    print("Running tournament sequentially to prevent standard stream conflicts...")

    start_tournament = time.time()
    for index, (seed, a0, a1) in enumerate(match_tasks, 1):
        print(
            f"[{index}/{len(match_tasks)}] Running: Seed {seed} | {a0} vs {a1}...",
            end="",
            flush=True,
        )
        res = run_single_match(seed, a0, a1)
        results.append(res)
        if res["success"]:
            winner_str = f"Winner: {res['winner']}" if res["winner"] != "Tie" else "Tie"
            print(
                f"\r[{index}/{len(match_tasks)}] Match Seed {seed:5d} | "
                f"{a0:18s} vs {a1:18s} | "
                f"Gold: {res['gold_0']:10,.0f} vs {res['gold_1']:10,.0f} | "
                f"{winner_str} ({res['duration']:.1f}s)"
            )
        else:
            print(
                f"\r[{index}/{len(match_tasks)}] Match Seed {seed:5d} | "
                f"{a0:18s} vs {a1:18s} | "
                f"FAILED: {res['error'].splitlines()[0]}"
            )

    duration_total = time.time() - start_tournament
    print("-" * 70)
    print(f"All matches completed in {duration_total:.2f} seconds.")
    print("=" * 70)

    # 3. Aggregate stats
    # Initialize metrics dict
    stats = {
        agent: {
            "matches": 0,
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "gold_scored": 0.0,
            "gold_conceded": 0.0,
            "errors": 0,
        }
        for agent in agents
    }

    # Record matchup matrix
    matrix = {
        a0: {a1: {"wins": 0, "losses": 0, "ties": 0} for a1 in agents if a0 != a1}
        for a0 in agents
    }

    for res in results:
        if not res["success"]:
            stats[res["agent_0"]]["errors"] += 1
            stats[res["agent_1"]]["errors"] += 1
            continue

        a0, a1 = res["agent_0"], res["agent_1"]
        g0, g1 = res["gold_0"], res["gold_1"]

        # Track global stats
        stats[a0]["matches"] += 1
        stats[a1]["matches"] += 1
        stats[a0]["gold_scored"] += g0
        stats[a0]["gold_conceded"] += g1
        stats[a1]["gold_scored"] += g1
        stats[a1]["gold_conceded"] += g0

        if res["winner"] == a0:
            stats[a0]["wins"] += 1
            stats[a1]["losses"] += 1
            matrix[a0][a1]["wins"] += 1
        elif res["winner"] == a1:
            stats[a1]["wins"] += 1
            stats[a0]["losses"] += 1
            matrix[a0][a1]["losses"] += 1
        else:
            stats[a0]["ties"] += 1
            stats[a1]["ties"] += 1
            matrix[a0][a1]["ties"] += 1

    # 4. Display Standings
    print(" " * 20 + "TOURNAMENT FINAL STANDINGS")
    print("-" * 70)
    print(
        f"{'Agent':20s} | {'Wins':4s} | {'Losses':6s} | {'Ties':4s} | {'Win %':6s} | "
        f"{'Avg Gold':12s} | {'Avg Margin':10s}"
    )
    print("-" * 70)

    for agent in sorted(
        agents,
        key=lambda x: (
            stats[x]["wins"] / max(1, stats[x]["matches"]),
            stats[x]["gold_scored"] / max(1, stats[x]["matches"]),
        ),
        reverse=True,
    ):
        s = stats[agent]
        matches = max(1, s["matches"])
        win_pct = (s["wins"] / matches) * 100
        avg_gold = s["gold_scored"] / matches
        avg_margin = (s["gold_scored"] - s["gold_conceded"]) / matches

        print(
            f"{agent:20s} | {s['wins']:4d} | {s['losses']:6d} | "
            f"{s['ties']:4d} | {win_pct:5.1f}% | "
            f"{avg_gold:12,.0f} | {avg_margin:+10,.0f}"
        )
    print("-" * 70)

    # 5. Display Head-to-Head Matrix
    print("\n" + " " * 20 + "HEAD-TO-HEAD MATCHUP MATRIX")
    print("-" * 70)
    print(
        f"{'Agent (Row) vs Opp (Col)':25s} | " + " | ".join(f"{a:18s}" for a in agents)
    )
    print("-" * 70)
    for a0 in agents:
        row_cells = []
        for a1 in agents:
            if a0 == a1:
                row_cells.append(f"{'-':^18s}")
            else:
                m = matrix[a0][a1]
                total = m["wins"] + m["losses"] + m["ties"]
                win_rate = (m["wins"] / total * 100) if total > 0 else 0
                cell = f"{m['wins']}W-{m['losses']}L-{m['ties']}T ({win_rate:.0f}%)"
                row_cells.append(f"{cell:18s}")
        print(f"{a0:25s} | " + " | ".join(row_cells))
    print("-" * 70)


if __name__ == "__main__":
    main()
