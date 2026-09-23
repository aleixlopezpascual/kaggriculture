import subprocess
import json
import time
import os
import sys

TARGET_A = 56467787  # Jaxa 2802 Variant B (H24, L2, U10)
TARGET_B = 56490949  # Shepherd Sovereign: Herd-Safe Sovereign Engine (Sept 23 SOTA)

LOG_WORKSPACE = "docs/superpowers/plans/kaggriculture_monitor.log"
LOG_PRIVATE = "/Users/aleix.lopez/.gemini/tmp/kaggriculture/memory/monitor.log"


def log_message(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}\n"
    print(formatted.strip())
    # Log to workspace
    os.makedirs(os.path.dirname(LOG_WORKSPACE), exist_ok=True)
    with open(LOG_WORKSPACE, "a", encoding="utf-8") as f:
        f.write(formatted)
    # Log to private memory folder
    os.makedirs(os.path.dirname(LOG_PRIVATE), exist_ok=True)
    try:
        with open(LOG_PRIVATE, "a", encoding="utf-8") as f:
            f.write(formatted)
    except IOError:
        pass


def fetch_submissions():
    try:
        cmd = [
            "kaggle",
            "competitions",
            "submissions",
            "kaggriculture",
            "--format",
            "json",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(res.stdout)
    except Exception as e:
        log_message(f"Error fetching submissions: {e}")
        return None


def monitor_ab_loop(ref_a: int, ref_b: int):
    log_message(
        f"Starting Active Duel Monitor:\n"
        f"  - Jaxa Variant B: Ref {ref_a}\n"
        f"  - Shepherd Sovereign: Ref {ref_b}"
    )

    while True:
        subs = fetch_submissions()
        if not subs:
            log_message(
                "No submissions retrieved or query failed. Retrying in 15 minutes..."
            )
            time.sleep(900)
            continue

        sub_a = next((s for s in subs if s.get("ref") == ref_a), None)
        sub_b = next((s for s in subs if s.get("ref") == ref_b), None)

        score_a_str = sub_a.get("publicScore", "") if sub_a else "N/A"
        score_b_str = sub_b.get("publicScore", "") if sub_b else "N/A"
        status_a = sub_a.get("status", "NOT_FOUND") if sub_a else "NOT_FOUND"
        status_b = sub_b.get("status", "NOT_FOUND") if sub_b else "NOT_FOUND"

        diff_str = "N/A"
        if score_a_str and score_b_str:
            try:
                diff = float(score_b_str) - float(score_a_str)
                diff_str = f"{diff:+.1f}"
            except ValueError:
                pass

        log_message(
            f"[Live Matchmaking] "
            f"Jaxa B ({ref_a}): {status_a} (Elo: {score_a_str}) | "
            f"Shepherd Sovereign ({ref_b}): {status_b} (Elo: {score_b_str}) | "
            f"Diff (Shepherd - Jaxa): {diff_str}"
        )

        time.sleep(900)


if __name__ == "__main__":
    ref_a = TARGET_A
    ref_b = TARGET_B
    if len(sys.argv) >= 3:
        try:
            ref_a = int(sys.argv[1])
            ref_b = int(sys.argv[2])
        except ValueError:
            pass
    monitor_ab_loop(ref_a, ref_b)
