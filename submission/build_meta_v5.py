#!/usr/bin/env python3
"""Build the Meta V5 package: frozen Meta V4 payload + Step1010 anti-idle layer.

Research basis (Phase 13). Across six top-agent replays the winning seat idled
1.8-4.5% of hand-turns while the losing seat idled 6.3-10.0%; the separation was
6/6. Our Meta V4 idles 6.7% and its whole fingerprint matches the losing seat.
Meanwhile the georgymamarin episode corpus shows every rating band from 1900 to
2700+ now shares an identical coarse fingerprint (tiles 239, wheat 154, carrot 40,
melon 12, crew 12 over the last seven days), so the remaining spread is in
micro-execution rather than strategy.

Step1010 therefore converts idle hand-turns into work that is legal at the hand's
own tile. It never displaces an action the parent engine chose: it only ever
rewrites PASS.

The Meta V4 payload is never edited. This script concatenates the frozen file with
the patch text, so provenance stays verifiable by hash.
"""

import hashlib
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "meta_v4_package" / "main.py"
PKG = ROOT / "meta_v5_package"
TAR = ROOT / "meta_v5_submission.tar.gz"
EXPECTED_V4_SHA256 = "55be5d5f124c8daaaa63c1a29ba4aab096004909666f04748007603c67b7d2a8"

PATCH = '''

# ---------------------------------------------------------------------------
# Step1010: anti-idle hand layer (Phase 13).
#
# Only rewrites hand slots whose action is PASS, and only to an action that is
# legal on the tile the hand already occupies -- no movement, no inventory
# assumptions beyond what the observation reports. Any failure falls back to the
# parent action unchanged.
# ---------------------------------------------------------------------------
_S1010_PARENT = agent
_S1010_REPORT = {'calls': 0, 'changed': 0, 'filled': 0, 'errors': 0}
_S1010_ENABLED = True


def _s1010_tile_at(farm, pos):
    """Return the tile dict under ``pos``, or None when off-grid/empty."""
    try:
        tiles = farm.get('tiles')
        r, c = int(pos[0]), int(pos[1])
        if r < 0 or c < 0 or r >= len(tiles):
            return None
        row = tiles[r]
        if c >= len(row):
            return None
        t = row[c]
        return t if isinstance(t, dict) else None
    except Exception:
        return None


# Default is 'safe' (water + upkeep). The 'harvest' branch is retained only so
# the Phase 13 ablation stays reproducible: opportunistic harvesting lost 0-48
# because yield_units > 0 means "has some yield", not "is at max yield".
_S1010_MODE = __import__('os').environ.get('S1010_MODE', 'safe')


def _s1010_work_for(tile, day):
    """Best legal zero-movement action on ``tile``, or None.

    Ordered by marginal value: realising yield first, then protecting yield,
    then the upkeep actions that feed the fertiliser loop.
    """
    if not tile:
        return None
    kind = tile.get('kind')
    if kind == 'PLANT':
        try:
            if float(tile.get('yield_units') or 0) > 0:
                if _S1010_MODE in ('all', 'harvest'):
                    return ['HARVEST']
        except Exception:
            pass
        if not tile.get('watered_today') and _S1010_MODE in ('all', 'water', 'safe'):
            return ['WATER']
        return None
    if kind in ('PASTURE', 'COOP'):
        if not tile.get('animal'):
            return None
        if _S1010_MODE not in ('all', 'upkeep', 'safe'):
            return None
        if tile.get('fertilizer_available'):
            return ['COLLECT_FERTILIZER']
        if not tile.get('cared_today'):
            return ['CARE']
    return None


def step1010_antiidle_agent(observation, configuration=None):
    if int(observation.get('step', 0)) == 0:
        _S1010_REPORT.update(calls=0, changed=0, filled=0, errors=0)
    _S1010_REPORT['calls'] += 1
    action = _S1010_PARENT(observation, configuration)
    if not _S1010_ENABLED:
        return action
    try:
        hands = action.get('hands')
        if not isinstance(hands, list) or not hands:
            return action
        if not any(isinstance(h, list) and h and h[0] == 'PASS' for h in hands):
            return action

        me = int(observation.get('player', 0))
        farm = observation['farms'][me]
        positions = farm.get('hands') or []
        day = int(observation.get('day', 0))

        # One hand per tile: two hands harvesting the same square wastes the
        # second, so claim tiles as they are assigned.
        claimed = set()
        for idx, h in enumerate(hands):
            if isinstance(h, list) and h and h[0] != 'PASS' and idx < len(positions):
                try:
                    claimed.add((int(positions[idx][0]), int(positions[idx][1])))
                except Exception:
                    pass

        out = list(hands)
        changed = False
        for idx, h in enumerate(hands):
            if not (isinstance(h, list) and h and h[0] == 'PASS'):
                continue
            if idx >= len(positions):
                continue
            try:
                key = (int(positions[idx][0]), int(positions[idx][1]))
            except Exception:
                continue
            if key in claimed:
                continue
            work = _s1010_work_for(_s1010_tile_at(farm, positions[idx]), day)
            if work is None:
                continue
            out[idx] = work
            claimed.add(key)
            changed = True
            _S1010_REPORT['filled'] += 1

        if not changed:
            return action

        result = dict(action)
        result['hands'] = out
        _S1010_REPORT['changed'] += 1
        # Mirror the Step1009 convention: the engine tracks the action it
        # believes it played, so the rewritten action must be written back.
        try:
            st = _RACE_STATE.get(me)
            if (st is not None and st.get('prev_action') is not None
                    and st.get('step') == int(observation.get('step', 0))):
                st['prev_action'] = result
        except Exception:
            pass
        return result
    except Exception:
        _S1010_REPORT['errors'] += 1
        return action


step1010_antiidle_agent.telemetry = _S1010_REPORT
agent = step1010_antiidle_agent
kaggle_submission_agent = agent
'''


def build() -> str:
    src = SRC.read_bytes()
    digest = hashlib.sha256(src).hexdigest()
    if digest != EXPECTED_V4_SHA256:
        raise SystemExit(
            "meta_v4_package/main.py has been modified; refusing to build.\n"
            f"  expected {EXPECTED_V4_SHA256}\n  actual   {digest}"
        )
    PKG.mkdir(exist_ok=True)
    out = PKG / "main.py"
    out.write_bytes(src + PATCH.encode())
    for name in ("LICENSE.txt", "NOTICE.txt"):
        srcf = ROOT / "meta_v4_package" / name
        if srcf.exists():
            (PKG / name).write_bytes(srcf.read_bytes())
    return hashlib.sha256(out.read_bytes()).hexdigest()


def archive() -> str:
    """Pack the deterministic submission tarball, matching the V4 convention."""

    def _reset(info: tarfile.TarInfo) -> tarfile.TarInfo:
        info.mtime = 0
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        info.mode = 0o644
        return info

    if TAR.exists():
        TAR.unlink()
    with tarfile.open(TAR, "w:gz", compresslevel=9) as tf:
        tf.gzip = None  # type: ignore[attr-defined]
        for name in sorted(["main.py", "LICENSE.txt", "NOTICE.txt"]):
            p = PKG / name
            if p.exists():
                tf.add(p, arcname=name, filter=_reset)
    return hashlib.sha256(TAR.read_bytes()).hexdigest()


if __name__ == "__main__":
    print(f"v4 payload sha256 {EXPECTED_V4_SHA256}")
    print(f"v5 main.py sha256 {build()}")
    print(f"v5 archive        {TAR.name}")
    print(f"v5 archive sha256 {archive()}")
