import argparse
import copy
import hashlib
import importlib.metadata
import json
import sys
import time
from pathlib import Path
from typing import Any

try:
    import kaggle_environments
except ImportError:
    print("Error: kaggle-environments not installed.", file=sys.stderr)
    sys.exit(1)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Validate Kaggriculture replay parity."
    )
    parser.add_argument(
        "--replay",
        action="append",
        required=True,
        help="Path to replay JSON",
    )
    parser.add_argument("--output", type=str, help="Output JSON results path")
    parser.add_argument("--force", action="store_true", help="Force overwrite output")
    return parser.parse_args()


class ReplayAgent:
    def __init__(self, seat: int, steps: list, turns_per_day: int):
        self.seat = seat
        self.steps = steps
        self.turns_per_day = turns_per_day
        self.call_count = 0

    def __call__(self, observation, configuration):
        if "day" not in observation or "hour" not in observation:
            raise ValueError("Missing clock fields 'day' or 'hour' in observation.")

        day = observation["day"]
        hour = observation["hour"]

        expected_turn_index = day * self.turns_per_day + hour

        if expected_turn_index != self.call_count:
            raise ValueError(
                f"Seat {self.seat}: Misalignment. Expected action index "
                f"{self.call_count}, but observation maps to turn index "
                f"{expected_turn_index} (day {day}, hour {hour})"
            )

        step_idx = expected_turn_index + 1
        if step_idx >= len(self.steps):
            raise ValueError(
                f"Seat {self.seat}: Extra call at turn index {expected_turn_index}, "
                f"but replay only has {len(self.steps)} steps."
            )

        seat_data = self.steps[step_idx][self.seat]
        recorded_action = seat_data.get("action")
        if not isinstance(recorded_action, dict):
            raise ValueError(
                f"Seat {self.seat}: action is not a valid action dictionary at "
                f"step {step_idx}."
            )

        self.call_count += 1

        return copy.deepcopy(recorded_action)


def compare_states(
    local_state: list[dict[str, Any]],
    recorded_rewards: list[float],
    recorded_statuses: list[str],
) -> bool:
    local_reward_0 = local_state[0]["reward"]
    local_reward_1 = local_state[1]["reward"]
    local_status_0 = local_state[0]["status"]
    local_status_1 = local_state[1]["status"]

    return (
        local_reward_0 == recorded_rewards[0]
        and local_reward_1 == recorded_rewards[1]
        and local_status_0 == recorded_statuses[0]
        and local_status_1 == recorded_statuses[1]
    )


def load_and_validate_replay(replay_path: Path) -> dict[str, Any]:
    with replay_path.open("rb") as f:
        content_bytes = f.read()
        sha256_hash = hashlib.sha256(content_bytes).hexdigest()
        replay = json.loads(content_bytes.decode("utf-8"))

    # Required structure validation
    if "info" not in replay:
        raise ValueError("Replay is missing 'info' block.")
    if "configuration" not in replay:
        raise ValueError("Replay is missing 'configuration' block.")
    if "steps" not in replay:
        raise ValueError("Replay is missing 'steps' block.")

    info = replay["info"]
    configuration = replay["configuration"]
    steps = replay["steps"]

    module_version = replay.get("module_version") or info.get("module_version")
    if module_version != "1.32.7":
        raise ValueError(
            f"Replay module_version {module_version} differs from required 1.32.7"
        )

    try:
        engine_version = importlib.metadata.version("kaggle-environments")
    except importlib.metadata.PackageNotFoundError:
        try:
            engine_version = importlib.metadata.version("kaggle_environments")
        except importlib.metadata.PackageNotFoundError:
            engine_version = None

    if engine_version != "1.32.7":
        raise ValueError(
            f"Installed kaggle_environments version {engine_version} differs "
            f"from required 1.32.7"
        )

    seed = info.get("seed")
    if seed is None or not isinstance(seed, int):
        raise ValueError("Replay must have a non-null integer info.seed.")

    config_seed = configuration.get("seed")
    if config_seed is not None and config_seed != seed:
        raise ValueError(
            f"Configuration seed {config_seed} differs from info.seed {seed}."
        )
    elif config_seed is None:
        configuration["seed"] = seed

    if "episodeSteps" not in configuration:
        raise ValueError("configuration.episodeSteps is required.")
    episode_steps = configuration["episodeSteps"]

    if "turnsPerDay" not in configuration:
        raise ValueError("configuration.turnsPerDay is required.")
    turns_per_day = configuration["turnsPerDay"]
    if not isinstance(turns_per_day, int) or turns_per_day <= 0:
        raise ValueError("configuration.turnsPerDay must be a positive integer.")

    if len(steps) != episode_steps:
        raise ValueError(
            f"len(steps) ({len(steps)}) != configuration.episodeSteps ({episode_steps})"
        )

    if len(steps) < 2:
        raise ValueError(
            "Replay must have at least initial and terminal rows (len(steps) >= 2)."
        )

    team_identities = info.get("TeamNames")
    if (
        not isinstance(team_identities, list)
        or len(team_identities) != 2
        or not all(isinstance(name, str) for name in team_identities)
    ):
        raise ValueError("info.TeamNames must be a list of exactly two strings.")

    recorded_rewards = replay.get("rewards")
    recorded_statuses = replay.get("statuses")

    if (
        not recorded_rewards
        or len(recorded_rewards) != 2
        or not all(isinstance(r, (int, float)) for r in recorded_rewards)
    ):
        raise ValueError("Replay must have exactly two numeric recorded rewards.")
    if not recorded_statuses or len(recorded_statuses) != 2:
        raise ValueError("Replay must have exactly two recorded statuses.")

    if recorded_statuses[0] != "DONE" or recorded_statuses[1] != "DONE":
        raise ValueError("Replay must have both recorded statuses to be DONE.")

    for idx, step in enumerate(steps):
        if len(step) != 2:
            raise ValueError(
                f"Step {idx} does not have exactly two seats. Has {len(step)}."
            )

        if idx > 0:
            for seat_idx in range(2):
                action = step[seat_idx].get("action")
                if action is None or not isinstance(action, dict):
                    raise ValueError(
                        f"Step {idx} seat {seat_idx} missing valid action dictionary."
                    )
                if not all(k in action for k in ("farmer", "hands", "market")):
                    raise ValueError(
                        f"Step {idx} seat {seat_idx} action is missing required keys."
                    )

    terminal_step = steps[-1]
    if (
        terminal_step[0].get("reward") != recorded_rewards[0]
        or terminal_step[1].get("reward") != recorded_rewards[1]
    ):
        raise ValueError(
            "Terminal step rewards do not match top-level recorded rewards"
        )
    if (
        terminal_step[0].get("status") != recorded_statuses[0]
        or terminal_step[1].get("status") != recorded_statuses[1]
    ):
        raise ValueError(
            "Terminal step statuses do not match top-level recorded statuses"
        )

    return {
        "replay": replay,
        "sha256_hash": sha256_hash,
        "engine_version": engine_version,
        "seed": seed,
        "episode_steps": episode_steps,
        "turns_per_day": turns_per_day,
        "team_identities": team_identities,
        "recorded_rewards": recorded_rewards,
        "recorded_statuses": recorded_statuses,
        "episode_id": info.get("EpisodeId", "Unknown"),
    }


