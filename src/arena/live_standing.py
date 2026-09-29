#!/usr/bin/env python3
"""Read our true live standing from Kaggle's public endpoints.

Phase 12 replaced the old Elo tracker, which polled a submission-list route
that lags badly: it reported Meta V4 at 1396 while the public leaderboard
already had it at 1964. These endpoints need no API token and no auth:

  * LeaderboardService/GetLeaderboard -- the full ranked board, so a raw
    rating becomes an actual rank out of the field.
  * EpisodeService/ListEpisodes -- per-submission episodes carrying both
    players' rewards plus their updatedScore, which gives a real win/loss
    record and the rating walk.

A third route, https://www.kaggleusercontent.com/episodes/{id}.json, returns
the full 720-step replay (~32 MB, requires following redirects). It is not used
here but is the route to opponent trajectories.

Usage:  python src/arena/live_standing.py [submission_id ...]
"""

from __future__ import annotations

import json
import statistics
import subprocess
import sys

COMPETITION_ID = 147_734
LEADERBOARD = (
    "https://www.kaggle.com/api/i/competitions.LeaderboardService/GetLeaderboard"
)
EPISODES = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"

# Our submissions, newest first. Only the latest two are active.
OURS = {
    56_670_729: "META_V4",
    56_668_154: "V3.1",
    56_531_885: "Prvsiyan Moon",
    56_490_949: "Shepherd Sovereign",
}


def post(url: str, payload: dict) -> dict:
    raw = subprocess.run(
        [
            "curl",
            "-s",
            "--max-time",
            "90",
            "-H",
            "Content-Type: application/json",
            "-X",
            "POST",
            "-d",
            json.dumps(payload),
            url,
        ],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(raw)


def leaderboard() -> list[dict]:
    return post(LEADERBOARD, {"competitionId": COMPETITION_ID})["publicLeaderboard"]


def episode_report(submission_id: int) -> dict:
    eps = post(EPISODES, {"submissionId": submission_id}).get("episodes", [])
    done = [e for e in eps if e.get("state") == "COMPLETED" and e.get("endTime")]
    done.sort(key=lambda e: e["endTime"])

    wins = losses = ties = 0
    mine: list[float] = []
    theirs: list[float] = []
    walk: list[float] = []

    for e in done:
        me = [a for a in e["agents"] if a.get("submissionId") == submission_id]
        op = [a for a in e["agents"] if a.get("submissionId") != submission_id]
        if not me or not op:
            continue
        me, op = me[0], op[0]
        if me.get("updatedScore") is not None:
            walk.append(me["updatedScore"])
        if me.get("reward") is None or op.get("reward") is None:
            continue
        mine.append(me["reward"])
        theirs.append(op["reward"])
        if me["reward"] > op["reward"]:
            wins += 1
        elif me["reward"] < op["reward"]:
            losses += 1
        else:
            ties += 1

    return {
        "episodes": len(done),
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "median_gold": statistics.median(mine) if mine else None,
        "median_opponent_gold": statistics.median(theirs) if theirs else None,
        "walk": walk,
    }


def main() -> None:
    targets = [int(a) for a in sys.argv[1:]] or list(OURS)

    board = leaderboard()
    rank_of = {
        r["submissionId"]: (i, r.get("displayScore"))
        for i, r in enumerate(board, 1)
        if r.get("submissionId")
    }
    print(f"field size {len(board)}   leader {board[0].get('displayScore')}")

    for sid in targets:
        name = OURS.get(sid, str(sid))
        rank, score = rank_of.get(sid, (None, None))
        where = f"rank {rank}/{len(board)}  score {score}" if rank else "not ranked"
        print(f"\n{name}  (sub {sid})\n  {where}")

        rep = episode_report(sid)
        played = rep["wins"] + rep["losses"] + rep["ties"]
        if played:
            print(
                f"  record W{rep['wins']} L{rep['losses']} T{rep['ties']}"
                f"  -> {rep['wins'] / played * 100:.0f}% over {played} episodes"
            )
            print(
                f"  gold median ${rep['median_gold']:,.0f}"
                f"  vs opponents ${rep['median_opponent_gold']:,.0f}"
            )
        if rep["walk"]:
            tail = " -> ".join(f"{s:.0f}" for s in rep["walk"][-8:])
            print(f"  rating walk {tail}")
            if len(rep["walk"]) >= 4:
                recent = rep["walk"][-4:]
                drift = (recent[-1] - recent[0]) / 3
                verdict = "still climbing" if drift > 5 else "flattening"
                print(f"  drift {drift:+.0f}/episode -> {verdict}")


if __name__ == "__main__":
    main()
