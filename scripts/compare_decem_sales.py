import json
from collections import Counter
from pathlib import Path


def main():
    rep_path = Path("replays/episode-114621874-replay.json")
    with rep_path.open(encoding="utf-8") as fp:
        rep = json.load(fp)

    steps = rep["steps"]

    our_sales = Counter()
    our_units = Counter()
    dec_sales = Counter()
    dec_units = Counter()

    for s in steps:
        # Our bot (Seat 0)
        for o in s[0].get("action", {}).get("market", []):
            if len(o) >= 3 and o[0] == "SELL":
                item, qty = o[1], int(o[2])
                price = s[0]["observation"]["market"]["prices"].get(item, 0)
                our_sales[item] += qty * price
                our_units[item] += qty
        # DECEM (Seat 1)
        for o in s[1].get("action", {}).get("market", []):
            if len(o) >= 3 and o[0] == "SELL":
                item, qty = o[1], int(o[2])
                price = s[1]["observation"]["market"]["prices"].get(item, 0)
                dec_sales[item] += qty * price
                dec_units[item] += qty

    all_items = sorted(
        set(our_sales.keys()) | set(dec_sales.keys()),
        key=lambda x: dec_sales[x],
        reverse=True,
    )
    print(
        f"{'Item':12s} | {'Our Units':9s} {'Our Rev':10s} | "
        f"{'DECEM Units':11s} {'DECEM Rev':10s} | {'Rev Diff':10s}"
    )
    print("-" * 65)
    for item in all_items:
        o_u, o_r = our_units[item], our_sales[item]
        d_u, d_r = dec_units[item], dec_sales[item]
        diff = d_r - o_r
        print(f"{item:12s} | {o_u:9d} ${o_r:9,d} | {d_u:11d} ${d_r:9,d} | {diff:+10,d}")

    print("-" * 65)
    t_ou, t_or = sum(our_units.values()), sum(our_sales.values())
    t_du, t_dr = sum(dec_units.values()), sum(dec_sales.values())
    tot_diff = t_dr - t_or
    print(
        f"{'TOTAL':12s} | {t_ou:9d} ${t_or:9,d} | "
        f"{t_du:11d} ${t_dr:9,d} | {tot_diff:+10,d}"
    )


if __name__ == "__main__":
    main()
