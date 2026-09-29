# Meta V4 submission package

Third-party agent adopted verbatim from the public Kaggriculture notebook
lineage. **`main.py` is byte-identical to the upstream payload** and is not
modified here.

| property | value |
| --- | --- |
| `main.py` SHA-256 | `55be5d5f124c8daaaa63c1a29ba4aab096004909666f04748007603c67b7d2a8` |
| upstream declared `EXPECTED_MAIN_SHA256` | identical (integrity confirmed) |
| license | Apache-2.0 (`LICENSE.txt`, `NOTICE.txt` preserved verbatim) |
| dependencies | Python stdlib only |
| measured latency | ~7.8 ms/step for both agents; overage budget untouched |

## Provenance

Recovered from the public notebook `demand-preserving-turn-sale-timing` using
an AST-based decoder that never executes untrusted code. The upstream
`NOTICE.txt` documents the full attribution chain (shiiin9 -> Ahmed Berat Ozer
-> Thomas Tschinkel -> Yusuke Hayashi -> aurax7, refresh by Dmitrii Gluzdov);
that file is shipped unchanged and is the authoritative attribution.

Our own Prvsiyan line descends from the same public chain.

## Why this package exists

Measured over 160 fresh-seed matches (both seats, 0 errors, all `DONE`):

| matchup | our win rate | median margin |
| --- | --- | --- |
| V2.1 vs this engine | 12.5% | -$689 |
| V3.1 vs this engine | 13.8% | -$846 |

Sign test p ~ 1.6e-12: the difference is not seed noise.

The public meta has converged. This payload and the separately published
`the-2965-master-hybrid-engine` / `top-2-master-engine-v4` produced **38/40
exact ties** head-to-head (the only two non-ties were +/-$116 on a single
seed), so the top of the leaderboard is effectively one shared engine.

## Verification

Rebuild the archive and confirm the payload hash is unchanged:

```bash
.venv/bin/python submission/build_meta_v4.py
shasum -a 256 submission/meta_v4_package/main.py
```