def validate_replay(replay_path: Path):
    start_time = time.perf_counter()

    metadata = load_and_validate_replay(replay_path)

    replay = metadata["replay"]
    steps = replay["steps"]
    configuration = replay["configuration"]

    env = kaggle_environments.make("kaggriculture", configuration=configuration)

    agent0 = ReplayAgent(0, steps, metadata["turns_per_day"])
    agent1 = ReplayAgent(1, steps, metadata["turns_per_day"])

    env.run([agent0, agent1])

    final_state = env.steps[-1]

    local_status_0 = final_state[0]["status"]
    local_status_1 = final_state[1]["status"]
    local_reward_0 = final_state[0]["reward"]
    local_reward_1 = final_state[1]["reward"]

    if local_status_0 != "DONE" or local_status_1 != "DONE":
        raise ValueError(
            f"Local episode did not complete successfully. "
            f"Statuses: {local_status_0}, {local_status_1}"
        )

    exact_parity = compare_states(
        final_state, metadata["recorded_rewards"], metadata["recorded_statuses"]
    )

    if not exact_parity:
        raise ValueError(
            f"Parity mismatch! Local rewards: [{local_reward_0}, {local_reward_1}], "
            f"Recorded: {metadata['recorded_rewards']}. "
            f"Local statuses: [{local_status_0}, {local_status_1}], "
            f"Recorded: {metadata['recorded_statuses']}"
        )

    if agent0.call_count != len(steps) - 1 or agent1.call_count != len(steps) - 1:
        raise ValueError(
            f"Missing calls! Replay had {len(steps) - 1} actions, "
            f"agent0 called {agent0.call_count}, agent1 called {agent1.call_count}"
        )

    runtime = time.perf_counter() - start_time

    return {
        "episode_id": metadata["episode_id"],
        "seed": metadata["seed"],
        "team_identities": metadata["team_identities"],
        "sha256": metadata["sha256_hash"],
        "engine_version": metadata["engine_version"],
        "recorded_rewards": metadata["recorded_rewards"],
        "local_rewards": [local_reward_0, local_reward_1],
        "recorded_statuses": metadata["recorded_statuses"],
        "local_statuses": [local_status_0, local_status_1],
        "action_counts": [agent0.call_count, agent1.call_count],
        "exact_parity": exact_parity,
        "runtime_seconds": runtime,
    }


def main():
    args = parse_args()

    if args.output:
        out_path = Path(args.output)
        if out_path.exists() and not args.force:
            print(
                f"Error: Output file {args.output} exists. Use --force to overwrite.",
                file=sys.stderr,
            )
            sys.exit(1)

    results = []
    has_error = False

    for replay_file in args.replay:
        print(f"Validating {replay_file}...", file=sys.stderr)
        try:
            res = validate_replay(Path(replay_file))
            results.append(res)
            print(f"  OK! exact_parity={res['exact_parity']}", file=sys.stderr)
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            has_error = True

    if args.output and results:
        with Path(args.output).open("w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    if has_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
