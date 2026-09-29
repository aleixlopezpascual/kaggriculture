#!/usr/bin/env python3
"""Compile, verify, and package Prvsiyan V3 (Lot Metering) for Kaggle deployment.

Builds submission/prvsiyan_v3_submission.tar.gz with deterministic timestamps,
verifies component SHA-256 hashes, unpacks in a temp environment, and runs
full 720-turn simulation validation with monotonic latency profiling.
"""

import hashlib
import io
import json
import tarfile
import tempfile
import time
from pathlib import Path

import kaggle_environments

EXPECTED_HASHES = {
    "baseline.py": "178ae0f727641cf4b618ebb98ade7aa1a1bed7517281aab9849de82a59d8ed3a",
    "optimizer.py": "6d86d0bce7a3a40e2913b06c727816bbcce09e76531059e5bd344919d30cfb59",
    "meter.py": "a4403a92d3274ed8aef7fd9413e86747a1573613ec83f74bcd8748e71e60ac71",
}


def build_and_verify_v3_package():
    pkg_dir = Path("submission/prvsiyan_v3_package").resolve()
    assert pkg_dir.is_dir(), f"Missing package directory: {pkg_dir}"

    print("1. Verifying component integrity...")
    for filename, expected_hash in EXPECTED_HASHES.items():
        file_path = pkg_dir / filename
        assert file_path.is_file(), f"Missing {filename}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert (
            actual_hash == expected_hash
        ), f"Hash mismatch for {filename}: expected {expected_hash}, got {actual_hash}"
        print(f"  ✓ {filename:14s}: {actual_hash[:16]}... (MATCH)")

    for doc in ["main.py", "LICENSE.txt", "NOTICE.txt"]:
        assert (pkg_dir / doc).is_file(), f"Missing {doc}"
        print(f"  ✓ {doc:14s}: present")

    tar_out_path = Path("submission/prvsiyan_v3_submission.tar.gz").resolve()
    print(f"\n2. Building deterministic tarball: {tar_out_path}...")

    tar_files = [
        "main.py",
        "baseline.py",
        "optimizer.py",
        "meter.py",
        "LICENSE.txt",
        "NOTICE.txt",
    ]

    with (
        tar_out_path.open("wb") as f_out,
        tarfile.open(fileobj=f_out, mode="w:gz", format=tarfile.GNU_FORMAT) as tar,
    ):
        for fname in tar_files:
            fpath = pkg_dir / fname
            data = fpath.read_bytes()
            ti = tarfile.TarInfo(name=fname)
            ti.size = len(data)
            ti.mtime = 0
            ti.mode = 0o644
            ti.uid = 0
            ti.gid = 0
            ti.uname = "root"
            ti.gname = "root"
            tar.addfile(ti, io.BytesIO(data))

    tar_hash = hashlib.sha256(tar_out_path.read_bytes()).hexdigest()
    tar_size = tar_out_path.stat().st_size
    print(f"  ✓ Archive created: {tar_size:,} bytes")
    print(f"  ✓ Archive SHA-256: {tar_hash}")

    print("\n3. Testing container unpack & full 720-step simulation...")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        with tarfile.open(tar_out_path, "r:gz") as tar:
            tar.extractall(tmp_path, filter="data")

        extracted_main = tmp_path / "main.py"
        assert extracted_main.is_file(), "main.py not extracted"

        env = kaggle_environments.make(
            "kaggriculture", configuration={"seed": 848617604}
        )
        opp_path = str(
            Path("competitors/notebooks/shepherd_sovereign_main.py").resolve()
        )

        t0 = time.perf_counter()
        steps = env.run([str(extracted_main.resolve()), opp_path])
        total_match_time = time.perf_counter() - t0

        r0 = steps[-1][0]["reward"]
        r1 = steps[-1][1]["reward"]
        s0 = steps[-1][0]["status"]
        s1 = steps[-1][1]["status"]

        assert s0 == "DONE", f"Player 0 status: {s0}"
        assert s1 == "DONE", f"Player 1 status: {s1}"
        assert r0 > 50000, f"Player 0 score unexpectedly low: {r0}"

        ms_per_turn = total_match_time * 1000.0 / 720.0
        print(
            f"  ✓ Full match complete: 720 steps in {total_match_time:.2f}s "
            f"(~{ms_per_turn:.2f}ms/turn)"
        )
        print(f"  ✓ P0 (V3): ${r0:,.0f} ({s0}) vs Shepherd: ${r1:,.0f} ({s1})")

    receipt = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        "archive_path": str(tar_out_path),
        "archive_bytes": tar_size,
        "archive_sha256": tar_hash,
        "components": {
            k: hashlib.sha256((pkg_dir / k).read_bytes()).hexdigest() for k in tar_files
        },
        "simulation_validation": {
            "seed": 848617604,
            "status": s0,
            "reward": r0,
            "opponent": "Shepherd Sovereign",
            "opponent_reward": r1,
            "elapsed_sec": total_match_time,
            "avg_ms_per_turn": total_match_time * 1000.0 / 720.0,
        },
    }

    receipt_path = Path("submission/prvsiyan_v3_build_receipt.json")
    with receipt_path.open("w", encoding="utf-8") as fp:
        json.dump(receipt, fp, indent=2)

    print(f"\n✓ Build receipt saved to: {receipt_path}")
    print("\nPrvsiyan V3 archive is fully compiled, verified, and deployment-ready.")


if __name__ == "__main__":
    build_and_verify_v3_package()
