#!/usr/bin/env python3
"""Build a deterministic submission archive for the Meta V4 package.

Mirrors the archive convention used by the Prvsiyan packages: fixed mtime,
fixed uid/gid, sorted member order, so the resulting tarball hash is
reproducible across machines and can be recorded in the experiment ledger.
"""

import hashlib
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PKG = ROOT / "meta_v4_package"
OUT = ROOT / "meta_v4_submission.tar.gz"

MEMBERS = ["main.py", "LICENSE.txt", "NOTICE.txt"]
EXPECTED_MAIN_SHA256 = (
    "55be5d5f124c8daaaa63c1a29ba4aab096004909666f04748007603c67b7d2a8"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> str:
    main_digest = _sha256(PKG / "main.py")
    if main_digest != EXPECTED_MAIN_SHA256:
        raise SystemExit(
            "main.py has been modified; refusing to build.\n"
            f"  expected {EXPECTED_MAIN_SHA256}\n  actual   {main_digest}"
        )

    def _reset(info: tarfile.TarInfo) -> tarfile.TarInfo:
        info.mtime = 0
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        info.mode = 0o644
        return info

    if OUT.exists():
        OUT.unlink()
    # mtime=0 in the gzip header keeps the outer container reproducible too.
    with tarfile.open(OUT, "w:gz", compresslevel=9) as tf:
        tf.gzip = None  # type: ignore[attr-defined]
        for name in sorted(MEMBERS):
            tf.add(PKG / name, arcname=name, filter=_reset)
    return _sha256(OUT)


if __name__ == "__main__":
    digest = build()
    print(f"main.py   sha256 {EXPECTED_MAIN_SHA256}")
    print(f"archive   {OUT.name}")
    print(f"archive   sha256 {digest}")
